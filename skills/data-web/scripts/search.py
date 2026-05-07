"""
Web research using OpenAI Responses API with built-in web_search tool.

Usage:
    python search.py --query "EV market trends 2024" [--model gpt-4o] [--output result.md]

Output: structured markdown with findings + citations to stdout (or --output file).
"""

import argparse
import os
import sys
from pathlib import Path


SYSTEM_PROMPT = """You are a research assistant. When given a research question:
1. Search the web for relevant, up-to-date information.
2. Synthesize findings into a clear structured report.
3. Include a source URL citation for EVERY statistic or fact.
4. Format your response as markdown with these sections:
   ## Key Findings
   ## Statistics & Data Points (as a markdown table)
   ## Gaps & Caveats
   ## Sources (numbered list with URLs)"""


def search_with_openai(query: str, model: str) -> tuple[str, list[dict]]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    response = client.responses.create(
        model=model,
        instructions=SYSTEM_PROMPT,
        tools=[{"type": "web_search_preview"}],
        input=query,
    )

    text = response.output_text

    citations = []
    for item in response.output:
        if item.type == "message":
            for content in item.content:
                for ann in getattr(content, "annotations", []):
                    if ann.type == "url_citation":
                        citations.append({"url": ann.url, "title": getattr(ann, "title", "")})

    return text, citations


def main():
    parser = argparse.ArgumentParser(description="Web research via OpenAI web_search")
    parser.add_argument("--query", required=True, help="Research question or topic")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use (default: gpt-4o)")
    parser.add_argument("--output", help="Write result to this file instead of stdout")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("[error] OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print(f"[search] query: {args.query}", file=sys.stderr)
    print(f"[search] model: {args.model}", file=sys.stderr)

    try:
        content, citations = search_with_openai(args.query, args.model)
    except Exception as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)

    result = f"# Research: {args.query}\n\n{content}"

    if citations:
        result += "\n\n---\n\n## Extracted Citations\n"
        for i, c in enumerate(citations, 1):
            result += f"{i}. [{c['title'] or c['url']}]({c['url']})\n"

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"[done] written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
