"""
Generate a chart from JSON data.

Usage:
    python generate.py --data data.json --type bar --output chart.png [--title "My Chart"] [--x col] [--y col]

data.json format:
    [{"label": "A", "value": 30}, {"label": "B", "value": 55}]
    or any list-of-dicts / dict-of-lists that pandas can read.

Supported --type: bar, line, pie, scatter, heatmap
"""

import argparse
import json
import os
import sys
from pathlib import Path


def load_data(path: str):
    import pandas as pd

    p = Path(path)
    if p.suffix == ".csv":
        return pd.read_csv(p)
    data = json.loads(p.read_text(encoding="utf-8"))
    return pd.DataFrame(data)


def make_chart(df, chart_type: str, x_col: str, y_col: str, title: str, output_path: str):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    PALETTE = ["#028090", "#00A896", "#02C39A", "#1E2761", "#F96167", "#F9E795"]

    fig = Figure(figsize=(12, 7))
    FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)

    x_col = x_col or df.columns[0]
    y_col = y_col or df.columns[1]

    if chart_type == "bar":
        ax.bar(df[x_col], df[y_col], color=PALETTE[: len(df)])
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.grid(axis="y", alpha=0.3)

    elif chart_type == "line":
        ax.plot(df[x_col], df[y_col], marker="o", color=PALETTE[0], linewidth=2)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.grid(alpha=0.3)

    elif chart_type == "pie":
        ax.pie(df[y_col], labels=df[x_col], colors=PALETTE, autopct="%1.1f%%", startangle=90)
        ax.axis("equal")

    elif chart_type == "scatter":
        ax.scatter(df[x_col], df[y_col], color=PALETTE[0], alpha=0.7, s=60)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.grid(alpha=0.3)

    elif chart_type == "heatmap":
        import numpy as np

        matrix = df.select_dtypes(include=[float, int]).values
        im = ax.imshow(matrix, aspect="auto", cmap="Blues")
        fig.colorbar(im, ax=ax)
        ax.set_xticks(range(len(df.select_dtypes(include=[float, int]).columns)))
        ax.set_xticklabels(df.select_dtypes(include=[float, int]).columns, rotation=45, ha="right")

    else:
        print(f"[error] unsupported chart type: {chart_type}", file=sys.stderr)
        sys.exit(1)

    ax.set_title(title or f"{chart_type.title()} Chart", fontsize=15, fontweight="bold", pad=14)
    fig.tight_layout()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate a chart from JSON/CSV data")
    parser.add_argument("--data", required=True, help="Path to JSON or CSV data file")
    parser.add_argument("--type", default="bar", choices=["bar", "line", "pie", "scatter", "heatmap"])
    parser.add_argument("--output", default="temp/chart.png", help="Output PNG path")
    parser.add_argument("--title", help="Chart title")
    parser.add_argument("--x", help="Column to use as X axis / labels")
    parser.add_argument("--y", help="Column to use as Y axis / values")
    args = parser.parse_args()

    output = os.environ.get("CHART_OUTPUT", args.output)

    print(f"[chart] loading {args.data}", file=sys.stderr)
    df = load_data(args.data)
    print(f"[chart] {df.shape[0]} rows × {df.shape[1]} cols", file=sys.stderr)

    out = make_chart(df, args.type, args.x, args.y, args.title, output)
    print(f"[done] {out}", file=sys.stderr)
    print(out)


if __name__ == "__main__":
    main()
