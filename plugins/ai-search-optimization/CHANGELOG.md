# Changelog

All notable changes to this plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] — 2026-05-17

### Changed — zero-dependency rewrite

The whole plugin now runs on **Python standard library only**. Users install with `/plugin install ai-search-optimization@sumvecai` and everything works immediately — no `pip install`, no `brew install`, no system-package management.

- `scripts/fetch_and_audit.py` rewritten using `urllib.request` + `html.parser` (was `requests` + `beautifulsoup4`). Adds robust gzip handling via magic-byte detection and case-insensitive HTTP header lookup.
- `scripts/check_schema.py` rewritten the same way.
- `scripts/generate_pdf.py` removed and replaced by `scripts/generate_report.py`:
  - Always writes a self-contained branded **HTML** report (inline CSS, inline base64 Sumvec logo, no external fetches).
  - If a Chromium-family browser (Chrome / Brave / Chromium / Edge) is found on the system, **also** writes a PDF via headless print-to-PDF.
  - If no such browser is found, the HTML is still produced and the user is told to print-to-PDF from their own browser (`Cmd-P` / `Ctrl-P` → Save as PDF). No pip dependency on `weasyprint`, no system dependency on `pango`.

### Why this is a major bump

- Behavior change: PDF generation no longer requires `pip install weasyprint markdown` + `brew install pango`. v1.2.0 install instructions in the wild are stale.
- Script signatures changed: `generate_pdf.py` is gone; the new entry point is `generate_report.py`. SKILL.md and `/aiso-audit` were updated; any external invocations need the new name.
- Output filenames are unchanged for HTML/PDF (`<host>-<YYYY-MM-DD>-<HHMM>.{html,pdf}`); Markdown report path is unchanged.

### Why this matters for marketplace review

A clean plugin with zero third-party Python deps is faster to review, easier to audit for security, and trivially install-and-go for end users — important for both Anthropic's official directory submission and community awesome-list listings.

## [1.2.0] — 2026-05-17

### Added

- **Sumvec-branded PDF audit report.** New `scripts/generate_pdf.py` renders the Markdown audit into a styled PDF using `weasyprint` and `python-markdown`. PDF includes a dark-navy cover page with the Sumvec logo, an accent bar in Sumvec Blue / Orange, Inter typography (with system fallbacks), page numbers, and a citation-discipline footer. Filename pattern: `<host>-<YYYY-MM-DD>-<HHMM>.pdf`.
- `assets/sumvec-logo.svg` bundled with the plugin so the PDF is self-contained — no external asset fetch required.
- SKILL.md and `/aiso-audit` both invoke the PDF step automatically after writing the Markdown report.

### Behavior

- PDF generation is opt-in via dependencies. If `weasyprint` or `markdown` aren't installed, the script prints `pip install weasyprint markdown` and exits 0 so the Markdown deliverable is never blocked.
- Brand palette is fixed to Sumvec.AI's guide (Blue `#00A5E0`, Orange `#FF8101`, Dark Navy `#1E2A3A`, Warm Gray `#808080`). Forks can swap the logo via `--logo <path>` on the CLI.

## [1.1.0] — 2026-05-17

### Added

- `/aiso-audit <url-or-sitemap-url>` slash command. Runs the full 10-step audit workflow with explicit source-stamping on every finding (`[google: …]`, `[research: …]`, `[vendor: …]`, or `[Industry practice]`) and writes the report to `./aiso-audit-<host>-<date>.md`. Accepts a page URL, a sitemap URL, or a bare domain; for sitemaps, asks the user which pages to audit (default 3–8 representative pages).
- Source-class tagging convention documented in the command and enforced in the output spec. The plugin's existing "Google-stated vs. industry practice" discipline is now visible inline in every audit deliverable.

### Changed

- Marketplace description updated to mention the slash command.

## [1.0.0] — 2026-05-16

### Initial release

Anchored on Google's [AI Optimization Guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) (last updated by Google 2026-05-15).

- `SKILL.md` with trigger-rich description covering AISO / GEO / AI Overviews / ChatGPT Search / Perplexity / Claude / Gemini / Copilot.
- 10-step audit workflow producing a Markdown audit report with scorecard, findings, and prioritized action plan.
- Five reference files: Google's principles distilled with citations, schema templates by page type, 10-dimension scoring rubric, an honest `llms.txt` guide, and engine-by-engine notes.
- Six drop-in JSON-LD schema templates (Article, FAQ, HowTo, Organization, Breadcrumb, Product).
- `llms.txt.example` and pre-publish checklist.
- Two helper scripts: `fetch_and_audit.py` for URL → Markdown audit summary, and `check_schema.py` for JSON-LD validation and missing-field detection.
- Cleanly separates Google-stated rules from broader industry practice.
