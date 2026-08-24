"""shopify-ai-agent.

Read a Shopify products CSV export and enrich each product (SEO title, meta
description, tags) using a pluggable LLM provider. The core is pure stdlib so it
runs without the live API; a MockProvider produces deterministic output for
tests/offline use, and an OpenAI-compatible provider can be swapped in.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class Product:
    handle: str = ""
    title: str = ""
    body_html: str = ""
    vendor: str = ""
    product_type: str = ""
    tags: str = ""
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    suggested_tags: List[str] = field(default_factory=list)

    @classmethod
    def from_row(cls, row: dict) -> "Product":
        return cls(
            handle=(row.get("Handle") or "").strip(),
            title=(row.get("Title") or "").strip(),
            body_html=(row.get("Body (HTML)") or "").strip(),
            vendor=(row.get("Vendor") or "").strip(),
            product_type=(row.get("Product Category") or row.get("Type") or "").strip(),
            tags=(row.get("Tags") or "").strip(),
        )


def read_products(path: str | Path) -> List[Product]:
    """Read a Shopify products CSV export into Product objects."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return [Product.from_row(r) for r in reader if (r.get("Handle") or "").strip()]


class LLMProvider:
    """Pluggable text generator. Subclasses implement ``generate``."""

    name = "base"

    def generate(self, prompt: str) -> str:  # pragma: no cover - abstract
        raise NotImplementedError


class MockProvider(LLMProvider):
    name = "mock"

    def generate(self, prompt: str) -> str:
        title = "(unknown)"
        for line in prompt.splitlines():
            if line.startswith("Title:"):
                title = line.split(":", 1)[1].strip()
        safe = title[:60]
        return json.dumps(
            {
                "seo_title": f"{safe} — Premium Quality | Shop",
                "seo_description": f"Discover {safe}. Free shipping over 400 MAD. Authentic quality, fast delivery.",
                "tags": ["premium", "bestseller", "fast-shipping"],
            }
        )


def _parse(raw: str) -> dict:
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model response did not contain JSON.")
    return json.loads(cleaned[start : end + 1])


def build_prompt(p: Product) -> str:
    return "\n".join(
        [
            "You are a Shopify SEO copywriter. Return ONLY valid JSON with keys:",
            "seo_title (string), seo_description (string, <=160 chars), tags (array of strings).",
            "",
            f"Title: {p.title or '(unknown)'}",
            f"Type: {p.product_type or '(unknown)'}",
            f"Vendor: {p.vendor or '(unknown)'}",
            f"Current tags: {p.tags or '(none)'}",
            f"Body: {p.body_html[:300] or '(none)'}",
        ]
    )


def enrich(product: Product, provider: LLMProvider) -> Product:
    out = _parse(provider.generate(build_prompt(product)))
    product.seo_title = str(out.get("seo_title") or product.title)
    product.seo_description = str(out.get("seo_description") or "")
    product.suggested_tags = [str(t) for t in out.get("tags", [])]
    return product


def enrich_all(products: Iterable[Product], provider: LLMProvider) -> List[Product]:
    return [enrich(p, provider) for p in products]


def to_csv(products: List[Product], path: str | Path) -> None:
    """Write enriched products to a CSV (overwrites)."""
    cols = ["Handle", "Title", "Body (HTML)", "Vendor", "Product Type",
            "Tags", "SEO Title", "SEO Description", "Suggested Tags"]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for p in products:
            w.writerow([
                p.handle, p.title, p.body_html, p.vendor, p.product_type,
                p.tags, p.seo_title or "", p.seo_description or "",
                ",".join(p.suggested_tags),
            ])
