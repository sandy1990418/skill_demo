---
name: data-local
description: "Use this skill whenever you need to read, parse, or extract data from local files — PDFs, Word docs, Excel/CSV, JSON, or plain text. Output is structured markdown with key facts, tables, and statistics ready for downstream skills (chart, table, pptx). Trigger when the user provides a file path or says 'read this file', 'summarize this document', 'extract data from'."
---

# Data — Local Files Skill

## Usage

```bash
# Single file
python skills/data-local/scripts/extract.py --file /data/report.pdf

# PDF with page range
python skills/data-local/scripts/extract.py --file /data/report.pdf --pages 1-10

# Entire directory (batch)
python skills/data-local/scripts/extract.py --file /data/

# Save output to file
python skills/data-local/scripts/extract.py --file /data/report.pdf --output temp/extracted.md
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--file` | Yes | File path or directory |
| `--pages` | No | PDF page range, e.g. `1-5` |
| `--output` | No | Write to file instead of stdout |

## Supported File Types

| Extension | Extracted content |
|-----------|------------------|
| `.pdf` | Text + tables (via pdfplumber) |
| `.docx` | Paragraphs + tables |
| `.xlsx` / `.xls` | All sheets as markdown tables + stats |
| `.csv` | Table + stats summary |
| `.json` | Pretty-printed JSON |
| `.txt` / `.md` | Raw text |

## Output Format

The script outputs structured markdown:

```
## Source: filename.pdf

### Page 1

<extracted text>

| Col1 | Col2 |
|------|------|
| ...  | ...  |
```

Pass this output directly to `chart`, `table`, or `pptx` skills.

## Dependencies

```bash
pip install pdfplumber pypdf python-docx openpyxl pandas tabulate
```
