---
name: video-meeting-notes
description: Convert a meeting/lecture/talk video into illustrated markdown notes by transcribing speech with OpenAI Whisper, extracting scene-change keyframes, and aligning images to topic sections. Use when the user provides a video file or YouTube URL and wants a structured, image-rich summary.
---

# Video Meeting Notes

Three-stage pipeline. Run scripts in order. Each accepts `--help`; check it if unsure of args.

## When to use

- User has a `.mp4` / `.mov` / `.mkv` / `.webm` file, OR a YouTube URL
- User wants a markdown document with section headings, bullet summaries, AND embedded screenshots from the video
- Talks, lectures, demos, meeting recordings, conference sessions

## Resolving the input path

The user will give you EITHER a local file path OR a YouTube URL. Treat it as a literal string — do NOT invent paths.

1. **Local path**: convert to absolute (`realpath` or `python -c 'import os,sys;print(os.path.abspath(sys.argv[1]))' <path>`). Verify it exists with `ls -la <abs-path>` before running the pipeline. If it doesn't exist, ask the user to confirm.
2. **YouTube URL** (contains `youtube.com` or `youtu.be`): download first with
   ```
   yt-dlp -f "bv*[height<=480]+ba/b[height<=480]" --merge-output-format mp4 \
     -o '/tmp/vmn_input.%(ext)s' '<URL>'
   ```
   Then use the resulting `/tmp/vmn_input.mp4` as the video path.
3. Pick a working directory for outputs. Default: `/tmp/vmn_<short-slug>/`. Pass absolute paths to every script.

## Required environment

- `OPENAI_API_KEY` set in the environment
- `ffmpeg` on PATH
- Run scripts from the project root with `.venv/bin/python` (or whatever uv-managed python the user has)

## Pipeline

For a YouTube URL, first download with `yt-dlp -f "bv*[height<=480]+ba/b[height<=480]" -o '/tmp/vmn_input.%(ext)s' <URL>` and use the resulting file path.

```
1) scripts/transcribe.py        video.mp4   -> transcript.json
2) scripts/extract_frames.py    video.mp4   -> frames/*.jpg + frames/frame_times.json
3) scripts/compose_notes.py     ^ both       -> notes.md
```

### 1. Transcribe

```
python scripts/transcribe.py \
  --video <video-path> \
  --output /tmp/vmn_transcript.json \
  --language <iso-code>      # optional; auto-detect if omitted
```

Produces `{ "language": "...", "duration": ..., "segments": [{"start", "end", "text"}, ...] }`.

### 2. Extract keyframes

```
python scripts/extract_frames.py \
  --video <video-path> \
  --output-dir /tmp/vmn_frames \
  --threshold 27.0           # AdaptiveDetector sensitivity, lower = more cuts
  --min-scene-len 2.0        # seconds, suppresses flicker
```

Saves `frame_NNN.jpg` files plus `frame_times.json` mapping each filename to its timestamp (seconds).

### 3. Compose notes

```
python scripts/compose_notes.py \
  --transcript /tmp/vmn_transcript.json \
  --frames-dir /tmp/vmn_frames \
  --output /tmp/vmn_notes.md \
  --model gpt-4o-mini \
  --segment-strategy topic   # topic | whisper
  --max-images-per-section 2
```

`topic` strategy uses an LLM to chunk the transcript into topical sections; `whisper` uses raw whisper segments (cheaper, less coherent).

Each section gets the keyframe whose timestamp lies inside the section's time range. If multiple keyframes fall in one section, keep the first `--max-images-per-section`.

## Output format

```markdown
# {{ derived title }}

_Source: {{ video filename }} · Duration: {{ mm:ss }} · Language: {{ lang }}_

## {{ section title }}

![](frames/frame_007.jpg)

- {{ bullet summary }}
- {{ bullet summary }}

## {{ next section }}
...
```

## Gotchas

- See `references/gotchas.md` for the long list. Most common: forgetting `OPENAI_API_KEY`, video too long (split first), zero scene cuts on a static talking-head (lower `--threshold` to 15).
- See `references/output-format.md` for the full markdown spec the composer follows.
- See `references/pipeline.md` for parameter tuning per content type.
