from __future__ import annotations
from typing import Protocol, List
from .schema import Source

class Extractor(Protocol):
    domain: str
    def run(self) -> List[Source]:
        ...
