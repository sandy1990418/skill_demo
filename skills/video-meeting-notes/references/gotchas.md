# Gotchas

## Setup

- `OPENAI_API_KEY` must be exported. The transcribe and compose scripts both fail loudly if missing.
- `ffmpeg` must be on PATH. `transcribe.py` calls it directly to extract audio.

## Transcription

- OpenAI audio upload limit is 25 MB. The audio is extracted as 16 kHz mono mp3, which keeps roughly 90 min under the cap. For longer videos, split first (see `pipeline.md`).
- If `--language` is wrong, Whisper still produces output but quality drops sharply. Prefer auto-detect unless you know the language.
- Whisper segment timestamps are utterance-level, not word-level. They can drift by 1–2 seconds. This is fine for image alignment but not for subtitle work.

## Frame extraction

- Static talking-head videos may yield 0 keyframes at default threshold. Lower to 12–15.
- Slide decks may yield too many keyframes (one per build animation). Raise threshold to 30+ and `--min-scene-len` to 4.
- The first frame (t=0) is always saved as `frame_000.jpg` so even videos with zero cuts get one image.

## Alignment

- A section may contain multiple keyframes; the composer caps at `--max-images-per-section`.
- A section may contain zero keyframes (rare but possible if scene cuts cluster). Do NOT fabricate or reuse an image — leave the section image-less.
- Keyframe filenames sort lexicographically by index, NOT by timestamp. Always use `frame_times.json` to map filename → time.

## Compose

- `--segment-strategy topic` makes one LLM call with the full transcript. For >2 hours of content this can exceed model context. Use `whisper` strategy as fallback.
- The LLM occasionally hallucinates section titles unrelated to the content. Re-run with a different `--model` or temperature 0 if this happens.
