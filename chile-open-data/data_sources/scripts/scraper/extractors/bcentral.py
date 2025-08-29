from __future__ import annotations
from typing import List
from .generic_table import GenericTableExtractor
from ..schema import Source

def run() -> List[Source]:
    extractor = GenericTableExtractor(
        base_url="https://www.bcentral.cl/estadisticas",  # TODO: ajusta con la URL concreta
        source_id="bcentral_catalogo",
        name="Catálogo Banco Central de Chile",
        domain="www.bcentral.cl",
        category="economía",
        description="Recursos del catálogo del Banco Central de Chile",
        row_selectors=[".dataset-item", "table tr", "ul.datasets li"],
        title_selectors=[".dataset-title", "a", "td:nth-child(1)"],
        link_selectors=[
            "a[href*='.csv'], a[href*='.xlsx'], a[href*='.xls'], a[href*='.json'], a[href*='.zip'], a[href*='/series/']"
        ]
    )
    return extractor.run()
