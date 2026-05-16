# Schema.org templates — which to use, when, and why

**Note on Google's position:** Google says structured data is **not required** for AI Overviews / AI Mode. It is still worth implementing because (a) it powers rich results in classical Search, (b) other AI engines (ChatGPT, Perplexity) parse JSON-LD when they crawl, and (c) it gives a clean, explicit signal of what an entity is.

Source for Google's stance: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide (Mythbusting section).
Source for individual schema specs: https://developers.google.com/search/docs/appearance/structured-data/search-gallery and https://schema.org/

All snippets below are JSON-LD (`<script type="application/ld+json">`). JSON-LD is Google's recommended encoding — easier to inject and maintain than microdata or RDFa.

## Picking the right schema by page type

| Page type | Primary schema | Optional adds |
|---|---|---|
| Blog post / article / news | `Article`, `BlogPosting`, or `NewsArticle` | `BreadcrumbList`, `Person` (author) |
| Product page | `Product` | `Offer`, `AggregateRating`, `Review` |
| Local business page | `LocalBusiness` (or subtype like `Restaurant`) | `OpeningHoursSpecification`, `GeoCoordinates` |
| Homepage / about page | `Organization` (or `LocalBusiness`) | `WebSite` with `SearchAction` |
| FAQ page | `FAQPage` | — |
| How-to / tutorial | `HowTo` | `VideoObject`, `ImageObject` |
| Documentation / API reference | `TechArticle` | `Breadcrumb` |
| Event listing | `Event` | `Place`, `Offer` |
| Recipe | `Recipe` | `NutritionInformation`, `Review` |
| Job posting | `JobPosting` | — |
| Software product | `SoftwareApplication` | `AggregateRating` |

## Cross-cutting recommendations

1. **Always include `BreadcrumbList`** on any page deeper than the homepage. It clarifies site structure and powers breadcrumb appearance in Google's results.
2. **Always include an `Organization` block on the homepage** with `name`, `url`, `logo`, and `sameAs` pointing to verified profiles (LinkedIn, Wikipedia, Wikidata, X, GitHub for software). `sameAs` is the canonical way to assert entity identity.
3. **Use `@id` to link entities across blocks.** If an Article references an Organization, give the Organization a stable `@id` (e.g. `https://example.com/#organization`) and reference it from `publisher`.
4. **`Author` should be a `Person` object** with a name, URL (link to author bio page), `jobTitle`, and optionally `sameAs` to credible profiles. Author authority is increasingly weighted by both Google and AI engines.
5. **Match visible content.** Google penalizes structured data that doesn't match what's on the page. Don't mark up an FAQ that isn't actually rendered.

## Common mistakes to flag in an audit

- Schema is present but blocked by CSP or only injected in JS Google doesn't render.
- `FAQPage` used on a page that isn't actually a Q&A — current Google policy reserves FAQ rich results for government and authoritative health sites in some markets, but `FAQPage` schema is still valid markup.
- `Article.datePublished` missing or in the wrong format (should be ISO 8601).
- `Image` URLs not absolute, or the image is smaller than 1200px on the long edge.
- Multiple conflicting `Organization` entries across pages with different `@id`s.
- Markup duplicated in microdata AND JSON-LD — pick one.

## Templates

The drop-in JSON-LD templates live in `../assets/`:
- `schema-article.jsonld`
- `schema-faq.jsonld`
- `schema-howto.jsonld`
- `schema-organization.jsonld`
- `schema-breadcrumb.jsonld`
- `schema-product.jsonld`

Edit the placeholder fields (anything in `<<…>>`) before deploying. Validate with [Google's Rich Results Test](https://search.google.com/test/rich-results) and [Schema.org validator](https://validator.schema.org/) before shipping.

## When NOT to recommend more schema

If a page already has clean, valid JSON-LD that matches its content and the audit's bottleneck is content quality or crawlability, don't pad recommendations with extra schema. Google's mythbusting note applies: structured data is not the lever for AI Overviews. Fix the actual blocker first.
