#!/usr/bin/env python3
"""
check_schema.py — Inspect JSON-LD on a URL and report types, key fields, and likely issues.

Usage:
    python check_schema.py <url>

Outputs Markdown to stdout. Designed to be pasted directly into an AISO audit report.

Dependencies: Python 3.9+ standard library only.
"""

from __future__ import annotations

import gzip
import json
import re
import ssl
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = "ai-search-optimization-skill/2.0 (+https://sumvec.ai)"
TIMEOUT = 15

# Per-type required and recommended fields. Sourced from Google's developer docs
# for rich results (developers.google.com/search/docs/appearance/structured-data/*).
TYPE_FIELDS: dict[str, dict[str, list[str]]] = {
    "Article": {
        "required": ["headline", "image", "datePublished", "author"],
        "recommended": ["dateModified", "publisher", "mainEntityOfPage", "description"],
    },
    "NewsArticle": {
        "required": ["headline", "image", "datePublished", "author"],
        "recommended": ["dateModified", "publisher", "description"],
    },
    "BlogPosting": {
        "required": ["headline", "image", "datePublished", "author"],
        "recommended": ["dateModified", "publisher", "description"],
    },
    "Product": {
        "required": ["name"],
        "recommended": [
            "image",
            "description",
            "brand",
            "offers",
            "aggregateRating",
            "review",
            "sku",
            "gtin13",
        ],
    },
    "FAQPage": {"required": ["mainEntity"], "recommended": []},
    "HowTo": {
        "required": ["name", "step"],
        "recommended": ["description", "image", "totalTime", "estimatedCost", "supply", "tool"],
    },
    "Organization": {
        "required": ["name", "url"],
        "recommended": ["logo", "sameAs", "contactPoint", "description"],
    },
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": ["telephone", "openingHoursSpecification", "geo", "image", "priceRange"],
    },
    "BreadcrumbList": {"required": ["itemListElement"], "recommended": []},
    "Person": {
        "required": ["name"],
        "recommended": ["url", "image", "jobTitle", "sameAs"],
    },
    "Recipe": {
        "required": ["name", "image", "recipeIngredient", "recipeInstructions"],
        "recommended": [
            "author",
            "datePublished",
            "description",
            "prepTime",
            "cookTime",
            "totalTime",
            "nutrition",
        ],
    },
    "Event": {
        "required": ["name", "startDate", "location"],
        "recommended": [
            "endDate",
            "description",
            "image",
            "offers",
            "performer",
            "organizer",
        ],
    },
    "JobPosting": {
        "required": ["title", "description", "datePosted", "hiringOrganization", "jobLocation"],
        "recommended": ["baseSalary", "employmentType", "validThrough"],
    },
    "VideoObject": {
        "required": ["name", "description", "thumbnailUrl", "uploadDate"],
        "recommended": ["contentUrl", "embedUrl", "duration"],
    },
}


def fetch(url: str) -> tuple[int, dict, str, str]:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, identity"})
    with urlopen(req, timeout=TIMEOUT, context=ssl.create_default_context()) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        raw = resp.read()
        # urllib does not auto-decompress; detect via magic bytes for robustness
        if raw[:2] == b"\x1f\x8b" or headers.get("content-encoding", "").lower() == "gzip":
            try:
                raw = gzip.decompress(raw)
            except OSError:
                pass
        charset = "utf-8"
        m = re.search(r"charset=([^\s;]+)", headers.get("content-type", ""), re.I)
        if m:
            charset = m.group(1).strip().lower()
        try:
            body = raw.decode(charset, errors="replace")
        except LookupError:
            body = raw.decode("utf-8", errors="replace")
        return resp.status, headers, resp.geturl(), body


class _JsonLdExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict] = []
        self._capture = False
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            a = {k.lower(): (v or "") for k, v in attrs}
            if a.get("type", "").lower() == "application/ld+json":
                self._capture = True
                self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._capture:
            raw = "".join(self._buf).strip()
            self._capture = False
            self._buf = []
            if not raw:
                return
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                self.blocks.append({"error": str(e), "raw": raw[:300]})
                return
            if isinstance(data, list):
                for item in data:
                    self.blocks.append({"data": item})
            else:
                self.blocks.append({"data": data})

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buf.append(data)


def get_type(node) -> str | None:
    if not isinstance(node, dict):
        return None
    t = node.get("@type")
    if isinstance(t, list):
        return t[0] if t else None
    return t


def check_fields(node: dict, type_name: str) -> dict | None:
    spec = TYPE_FIELDS.get(type_name)
    if not spec:
        return None
    missing_required = [f for f in spec["required"] if not node.get(f)]
    missing_recommended = [f for f in spec["recommended"] if not node.get(f)]
    return {
        "type": type_name,
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
    }


def value_preview(v) -> str:
    if isinstance(v, (str, int, float, bool)):
        s = str(v)
        return s if len(s) <= 80 else s[:77] + "..."
    if isinstance(v, list):
        return f"[{len(v)} items]"
    if isinstance(v, dict):
        t = get_type(v)
        return f"{{{t}}}" if t else "{object}"
    return repr(v)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    url = sys.argv[1]
    if "://" not in url:
        url = "https://" + url

    try:
        status, _, final_url, body = fetch(url)
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"# Schema check error\n\nFailed to fetch {url}: {e}")
        return 1
    except Exception as e:
        print(f"# Schema check error\n\nFailed to fetch {url}: {e}")
        return 1

    if status != 200:
        print(f"# Schema check: {url}\n\nHTTP {status} — page not fetched OK.")
        return 1

    extractor = _JsonLdExtractor()
    extractor.feed(body)
    blocks = extractor.blocks

    print(f"# JSON-LD schema check: {final_url}\n")

    if not blocks:
        print(
            "No JSON-LD blocks found. Consider adding structured data for your primary page type. "
            "Note: per Google, structured data is not required for AI Overviews, but it powers rich "
            "results and helps non-Google AI engines."
        )
        return 0

    for i, block in enumerate(blocks, 1):
        print(f"## Block {i}\n")
        if "error" in block:
            print(f"- **Invalid JSON-LD:** {block['error']}")
            print(f"- Preview: `{block['raw']}`\n")
            continue
        data = block["data"]
        type_name = get_type(data)
        print(f"- **@type:** {type_name or '(missing)'}")
        if type_name and type_name in TYPE_FIELDS:
            result = check_fields(data, type_name)
            if result and result["missing_required"]:
                print(f"- **Missing REQUIRED fields:** {', '.join(result['missing_required'])}")
            else:
                print("- **Required fields:** all present.")
            if result and result["missing_recommended"]:
                print(f"- Missing recommended fields: {', '.join(result['missing_recommended'])}")
        elif type_name:
            print(f"- (No per-field rules configured for `{type_name}` in this checker.)")

        if isinstance(data, dict):
            print("- Top-level fields:")
            for k, v in data.items():
                if k.startswith("@"):
                    continue
                print(f"  - `{k}`: {value_preview(v)}")
        print()

    print("---")
    print(
        "_Validate further with Google's [Rich Results Test](https://search.google.com/test/rich-results) "
        "and [Schema.org validator](https://validator.schema.org/) before deployment._"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
