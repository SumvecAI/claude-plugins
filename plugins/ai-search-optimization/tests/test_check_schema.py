"""Tests for scripts/check_schema.py — Python stdlib only (unittest)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Make scripts/ importable
SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "ai-search-optimization" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import check_schema  # noqa: E402


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------

# Mirrors what catalognow.ai (and many Next.js sites) emit: a single
# JSON-LD block containing an @graph array. The root has no @type;
# entities live inside @graph.
GRAPH_PAGE = """
<!DOCTYPE html>
<html><head>
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {"@type": "WebSite", "url": "https://example.com", "name": "Example"},
    {"@type": "Organization", "name": "Example Inc", "url": "https://example.com"},
    {"@type": "SoftwareApplication", "name": "ExampleApp",
     "applicationCategory": "BusinessApplication"},
    {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
  ]
}
</script>
</head><body></body></html>
"""

TRADITIONAL_PAGE = """
<script type="application/ld+json">
{"@type":"Article","headline":"Hi","author":"X","image":"y","datePublished":"2026-01-01"}
</script>
"""

TOP_LEVEL_ARRAY_PAGE = """
<script type="application/ld+json">
[
  {"@type":"Article","headline":"x","author":"y","image":"z","datePublished":"2026-01-01"},
  {"@type":"Person","name":"y"}
]
</script>
"""


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

class TestJsonLdExtractor(unittest.TestCase):

    def _types_for(self, html: str) -> list:
        extractor = check_schema._JsonLdExtractor()
        extractor.feed(html)
        return [check_schema.get_type(b.get("data")) for b in extractor.blocks if "data" in b]

    def test_at_graph_pattern_unpacks_entities(self):
        """@graph containers must expand into their child entities.

        Regression test for the v2.0.0 bug where check_schema reported
        '@type: (missing)' for any page using the standard @graph wrapper
        (every Next.js site, plus many CMS-generated pages).
        """
        types = self._types_for(GRAPH_PAGE)
        self.assertIn("WebSite", types, f"WebSite missing from {types}")
        self.assertIn("Organization", types, f"Organization missing from {types}")
        self.assertIn("SoftwareApplication", types, f"SoftwareApplication missing from {types}")
        self.assertIn("Offer", types, f"Offer missing from {types}")
        self.assertNotIn(
            None, types,
            f"@graph container leaked through as a typeless entity: {types}",
        )

    def test_traditional_root_type_still_works(self):
        """Pages with a plain root @type must continue to parse as one entity."""
        self.assertEqual(self._types_for(TRADITIONAL_PAGE), ["Article"])

    def test_top_level_array_still_works(self):
        """Top-level JSON arrays must continue to parse one entity per item."""
        self.assertEqual(self._types_for(TOP_LEVEL_ARRAY_PAGE), ["Article", "Person"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
