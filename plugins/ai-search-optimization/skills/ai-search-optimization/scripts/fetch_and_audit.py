#!/usr/bin/env python3
"""
fetch_and_audit.py — Fetch a URL and produce a Markdown audit summary.

Usage:
    python fetch_and_audit.py <url>

Reports:
  - HTTP status, final URL after redirects, server, content-type
  - <title>, meta description, canonical, robots meta
  - Heading outline (h1..h3)
  - JSON-LD blocks found and their @type values
  - Image alt-text coverage
  - robots.txt summary for major AI crawlers
  - Sitemap reference
  - Render hint (high JS dependency vs. mostly static)

Dependencies: requests, beautifulsoup4
    pip install requests beautifulsoup4
"""

import json
import re
import sys
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.stderr.write(
        "Missing dependencies. Run: pip install requests beautifulsoup4\n"
    )
    sys.exit(2)

USER_AGENT = "ai-search-optimization-skill/1.0 (+https://sumvec.ai)"
TIMEOUT = 15

AI_CRAWLERS = [
    "Googlebot",
    "Google-Extended",
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-Web",
    "claude-searchbot",
    "PerplexityBot",
    "Perplexity-User",
    "Applebot",
    "Applebot-Extended",
    "Bingbot",
    "CCBot",
    "Meta-ExternalAgent",
    "FacebookBot",
    "Bytespider",
]


def fetch(url):
    r = requests.get(
        url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, allow_redirects=True
    )
    return r


def fetch_robots(base_url):
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        r = requests.get(
            robots_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT
        )
        if r.status_code == 200:
            return robots_url, r.text
        return robots_url, None
    except requests.RequestException:
        return robots_url, None


def parse_robots(robots_text):
    """Return dict of user-agent -> list of (directive, value)."""
    if not robots_text:
        return {}
    blocks = {}
    current_agents = []
    for raw_line in robots_text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            current_agents = []
            continue
        if ":" not in line:
            continue
        directive, value = [x.strip() for x in line.split(":", 1)]
        directive_l = directive.lower()
        if directive_l == "user-agent":
            current_agents = [value]
            blocks.setdefault(value, [])
        elif current_agents:
            for ua in current_agents:
                blocks.setdefault(ua, []).append((directive, value))
    return blocks


def summarize_ai_crawler_policy(robots_blocks):
    lines = []
    seen = set(robots_blocks.keys())
    for crawler in AI_CRAWLERS:
        if crawler in seen:
            directives = robots_blocks[crawler]
            disallows = [v for d, v in directives if d.lower() == "disallow"]
            allows = [v for d, v in directives if d.lower() == "allow"]
            if any(d == "/" for d in disallows):
                lines.append(f"- **{crawler}**: BLOCKED (Disallow: /)")
            elif disallows or allows:
                rules = ", ".join(
                    [f"Disallow {d}" for d in disallows]
                    + [f"Allow {a}" for a in allows]
                )
                lines.append(f"- **{crawler}**: custom rules — {rules}")
            else:
                lines.append(f"- **{crawler}**: declared but no Allow/Disallow rules")
        else:
            lines.append(f"- {crawler}: no explicit rule (default: allowed)")
    # Detect global Disallow: / under User-agent: *
    if "*" in robots_blocks:
        if any(
            d.lower() == "disallow" and v == "/"
            for d, v in robots_blocks["*"]
        ):
            lines.insert(0, "- **GLOBAL (User-agent: \\*)**: Disallow: / — site is blocking ALL crawlers")
    return lines


def extract_headings(soup):
    out = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = " ".join(tag.get_text(separator=" ").split())
        out.append((tag.name, text))
    return out


def extract_jsonld(soup):
    blocks = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            blocks.append({"error": f"Invalid JSON-LD: {e}", "raw_preview": raw[:200]})
            continue
        types = collect_types(data)
        blocks.append({"types": types, "data": data})
    return blocks


def collect_types(node):
    found = []

    def walk(n):
        if isinstance(n, dict):
            if "@type" in n:
                t = n["@type"]
                if isinstance(t, list):
                    found.extend(t)
                else:
                    found.append(t)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(node)
    return found


def image_alt_coverage(soup):
    imgs = soup.find_all("img")
    total = len(imgs)
    with_alt = sum(1 for i in imgs if (i.get("alt") or "").strip())
    return total, with_alt


