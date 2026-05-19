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

Dependencies: Python 3.9+ standard library only.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import ssl
import subprocess
import sys
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen

from _chrome import find_chromium_binary


USER_AGENT = "ai-search-optimization-skill/2.0 (+https://sumvec.ai)"
TIMEOUT = 15
RENDER_TIMEOUT = 30

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


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    return ctx


def fetch_rendered(chrome: str, url: str) -> str | None:
    """Use headless Chrome --dump-dom to fetch the post-JS rendered HTML.

    Returns the rendered DOM as a string, or None if the subprocess fails.
    Used when --render is passed to audit JS-heavy / single-page apps where
    the static HTML carries no content.
    """
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--virtual-time-budget=5000",
        "--user-agent=" + USER_AGENT,
        "--dump-dom",
        url,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=RENDER_TIMEOUT, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[fetch_and_audit] Chrome render failed: {e}", file=sys.stderr)
        return None
    if result.returncode != 0:
        err = (result.stderr or "").strip()
        print(f"[fetch_and_audit] Chrome exited {result.returncode}: {err[:200]}", file=sys.stderr)
        return None
    return result.stdout or None


def fetch(url: str, render: bool = False) -> tuple[int, dict, str, str]:
    """Return (status, headers, final_url, body_text).

    Always performs a static fetch (so we keep real HTTP headers, status,
    redirects). When `render=True`, additionally runs the URL through
    headless Chrome's --dump-dom and substitutes the rendered HTML for the
    body. Headers + status still come from the static fetch — Chrome's
    --dump-dom does not expose response metadata.
    """
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, identity"})
    with urlopen(req, timeout=TIMEOUT, context=_ssl_context()) as resp:
        status = resp.status
        final_url = resp.geturl()
        # Case-insensitive lookup; urllib's HTTPMessage doesn't lowercase keys
        headers_lc = {k.lower(): v for k, v in resp.headers.items()}
        raw = resp.read()
        # urllib does not auto-decompress; detect via magic bytes for robustness
        if raw[:2] == b"\x1f\x8b" or headers_lc.get("content-encoding", "").lower() == "gzip":
            try:
                raw = gzip.decompress(raw)
            except OSError:
                pass
        charset = "utf-8"
        ct = headers_lc.get("content-type", "")
        m = re.search(r"charset=([^\s;]+)", ct, re.I)
        if m:
            charset = m.group(1).strip().lower()
        try:
            body = raw.decode(charset, errors="replace")
        except LookupError:
            body = raw.decode("utf-8", errors="replace")

    # Optional second pass: rendered DOM via headless Chrome. Static headers
    # + status code are kept; only the body is replaced when render succeeds.
    if render:
        chrome = find_chromium_binary()
        if not chrome:
            print(
                "[fetch_and_audit] --render requested but no Chromium-family browser "
                "found; falling back to static HTML.",
                file=sys.stderr,
            )
        else:
            rendered = fetch_rendered(chrome, final_url)
            if rendered:
                body = rendered
            else:
                print(
                    "[fetch_and_audit] Chrome render failed; falling back to static HTML.",
                    file=sys.stderr,
                )
    return status, headers_lc, final_url, body


def fetch_robots(base_url: str) -> tuple[str, str | None]:
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        status, _, _, text = fetch(robots_url)
        return robots_url, text if status == 200 else None
    except (HTTPError, URLError, TimeoutError):
        return robots_url, None
    except Exception:
        return robots_url, None


def parse_robots(robots_text: str | None) -> dict[str, list[tuple[str, str]]]:
    if not robots_text:
        return {}
    blocks: dict[str, list[tuple[str, str]]] = {}
    current_agents: list[str] = []
    for raw_line in robots_text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            current_agents = []
            continue
        if ":" not in line:
            continue
        directive, value = (x.strip() for x in line.split(":", 1))
        directive_l = directive.lower()
        if directive_l == "user-agent":
            current_agents = [value]
            blocks.setdefault(value, [])
        elif current_agents:
            for ua in current_agents:
                blocks.setdefault(ua, []).append((directive, value))
    return blocks


