"""
Aggregate and synthesize multiple data sources into one structured summary.

Usage:
    python summarize.py --files a.md b.md [--focus "..."] [--output result.md] [--model gpt-4o]

Output: structured markdown summary to stdout (or --output file).
"""

import argparse
import os
import sys
from pathlib import Path


SYSTEM_PROMPT = """You are a data synthesis expert. You will receive content from multiple sources.
Your job is to:
1. Merge and deduplicate overlapping information.
2. Note any conflicts between sources (do not silently discard either version).
3. Produce a single, well-structured markdown report with these sections:

## Executive Summary
(2-3 sentences)

## Key Findings
(bullet points, each tagged with its source filename)

## Consolidated Data
(markdown table where applicable)

## Conflicts & Gaps
(contradictions found across sources, or missing data)

## Recommended Next Steps
(actionable suggestions based on the data)

Be concise and factual. Do not invent data not present in the sources."""


def summarize(contents: list[tuple[str, str]], focus: str | None, model: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    body = ""
    for name, text in contents:
        body += f"\n\n---\n### Source: {name}\n\n{text}"

    user_message = body.strip()
    if focus:
        user_message = f"[Focus instruction: {focus}]\n\n{user_message}"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(description="Aggregate multiple data files into one summary")
    parser.add_argument("--files", required=True, nargs="+", help="Input file paths to aggregate")
    parser.add_argument("--focus", help="Extra instruction to guide synthesis")
    parser.add_argument("--output", help="Write result to this file instead of stdout")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model (default: gpt-4o)")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("[error] OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    contents = []
    for path_str in args.files:
        path = Path(path_str)
        if not path.exists():
            print(f"[error] file not found: {path_str}", file=sys.stderr)
            sys.exit(1)
        print(f"[read] {path_str}", file=sys.stderr)
        contents.append((path.name, path.read_text(encoding="utf-8")))

    print(f"[summarize] {len(contents)} source(s), model: {args.model}", file=sys.stderr)

    try:
        result = summarize(contents, args.focus, args.model)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)

    source_list = ", ".join(name for name, _ in contents)
    output = f"# Summary Report\n_Sources: {source_list}_\n\n{result}"

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"[done] written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
