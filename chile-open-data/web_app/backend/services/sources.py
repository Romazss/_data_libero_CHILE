# /web_app/backend/services/sources.py
from pathlib import Path
import yaml

# Ruta corregida para encontrar sources.yaml desde el backend
DEFAULT_SOURCES_PATH = Path(__file__).resolve().parents[3] / "data_sources" / "config" / "sources.yaml"

class SourceConfigError(Exception):
    pass

def load_sources(path: Path = DEFAULT_SOURCES_PATH) -> list[dict]:
    """Carga y valida el YAML de fuentes."""
    if not path.exists():
        raise SourceConfigError(f"No se encontró sources.yaml en {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    datasets = data.get("datasets", [])
    if not isinstance(datasets, list) or not datasets:
        raise SourceConfigError("El YAML debe contener una lista 'datasets' no vacía.")

    required = {"id", "name", "category", "url"}
    for ds in datasets:
        missing = required - set(ds.keys())
        if missing:
            raise SourceConfigError(f"Dataset con campos faltantes: {missing} en {ds}")
        ds.setdefault("method", "HEAD")
        ds.setdefault("timeout", 6)
    return datasets
