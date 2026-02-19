from __future__ import annotations

import hashlib
from typing import Union

BytesLike = Union[bytes, bytearray, memoryview]


def sha256_hex(data: BytesLike | str) -> str:
    payload = data.encode("utf-8") if isinstance(data, str) else bytes(data)
    return hashlib.sha256(payload).hexdigest()


def deterministic_seed(*parts: str) -> int:
    digest = sha256_hex("::".join(parts))
    return int(digest[:16], 16)
