# Changelog

All notable changes to this plugin are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
