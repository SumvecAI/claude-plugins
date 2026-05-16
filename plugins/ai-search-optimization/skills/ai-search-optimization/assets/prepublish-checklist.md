# AISO Pre-publish Checklist

Run through this before publishing any new page. Items marked **[Google]** trace directly to Google's AI optimization guide; items marked **[Industry]** are broader AISO/GEO practice.

## Indexability and crawlability **[Google]**
- [ ] Page is reachable (no auth, no `robots.txt` block).
- [ ] Page returns HTTP 200.
- [ ] No `noindex` meta tag or `X-Robots-Tag: noindex` header.
- [ ] `rel="canonical"` points to this URL (or to the intended canonical).
- [ ] Page is included in the XML sitemap or will be discovered via internal links.
- [ ] Main content renders without requiring JavaScript execution beyond Googlebot's capabilities.
- [ ] No `data-nosnippet` or `max-snippet:0` blocking the main content.

## Content quality (Google's four dimensions) **[Google]**
- [ ] Page provides a unique point of view that a generic LLM could not produce verbatim.
- [ ] Page is non-commodity — has a specific angle, not "X tips for Y."
- [ ] Page has semantic heading hierarchy (one `<h1>`, descriptive `<h2>`/`<h3>`).
- [ ] Page includes relevant, high-quality images and/or video (where appropriate).
- [ ] Lead paragraph clearly states what the page is about and what the reader gets.

## Citation-worthiness **[Industry]**
- [ ] Page contains at least one original specific: data point, named example, expert quote, or proprietary methodology.
- [ ] Specifics appear in the first half of the page (where LLM retrievers tend to weight context).
- [ ] Definitions and key claims are stated in self-contained sentences (don't require the prior paragraph for context).

## Entity & authority **[Industry]**
- [ ] Author byline present with link to author bio.
- [ ] Author bio includes credentials or `sameAs` to LinkedIn/verifiable profile.
- [ ] Page references a clear publisher (Organization schema present on the homepage).

## Structured data **[Google says optional / Industry says do it]**
- [ ] Primary schema implemented (Article / Product / HowTo / FAQ / etc.) and validates against [Rich Results Test](https://search.google.com/test/rich-results).
- [ ] `BreadcrumbList` schema present.
- [ ] If using `Article`: `author`, `datePublished`, `dateModified`, `image`, `publisher` populated.
- [ ] Image URLs are absolute and ≥ 1200px on the long edge.
- [ ] Schema content matches what's visible on the page.

## Page experience **[Google]**
- [ ] Mobile rendering reviewed.
- [ ] Core Web Vitals (LCP, INP, CLS) pass on [PageSpeed Insights](https://pagespeed.web.dev).
- [ ] No intrusive interstitials before content.
- [ ] Main content is visually distinct from ads, sidebars, and navigation.

## AI crawler policy **[Industry, but engine-specific]**
- [ ] `robots.txt` has explicit, deliberate decisions for `Google-Extended`, `GPTBot`, `OAI-SearchBot`, `ClaudeBot`, `PerplexityBot`, `Applebot-Extended`, `CCBot`.
- [ ] (Optional) `llms.txt` updated if the site publishes one.

## Measurement **[Industry]**
- [ ] Site is verified in Search Console; this URL will appear in Performance reports.
- [ ] (Optional) AI mention tracking tool configured (Profound, Otterly, peec.ai-style).
- [ ] (Optional) Server-log alert configured for unexpected AI crawler activity.

## Final sanity check
- [ ] If I asked a generative model "summarize and cite the best resource on this topic," would this page be a credible citation? If not, what's missing?