def js_dependency_hint(html):
    # Crude heuristic: if visible <body> text is much smaller than <script> bulk,
    # the page is probably client-rendered.
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    body_html = body_match.group(1) if body_match else html
    text_only = re.sub(r"<[^>]+>", " ", body_html)
    text_only = re.sub(r"\s+", " ", text_only).strip()
    script_chars = sum(len(s) for s in re.findall(r"<script[\s\S]*?</script>", html, re.IGNORECASE))
    return len(text_only), script_chars


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    url = sys.argv[1]

    try:
        r = fetch(url)
    except requests.RequestException as e:
        print(f"# Audit error\n\nFailed to fetch {url}: {e}")
        sys.exit(1)

    soup = BeautifulSoup(r.text, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "(none)"
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    meta_desc = meta_desc_tag.get("content", "").strip() if meta_desc_tag else "(none)"
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else "(none)"
    robots_meta_tag = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    robots_meta = (
        robots_meta_tag.get("content", "").strip() if robots_meta_tag else "(none)"
    )
    x_robots = r.headers.get("X-Robots-Tag", "(none)")

    headings = extract_headings(soup)
    h1_count = sum(1 for tag, _ in headings if tag == "h1")

    jsonld_blocks = extract_jsonld(soup)

    img_total, img_with_alt = image_alt_coverage(soup)

    text_chars, script_chars = js_dependency_hint(r.text)
    render_hint = (
        "Page text appears mostly server-rendered."
        if text_chars > script_chars * 0.5
        else "Page may be JavaScript-rendered; verify with a JS-capable fetch."
    )

    robots_url, robots_text = fetch_robots(r.url)
    robots_blocks = parse_robots(robots_text) if robots_text else {}
    crawler_lines = summarize_ai_crawler_policy(robots_blocks) if robots_text else [
        f"- robots.txt not found at {robots_url}"
    ]

    sitemap_refs = []
    if robots_text:
        for line in robots_text.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_refs.append(line.split(":", 1)[1].strip())

    # ---- Emit Markdown report ----
    print(f"# Page audit: {r.url}\n")
    print("## HTTP & headers\n")
    print(f"- **Final URL:** {r.url}")
    print(f"- **Status:** {r.status_code}")
    print(f"- **Server:** {r.headers.get('Server', '(unknown)')}")
    print(f"- **Content-Type:** {r.headers.get('Content-Type', '(unknown)')}")
    print(f"- **X-Robots-Tag header:** {x_robots}")
    print()

    print("## Page metadata\n")
    print(f"- **Title:** {title}")
    print(f"- **Meta description:** {meta_desc}")
    print(f"- **Canonical:** {canonical}")
    print(f"- **Robots meta:** {robots_meta}")
    print()

    print("## Heading outline\n")
    if not headings:
        print("- (no h1/h2/h3 found)")
    else:
        for tag, text in headings:
            print(f"- `<{tag}>` {text[:120]}")
    print(f"\n**h1 count:** {h1_count} (ideal: 1)\n")

    print("## JSON-LD structured data\n")
    if not jsonld_blocks:
        print("- No JSON-LD blocks found.")
    else:
        for i, block in enumerate(jsonld_blocks, 1):
            if "error" in block:
                print(f"- Block {i}: ERROR — {block['error']}")
                print(f"  Preview: `{block['raw_preview']}`")
            else:
                types = ", ".join(block["types"]) if block["types"] else "(no @type)"
                print(f"- Block {i}: types = {types}")
    print()

    print("## Images\n")
    if img_total == 0:
        print("- No `<img>` elements found.")
    else:
        pct = (img_with_alt / img_total) * 100
        print(f"- Total images: {img_total}")
        print(f"- With alt text: {img_with_alt} ({pct:.0f}%)")
    print()

    print("## Render hint\n")
    print(f"- Body text chars: ~{text_chars}")
    print(f"- Script chars: ~{script_chars}")
    print(f"- {render_hint}")
    print()

    print(f"## robots.txt — {robots_url}\n")
    if not robots_text:
        print(f"- No robots.txt fetched (404, blocked, or error).")
    else:
        print(f"- robots.txt fetched ({len(robots_text)} chars).")
        if sitemap_refs:
            print(f"- Sitemap refs:")
            for s in sitemap_refs:
                print(f"  - {s}")
        else:
            print("- No `Sitemap:` directive found in robots.txt.")
        print("\n### AI crawler policy\n")
        for line in crawler_lines:
            print(line)
    print()

    print("---")
    print(
        "_Report generated by ai-search-optimization skill. "
        "Cross-reference findings with `references/google-aiso-principles.md` before recommending actions._"
    )


if __name__ == "__main__":
    main()
