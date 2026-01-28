import unicodedata
import re
import torch
from typing import List

def normalize_text(text: str) -> str:
    """
    Normalize text: NFKC, collapse multiple whitespaces, and standard LF endings.
    """
    # NFKC normalization
    text = unicodedata.normalize("NFKC", text)
    # Standardize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # Remove leading/trailing space per line
    text = "\n".join(line.strip() for line in text.split("\n"))
    # Collapse multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def l2_normalize(x: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    """
    L2 normalize a batch of tensors along the last dimension.
    Formula: x / max(norm(x), eps)
    """
    norm = torch.norm(x, p=2, dim=-1, keepdim=True)
    return x / torch.clamp(norm, min=eps)
