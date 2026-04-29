# Pipeline tuning

## Threshold per content type

| Content | `--threshold` | `--min-scene-len` |
|---|---|---|
| Slide-heavy talk | 20 | 3.0 |
| Whiteboard / static talking-head | 12 | 4.0 |
| Demo with screen recording | 27 | 2.0 |
| Edited video (cuts, b-roll) | 30 | 1.0 |

If `extract_frames.py` produces 0 frames, lower the threshold. If it produces hundreds, raise it.

## Whisper model choice

- `whisper-1` — segment-level timestamps via `verbose_json`. Default. Costs ~$0.006/min.
- `gpt-4o-transcribe` — better accuracy but unreliable timestamps. Avoid for this skill.
- `gpt-4o-mini-transcribe` — cheaper variant, same caveat as above.

## LLM model for composing

- `gpt-4o-mini` — sufficient for topic chunking + bullet summaries. Default.
- `gpt-4o` — use if transcript is dense / technical.

## Long videos

OpenAI audio API caps at 25 MB upload. `transcribe.py` already extracts mono 16 kHz audio which keeps ~90 min under the cap. For longer content, split before transcribing:

```
ffmpeg -i long.mp4 -t 3600 -c copy part1.mp4
ffmpeg -i long.mp4 -ss 3600 -c copy part2.mp4
```

Run pipeline on each part and concatenate the `notes.md` outputs.
