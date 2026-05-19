#!/usr/bin/env python3
"""
generate_report.py — Render an AISO audit Markdown report to a Sumvec-branded HTML
file, and optionally to PDF if a Chromium-family browser is present on the system.

Usage:
    python generate_report.py <path-to-audit.md> [--out-dir <dir>] [--target-url <url>]
                                                  [--no-pdf] [--logo <path>]

Output (next to the input by default):
    <host>-<YYYY-MM-DD>-<HHMM>.html        # always
    <host>-<YYYY-MM-DD>-<HHMM>.pdf         # only if a Chromium-family browser is found

Dependencies: Python 3.9+ standard library only.

PDF conversion uses headless Chrome / Brave / Chromium / Edge if available — no pip
installs required. If none is found, the HTML is still written and the user can
print-to-PDF from their own browser (Cmd-P / Ctrl-P → Save as PDF).
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

# Local module — same directory; relies on Python adding script-dir to sys.path
from _chrome import find_chromium_binary


SUMVEC_BLUE = "#00A5E0"
SUMVEC_ORANGE = "#FF8101"
DARK_NAVY = "#1E2A3A"
WARM_GRAY = "#808080"


# ----------------------------- URL / filename helpers ----------------------------

def _sanitize_host(host: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", host.lower()).strip("-") or "audit"


def _host_from_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return _sanitize_host(parsed.netloc or url)


def _derive_host_from_filename(md_path: Path) -> str:
    m = re.match(r"aiso-audit-(.+)-(\d{4}-\d{2}-\d{2})$", md_path.stem)
    return m.group(1) if m else _sanitize_host(md_path.stem)


# ------------------------------- Markdown → HTML --------------------------------

_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_HR_RE = re.compile(r"^\s*-{3,}\s*$")


def _escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _render_inline(text: str) -> str:
    # Protect inline code first
    placeholders: list[str] = []

    def _stash(m: re.Match) -> str:
        placeholders.append(m.group(1))
        return f"\x00CODE{len(placeholders) - 1}\x00"

    text = _INLINE_CODE_RE.sub(_stash, text)
    text = _escape(text)
    text = _LINK_RE.sub(
        lambda m: f'<a href="{_escape(m.group(2))}">{m.group(1)}</a>', text
    )
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)
    # Restore inline code (escaped)
    text = re.sub(
        r"\x00CODE(\d+)\x00",
        lambda m: f"<code>{_escape(placeholders[int(m.group(1))])}</code>",
        text,
    )
    return text


def _md_table_row_to_cells(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    in_para: list[str] = []
    in_ul = False
    in_ol = False
    in_bq = False

    def flush_para() -> None:
        nonlocal in_para
        if in_para:
            out.append(f"<p>{_render_inline(' '.join(in_para).strip())}</p>")
            in_para = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol, in_bq
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False
        if in_bq:
            out.append("</blockquote>")
            in_bq = False

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        # Fenced code block
        if line.lstrip().startswith("```"):
            flush_para()
            close_lists()
            i += 1
            buf: list[str] = []
            while i < len(lines) and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append(f"<pre><code>{_escape(chr(10).join(buf))}</code></pre>")
            continue

        # Horizontal rule
        if _HR_RE.match(line):
            flush_para()
            close_lists()
            out.append("<hr />")
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if m:
            flush_para()
            close_lists()
            level = len(m.group(1))
            out.append(f"<h{level}>{_render_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # Table — detect a header line followed by separator
        if "|" in line and i + 1 < len(lines) and re.match(
            r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?\s*$", lines[i + 1]
        ):
            flush_para()
            close_lists()
            header_cells = _md_table_row_to_cells(line)
            i += 2  # skip separator
            rows: list[list[str]] = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append(_md_table_row_to_cells(lines[i]))
                i += 1
            out.append("<table>")
            out.append("<thead><tr>" + "".join(f"<th>{_render_inline(c)}</th>" for c in header_cells) + "</tr></thead>")
            out.append("<tbody>")
            for row in rows:
                out.append("<tr>" + "".join(f"<td>{_render_inline(c)}</td>" for c in row) + "</tr>")
            out.append("</tbody></table>")
            continue

        # Blockquote
        if line.startswith(">"):
            flush_para()
            if in_ul or in_ol:
                close_lists()
            if not in_bq:
                out.append("<blockquote>")
                in_bq = True
            content = line[1:].lstrip()
            out.append(f"<p>{_render_inline(content)}</p>")
            i += 1
            continue
        elif in_bq:
            close_lists()

        # Bulleted list
        m = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        if m:
            flush_para()
            if in_ol:
                close_lists()
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{_render_inline(m.group(2))}</li>")
            i += 1
            continue

        # Numbered list
        m = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if m:
            flush_para()
            if in_ul:
                close_lists()
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{_render_inline(m.group(2))}</li>")
            i += 1
            continue

        # Blank line
        if not line.strip():
            flush_para()
            close_lists()
            i += 1
            continue

        # Paragraph text
        if in_ul or in_ol or in_bq:
            close_lists()
        in_para.append(line.strip())
        i += 1

    flush_para()
    close_lists()
    return "\n".join(out)


# ------------------------------ Logo / branding --------------------------------

def _logo_data_uri(logo_path: Path | None) -> str | None:
    if not logo_path or not logo_path.exists():
        return None
    try:
        svg = logo_path.read_text(encoding="utf-8")
    except OSError:
        return None
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


def _resolve_logo_path(script_path: Path, override: str | None) -> Path | None:
    if override:
        p = Path(override).expanduser().resolve()
        return p if p.exists() else None
    default = script_path.parent.parent / "assets" / "sumvec-logo.svg"
    return default if default.exists() else None


def _extract_title(md: str) -> str:
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return "AI Search Optimization Audit"


# ------------------------------- HTML template ---------------------------------

def build_html(md: str, target_url: str, generated_at: dt.datetime, logo_uri: str | None) -> str:
    body_html = markdown_to_html(md)
    title = _extract_title(md)

    if logo_uri:
        logo_block = f'<img class="logo" src="{logo_uri}" alt="Sumvec.AI" />'
    else:
        logo_block = '<div class="logo-text">sumvec<span>.AI</span></div>'

    css = f"""
    :root {{
        --blue: {SUMVEC_BLUE};
        --orange: {SUMVEC_ORANGE};
        --navy: {DARK_NAVY};
        --gray: {WARM_GRAY};
    }}

    @page {{
        size: A4;
        margin: 22mm 18mm 22mm 18mm;
        @top-left {{ content: "AI Search Optimization Audit"; font-size: 8.5pt; color: var(--gray); }}
        @top-right {{ content: "sumvec.ai"; font-size: 8.5pt; color: var(--blue); font-weight: 600; }}
        @bottom-left {{ content: "Generated by ai-search-optimization · Sumvec.AI"; font-size: 7.5pt; color: var(--gray); }}
        @bottom-right {{ content: counter(page) " / " counter(pages); font-size: 7.5pt; color: var(--gray); }}
    }}
    @page :first {{
        margin: 0;
        @top-left {{ content: none; }} @top-right {{ content: none; }}
        @bottom-left {{ content: none; }} @bottom-right {{ content: none; }}
    }}

    html, body {{
        font-family: 'Inter', 'Helvetica Neue', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.55;
        color: var(--navy);
        margin: 0;
        padding: 0;
        background: #ffffff;
    }}

    /* On-screen padding so HTML reads nicely in a browser too */
    body.screen {{
        max-width: 820px;
        margin: 0 auto;
        padding: 48px 56px;
    }}

    .cover {{
        background: var(--navy);
        color: #ffffff;
        padding: 56px 56px 44px 56px;
        position: relative;
        page-break-after: always;
        margin: -48px -56px 48px -56px;
    }}
    @media print {{
        .cover {{ margin: 0; padding: 28mm 22mm 22mm 22mm; min-height: 100vh; }}
    }}
    .cover .accent-bar {{
        position: absolute; top: 0; left: 0; right: 0; height: 8px;
        background: linear-gradient(to right, var(--blue), var(--orange));
    }}
    .cover .logo {{ height: 44px; margin-bottom: 56px; display: block; }}
    .cover .logo-text {{
        font-size: 28pt; font-weight: 800; color: var(--blue); margin-bottom: 56px;
    }}
    .cover .logo-text span {{ color: var(--gray); font-size: 16pt; vertical-align: super; }}
    .cover .eyebrow {{
        font-size: 10pt; text-transform: uppercase; letter-spacing: 0.18em;
        color: var(--orange); font-weight: 600; margin-bottom: 12px;
    }}
    .cover h1.title {{
        font-size: 30pt; font-weight: 800; line-height: 1.15;
        color: #ffffff; margin: 0 0 16px 0; letter-spacing: -0.01em;
    }}
    .cover .target {{
        font-size: 14pt; font-weight: 600; color: var(--blue);
        word-break: break-all; margin-bottom: 56px;
    }}
    .cover .meta {{
        border-top: 1px solid rgba(0, 165, 224, 0.4);
        padding-top: 16px; margin-top: 32px;
    }}
    .cover .meta .row {{
        display: flex; justify-content: space-between;
        font-size: 10pt; color: rgba(255, 255, 255, 0.85); margin-bottom: 6px;
    }}
    .cover .meta .label {{
        color: var(--gray); text-transform: uppercase;
        letter-spacing: 0.12em; font-size: 8pt;
    }}

    h1, h2, h3, h4, h5, h6 {{
        font-weight: 700; line-height: 1.25;
        margin: 1.4em 0 0.5em 0; page-break-after: avoid;
    }}
    h1 {{ font-size: 22pt; color: var(--blue); border-bottom: 2px solid var(--blue); padding-bottom: 0.2em; }}
    h2 {{ font-size: 16pt; color: var(--navy); border-bottom: 1px solid var(--blue); padding-bottom: 0.15em; }}
    h3 {{ font-size: 12.5pt; color: var(--blue); }}
    h4 {{ font-size: 11pt; color: var(--navy); }}

    p {{ margin: 0 0 0.6em 0; }}
    a {{ color: var(--blue); text-decoration: none; word-break: break-word; }}
    a:hover {{ text-decoration: underline; }}

    code {{
        font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
        font-size: 0.9em; background: #f4f7fa; color: var(--navy);
        padding: 1px 4px; border-radius: 3px;
    }}
    pre {{
        font-family: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
        font-size: 9.5pt; background: #f4f7fa;
        border-left: 3px solid var(--blue);
        padding: 12px 14px; line-height: 1.4;
        white-space: pre-wrap; word-wrap: break-word;
        page-break-inside: avoid; margin: 0.8em 0;
    }}
    pre code {{ background: none; padding: 0; }}

    blockquote {{
        border-left: 3px solid var(--orange); padding: 4px 14px;
        background: #fff8f0; margin: 0.8em 0;
    }}
    blockquote p {{ margin: 0.2em 0; }}

    ul, ol {{ margin: 0.5em 0 1em 0; padding-left: 1.6em; }}
    li {{ margin-bottom: 0.3em; }}

    table {{
        border-collapse: collapse; width: 100%;
        margin: 1.2em 0; font-size: 10pt;
        page-break-inside: avoid;
    }}
    th, td {{
        border: 1px solid #d8e0e7; padding: 7px 10px;
        text-align: left; vertical-align: top;
    }}
    th {{
        background: var(--blue); color: #ffffff;
        font-weight: 600; font-size: 9.5pt;
    }}
    tr:nth-child(even) td {{ background: #f4f7fa; }}

    hr {{ border: none; border-top: 1px solid #d8e0e7; margin: 2em 0; }}

    .footer-note {{
        margin-top: 48px; padding-top: 16px;
        border-top: 1px solid #d8e0e7;
        font-size: 9.5pt; color: var(--gray);
    }}
    """

    cover = f"""
    <section class="cover">
        <div class="accent-bar"></div>
        {logo_block}
        <div class="eyebrow">AI Search Optimization Audit</div>
        <h1 class="title">{_escape(title)}</h1>
        <div class="target">{_escape(target_url)}</div>
        <div class="meta">
            <div class="row"><span class="label">Generated</span><span>{generated_at.strftime("%Y-%m-%d · %H:%M")}</span></div>
            <div class="row"><span class="label">Auditor</span><span>ai-search-optimization · Sumvec.AI</span></div>
            <div class="row"><span class="label">Reference</span><span>developers.google.com/search/docs/fundamentals/ai-optimization-guide</span></div>
        </div>
    </section>
    """

    footer = """
    <div class="footer-note">
        Every Google-attributed claim in this audit cites <code>developers.google.com</code> directly.
        Everything else is labeled <code>[Industry practice]</code>. The Sumvec plugin re-verifies the
        canonical Google guide before each release.
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{_escape(title)}</title>
<style>{css}</style>
</head>
<body class="screen">
{cover}
{body_html}
{footer}
</body>
</html>"""


# ----------------------------- PDF via headless Chrome --------------------------

def render_pdf_via_chromium(chrome: str, html_path: Path, pdf_path: Path) -> bool:
    """Run headless Chrome to render html_path → pdf_path. Return True on success."""
    file_uri = html_path.resolve().as_uri()
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--virtual-time-budget=5000",
        f"--print-to-pdf={pdf_path.resolve()}",
        file_uri,
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"[generate_report] Chromium invocation failed: {e}", file=sys.stderr)
        return False
    if result.returncode != 0:
        # Some Chrome versions still print headers; retry without that flag.
        cmd_retry = [c for c in cmd if c != "--no-pdf-header-footer"]
        result = subprocess.run(
            cmd_retry, capture_output=True, text=True, timeout=60, check=False
        )
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            print(f"[generate_report] Chromium exited {result.returncode}: {err[:300]}", file=sys.stderr)
            return False
    return pdf_path.exists()


# ----------------------------------- main --------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Render an AISO audit Markdown file into a Sumvec-branded HTML "
        "(always) plus PDF (if a Chromium-family browser is installed)."
    )
    ap.add_argument("md_path", help="Path to the audit Markdown file.")
    ap.add_argument("--out-dir", help="Directory for outputs. Default: same dir as the input.")
    ap.add_argument("--target-url", help="The URL that was audited. Used for cover + filename.")
    ap.add_argument("--no-pdf", action="store_true", help="Skip PDF generation even if a browser is found.")
    ap.add_argument("--logo", help="Path to an SVG/PNG logo. Default: bundled assets/sumvec-logo.svg.")
    args = ap.parse_args()

    md_path = Path(args.md_path).expanduser().resolve()
    if not md_path.exists():
        print(f"[generate_report] Input not found: {md_path}", file=sys.stderr)
        return 1

    md_text = md_path.read_text(encoding="utf-8")
    generated_at = dt.datetime.now()

    if args.target_url:
        host = _host_from_url(args.target_url)
        display_url = args.target_url
    else:
        host = _derive_host_from_filename(md_path)
        display_url = host.replace("-", ".")

    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else md_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = generated_at.strftime("%Y-%m-%d-%H%M")
    base = f"{host}-{stamp}"
    html_path = out_dir / f"{base}.html"
    pdf_path = out_dir / f"{base}.pdf"

    script_path = Path(__file__).resolve()
    logo = _resolve_logo_path(script_path, args.logo)
    logo_uri = _logo_data_uri(logo)

    html = build_html(md_text, display_url, generated_at, logo_uri)
    html_path.write_text(html, encoding="utf-8")
    print(f"[generate_report] HTML written: {html_path}")

    if args.no_pdf:
        print("[generate_report] PDF skipped (--no-pdf).")
        return 0

    chrome = find_chromium_binary()
    if not chrome:
        print(
            "[generate_report] No Chromium-family browser found on this system. "
            "HTML is ready — open it in your browser and use Print → Save as PDF "
            "to get a branded PDF (Cmd-P on macOS, Ctrl-P elsewhere)."
        )
        return 0

    print(f"[generate_report] Rendering PDF via: {chrome}")
    if render_pdf_via_chromium(chrome, html_path, pdf_path):
        print(f"[generate_report] PDF written: {pdf_path}")
    else:
        print(
            "[generate_report] PDF render failed. HTML is available; you can "
            "open it and print-to-PDF from your browser."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
