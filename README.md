<p align="center">
  <a href="https://causabi.com"><img src="https://img.shields.io/badge/causabi.com-free%20score-black?style=flat-square" alt="causabi.com" /></a>
  <a href="https://pypi.org/project/causabi-geo/"><img src="https://img.shields.io/pypi/v/causabi-geo?style=flat-square&color=blue" alt="PyPI" /></a>
  <a href="https://pypi.org/project/causabi-geo/"><img src="https://img.shields.io/pypi/pyversions/causabi-geo?style=flat-square" alt="Python" /></a>
  <img src="https://img.shields.io/github/license/SHADRINMMM/causabi-geo?style=flat-square" alt="MIT" />
</p>

<h1 align="center">causabi-geo</h1>
<p align="center"><b>Optimize your website for AI search — ChatGPT, Perplexity, Gemini, Yandex GPT</b></p>

---

AI search engines actively pick sources to cite. Most sites never appear because they block AI crawlers, have no structured data, or lack FAQ markup. **causabi-geo** finds and fixes all of it.

```bash
pip install causabi-geo
geo-optimizer analyze https://yourdomain.com
```

```
AI Readiness Score: 47/100  Grade C
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  robots.txt       0 / 20   ❌  GPTBot, PerplexityBot blocked
  Schema.org       5 / 25   ❌  No structured data
  FAQ Schema       0 / 20   ❌  FAQPage JSON-LD missing  (+41% citations)
  Content depth   13 / 15   ✅
  Brand signals    8 / 10   ✅
  Freshness       21 / 10   ⚠️  Last updated 7 months ago
```

## What It Fixes

Run `geo-optimizer fix https://yourdomain.com --output ./geo-fixes` and get:

| File | What it does |
|------|-------------|
| `robots.txt` | Allows GPTBot, ClaudeBot, PerplexityBot, and 7 more AI crawlers |
| `schema.json` | Organization / SoftwareApplication JSON-LD for your homepage |
| `faq-schema.json` | FAQPage JSON-LD — the #1 signal for AI citations (+41%) |
| `llms.txt` | Site overview for AI agents (Claude, GPT-4, Perplexity) |
| `HOW-TO-APPLY.md` | Step-by-step guide to deploy each file |

## Why It Matters

| Signal | Without | With |
|--------|---------|------|
| FAQPage JSON-LD | 24% citation rate | **65% citation rate** (+41%) |
| Correct robots.txt | Invisible to ChatGPT/Perplexity | Crawlable and indexable |
| Schema.org markup | AI can't identify your business | Appears in AI Overviews |

Research sources: [Princeton GEO paper (2023)](https://arxiv.org/abs/2311.09735) · [Digital Bloom citation study](https://www.digitalbloom.agency/research)

## Install & Usage

```bash
pip install causabi-geo

# Analyze
geo-optimizer analyze https://yourdomain.com
geo-optimizer analyze https://yourdomain.com --json

# Fix (generates ready-to-deploy files)
geo-optimizer fix https://yourdomain.com
geo-optimizer fix https://yourdomain.com --output ./out

# Fix with AI-generated FAQ (requires Gemini API key)
geo-optimizer fix https://yourdomain.com --api-key YOUR_GEMINI_KEY
```

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).

## Scoring

| Category | Max | Signal |
|----------|-----|--------|
| robots.txt | 20 | GPTBot, ClaudeBot, PerplexityBot, Applebot, Bytespider and more |
| Schema.org | 25 | Organization, SoftwareApplication, WebSite, LocalBusiness |
| FAQ Schema | 20 | FAQPage JSON-LD with quality questions |
| Content depth | 15 | Word count, headers, link structure |
| Brand signals | 10 | LinkedIn, GitHub, Wikipedia sameAs links |
| Freshness | 10 | Date of last content update |

## Full Platform

The CLI analyzes a single page. **[causabi.com](https://causabi.com)** provides:

- Deep multi-page crawl
- Weekly citation monitoring (ChatGPT, Perplexity, Gemini, Yandex)
- Auto-generated fixes with AI (llms.txt, FAQ, Schema)
- Free first audit · no credit card

## License

MIT — see [LICENSE](LICENSE)
