---
name: table
description: "Use this skill whenever you need to create a styled data table — as a PNG image (for slides/reports), Excel file, or CSV. Input is JSON or CSV data; output is a formatted file. Trigger when the user says 'make a table', 'format this data as a table', 'export to Excel', or when structured data needs tabular presentation."
---

# Table Skill

## Usage

```bash
# PNG table (for embedding in slides)
python skills/table/scripts/generate.py --data data.json --output temp/table.png

# With title
python skills/table/scripts/generate.py --data data.json --output temp/table.png --title "Sales Summary"

# Excel
python skills/table/scripts/generate.py --data data.json --output temp/table.xlsx

# CSV
python skills/table/scripts/generate.py --data data.json --output temp/table.csv
```

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--data` | Yes | — | Path to JSON or CSV data file |
| `--output` | No | `temp/table.png` | Output path — extension sets format |
| `--title` | No | — | Table title (PNG only) |

## Output Format by Extension

| Extension | Output |
|-----------|--------|
| `.png` | Styled image (dark header, alternating rows) |
| `.xlsx` | Excel with formatted header + alternating rows |
| `.csv` | Raw CSV, no formatting |

## Data Format

JSON (list-of-dicts):
```json
[
  {"Name": "Product A", "Q1": 120, "Q2": 145},
  {"Name": "Product B", "Q1": 98,  "Q2": 110}
]
```

## PNG Style

- Header: dark navy background (`#1E2761`), white bold text
- Alternating rows: white / light gray (`#F5F5F5`)
- Font: 11pt, centered
- Auto-sized height based on row count

## Dependencies

```bash
pip install matplotlib pandas openpyxl
```
