from __future__ import annotations
import time, random
from typing import Optional
import requests

DEFAULT_HEADERS = {
    "User-Agent": "BibliotecaDatosCL/1.0 (+https://github.com/tu-org/tu-repo)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

class HttpClient:
    def __init__(self, timeout: float = 15.0, max_retries: int = 3, backoff: float = 0.8):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def get(self, url: str, *, headers: Optional[dict] = None) -> requests.Response:
        last_exc = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout, headers=headers)
                if 500 <= resp.status_code < 600:
                    raise requests.HTTPError(f"{resp.status_code} server error")
                return resp
            except Exception as e:
                last_exc = e
                sleep_s = (self.backoff ** attempt) + random.uniform(0, 0.3)
                time.sleep(sleep_s)
        raise RuntimeError(f"GET failed after {self.max_retries} retries: {url}") from last_exc
