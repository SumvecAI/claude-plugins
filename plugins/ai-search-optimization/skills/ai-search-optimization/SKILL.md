---
name: ai-search-optimization
description: Audit and optimize a webpage, site, or piece of content for visibility in AI-powered search experiences — Google AI Overviews, Google AI Mode, ChatGPT Search, Perplexity, Claude, Gemini, Copilot. Use this skill whenever the user mentions AI SEO, AISO, GEO, AEO, generative engine optimization, answer engine optimization, AI Overviews, optimizing for ChatGPT / Perplexity / Gemini / Claude, llms.txt, RAG visibility, grounding citations, AI search visibility, AI search audit, or asks how to rank in / get cited by / appear in AI answers. Trigger even when the user does not say "skill" — phrases like "audit my homepage for AI search", "why isn't my site showing up in AI Overviews", "make my content show up in ChatGPT", "is my site optimized for generative search" all qualify.
---

# AI Search Optimization (AISO / GEO)

This skill helps a user audit and improve a webpage or site for visibility in AI-powered search experiences. It anchors recommendations in Google's official guide on optimizing for generative AI features and clearly distinguishes Google-stated rules from broader industry practice for non-Google AI engines (ChatGPT Search, Perplexity, Claude, etc.).

**Authoritative source:** [Google's Guide to Optimizing for Generative AI Features on Google Search](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) (last updated 2026-05-15).

**Skill authored:** 2026-05-16. Re-read the Google page when running an audit if the linked page's "Last updated" date has moved forward — Google's guidance on AI Overviews is still evolving.

## Core mental model — what's actually being optimized

Google's generative AI features (AI Overviews, AI Mode) sit on top of the core Search index. Two mechanisms matter:

1. **Retrieval-augmented generation (RAG / grounding).** The model retrieves indexed pages via core ranking, then summarizes and cites them.
2. **Query fan-out.** The model issues many concurrent related queries and fetches more pages to answer one user question.

This has one consequence the skill must communicate plainly: **for Google AI features, ranking in classical Google Search is the prerequisite.** A page that is not indexed, not crawlable, or not snippet-eligible cannot appear in AI Overviews. Most "AISO/GEO hacks" do not change this.

Other AI engines (ChatGPT Search, Perplexity, Claude, Gemini grounding) use different retrieval pipelines (Bing index, custom crawlers, hosted search APIs). Some signals that Google says are unnecessary — `llms.txt`, content chunking, AI-crawler policies — may still matter for those engines. Be explicit about which engine each recommendation targets.

## When invoked, run this audit workflow

Walk the user through these steps in order. Skip steps the user has already addressed, but never skip step 1 (inputs) or step 10 (prioritization).

1. **Gather inputs.** Ask for: target URL or content, 3–5 representative user queries to optimize for, which AI engines matter most (Google AI Overviews, ChatGPT Search, Perplexity, Claude, all of them), audience, and whether this is one page or a site-wide audit.
2. **Crawlability & indexability check.** Read `references/google-aiso-principles.md` §1. Use `scripts/fetch_and_audit.py` if available to fetch the page, robots.txt, and sitemap. Flag: blocked by robots, `noindex`, broken canonical, JS-only rendering, missing in sitemap. For non-Google engines, also check `Google-Extended`, `GPTBot`, `OAI-SearchBot`, `PerplexityBot`, `ClaudeBot`, `CCBot` permissions.
3. **Content quality assessment.** Score against Google's four published quality dimensions (see `references/google-aiso-principles.md` §2): unique point of view, non-commodity, helpful organization, helpful images/video. Quote the page where it fails and where it succeeds.
4. **Structured data review.** Identify the page type (Article, FAQ, HowTo, Product, Local Business, Organization) and check existing JSON-LD. Google says structured data is **not required** for AI features but **is helpful** for rich results and other AI engines. Recommend specific schema using templates in `assets/`.
5. **Passage/chunk optimization.** Google explicitly says you do **not** need to "chunk" content. Frame this honestly: clear headings, scannable sections, and self-contained paragraphs serve human readers and happen to help retrieval — write for humans first. See `references/google-aiso-principles.md` §3.
6. **Entity & topical authority.** Industry best practice, not Google-stated. Check whether the page declares the entity clearly (Organization schema, About page, author bios, sameAs links to Wikipedia/Wikidata/LinkedIn). Check site-level topical depth around the target query.
7. **Citation-worthiness.** What on this page would a generative model quote? Original data, specific numbers, named examples, primary research, expert opinion, unique angles. Commodity content rarely gets cited. Suggest concrete additions.
8. **AI-crawler policy review.** Read `references/llms-txt-guide.md`. Google says `llms.txt` is not used. For ChatGPT, Perplexity, and others, decide whether to allow training, search-grounding, both, or neither. Provide robots.txt directives for the major AI crawlers.
9. **Measurement plan.** Search Console: monitor impressions/clicks (AI feature traffic shows up in standard Performance reports — Google does not currently provide an AI-Overview-specific filter as of 2026-05-15). For other engines: server logs for AI crawler hits, manual prompting in ChatGPT/Perplexity/Claude to see if the site is being cited, dedicated tools (e.g., Profound, Otterly, peec.ai) for AI mention tracking.
10. **Prioritized fix list.** Output P0/P1/P2 grouped by effort × impact, with explicit "do this" guidance for each item. Use the rubric in `references/audit-rubric.md`.

## Output format — final audit report

Produce a Markdown audit report with this exact structure:

```
# AI Search Optimization Audit: <page or site>
**Date:** <ISO date>  **Target engines:** <list>  **Target queries:** <list>

## TL;DR
3-bullet summary: biggest wins, biggest gaps, top 3 actions.

## Scorecard
Table with one row per audit dimension (see references/audit-rubric.md), columns: Score 1–5, Evidence, Recommendation.

## Findings by section
1. Crawlability & indexability
2. Content quality (Google's 4 criteria)
3. Structured data
4. Passage & section structure
5. Entity & topical authority
6. Citation-worthiness
7. AI crawler policy

For each: what's working, what's broken, exact remediation with sample markup/copy.

## Prioritized action plan
P0 (this week): ...
P1 (this month): ...
P2 (this quarter): ...
Each item: effort (S/M/L), expected impact, owner-ready instructions.

## Measurement plan
Which Search Console reports to watch, which AI engines to probe, which tools to consider.

## Sources
Inline links to Google's documentation for every Google-attributed claim.
```

## Hard rules — accuracy and integrity

1. **Cite Google for every Google-attributed claim.** Link directly to https://developers.google.com/search/docs/fundamentals/ai-optimization-guide or other developers.google.com pages. Quote sparingly and precisely.
2. **Label everything not from Google.** Use the marker `[Industry practice — not Google-stated]` next to any recommendation that comes from broader AISO/GEO community guidance.
3. **Never repeat debunked tactics.** Google explicitly says you do **not** need: `llms.txt`, content chunking, AI-only rewrites, inauthentic mentions, or special schema for AI Overviews. Repeating these for Google AI search is wrong. (See `references/google-aiso-principles.md` §5 — Mythbusting.)
4. **Be engine-aware.** Google's stance does not bind ChatGPT, Perplexity, or Claude. Where guidance diverges, say so. See `references/multi-engine-notes.md`.
5. **Recommend "do this", not "be more X".** Every action item should include either a code block (schema, robots.txt directive, sample copy pattern) or a precise checklist step.
6. **Don't hallucinate Google features.** If unsure whether something is real, say "I'd want to verify this — Google's guide doesn't state it directly."

## Reference files — load on demand

- `references/google-aiso-principles.md` — Distilled, citation-anchored summary of Google's guide (the primary reference; read whenever you need to make a Google-attributed claim).
- `references/schema-templates.md` — Which Schema.org type to pick by page type, with notes.
- `references/audit-rubric.md` — 1–5 scoring rubric for each audit dimension.
- `references/llms-txt-guide.md` — What `llms.txt` is, why Google ignores it, how other engines treat it, sample file.
- `references/multi-engine-notes.md` — Engine-by-engine differences (Google AI Overviews vs. ChatGPT Search vs. Perplexity vs. Claude vs. Gemini grounding vs. Copilot).

## Asset files — drop-in templates

- `assets/schema-article.jsonld` — Article / NewsArticle / BlogPosting template.
- `assets/schema-faq.jsonld` — FAQPage template.
- `assets/schema-howto.jsonld` — HowTo template.
- `assets/schema-organization.jsonld` — Organization + sameAs template.
- `assets/schema-breadcrumb.jsonld` — BreadcrumbList template.
- `assets/schema-product.jsonld` — Product template.
- `assets/llms.txt.example` — Sample `llms.txt` (with explanatory comments).
- `assets/prepublish-checklist.md` — AISO checklist to run before publishing any new page.

## Scripts — run when useful

All three helper scripts are **Python standard library only** — no `pip install` required. They run on any system with Python 3.9+.

- `scripts/fetch_and_audit.py <url> [--render]` — Fetches a URL, extracts headings, JSON-LD blocks, meta tags, image alt coverage; fetches `/robots.txt` and looks for the major AI crawler directives; emits a Markdown summary. Pass `--render` for SPAs (Next.js, React) — the script will use headless Chrome to fetch the post-JS rendered DOM. Falls back to static fetch if no Chromium-family browser is installed.
- `scripts/check_schema.py <url>` — Parses JSON-LD on a page and reports which Schema.org types are present, missing recommended fields, and obvious errors.
- `scripts/generate_report.py <path-to-audit.md> --target-url <url>` — Renders the finished Markdown audit into a Sumvec-branded **HTML** report (cover page, brand palette, page numbers, source-attribution footer). Always produces HTML; **also produces a PDF if a Chromium-family browser (Chrome / Brave / Chromium / Edge) is installed on the system**. Filename pattern: `<host>-<YYYY-MM-DD>-<HHMM>.{html,pdf}`.

## Closing the audit: produce Markdown + HTML (and PDF if Chrome is present)

After writing the Markdown audit, run `scripts/generate_report.py` to produce the branded deliverables:

```bash
python scripts/generate_report.py <path-to-audit.md> --target-url <audited-url>
```

The HTML and (when possible) PDF land next to the Markdown report. Report all written paths to the user. If no Chromium-family browser is detected, the script tells the user to open the HTML in their browser and Save as PDF (Cmd-P → Save as PDF on macOS, Ctrl-P elsewhere). The HTML is the universal portable artifact; the PDF is the convenience layer.

## A note on style

When delivering the audit, be direct and specific. "Add `<h2>` headings every ~200 words to make the page scannable, e.g. `<h2>How weed-and-feed differs from straight herbicide</h2>`" beats "improve content structure." The point of this skill is to replace vague AISO advice with concrete, executable, and honestly-sourced changes.
