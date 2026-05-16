# Sumvec Claude Plugins

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintained by Sumvec.ai](https://img.shields.io/badge/Maintained%20by-Sumvec.ai-0E0E0E)](https://sumvec.ai)

Plugins from **[Sumvec.ai](https://sumvec.ai)** for Claude Code — practical, source-anchored tools for marketing, SEO, and AI-search work. Built for teams who would rather cite the primary source than chase the hype cycle.

## Plugins in this marketplace

| Plugin | What it does |
|---|---|
| [`ai-search-optimization`](./plugins/ai-search-optimization/) | Audits and optimizes a webpage or site for visibility in AI-powered search (Google AI Overviews, ChatGPT Search, Perplexity, Claude, Gemini). Anchored in Google's official AI optimization guide; cleanly separates Google-stated rules from broader AISO/GEO industry practice. |

More plugins coming. If there's something you want next, open an issue.

## Install

Add the marketplace once:

```bash
/plugin marketplace add sumvecai/claude-plugins
```

Then install any plugin from it:

```bash
/plugin install ai-search-optimization@sumvecai
```

Run `/plugin marketplace update` periodically to pick up new releases.

## Why "source-anchored"

The Sumvec plugins draw a line between **what an authoritative source actually states** and **what the industry says you should do**. For example, the `ai-search-optimization` plugin cites Google's own AI optimization guide for every Google-attributed recommendation and explicitly labels everything else `[Industry practice]`. You can tell, line by line, which advice is canonical and which is community guidance — so you can trust the audit and stand behind the action items you take from it.

## Versioning

Each plugin pins an explicit semantic version in its `plugin.json`. We bump:

- **patch** for documentation tweaks and reference updates,
- **minor** for new references, assets, or scripts,
- **major** for any breaking change to skill output formats or audit structure.

Run `/plugin update` to pick up new versions.

## Contributing

Issues, suggestions, and pull requests are welcome.

- **Bug reports / Google guidance changes:** [open a GitHub issue](https://github.com/SumvecAI/claude-plugins/issues)
- **Plugin feedback:** [connect@sumvec.ai](mailto:connect@sumvec.ai)
- **Pull requests:** please run `claude plugin validate .` locally and confirm the affected SKILL.md still triggers cleanly before opening.

## License

[MIT](./LICENSE) — see the LICENSE file for the full text. Copyright (c) 2026 Sumvec.ai.

## About Sumvec.ai

Sumvec.ai builds practical AI tooling for marketers, founders, and operators who care about doing the work properly. Learn more at [sumvec.ai](https://sumvec.ai).
