# `llms.txt` — what it is, what Google says, what to actually do

## What `llms.txt` claims to be

[`llms.txt`](https://llmstxt.org/) is a proposed convention (originated by Jeremy Howard / Answer.AI in 2024) for a Markdown file at the site root that summarizes a site's content for LLMs. The pitch: give models a curated, plaintext index of your most important pages, so they can ground responses on the canonical sources rather than crawled HTML.

A typical `llms.txt` looks like:

```
# Example Co.

> One-paragraph description of what this site is.

## Docs
- [Quickstart](https://example.com/docs/quickstart): Get started in 5 minutes.
- [API reference](https://example.com/docs/api): Full API surface.

## Blog
- [How we built X](https://example.com/blog/x): Engineering deep-dive on system X.
```

## What Google says about `llms.txt`

Direct quote from Google's [AI Optimization Guide](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide), Mythbusting section:

> *"You don't need to create new machine readable files, AI text files, markup, or Markdown to appear in generative AI search. Note that Google may discover, crawl, and index many kinds of files in addition to HTML on a website: this doesn't mean that the file is treated in a special way."*

**Translation:** For Google AI Overviews and AI Mode, `llms.txt` is not used. Publishing one doesn't help and doesn't hurt for Google.

## What other AI engines do with `llms.txt`

This is a fast-moving area. As of 2026-05, the public position of major AI vendors:

- **OpenAI (ChatGPT Search):** No public commitment that `llms.txt` is consumed. Uses `OAI-SearchBot` (search grounding) and `GPTBot` (training), governed by robots.txt.
- **Anthropic (Claude):** Uses `ClaudeBot` and `Claude-Web` user agents, governed by robots.txt. No public commitment on `llms.txt`.
- **Perplexity:** Uses `PerplexityBot`. No public commitment on `llms.txt`. Some community claims of partial parsing — unverified.
- **Microsoft (Copilot / Bing):** Uses Bingbot. No public commitment on `llms.txt`.

**Bottom line:** No major AI engine has publicly committed to consuming `llms.txt` as a ranking or grounding signal as of the date of this skill (2026-05). It is, in 2026, more of an aspirational community convention than an interoperable standard.

## Should the audited site publish one?

A reasonable cost/benefit:

- **Low cost** to produce — a single Markdown file, ~50–200 lines for a typical site.
- **Plausibly useful** for: agentic clients that crawl and parse on the fly, internal LLM ingestion pipelines, future protocols that may pick it up, dev-doc-heavy sites (the original use case).
- **Definitely useful** as a single-page summary humans (including journalists, partners, developers) can read to understand the site fast.
- **Not useful** as a Google AI Overviews ranking lever.

**Recommendation when auditing:** if the site is dev-tools, documentation, or API-heavy → publish one (the audience benefits). Otherwise → optional, and never sell it to the user as the thing that unlocks AI search visibility.

## How to write a good `llms.txt`

1. Place it at `https://example.com/llms.txt`. Optionally also `/llms-full.txt` with the full content (not just links).
2. Start with the site name as an H1.
3. Add a one-paragraph blockquote describing the site.
4. Group links by section (`## Docs`, `## API`, `## Blog`, `## Company`).
5. For each link: `[Title](URL): Concise one-sentence description.`
6. Keep total length under ~10k tokens so it fits in a single LLM context window.
7. Update it when major sections are added or removed.

A starter file lives at `../assets/llms.txt.example`.

## Related: actual AI crawler controls (these DO work)

For each major AI crawler, you can set explicit allow/disallow in `/robots.txt`:

```
# Google's AI training opt-out (does not affect AI Overviews — those use the regular Search index)
User-agent: Google-Extended
Disallow: /

# OpenAI training
User-agent: GPTBot
Disallow: /

# OpenAI search grounding (used by ChatGPT Search)
User-agent: OAI-SearchBot
Disallow: /

# Anthropic
User-agent: ClaudeBot
Disallow: /
User-agent: Claude-Web
Disallow: /

# Perplexity
User-agent: PerplexityBot
Disallow: /

# Common Crawl (used by many model training pipelines)
User-agent: CCBot
Disallow: /

# Apple
User-agent: Applebot-Extended
Disallow: /
```

Important nuance: **`Google-Extended` controls Google's use of your content for training Gemini and other AI products. It does NOT remove your pages from AI Overviews / AI Mode** — those features rely on the regular Search index, so Googlebot's access governs them. To remove a page from AI Overviews specifically, use `nosnippet` or `noindex` (which also removes it from regular Search).

Sources:
- https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers
- https://platform.openai.com/docs/bots
- https://docs.anthropic.com/en/docs/agents-and-tools/web-fetch-tool (and Anthropic's published crawler list)
- https://docs.perplexity.ai/guides/bots
