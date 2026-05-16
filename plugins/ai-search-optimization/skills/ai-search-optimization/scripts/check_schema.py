#!/usr/bin/env python3
"""
check_schema.py — Inspect JSON-LD on a URL and report types, key fields, and likely issues.

Usage:
    python check_schema.py <url>

Outputs Markdown to stdout. Designed to be pasted directly into an AISO audit report.

Dependencies: requests, beautifulsoup4
    pip install requests beautifulsoup4
"""

import json
import re
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write("Missing dependencies. Run: pip install requests beautifulsoup4\n")
    sys.exit(2)

USER_AGENT = "ai-search-optimization-skill/1.0 (+https://sumvec.ai)"
TIMEOUT = 15

# Per-type required and recommended fields. Sourced from Google's developer docs
# for rich results (developers.google.com/search/docs/appearance/structured-data/*).
TYPE_FIELDS = {
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
        "recommended": ["image", "description", "brand", "offers", "aggregateRating", "review", "sku", "gtin13"],
    },
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
    },
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
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
    },
    "Person": {
        "required": ["name"],
        "recommended": ["url", "image", "jobTitle", "sameAs"],
    },
    "Recipe": {
        "required": ["name", "image", "recipeIngredient", "recipeInstructions"],
        "recommended": ["author", "datePublished", "description", "prepTime", "cookTime", "totalTime", "nutrition"],
    },
    "Event": {
        "required": ["name", "startDate", "location"],
        "recommended": ["endDate", "description", "image", "offers", "performer", "organizer"],
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


def fetch(url):
    return requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)


def extract_blocks(soup):
    out = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            out.append({"error": str(e), "raw": raw[:300]})
            continue
        # Some publishers wrap multiple objects in an array
        if isinstance(data, list):
            for item in data:
                out.append({"data": item})
        else:
            out.append({"data": data})
    return out


def get_type(node):
    if not isinstance(node, dict):
        return None
    t = node.get("@type")
    if isinstance(t, list):
        return t[0] if t else None
    return t


def check_fields(node, type_name):
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


def value_preview(v):
    if isinstance(v, (str, int, float, bool)):
        s = str(v)
        return s if len(s) <= 80 else s[:77] + "..."
    if isinstance(v, list):
        return f"[{len(v)} items]"
    if isinstance(v, dict):
        t = get_type(v)
        return f"{{{t}}}" if t else "{object}"
    return repr(v)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    url = sys.argv[1]

    try:
        r = fetch(url)
    except requests.RequestException as e:
        print(f"# Schema check error\n\nFailed to fetch {url}: {e}")
        sys.exit(1)

    if r.status_code != 200:
        print(f"# Schema check: {url}\n\nHTTP {r.status_code} — page not fetched OK.")
        sys.exit(1)

    soup = BeautifulSoup(r.text, "html.parser")
    blocks = extract_blocks(soup)

    print(f"# JSON-LD schema check: {r.url}\n")

    if not blocks:
        print("No JSON-LD blocks found. Consider adding structured data for your primary page type. "
              "Note: per Google, structured data is not required for AI Overviews, but it powers rich results "
              "and helps non-Google AI engines.")
        return

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
            if result["missing_required"]:
                print(f"- **Missing REQUIRED fields:** {', '.join(result['missing_required'])}")
            else:
                print("- **Required fields:** all present.")
            if result["missing_recommended"]:
                print(f"- Missing recommended fields: {', '.join(result['missing_recommended'])}")
        elif type_name:
            print(f"- (No per-field rules configured for `{type_name}` in this checker.)")

        # Show top-level field preview
        if isinstance(data, dict):
            print("- Top-level fields:")
            for k, v in data.items():
                if k.startswith("@"):
                    continue
                print(f"  - `{k}`: {value_preview(v)}")
        print()

    print("---")
    print("_Validate further with Google's [Rich Results Test](https://search.google.com/test/rich-results) "
          "and [Schema.org validator](https://validator.schema.org/) before deployment._")


if __name__ == "__main__":
    main()
