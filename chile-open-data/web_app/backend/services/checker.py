# /web_app/backend/services/checker.py
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import time
import requests

@dataclass
class CheckResult:
    id: str
    name: str
    category: str
    url: str
    status: str         # "up" | "down" | "unknown"
    http_code: int | None
    latency_ms: float | None
    error: str | None

def _check_one(ds: dict) -> CheckResult:
    method = ds.get("method", "HEAD").upper()
    timeout = float(ds.get("timeout", 6))
    url = ds["url"]
    t0 = time.perf_counter()
    try:
        # Preferimos HEAD para rapidez; si falla, intentamos GET liviano.
        if method == "HEAD":
            resp = requests.head(url, timeout=timeout, allow_redirects=True)
            if resp.status_code >= 400:
                # fallback a GET por si el servidor no implementa HEAD correctamente
                resp = requests.get(url, timeout=timeout, stream=True)
        else:
            resp = requests.get(url, timeout=timeout, stream=True)

        latency = (time.perf_counter() - t0) * 1000
        status = "up" if 200 <= resp.status_code < 400 else "down"
        # cerrar stream si corresponde
        try:
            resp.close()
        except Exception:
            pass
        return CheckResult(
            id=ds["id"],
            name=ds["name"],
            category=ds["category"],
            url=url,
            status=status,
            http_code=resp.status_code,
            latency_ms=round(latency, 1),
            error=None
        )
    except Exception as e:
        latency = (time.perf_counter() - t0) * 1000
        return CheckResult(
            id=ds["id"],
            name=ds["name"],
            category=ds["category"],
            url=url,
            status="down",
            http_code=None,
            latency_ms=round(latency, 1),
            error=str(e.__class__.__name__)
        )

def check_all(datasets: list[dict], max_workers: int = 8) -> list[dict]:
    """Chequea todos los datasets en paralelo y devuelve lista de dicts serializables."""
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_check_one, ds): ds["id"] for ds in datasets}
        for fut in as_completed(futures):
            r: CheckResult = fut.result()
            results.append({
                "id": r.id,
                "name": r.name,
                "category": r.category,
                "url": r.url,
                "status": r.status,
                "http_code": r.http_code,
                "latency_ms": r.latency_ms,
                "error": r.error
            })
    # ordenemos por categoría y nombre para una UI estable
    results.sort(key=lambda x: (x["category"], x["name"]))
    return results