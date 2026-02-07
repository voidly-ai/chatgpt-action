# Voidly OpenAI Action

OpenAI GPT Action spec for the Voidly Global Censorship Index.

## Setup in ChatGPT

1. Go to [ChatGPT GPT Builder](https://chat.openai.com/gpts/editor)
2. Create new GPT or edit existing
3. Go to **Configure** → **Actions** → **Create new action**
4. Import `openapi.yaml` or paste its contents
5. Save and test

## Available Actions

| Action | Description |
|--------|-------------|
| `getCensorshipIndex` | Get global rankings for all 50+ countries |
| `getCountryStatus` | Get detailed data for a specific country |
| `getMethodology` | How we calculate scores |

## Example Prompts

- "What are the most censored countries right now?"
- "Is internet censored in Iran?"
- "Compare China and Russia's censorship levels"
- "What services are blocked in Turkey?"

## Data

- **11.7M** live OONI measurements
- **1B+** historical measurements (10-year archive)
- **120+** countries monitored
- Updated every 5 minutes

## No Auth Required

Public endpoints - no API key needed for basic queries.

## Links

- Website: https://voidly.ai/censorship-index
- MCP Server: `npx @voidly/mcp-server`
- API Docs: https://api.voidly.ai/data/methodology
