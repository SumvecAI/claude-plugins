# Multi-engine notes — how AI search engines differ

Date: 2026-05-16. The AI search landscape changes fast; re-verify before relying on this.

This file summarizes what's known about how each major AI search experience retrieves, ranks, and cites content. Use it to decide which recommendations to make for which engine.

---

## Google AI Overviews & AI Mode

- **Retrieval index:** Google Search index.
- **Crawler:** Googlebot (regular). `Google-Extended` controls *training use*, not AI Overview eligibility.
- **Optimization levers (per Google's official guide):**
  - Be indexed and snippet-eligible.
  - Foundational SEO: technical hygiene, helpful content, page experience.
  - Non-commodity content with unique POV.
  - High-quality images and video.
  - For commerce: Merchant Center feeds. For local: Google Business Profile.
- **Levers Google explicitly says do NOT work:** `llms.txt`, chunking, AI-only rewrites, inauthentic mentions, AI-specific schema.
- **Measurement:** Google Search Console performance reports. As of 2026-05, no separate AI Overview impression filter is published.

## ChatGPT Search (OpenAI)

- **Retrieval index:** Hybrid — proprietary search index built from web crawl + partnerships (e.g., with various publishers). Underlying ranking signals not public.
- **Crawlers:** `GPTBot` (training), `OAI-SearchBot` (real-time grounding), `ChatGPT-User` (when a user clicks a link in chat).
- **Optimization levers [Industry practice]:**
  - Allow `OAI-SearchBot` in `robots.txt` if you want to be cited.
  - Clear page structure and citable specifics — ChatGPT often summarizes and cites.
  - JSON-LD is parsed.
  - Bing presence helps because OpenAI's partnership with Microsoft historically channeled some retrieval through Bing's index; verify before relying on this in audits.
- **Citation style:** Inline citations and a "Sources" list. Tends to cite a small handful (3–10) of pages per response.

## Perplexity

- **Retrieval index:** Proprietary, multi-source. Heavy reliance on real-time web search per query.
- **Crawler:** `PerplexityBot` (search), `Perplexity-User` (user-triggered fetch).
- **Optimization levers [Industry practice]:**
  - Be reachable to `PerplexityBot` (do not block).
  - Strong topical authority — Perplexity heavily cites authoritative sources.
  - First-paragraph and clear sub-section summaries help (Perplexity often quotes lead paragraphs).
  - Recency matters more than for Google — fresh content is favored.
- **Citation style:** Numbered footnotes per claim. Cites more sources per answer than ChatGPT (often 5–15).

## Claude (Anthropic)

- **Retrieval index:** Claude itself does not maintain a web index; when used in products like Claude.ai with web access, it uses Brave Search as a backend (verify — this has shifted historically). In Claude API, web search is a tool feature.
- **Crawler:** `ClaudeBot` (training), `Claude-Web` (user-triggered fetch), `claude-searchbot` (search).
- **Optimization levers [Industry practice]:**
  - Allow Anthropic's crawlers if you want to be retrievable.
  - Clean, parseable HTML — Claude does not deeply parse JS-rendered content in tool-use fetches by default.
  - Citation-ready specifics in the first half of the page.
- **Citation style:** Cites inline when web search is used; tends to summarize fewer sources more deeply.

## Gemini (Google's standalone product, distinct from AI Overviews)

- **Retrieval:** Uses Google's grounding-with-Google-Search feature for the most current data.
- **Crawler:** Same Googlebot for indexing; `Google-Extended` opts out of training use.
- **Optimization levers:** Same as Google AI Overviews. Same caveats.

## Microsoft Copilot (Bing Chat lineage)

- **Retrieval index:** Bing index.
- **Crawler:** `Bingbot`.
- **Optimization levers [Industry practice]:**
  - Bing Webmaster Tools verification.
  - IndexNow protocol for rapid recrawl (https://www.indexnow.org/).
  - Bing weights site authority and freshness similarly to classical search.
  - JSON-LD is parsed.

## SearchGPT-class agentic crawlers

For any engine where a browser-based agent is the retrieval mechanism (rather than an index lookup):
- Semantic HTML matters more.
- Deterministic DOM (don't reshuffle on each render) matters.
- Accessibility tree quality matters (`aria-label`, `role`, proper heading order).
- Avoid bot-protection that blocks legitimate AI crawlers if you want to be cited.

See Google's note in the AI Optimization Guide and [web.dev's agent-friendly UX guide](https://web.dev/articles/ai-agent-site-ux) for general agent considerations.

---

## Engine-by-engine cheat sheet

| Need to be cited in… | Most leveraged signals | Watch out for |
|---|---|---|
| Google AI Overviews | Indexability, content quality, foundational SEO | Believing GEO hacks Google has debunked |
| ChatGPT Search | OAI-SearchBot allow, citable specifics, JSON-LD | Bing index dependency (unconfirmed degree) |
| Perplexity | PerplexityBot allow, topical authority, freshness | Recency-driven, can churn citations fast |
| Claude (web-enabled) | ClaudeBot allow, clean HTML, citation-ready leads | JS rendering — Claude may not execute JS |
| Gemini | Same as Google AI Overviews | — |
| Copilot | Bing presence, IndexNow, JSON-LD | Bing-specific submission tools |

## A practical default

When you don't know which engine matters most to the user, optimize for Google AI Overviews first (it's the highest-volume AI search surface and Google's guidance is most concrete), then add ChatGPT Search and Perplexity allow-rules and citable specifics on top. That covers ~80%+ of AI search traffic in 2026.