def summarize_ai_crawler_policy(blocks: dict[str, list[tuple[str, str]]]) -> list[str]:
    lines: list[str] = []
    seen = set(blocks.keys())
    for crawler in AI_CRAWLERS:
        if crawler in seen:
            directives = blocks[crawler]
            disallows = [v for d, v in directives if d.lower() == "disallow"]
            allows = [v for d, v in directives if d.lower() == "allow"]
            if any(d == "/" for d in disallows):
                lines.append(f"- **{crawler}**: BLOCKED (Disallow: /)")
            elif disallows or allows:
                rules = ", ".join(
                    [f"Disallow {d}" for d in disallows] + [f"Allow {a}" for a in allows]
                )
                lines.append(f"- **{crawler}**: custom rules — {rules}")
            else:
                lines.append(f"- **{crawler}**: declared but no Allow/Disallow rules")
        else:
            lines.append(f"- {crawler}: no explicit rule (default: allowed)")
    if "*" in blocks:
        if any(d.lower() == "disallow" and v == "/" for d, v in blocks["*"]):
            lines.insert(
                0,
                "- **GLOBAL (User-agent: \\*)**: Disallow: / — site is blocking ALL crawlers",
            )
    return lines


class _PageParser(HTMLParser):
    """Single-pass HTML parser extracting title, meta, headings, images, JSON-LD."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.meta_description = ""
        self.canonical = ""
        self.robots_meta = ""
        self.headings: list[tuple[str, str]] = []
        self._heading_stack: list[str] = []
        self._heading_buf: list[str] = []
        self.images_total = 0
        self.images_with_alt = 0
        self.jsonld_blocks: list[dict] = []
        self._in_jsonld = False
        self._jsonld_buf: list[str] = []
        self.text_len = 0
        self.script_len = 0
        self._in_script_general = False
        self._in_style = False
        self._in_body = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
            return
        if tag == "meta":
            name = a.get("name", "").lower()
            if name == "description" and not self.meta_description:
                self.meta_description = a.get("content", "").strip()
            elif name == "robots" and not self.robots_meta:
                self.robots_meta = a.get("content", "").strip()
            return
        if tag == "link" and a.get("rel", "").lower() == "canonical":
            if not self.canonical:
                self.canonical = a.get("href", "").strip()
            return
        if tag in ("h1", "h2", "h3"):
            self._heading_stack.append(tag)
            self._heading_buf = []
            return
        if tag == "img":
            self.images_total += 1
            if a.get("alt", "").strip():
                self.images_with_alt += 1
            return
        if tag == "script":
            self._in_script_general = True
            if a.get("type", "").lower() == "application/ld+json":
                self._in_jsonld = True
                self._jsonld_buf = []
            return
        if tag == "style":
            self._in_style = True
            return
        if tag == "body":
            self._in_body = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3") and self._heading_stack:
            popped = self._heading_stack.pop()
            text = " ".join("".join(self._heading_buf).split()).strip()
            if text:
                self.headings.append((popped, text))
            self._heading_buf = []
        elif tag == "script":
            if self._in_jsonld:
                raw = "".join(self._jsonld_buf).strip()
                self._jsonld_buf = []
                self._in_jsonld = False
                if raw:
                    try:
                        data = json.loads(raw)
                        self.jsonld_blocks.append({"types": _collect_types(data), "data": data})
                    except json.JSONDecodeError as e:
                        self.jsonld_blocks.append(
                            {"error": f"Invalid JSON-LD: {e}", "raw_preview": raw[:200]}
                        )
            self._in_script_general = False
        elif tag == "style":
            self._in_style = False
        elif tag == "body":
            self._in_body = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
            return
        if self._in_jsonld:
            self._jsonld_buf.append(data)
            return
        if self._heading_stack:
            self._heading_buf.append(data)
        if self._in_script_general:
            self.script_len += len(data)
            return
        if self._in_style:
            return
        if self._in_body:
            self.text_len += len(data.strip())


def _collect_types(node) -> list[str]:
    found: list[str] = []

    def walk(n) -> None:
        if isinstance(n, dict):
            t = n.get("@type")
            if isinstance(t, list):
                found.extend(t)
            elif t:
                found.append(t)
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)

    walk(node)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fetch a URL and produce a Markdown audit summary (stdlib-only).",
    )
    ap.add_argument("url", help="The URL to audit. Bare domain accepted.")
    ap.add_argument(
        "--render",
        action="store_true",
        help="Use headless Chrome to fetch the post-JS rendered DOM. "
        "Required for SPAs / Next.js / React-heavy pages where the static HTML "
        "carries little content. Falls back to static fetch if no Chromium-family "
        "browser is installed.",
    )
    args = ap.parse_args()

    url = args.url
    if "://" not in url:
        url = "https://" + url

    try:
        status, headers, final_url, body = fetch(url, render=args.render)
    except (HTTPError, URLError, TimeoutError) as e:
        print(f"# Audit error\n\nFailed to fetch {url}: {e}")
        return 1
    except Exception as e:
        print(f"# Audit error\n\nFailed to fetch {url}: {e}")
        return 1

    parser = _PageParser()
    parser.feed(body)

    x_robots = headers.get("x-robots-tag", "(none)")
    render_hint = (
        "Page text appears mostly server-rendered."
        if parser.text_len > parser.script_len * 0.5
        else "Page may be JavaScript-rendered; verify with a JS-capable fetch."
    )

    robots_url, robots_text = fetch_robots(final_url)
    blocks = parse_robots(robots_text)
    crawler_lines = (
        summarize_ai_crawler_policy(blocks)
        if robots_text
        else [f"- robots.txt not found at {robots_url}"]
    )

    sitemap_refs: list[str] = []
    if robots_text:
        for line in robots_text.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_refs.append(line.split(":", 1)[1].strip())

    print(f"# Page audit: {final_url}\n")
    print("## HTTP & headers\n")
    print(f"- **Final URL:** {final_url}")
    print(f"- **Status:** {status}")
    print(f"- **Server:** {headers.get('server', '(unknown)')}")
    print(f"- **Content-Type:** {headers.get('content-type', '(unknown)')}")
    print(f"- **X-Robots-Tag header:** {x_robots}")
    print()

    print("## Page metadata\n")
    print(f"- **Title:** {parser.title.strip() or '(none)'}")
    print(f"- **Meta description:** {parser.meta_description or '(none)'}")
    print(f"- **Canonical:** {parser.canonical or '(none)'}")
    print(f"- **Robots meta:** {parser.robots_meta or '(none)'}")
    print()

    print("## Heading outline\n")
    if not parser.headings:
        print("- (no h1/h2/h3 found)")
    else:
        for tag, text in parser.headings:
            print(f"- `<{tag}>` {text[:120]}")
    h1_count = sum(1 for tag, _ in parser.headings if tag == "h1")
    print(f"\n**h1 count:** {h1_count} (ideal: 1)\n")

    print("## JSON-LD structured data\n")
    if not parser.jsonld_blocks:
        print("- No JSON-LD blocks found.")
    else:
        for i, block in enumerate(parser.jsonld_blocks, 1):
            if "error" in block:
                print(f"- Block {i}: ERROR — {block['error']}")
                print(f"  Preview: `{block['raw_preview']}`")
            else:
                types = ", ".join(block["types"]) if block["types"] else "(no @type)"
                print(f"- Block {i}: types = {types}")
    print()

    print("## Images\n")
    if parser.images_total == 0:
        print("- No `<img>` elements found.")
    else:
        pct = (parser.images_with_alt / parser.images_total) * 100
        print(f"- Total images: {parser.images_total}")
        print(f"- With alt text: {parser.images_with_alt} ({pct:.0f}%)")
    print()

    print("## Render hint\n")
    print(f"- Body text chars: ~{parser.text_len}")
    print(f"- Script chars: ~{parser.script_len}")
    print(f"- {render_hint}")
    print()

    print(f"## robots.txt — {robots_url}\n")
    if not robots_text:
        print("- No robots.txt fetched (404, blocked, or error).")
    else:
        print(f"- robots.txt fetched ({len(robots_text)} chars).")
        if sitemap_refs:
            print("- Sitemap refs:")
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
