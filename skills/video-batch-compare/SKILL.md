---
name: video-batch-compare
description: Process MULTIPLE (2 or more) meeting/lecture videos and produce a cross-video comparison report. Use ONLY when the user provides 2+ video files or URLs and wants to compare them. For a single video use video-meeting-notes instead.
---

# Video Batch Compare

This skill orchestrates the `video-processor` subagent to handle multiple videos in parallel, then synthesises a comparison. It does NOT run the video pipeline directly — that is the subagent's responsibility.

## Required subagent

This skill uses the built-in `general-purpose` subagent — no Python-side declaration needed.

## When to use

- User gives 2 or more video paths or YouTube URLs
- User asks to "compare", "contrast", or "summarise across" multiple videos
- User provides a playlist or folder of recordings from the same event / series

## Step-by-step

### 1. Collect inputs

Extract all video paths or URLs from the user's message. For each, assign an index (1, 2, 3...) and a working output directory:

```
/tmp/vmn_batch_<index>/
```

### 2. Spawn one note-generation task per video IN PARALLEL

For EACH video, spawn an independent note-generation task via the `task` tool. Each task is self-contained — it receives the video path and owns its outputs.

```
subagent_type: "general-purpose"
description:   "Generate illustrated meeting notes for video <index> of <total>: <filename>"
prompt: |
  Task: generate illustrated meeting notes from the video below.
  You have access to the video-meeting-notes skill — read its SKILL.md
  and follow it exactly (it will tell you to spawn further tasks for
  transcription, frame extraction, and composition).

  Video: `<video-path-or-url>`
  Output directory: `/tmp/vmn_batch_<index>/`

  FIRST thing: run `echo "[subagent-start] $(date)" >> /tmp/vmn_subagent.log`
  LAST thing before responding: run `echo "[subagent-done] $(date)" >> /tmp/vmn_subagent.log`

  When everything is done, respond with ONLY one line —
  the absolute path to the produced notes.md.
```

Spawn all tasks in a single response turn (parallel). Do NOT wait for one task to finish before spawning the next.

### 3. Collect results

Wait for all subagents to return. Each should return a single line: an absolute path to a `notes.md` file. If any subagent fails, note the error and continue with the successful ones.

### 4. Read all notes

Use `read_file` to read each returned `notes.md`.

### 5. Write comparison report

Produce a markdown report saved to `/tmp/vmn_batch_comparison.md` with this structure:

```markdown
# Video Comparison Report

_<N> videos processed on <date>_

## Overview table

| # | Video | Duration | Language | Sections |
|---|-------|----------|----------|---------|
| 1 | ...   | ...      | ...      | ...     |

## Shared themes

- ...

## Key differences

| Theme | Video 1 | Video 2 | ... |
|-------|---------|---------|-----|

## Per-video summaries

### Video 1 — <title>
...

### Video 2 — <title>
...

## Recommendation

<1-3 sentences on which video covers a topic best, or which to watch first>
```

Save the report, then tell the user its path and print the Overview table.

## Gotchas

- See `references/gotchas.md` for common failure modes.
- If a subagent returns more than one line, extract the line that looks like an absolute file path (starts with `/`).
- If only one video succeeds, still produce the report with a note that comparison is incomplete.
