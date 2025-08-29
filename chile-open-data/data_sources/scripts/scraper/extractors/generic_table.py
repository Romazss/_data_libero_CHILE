from __future__ import annotations
from bs4 import BeautifulSoup
from typing import List
from urllib.parse import urljoin
from ..fetch import HttpClient
from ..schema import Source, Resource

class GenericTableExtractor:
    def __init__(self, *, base_url: str, source_id: str, name: str, domain: str,
                 category: str, description: str | None = None,
                 row_selectors: list[str] = None,
                 title_selectors: list[str] = None,
                 link_selectors: list[str] = None):
        self.client = HttpClient()
        self.base_url = base_url
        self.source_id = source_id
        self.name = name
        self.domain = domain
        self.category = category
        self.description = description
        self.row_selectors = row_selectors or ["table tr", "ul li", ".dataset-item"]
        self.title_selectors = title_selectors or ["th", ".title", "a", "td"]
        self.link_selectors = link_selectors or ["a[href]"]

    def run(self) -> List[Source]:
        resp = self.client.get(self.base_url)
        soup = BeautifulSoup(resp.text, "lxml")

        rows = []
        for sel in self.row_selectors:
            rows = soup.select(sel)
            if rows:
                break

        resources: list[Resource] = []
        for r in rows:
            title_txt = None
            for ts in self.title_selectors:
                el = r.select_one(ts)
                if el and el.get_text(strip=True):
                    title_txt = el.get_text(" ", strip=True)
                    break

            link = None
            for ls in self.link_selectors:
                a = r.select_one(ls)
                if a and a.get("href"):
                    link = urljoin(self.base_url, a["href"])
                    break

            if not link:
                continue

            fmt = link.split("?")[0].split("#")[0].split(".")[-1].lower()
            if fmt not in {"csv", "xlsx", "xls", "json", "zip", "xml"}:
                fmt = "html"

            resources.append(Resource(title=title_txt or "Recurso", download_url=link, format=fmt))

        if not resources:
            raise RuntimeError(f"[GenericTableExtractor] No se encontraron recursos en {self.base_url}")

        src = Source(
            id=self.source_id,
            name=self.name,
            domain=self.domain,
            category=self.category,
            description=self.description,
            resources=resources
        )
        return [src]
