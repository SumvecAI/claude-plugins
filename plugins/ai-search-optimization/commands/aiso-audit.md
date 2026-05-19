---
description: Run a source-anchored AI search optimization audit on a URL or sitemap. Produces a Markdown report with every finding stamped to its source (Google docs vs. industry practice).
argument-hint: <url-or-sitemap-url>
---

You are running an AI Search Optimization audit using the `ai-search-optimization` skill that this plugin ships.

## Target

```
$ARGUMENTS
```

Treat the argument as one of:

1. **A single page URL** (e.g. `https://example.com/blog/post`) — audit that one page.
2. **A sitemap URL** (`.xml`, or path contains `sitemap`, or `Content-Type: application/xml`) — fetch it, list the URLs it contains, then **stop and ask the user which pages to audit**. Suggest a representative sample of 3–8 pages: the homepage, one product/service page, one blog/article, one pricing or about page, plus the highest-traffic candidates if obvious. Do not audit more than 8 pages in a single run unless the user explicitly asks for site-wide coverage.
3. **A bare domain** (`example.com` or `https://example.com`) — audit the homepage AND offer to fetch `<domain>/sitemap.xml` to surface other candidate pages.

If `$ARGUMENTS` is empty or malformed, ask the user for a URL and stop.

## Procedure

Follow the audit workflow defined in this plugin's skill (`skills/ai-search-optimization/SKILL.md`). Do not paraphrase it — load it and run all 10 steps in order:

1. Inputs — confirm target URL(s), 3–5 representative queries, which AI engines matter most, and the audience.
2. Crawlability & indexability check — use `scripts/fetch_and_audit.py <url>` to gather robots.txt, headers, render hint, AI-crawler policy. If the render hint flags the page as JavaScript-heavy, re-run with `python scripts/fetch_and_audit.py --render <url>` to get the post-JS rendered DOM via headless Chrome.
3. Content quality — score against Google's four published dimensions (`references/google-aiso-principles.md` §2).
4. Structured data — use `scripts/check_schema.py <url>` and recommend missing schema with templates from `assets/`.
5. Passage/chunk structure (honestly framed — Google says chunking is not required).
6. Entity & topical authority.
7. Citation-worthiness.
8. AI crawler policy (`references/llms-txt-guide.md` for `Google-Extended`, `GPTBot`, `OAI-SearchBot`, `ClaudeBot`, `PerplexityBot`, etc.).
9. Measurement plan.
10. Prioritized P0/P1/P2 action list using the rubric in `references/audit-rubric.md`.

## Source-stamping — **non-negotiable**

Every factual claim or recommendation in the report must end with an inline tag identifying its source class:

- `[google: <full-url>]` — for any claim attributable to Google. The URL must be the specific page on `developers.google.com` that supports the claim. Use the page anchor when possible.
- `[research: <full-url>]` — for peer-reviewed papers or vendor-published technical reports.
- `[vendor: <full-url>]` — for non-Google vendor documentation (OpenAI bots page, Anthropic crawler docs, Perplexity bots, Bing Webmaster, etc.).
- `[Industry practice]` — for community AISO/GEO/AEO conventions with no canonical source. Use this honestly; do not invent citations.

If you cannot defend a recommendation with one of those tags, drop it. Do not output unsourced advice.

When `references/google-aiso-principles.md` is the proximate evidence, still link to the underlying Google URL — never use the reference file itself as the citation.

## Output

Write the audit report to a deterministic path relative to the current working directory:

```
./aiso-audit-<sanitized-host>-<YYYY-MM-DD>.md
```

Where `<sanitized-host>` is the target's hostname with dots replaced by hyphens (e.g. `example-com`). If multiple URLs are audited from one sitemap run, write a single report with one `## Findings — <url>` block per page, plus a single TL;DR and a unified prioritized action plan.

The report structure (no deviations):

```markdown
# AI Search Optimization Audit: <target>

**Date:** <YYYY-MM-DD>
**Target engines:** <list of AI engines the user named>
**Target queries:** <list>
**Auditor:** ai-search-optimization v1.1.0 (Sumvec.ai)

## TL;DR
- Biggest win: …
- Biggest gap: …
- Top 3 actions: …

## Scorecard
| Dimension | Score (1–5) | Evidence | Source class |
|---|---:|---|---|
| D1. Crawlability & indexability | … | quoted page text or HTTP detail | [google: …] |
| D2. Unique point of view | … | … | [google: …] |
| … | … | … | … |

(All 10 dimensions from `references/audit-rubric.md`.)

## Findings

### 1. Crawlability & indexability
What works · What's broken · Exact remediation (code block where applicable) — each finding source-stamped.

### 2. Content quality (Google's four criteria)
…

(through section 7 — AI crawler policy.)

## Prioritized action plan
**P0 (this week):**
- [ ] Action (effort: S/M/L, expected impact: S/M/L) — exact instruction. [source]

**P1 (this month):** …

**P2 (this quarter):** …

## Measurement plan
Search Console reports to watch · which AI engines to probe manually · tools to consider. [source-stamped]

## Sources
Bulleted list of every URL cited above, grouped by source class:
- **Google:** …
- **Research:** …
- **Vendor:** …
- **Industry practice (no canonical source):** brief notes.
```

## Then render a Sumvec-branded HTML report (and PDF if Chrome is installed)

After the Markdown file is written, invoke the bundled report generator:

```bash
python scripts/generate_report.py <path-to-md-report> --target-url <the-audited-url>
```

The script is **stdlib-only** — no `pip install` required.

- It always writes a self-contained HTML report at `<host>-<YYYY-MM-DD>-<HHMM>.html` (inline CSS, inline Sumvec logo, no external fetches — opens in any browser).
- If a Chromium-family browser (Chrome / Brave / Chromium / Edge) is detected, it also writes `<host>-<YYYY-MM-DD>-<HHMM>.pdf` via headless print-to-PDF.
- If no such browser is found, the HTML is still produced and the script prints a one-line instruction to use the user's own browser's Print → Save as PDF.

Sumvec branding: dark-navy cover, accent bar (Sumvec Blue → Sumvec Orange gradient), the Sumvec logo, page numbers, and a citation-discipline footer.

## Final output to the user

Print, in this order:

1. The absolute path of the Markdown audit report.
2. The absolute path of the HTML report.
3. The absolute path of the PDF (or the print-to-PDF instruction if no Chromium-family browser is installed).
4. A 3-bullet summary (matches the report's TL;DR).
5. The top P0 action verbatim.

Do not commit the report. Do not open a PR. Do not modify any files on the audited site.

## Hard rules — recap

1. Cite Google for every Google-attributed claim. Quote sparingly and precisely; the full developers.google.com URL goes in the source tag.
2. Label everything not from Google. No silent slippage between canonical and consensus.
3. Never repeat debunked tactics (`llms.txt` as a Google ranking lever, content chunking for Google AI Overviews, AI-only content rewrites, inauthentic mentions, "special schema for AI Overviews"). See `references/google-aiso-principles.md` §5.
4. Be engine-aware. Where Google's stance and ChatGPT/Perplexity/Claude practice diverge, name the engine and say so explicitly.
5. Every action item must include either a code block (schema snippet, robots.txt directive, sample copy) or a precise checklist step. No "be more authoritative."
6. If a script fails or the target page can't be fetched, report the failure and continue with the steps that don't depend on it — don't silently drop sections.
