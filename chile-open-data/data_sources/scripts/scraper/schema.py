from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, field_validator
from datetime import datetime

class Resource(BaseModel):
    title: str
    download_url: str
    format: str
    update_frequency: Optional[str] = None
    last_checked: Optional[datetime] = None
    status: Optional[str] = "unknown"
    checksum: Optional[str] = None

    @field_validator("format")
    @classmethod
    def fmt_lower(cls, v: str) -> str:
        return v.lower()

class Source(BaseModel):
    id: str
    name: str
    domain: str
    category: str
    description: Optional[str] = None
    resources: List[Resource]

class SourcesFile(BaseModel):
    version: int
    updated_at: datetime
    sources: List[Source]
