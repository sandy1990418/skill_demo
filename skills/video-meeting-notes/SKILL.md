---
name: video-meeting-notes
description: Convert a meeting/lecture/talk video into illustrated markdown notes by transcribing speech and extracting scene keyframes, then composing an image-rich summary. Use when the user provides a video file or YouTube URL and wants structured, illustrated notes.
---

# Video Meeting Notes

Orchestrates three tasks to produce illustrated notes from a video.
Tasks A and B are independent and MUST be spawned in parallel.
Task C depends on both and runs after they complete.

## Required environment

- `OPENAI_API_KEY` in the environment (used by transcription and compose tasks)
- `ffmpeg` on PATH
- Python: `.venv/bin/python`

## Step 0 — Resolve input

Determine the video path:

- **Local file**: convert to absolute path. Verify with `ls -la <path>` — stop and ask user if missing.
- **YouTube URL** (`youtube.com` or `youtu.be`): download first:
  ```
  yt-dlp -f "bv*[height<=480]+ba/b[height<=480]" --merge-output-format mp4 \
    -o '/tmp/vmn_input.%(ext)s' '<URL>'
  ```
  Use the resulting `/tmp/vmn_input.mp4` as the video path.

Pick a run directory (default `/tmp/vmn_<slug>/`) and use it for all outputs.

---

## Step 1 — Spawn Task A and Task B IN PARALLEL

Spawn both tasks in a **single response turn**. Do NOT wait for one before spawning the other.

### Task A — Transcribe audio

```
subagent_type: "general-purpose"
description:   "Transcribe audio from video to JSON segments"
prompt: |
  Task: transcribe the audio from a video file.

  Run this command exactly:
    .venv/bin/python skills/video-meeting-notes/scripts/transcribe.py \
      --video <abs-video-path> \
      --output <run-dir>/transcript.json

  When done, respond with one line: the absolute path to transcript.json.
  If it fails, respond with the full error output.
```

### Task B — Extract keyframes

```
subagent_type: "general-purpose"
description:   "Extract scene-change keyframes from video"
prompt: |
  Task: detect scene cuts in a video and save one keyframe image per scene.

  Run this command exactly:
    .venv/bin/python skills/video-meeting-notes/scripts/extract_frames.py \
      --video <abs-video-path> \
      --output-dir <run-dir>/frames

  When done, respond with one line: the absolute path to frame_times.json.
  If it fails, respond with the full error output.
```

---

## Step 2 — Wait for Task A and Task B

Both tasks must succeed before proceeding. If either fails:
- Check `references/gotchas.md` for fix suggestions
- Report the error to the user; do NOT proceed to Task C

---

## Step 3 — Spawn Task C (compose notes)

```
subagent_type: "general-purpose"
description:   "Compose illustrated markdown notes from transcript and keyframes"
prompt: |
  Task: align keyframes to transcript sections and write illustrated markdown notes.

  Run this command exactly:
    .venv/bin/python skills/video-meeting-notes/scripts/compose_notes.py \
      --transcript <run-dir>/transcript.json \
      --frames-dir <run-dir>/frames \
      --output <run-dir>/notes.md \
      --model gpt-4o-mini \
      --segment-strategy topic

  When done, respond with one line: the absolute path to notes.md.
  If it fails, respond with the full error output.
```

---

## Step 4 — Return result

Tell the user:
1. The path to `notes.md`
2. Print the first 40 lines of `notes.md` using `read_file`

## Gotchas

See `references/gotchas.md` for troubleshooting.
See `references/pipeline.md` for parameter tuning per content type.
See `references/output-format.md` for the markdown spec.
