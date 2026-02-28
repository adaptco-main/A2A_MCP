"""
Docling Core Libraries.
Provides unified access to canonicalization, normalization, and ledger utilities.
"""
from .canonical import (
    jcs_canonical_bytes,
    sha256_hex,
    hash_canonical_without_integrity,
    append_to_ledger,
    compute_chunk_id,
    compute_doc_id
)
from .normalize import (
    normalize_text,
    l2_normalize,
    normalize_unicode,
    collapse_whitespace
)
from .ledger import (
    Ledger,
    get_ledger
)

__all__ = [
    "jcs_canonical_bytes",
    "sha256_hex",
    "hash_canonical_without_integrity",
    "append_to_ledger",
    "compute_chunk_id",
    "compute_doc_id",
    "normalize_text",
    "l2_normalize",
    "normalize_unicode",
    "collapse_whitespace",
    "Ledger",
    "get_ledger"
]
