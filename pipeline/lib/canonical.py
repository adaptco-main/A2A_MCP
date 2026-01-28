import hashlib
import json
import os
from typing import Any, Dict

def jcs_canonical_bytes(obj: Any) -> bytes:
    """
    RFC8785-style JSON canonicalization.
    Ensures deterministic serialization for hashing.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")

def sha256_hex(b: bytes) -> str:
    """SHA256 hex digest."""
    return hashlib.sha256(b).hexdigest()

def hash_canonical_without_integrity(payload: Dict[str, Any]) -> str:
    """
    Strips 'integrity' field if present, hashes the canonical form,
    and returns the hex string.
    """
    data = payload.copy()
    data.pop("integrity", None)
    return sha256_hex(jcs_canonical_bytes(data))

def append_to_ledger(record: Dict[str, Any], ledger_path: str) -> str:
    """
    Appends a record to a JSONL ledger with a previous hash chain.
    Returns the new ledger hash.
    """
    prev_hash = "0" * 64
    
    if os.path.exists(ledger_path) and os.path.getsize(ledger_path) > 0:
        with open(ledger_path, "rb") as f:
            # Simple way to get last line hash
            f.seek(0, os.SEEK_END)
            pos = f.tell()
            while pos > 0:
                pos -= 1
                f.seek(pos)
                if f.read(1) == b"\n" and pos != os.path.getsize(ledger_path) - 1:
                    line = f.readline()
                    try:
                        last_record = json.loads(line)
                        prev_hash = last_record.get("ledger_hash", prev_hash)
                        break
                    except:
                        pass
            else:
                f.seek(0)
                line = f.readline()
                try:
                    last_record = json.loads(line)
                    prev_hash = last_record.get("ledger_hash", prev_hash)
                except:
                    pass

    record["prev_ledger_hash"] = prev_hash
    # Hashing the record itself as part of the chain
    record["ledger_hash"] = sha256_hex(jcs_canonical_bytes(record))
    
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
    return record["ledger_hash"]
