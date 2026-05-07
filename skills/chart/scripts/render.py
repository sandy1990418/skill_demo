"""Render harness for chart skill — runs a chart script with CHART_OUTPUT env var."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script", help="Path to chart .py script to execute")
    parser.add_argument("--output", default="/tmp/chart_review.png", help="Output PNG path")
    parser.add_argument("--cleanup", action="store_true", help="Delete script after render")
    args = parser.parse_args()

    script_path = Path(args.script).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["CHART_OUTPUT"] = str(output_path)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        env=env,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"ERROR: chart script failed (exit {result.returncode})", file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    if not output_path.exists():
        print(f"ERROR: script ran but {output_path} was not created", file=sys.stderr)
        sys.exit(1)

    if args.cleanup:
        script_path.unlink(missing_ok=True)

    print(str(output_path))


if __name__ == "__main__":
    main()
