"""Library package for Docling pipeline utilities."""
from .canonical import (
    jcs_canonical_bytes,
    sha256_hex,
    hash_canonical_without_integrity,
    append_to_ledger
)
from .normalize import (
    normalize_text,
    l2_normalize
)

__all__ = [
    # Canonical
    "jcs_canonical_bytes",
    "sha256_hex",
    "hash_canonical_without_integrity",
    "append_to_ledger",
    # Normalize
    "normalize_text",
    "l2_normalize",
]

__all__ = [
    # Canonical
    "jcs_canonical_bytes",
    "sha256_hex",
    "hash_canonical",
    "hash_canonical_without_integrity",
    "compute_doc_id",
    "compute_chunk_id",
    # Ledger
    "Ledger",
    "get_ledger",
    # Normalize
    "normalize_unicode",
    "collapse_whitespace",
    "normalize_line_endings",
    "normalize_text",
    "stable_block_sort_key",
    "serialize_table_row_major",
]
