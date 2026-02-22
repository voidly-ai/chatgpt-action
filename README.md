# Voidly OpenAI Action

OpenAI GPT Action for the **Voidly Global Censorship Index** — query real-time censorship data across 119 countries from ChatGPT.

## Setup in ChatGPT

1. Go to [ChatGPT GPT Builder](https://chat.openai.com/gpts/editor)
2. Create or edit a GPT
3. Go to **Configure** → **Actions** → **Create new action**
4. Import `openapi.yaml` or paste its contents
5. Save and test

## What It Can Do

### Core Queries
- **Censorship Index** — Global country rankings with composite scores
- **Country Status** — Detailed data for any of 119 monitored countries
- **Methodology** — How scores are calculated

### Incidents & Verification
- **Active Incidents** — Current censorship events with severity levels
- **Incident Detail** — Full report for a specific incident (e.g., `IR-2026-0142`)
- **Claim Verification** — Fact-check natural language censorship claims

### Risk Intelligence
- **Domain Accessibility** — Is a domain blocked in a specific country?
- **7-Day Forecast** — Shutdown risk predictions
- **Platform Risk** — Per-platform censorship scores
- **ISP Risk** — ISP-level censorship scoring
- **Election Risk** — Election-censorship correlation

## Example Prompts

- *"What are the most censored countries right now?"*
- *"Is Twitter blocked in Iran?"*
- *"Compare China and Russia's internet censorship"*
- *"What censorship incidents happened this week?"*
- *"Verify: WhatsApp is blocked in Turkey"*
- *"What's the censorship forecast for Egypt?"*
- *"Which ISPs in Pakistan are the worst for blocking?"*

## Data

| Metric | Value |
|--------|-------|
| Live Measurements | 11.7M |
| Documented Incidents | 5,356+ |
| Countries Tracked | 119 |
| Data Sources | OONI, IODA, CensoredPlanet, Voidly Probes |
| Update Frequency | Every 30 minutes |

## No Auth Required

All public endpoints work without an API key.

## Full API Spec

The `openapi.yaml` in this repo covers core endpoints. For the complete API with all endpoints, see [voidly.ai/api-docs](https://voidly.ai/api-docs).

## Links

- [Voidly](https://voidly.ai) — Website
- [Censorship Index](https://voidly.ai/censorship-index) — Live rankings
- [API Docs](https://voidly.ai/api-docs) — Full REST API
- [MCP Server](https://github.com/voidly-ai/mcp-server) — For Claude/Cursor (`npx @voidly/mcp-server`)

## License

MIT — see [LICENSE](LICENSE)
