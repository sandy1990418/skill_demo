#!/usr/bin/env python3
"""Transcribe a video using OpenAI Whisper, save segments JSON."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from openai import OpenAI

_ENV_FILE = Path(__file__).parents[3] / ".env"
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())


def extract_audio(video_path: Path, audio_path: Path) -> None:
    if shutil.which("ffmpeg") is None:
        sys.exit("ERROR: ffmpeg not found on PATH")
    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000",
        "-b:a", "64k", str(audio_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"ERROR: ffmpeg failed:\n{proc.stderr[-2000:]}")


def transcribe(audio_path: Path, model: str, language: str | None) -> dict:
    client = OpenAI()
    kwargs = {
        "model": model,
        "response_format": "verbose_json",
        "timestamp_granularities": ["segment"],
    }
    if language:
        kwargs["language"] = language
    with audio_path.open("rb") as f:
        kwargs["file"] = f
        resp = client.audio.transcriptions.create(**kwargs)
    data = resp.model_dump() if hasattr(resp, "model_dump") else dict(resp)
    return {
        "language": data.get("language"),
        "duration": data.get("duration"),
        "text": data.get("text"),
        "segments": [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip()}
            for s in data.get("segments", [])
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--model", default="whisper-1")
    p.add_argument("--language", default=None,
                   help="ISO code (e.g. en, zh). Auto-detect if omitted.")
    args = p.parse_args()

    if not args.video.exists():
        sys.exit(f"ERROR: video not found: {args.video}")
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("ERROR: OPENAI_API_KEY not set")

    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / "audio.mp3"
        print(f"[1/2] extracting audio -> {audio.name}", file=sys.stderr)
        extract_audio(args.video, audio)

        size_mb = audio.stat().st_size / 1024 / 1024
        if size_mb > 25:
            sys.exit(f"ERROR: audio is {size_mb:.1f} MB, exceeds OpenAI 25 MB limit. "
                     "Split the video and run pipeline on each part.")
        print(f"[2/2] transcribing ({size_mb:.1f} MB) with {args.model}", file=sys.stderr)
        result = transcribe(audio, args.model, args.language)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    n = len(result["segments"])
    print(f"OK transcribed {n} segments, lang={result['language']}, "
          f"duration={result['duration']:.1f}s -> {args.output}")


if __name__ == "__main__":
    main()
