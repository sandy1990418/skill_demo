---
name: summarize
description: "Use this skill whenever you need to merge, aggregate, or synthesize multiple data sources into one coherent summary. Input can be any combination of: local markdown/text files (data-local output), web research files (data-web output), or raw text pasted inline. Output is a structured markdown summary with key findings, tables, and actionable insights — ready for downstream skills (chart, table, pptx). Trigger when the user says 'summarize these', 'combine this data', 'aggregate', 'merge findings', 'write a report from', or when multiple source files need to be unified."
---

# Summarize — Data Aggregation Skill

## Usage

```bash
# Aggregate two or more files
python skills/summarize/scripts/summarize.py --files temp/research.md temp/data.md

# With a custom focus instruction
python skills/summarize/scripts/summarize.py \
  --files temp/research.md temp/data.md \
  --focus "Focus on market share and revenue trends"

# Save output to file
python skills/summarize/scripts/summarize.py \
  --files temp/a.md temp/b.md \
  --output temp/summary.md

# Override model
python skills/summarize/scripts/summarize.py \
  --files temp/a.md temp/b.md \
  --model gpt-4o
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--files` | Yes | — | One or more input file paths (space-separated) |
| `--focus` | No | — | Extra instruction to guide the synthesis (e.g. "focus on cost data") |
| `--output` | No | stdout | Write result to file instead of stdout |
| `--model` | No | `gpt-4o` | OpenAI model to use |

## How It Works

Reads all input files, concatenates them with source labels, then calls the OpenAI Chat API with a synthesis prompt. The model:
1. Deduplicates overlapping facts
2. Resolves conflicts by noting both versions
3. Produces a unified structured report

## Output Format

```markdown
# Summary Report

## Executive Summary
<2-3 sentence overview>

## Key Findings
- Finding (Source: filename)

## Consolidated Data
| Metric | Value | Source |
|--------|-------|--------|

## Conflicts & Gaps
<any contradictions found across sources>

## Recommended Next Steps
...
```

Pass this output directly to `chart`, `table`, or `pptx` skills.

## Environment

```bash
export OPENAI_API_KEY=sk-...
```

## Dependencies

```bash
pip install openai
```
