---
name: chart
description: "Use this skill whenever you need to create a chart or graph — bar, line, pie, scatter, or heatmap. Input is a JSON or CSV data file; output is a PNG image. Trigger when the user says 'make a chart', 'plot this data', 'visualize', or when research/extracted data needs to be turned into a visual for a report or presentation."
---

# Chart Skill

## Usage

```bash
# Bar chart (default)
python skills/chart/scripts/generate.py --data data.json --output temp/chart.png

# Specify chart type and columns
python skills/chart/scripts/generate.py \
  --data data.json \
  --type line \
  --x "Year" \
  --y "Revenue" \
  --title "Revenue Over Time" \
  --output temp/revenue_chart.png
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--data` | Yes | — | Path to JSON or CSV data file |
| `--type` | No | `bar` | Chart type: `bar`, `line`, `pie`, `scatter`, `heatmap` |
| `--output` | No | `temp/chart.png` | Output PNG path |
| `--title` | No | auto | Chart title |
| `--x` | No | first col | X-axis / label column |
| `--y` | No | second col | Y-axis / value column |

## Data Format

JSON (list-of-dicts):
```json
[
  {"Category": "A", "Value": 30},
  {"Category": "B", "Value": 55},
  {"Category": "C", "Value": 20}
]
```

CSV also supported — pass directly with `--data file.csv`.

## Chart Type Guide

| Type | Best For |
|------|----------|
| `bar` | Comparing categories |
| `line` | Trends over time |
| `pie` | Part-to-whole (≤6 slices) |
| `scatter` | Correlation between two variables |
| `heatmap` | Matrix / intensity data |

## Render-Review-Refine

After generating, **always read the PNG** with the `Read` tool to visually verify:

- Title visible and not cut off
- Axis labels readable, not overlapping
- Data values proportional and correct
- Colors distinguishable
- No clipping or overflow

If issues found, adjust params and re-run (max 3 cycles).

## Dependencies

```bash
pip install matplotlib pandas
```
