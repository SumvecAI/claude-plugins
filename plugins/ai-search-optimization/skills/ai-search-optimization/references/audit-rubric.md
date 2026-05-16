# AISO Audit Rubric (1–5)

Use this rubric to score each dimension during an audit. Each dimension gets a 1 (broken) → 5 (best in class) score, with evidence quoted from the page.

A score of 3 is "acceptable, not optimized." Below 3 should generate at least one P0 or P1 fix.

## Dimensions

### D1. Crawlability & indexability
- **1** — Blocked by robots, `noindex`, or returns non-200. Not in Google's index.
- **2** — Indexed but with major issues: bad canonical, JS-only rendering, blocked CSS/JS, broken sitemap.
- **3** — Indexed, snippet-eligible, basic technical hygiene in place.
- **4** — Add: clean sitemap submitted, canonical correct, Core Web Vitals pass, JS renders deterministically.
- **5** — All above + AI crawler permissions explicitly set (Google-Extended, GPTBot, etc., per policy), `Last-Modified`/`Etag` headers honored, structured XML sitemap with `<lastmod>`.

### D2. Unique point of view (Google quality dimension)
- **1** — Wholly derivative; could be produced verbatim by a generic LLM.
- **2** — Some reframing, but no first-hand insight, data, or named examples.
- **3** — Includes specific examples, but viewpoint is still consensus.
- **4** — First-hand experience, original observation, or named case study clearly present.
- **5** — Original research, primary data, or expert opinion that other sites would cite.

### D3. Non-commodity framing (Google quality dimension)
- **1** — Generic "X tips" or "what is Y" page indistinguishable from 100 others.
- **2** — Slight differentiation in copy, but the angle is still common.
- **3** — A clear specific angle but execution is generic.
- **4** — Specific, narrow angle with content that genuinely goes beyond common knowledge.
- **5** — Definitive resource for its narrow angle; the page other sites link as the source.

### D4. Page organization for readers (Google quality dimension)
- **1** — Wall of text, no headings, or random structure.
- **2** — Headings present but inconsistent or non-descriptive.
- **3** — Semantic heading hierarchy, scannable paragraphs.
- **4** — Lead summary, descriptive H2/H3s, clear sections, internal anchors.
- **5** — Above + intentional information design (callouts, tables, definitions), explicit summary at top.

### D5. Multimedia (Google quality dimension)
- **1** — No images or video; or only stock images with no relevance.
- **2** — Images present but generic, missing alt text or descriptive captions.
- **3** — Relevant images with alt text.
- **4** — Original images/diagrams/screenshots, alt text, ImageObject schema.
- **5** — Above + original video with transcript and VideoObject schema where appropriate.

### D6. Structured data
- **1** — None, or broken/invalid.
- **2** — Some markup but doesn't match page content or is missing required fields.
- **3** — Correct primary schema (Article, Product, etc.) validates.
- **4** — Primary schema + BreadcrumbList + Organization on homepage + author Person markup.
- **5** — Above + entity disambiguation via `sameAs` (Wikipedia, Wikidata, LinkedIn) and `@id` linking across blocks.

### D7. Entity & topical authority [Industry practice — not Google-stated as such]
- **1** — Anonymous, no clear publisher, no about page, no author bylines.
- **2** — Author byline exists but no bio; publisher unclear.
- **3** — Named publisher with about page, author bios with credentials.
- **4** — Above + `sameAs` linking to verified profiles, multiple pages on related sub-topics.
- **5** — Recognized authority in the topic area: original research, cited by other authoritative sites, deep topical coverage.

### D8. Citation-worthiness [Industry practice]
- **1** — Nothing on this page a generative model would have reason to quote.
- **2** — General statements, some specifics.
- **3** — Specific numbers or named examples, but available from many other sources.
- **4** — Original data, expert quotes, or proprietary methodology that's unique to this page.
- **5** — The canonical source for some specific fact, methodology, or framing in this topic.

### D9. AI crawler & policy posture
- **1** — Robots.txt blocks Googlebot or has accidental blocks. AI crawler stance unintentional.
- **2** — Crawlable but no explicit AI crawler policy; signals are inconsistent.
- **3** — Explicit decisions made for Google-Extended, GPTBot, PerplexityBot, ClaudeBot, etc. (allow or deny).
- **4** — Above + sitemap, `Last-Modified` headers correct, deliberate `llms.txt` if relevant to non-Google engines.
- **5** — Above + monitored: server logs reviewed for unexpected AI crawler traffic, robots.txt audited quarterly.

### D10. Measurement
- **1** — No tracking. Search Console not verified.
- **2** — Search Console verified, no regular review.
- **3** — Performance reports reviewed; impressions and clicks tracked.
- **4** — Above + AI engine mention checks (manual or via Profound / Otterly / peec.ai-style tool).
- **5** — Above + server-log review of AI crawlers, dashboard of citation share across engines.

## Scoring rollup

Total = sum of D1–D10 (max 50).
- **≥ 42:** Excellent — incremental tuning only.
- **35–41:** Strong — focused improvements will move the needle.
- **25–34:** Mixed — multiple structural fixes needed.
- **< 25:** Foundational work required — usually content quality, indexability, or both.

When reporting, always include the *evidence* column (quoted page text or a screenshot/URL of the issue) so the score is auditable.
