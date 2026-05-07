---
name: data-web
description: "Use this skill whenever you need to research or gather information from the internet. Calls OpenAI's Responses API with the built-in web_search tool — the model searches and synthesizes findings with citations automatically. Trigger when the user says 'search for', 'look up', 'research', or when the data needed is not available locally."
---

# Data — Web Search Skill

## Usage

```bash
# Basic research query
python skills/data-web/scripts/search.py --query "EV market trends 2024"

# Specify model
python skills/data-web/scripts/search.py --query "AI chip market 2025" --model gpt-4o

# Save output to file
python skills/data-web/scripts/search.py --query "EV market trends 2024" --output temp/research.md
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--query` | Yes | — | Research question or topic |
| `--model` | No | `gpt-4o` | OpenAI model to use |
| `--output` | No | stdout | Write to file instead of stdout |

## How It Works

Uses **OpenAI Responses API** with `web_search_preview` tool — the model performs live web searches, synthesizes results, and includes inline citations. No manual URL fetching needed.

## Writing Good Queries

Include:
- **Specific scope**: `"EV market 2024-2025"` not `"EVs"`
- **What you need**: `"market size, top 5 manufacturers, YoY growth"`
- **Time range**: helps the model filter for recent data
- **Format hint**: `"return as a markdown table"` if needed

Example:
```bash
python skills/data-web/scripts/search.py \
  --query "Global EV market 2024: market size, top 5 manufacturers by share, YoY growth. Include source for every number." \
  --output temp/ev_research.md
```

## Output Format

```markdown
# Research: <query>

## Key Findings
- Finding [Source: URL]

## Statistics & Data Points
| Metric | Value | Source |
|--------|-------|--------|

## Gaps & Caveats
...

## Extracted Citations
1. [Title](URL)
```

## Environment

```bash
export OPENAI_API_KEY=sk-...
```

## Dependencies

```bash
pip install openai
```
