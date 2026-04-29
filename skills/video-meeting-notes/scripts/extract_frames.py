#!/usr/bin/env python3
"""Detect scene cuts in a video and save one keyframe per scene."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
from scenedetect import AdaptiveDetector, SceneManager, open_video


def detect_scenes(video_path: Path, threshold: float, min_scene_len_sec: float):
    video = open_video(str(video_path))
    fps = video.frame_rate
    sm = SceneManager()
    sm.add_detector(
        AdaptiveDetector(
            adaptive_threshold=threshold,
            min_scene_len=max(1, int(min_scene_len_sec * fps)),
        )
    )
    sm.detect_scenes(video, show_progress=False)
    return sm.get_scene_list(), fps


def save_frame(cap: cv2.VideoCapture, time_sec: float, out_path: Path) -> bool:
    cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000)
    ok, frame = cap.read()
    if not ok or frame is None:
        return False
    cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return True


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--threshold", type=float, default=27.0,
                   help="AdaptiveDetector sensitivity. Lower = more cuts. Default 27.0")
    p.add_argument("--min-scene-len", type=float, default=2.0,
                   help="Min seconds between cuts. Default 2.0")
    args = p.parse_args()

    if not args.video.exists():
        sys.exit(f"ERROR: video not found: {args.video}")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/2] detecting scenes (threshold={args.threshold}, "
          f"min-len={args.min_scene_len}s)", file=sys.stderr)
    scenes, fps = detect_scenes(args.video, args.threshold, args.min_scene_len)

    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        sys.exit(f"ERROR: cv2 cannot open {args.video}")

    timings: dict[str, float] = {}

    # Always save t=0 so static videos still get an image.
    first = "frame_000.jpg"
    if save_frame(cap, 0.0, args.output_dir / first):
        timings[first] = 0.0

    print(f"[2/2] saving keyframes for {len(scenes)} scenes", file=sys.stderr)
    for idx, (start, _end) in enumerate(scenes, start=1):
        # Use a moment after the cut so we get the new scene, not the transition.
        t = start.get_seconds() + 0.3
        name = f"frame_{idx:03d}.jpg"
        if save_frame(cap, t, args.output_dir / name):
            timings[name] = t

    cap.release()

    times_path = args.output_dir / "frame_times.json"
    times_path.write_text(json.dumps(timings, indent=2, sort_keys=True))

    print(f"OK saved {len(timings)} keyframes to {args.output_dir} "
          f"(times -> {times_path.name})")


if __name__ == "__main__":
    main()
