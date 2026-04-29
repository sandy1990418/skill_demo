#!/usr/bin/env python3
"""Align keyframes to transcript sections and write illustrated markdown notes."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from openai import OpenAI

_ENV_FILE = Path(__file__).parents[3] / ".env"
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())


def fmt_time(sec: float) -> str:
    sec = max(0, int(sec))
    return f"{sec // 60:02d}:{sec % 60:02d}"


SYSTEM_PROMPT = """You are a meeting-note writer. Given a transcript split into
timestamped segments, group them into 3-8 coherent topical sections and return
strict JSON: {"title": str, "sections": [{"title": str, "start": float,
"end": float, "bullets": [str, ...]}]}.

Rules:
- Sections must be time-ordered and cover the whole transcript without overlap.
- start/end are seconds (floats), matching segment boundaries.
- Each section has 3-6 short bullet points summarising what was said.
- Title is content-based (not the filename).
- Output ONLY the JSON object, no prose, no code fences."""


def llm_topic_segment(transcript: dict, model: str) -> dict:
    client = OpenAI()
    segs = transcript["segments"]
    seg_lines = "\n".join(
        f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segs
    )
    user = f"Transcript ({transcript.get('language')}):\n\n{seg_lines}"

    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
    )
    return json.loads(resp.choices[0].message.content)


def whisper_segment(transcript: dict) -> dict:
    """Fallback: one section per ~10 whisper segments, no LLM."""
    segs = transcript["segments"]
    if not segs:
        return {"title": "Notes", "sections": []}
    chunk = max(1, len(segs) // 6)
    sections = []
    for i in range(0, len(segs), chunk):
        group = segs[i:i + chunk]
        bullets = [g["text"] for g in group[:5] if g["text"]]
        sections.append({
            "title": f"Section {i // chunk + 1}",
            "start": group[0]["start"],
            "end": group[-1]["end"],
            "bullets": bullets,
        })
    return {"title": "Notes", "sections": sections}


def assign_frames(sections: list[dict], frame_times: dict[str, float],
                  max_per_section: int) -> dict[int, list[str]]:
    """Map section index -> list of frame filenames whose timestamp lies inside."""
    by_time = sorted(frame_times.items(), key=lambda kv: kv[1])
    out: dict[int, list[str]] = {i: [] for i in range(len(sections))}
    for name, t in by_time:
        for i, sec in enumerate(sections):
            if sec["start"] <= t < sec["end"]:
                if len(out[i]) < max_per_section:
                    out[i].append(name)
                break
        else:
            # frame is past the last section's end; tack onto last
            if sections and t >= sections[-1]["end"]:
                if len(out[len(sections) - 1]) < max_per_section:
                    out[len(sections) - 1].append(name)
    return out


def render_markdown(title: str, video_name: str, duration: float, language: str,
                    sections: list[dict], frames_per_section: dict[int, list[str]],
                    frames_relpath: str) -> str:
    lines = [f"# {title}", ""]
    lines.append(
        f"_Source: {video_name} · Duration: {fmt_time(duration)} · "
        f"Language: {language or 'unknown'}_"
    )
    lines.append("")
    for i, sec in enumerate(sections):
        lines.append(f"## {sec['title']}")
        lines.append("")
        lines.append(f"_{fmt_time(sec['start'])} – {fmt_time(sec['end'])}_")
        lines.append("")
        for fname in frames_per_section.get(i, []):
            lines.append(f"![scene]({frames_relpath}/{fname})")
        if frames_per_section.get(i):
            lines.append("")
        for b in sec.get("bullets", []):
            b = b.strip()
            if b:
                lines.append(f"- {b}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--transcript", required=True, type=Path)
    p.add_argument("--frames-dir", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--segment-strategy", choices=["topic", "whisper"], default="topic")
    p.add_argument("--max-images-per-section", type=int, default=2)
    p.add_argument("--video-name", default=None,
                   help="Display name for the source line. Defaults to transcript filename.")
    args = p.parse_args()

    if not args.transcript.exists():
        sys.exit(f"ERROR: transcript not found: {args.transcript}")
    times_path = args.frames_dir / "frame_times.json"
    if not times_path.exists():
        sys.exit(f"ERROR: {times_path} not found — run extract_frames.py first")

    transcript = json.loads(args.transcript.read_text())
    frame_times = json.loads(times_path.read_text())

    if args.segment_strategy == "topic":
        if not os.getenv("OPENAI_API_KEY"):
            sys.exit("ERROR: OPENAI_API_KEY not set (required for --segment-strategy topic)")
        print(f"[1/2] topic-segmenting transcript with {args.model}", file=sys.stderr)
        plan = llm_topic_segment(transcript, args.model)
    else:
        print("[1/2] using whisper segments as sections", file=sys.stderr)
        plan = whisper_segment(transcript)

    sections = plan.get("sections", [])
    if not sections:
        sys.exit("ERROR: segmenter produced no sections")

    print(f"[2/2] aligning {len(frame_times)} frames to {len(sections)} sections",
          file=sys.stderr)
    frames_per_section = assign_frames(sections, frame_times, args.max_images_per_section)

    # frames path is relative to where the markdown lives
    frames_rel = os.path.relpath(args.frames_dir.resolve(),
                                 args.output.parent.resolve())

    md = render_markdown(
        title=plan.get("title") or "Video notes",
        video_name=args.video_name or args.transcript.stem,
        duration=transcript.get("duration") or 0,
        language=transcript.get("language") or "",
        sections=sections,
        frames_per_section=frames_per_section,
        frames_relpath=frames_rel,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md)
    used = sum(len(v) for v in frames_per_section.values())
    print(f"OK wrote {len(sections)} sections, {used}/{len(frame_times)} frames used "
          f"-> {args.output}")


if __name__ == "__main__":
    main()
