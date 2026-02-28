"""
Embed Worker - Creates embeddings for batches of chunks using PyTorch and stores in Qdrant.
"""
import os
import sys
from typing import List
import torch
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from redis import Redis
from rq import Queue, Worker

# Add parent paths for imports
sys.path.insert(0, "/app")
from lib import (
    compute_chunk_id,
    get_ledger,
    hash_canonical_without_integrity
)
from lib.normalize import l2_normalize
from schemas import ChunkEmbeddingV1, Chunker, Embedding, Provenance

from sentence_transformers import SentenceTransformer

# Configuration from environment
EMBEDDER_MODEL_ID = os.environ.get("EMBEDDER_MODEL_ID", "all-MiniLM-L6-v2")
CHUNKER_VERSION = os.environ.get("CHUNKER_VERSION", "chunk.v1")
WEIGHTS_HASH = os.environ.get("WEIGHTS_HASH", "sha256:unknown")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
COLLECTION_NAME = "document_chunks"
EMBEDDING_DIM = 384 # MiniLM-L6-v2 dimension

redis_conn = Redis.from_url(REDIS_URL)
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Initialize model
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer(EMBEDDER_MODEL_ID, device=device)

# Ensure collection exists
try:
    qdrant_client.get_collection(COLLECTION_NAME)
except Exception:
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )


class ChunkDataset(torch.utils.data.Dataset):
    """PyTorch Dataset for document chunks."""
    def __init__(self, texts: List[str]):
        self.texts = texts

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        return self.texts[idx]


def get_embeddings(texts: List[str]) -> torch.Tensor:
    """
    Generate embeddings for a batch of texts using SentenceTransformers.
    """
    embeddings = model.encode(
        texts, 
        convert_to_tensor=True, 
        show_progress_bar=False,
        normalize_embeddings=True # This performs L2 normalization
    )
    return embeddings


def embed_batch(job_payload: dict) -> dict:
    """
    Process a batch of chunks: embed, store in Qdrant, and update ledger.
    """
    batch = job_payload["batch"]
    texts = [c["chunk_text"] for c in batch]
    
    # Generate all embeddings in one vectorized pass using DataLoader logic
    vectors = get_embeddings(texts).tolist()
    
    points = []
    ledger_records = []
    bundle_id = batch[0]["bundle_id"]
    ledger = get_ledger()
    
    for i, chunk_data in enumerate(batch):
        doc_id = chunk_data["doc_id"]
        chunk_index = chunk_data["chunk_index"]
        chunk_text = chunk_data["chunk_text"]
        source_block_refs = chunk_data.get("source_block_refs", [])
        vector = vectors[i]
        
        # Compute IDs and Integrity
        chunk_id = compute_chunk_id(doc_id, chunk_index, chunk_text)
        
        chunk_embedding = ChunkEmbeddingV1(
            doc_id=doc_id,
            chunk_id=chunk_id,
            chunk_text=chunk_text,
            chunker=Chunker(version=CHUNKER_VERSION),
            embedding=Embedding(
                framework="pytorch",
                model_id=EMBEDDER_MODEL_ID,
                weights_hash=WEIGHTS_HASH,
                dim=EMBEDDING_DIM,
                normalization="l2",
                vector=vector
            ),
            provenance=Provenance(source_block_refs=source_block_refs)
        )
        
        sha256_canonical = hash_canonical_without_integrity(
            chunk_embedding.model_dump(by_alias=True, exclude_none=True)
        )
        
        # Prepare Qdrant Point
        points.append(PointStruct(
            id=chunk_id.replace("sha256:", "")[:32],
            vector=vector,
            payload={
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "chunk_text": chunk_text[:500],
                "source_block_refs": source_block_refs
            }
        ))
        
        # Prepare Ledger Record
        ledger_records.append({
            "event": "chunk.embedding.v1",
            "bundle_id": bundle_id,
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "chunk_index": chunk_index,
            "embedder_model_id": EMBEDDER_MODEL_ID,
            "weights_hash": WEIGHTS_HASH,
            "content_hash": sha256_canonical
        })
    
    # Bulk Upsert to Qdrant
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    
    # Bulk Append to Ledger
    for record in ledger_records:
        ledger.append(record)
    
    return {
        "status": "batch_embedded",
        "batch_size": len(batch),
        "bundle_id": bundle_id
    }

if __name__ == "__main__":
    worker = Worker(
        queues=[Queue("embed_queue", connection=redis_conn)],
        connection=redis_conn
    )
    worker.work()
