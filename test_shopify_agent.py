import csv
import os
from pathlib import Path

import pytest

from shopify_agent import (
    MockProvider,
    Product,
    enrich,
    enrich_all,
    read_products,
    to_csv,
)

HERE = Path(__file__).parent
SAMPLE = HERE / "sample_products.csv"


@pytest.fixture
def products():
    return read_products(SAMPLE)


def test_read_products_parses_rows(products):
    assert len(products) == 2
    assert products[0].handle == "aerolite-shoes"
    assert products[0].title == "Aerolite Running Shoes"


def test_enrich_with_mock_sets_fields(products):
    p = enrich(products[0], MockProvider())
    assert p.seo_title and "Aerolite" in p.seo_title
    assert p.seo_description
    assert isinstance(p.suggested_tags, list) and len(p.suggested_tags) > 0


def test_enrich_all(products):
    out = enrich_all(products, MockProvider())
    assert all(p.seo_title for p in out)


def test_to_csv_roundtrip(products, tmp_path):
    out = tmp_path / "out.csv"
    to_csv(enrich_all(products, MockProvider()), out)
    assert out.exists()
    rows = list(csv.DictReader(open(out, encoding="utf-8")))
    assert len(rows) == 2
    assert rows[0]["SEO Title"]
