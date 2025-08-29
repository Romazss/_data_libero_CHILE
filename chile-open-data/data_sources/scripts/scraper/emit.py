from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from typing import List
import yaml
from .schema import Source, SourcesFile

def load_existing(path: Path) -> SourcesFile | None:
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SourcesFile.model_validate(data)

def write_sources(path: Path, existing: SourcesFile | None, new_sources: List[Source]) -> None:
    all_sources = {s.id: s for s in (existing.sources if existing else [])}
    for s in new_sources:
        all_sources[s.id] = s  # upsert por id

    final = SourcesFile(
        version=1,
        updated_at=datetime.now(timezone.utc),
        sources=sorted(all_sources.values(), key=lambda s: (s.domain, s.id))
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml.safe_dump(
        final.model_dump(mode="json"),
        path.open("w", encoding="utf-8"),
        allow_unicode=True,
        sort_keys=False,
        width=1000,
        default_flow_style=False,
    )
