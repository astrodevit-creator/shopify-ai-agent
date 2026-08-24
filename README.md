# shopify-ai-agent

Read a Shopify **products CSV export** and enrich each product — SEO title,
meta description, and tags — using a pluggable LLM provider. Core is pure Python
standard library (no heavy deps); a `MockProvider` gives deterministic,
offline output for tests and demos, and an OpenAI-compatible provider can be
swapped in for live generation.

> Original project.

## Features

- Parse Shopify product CSV exports (Handles, Titles, Body, Vendor, Type, Tags).
- Enrich with SEO title / meta description / suggested tags.
- Pluggable `LLMProvider` (Mock + OpenAI-compatible ready).
- Batch enrich and write a new CSV.

## Usage

```python
from shopify_agent import read_products, enrich_all, MockProvider, to_csv

products = read_products("products_export.csv")
enriched = enrich_all(products, MockProvider())
to_csv(enriched, "products_enriched.csv")
```

## Testing

```bash
pip install -e .
pytest
```

## License

MIT — see [LICENSE](LICENSE).

---

## Links

- 🌐 Website: [huggehub.com](https://www.huggehub.com)
- 💻 GitHub: [@astrodevit-creator](https://github.com/astrodevit-creator)
- 🔗 LinkedIn: _(add your profile URL)_
