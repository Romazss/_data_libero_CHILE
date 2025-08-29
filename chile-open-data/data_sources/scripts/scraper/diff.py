from __future__ import annotations
import hashlib
from dataclasses import dataclass

def sha1(content: bytes) -> str:
    return hashlib.sha1(content).hexdigest()

@dataclass
class PageSnapshot:
    url: str
    sha1: str
