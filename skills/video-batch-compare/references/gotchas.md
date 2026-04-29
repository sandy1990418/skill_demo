# Gotchas

## Subagent availability

This skill depends on the `video-processor` subagent. If the main agent does not have it registered, the task() call will silently fall back to general-purpose, which may not know the video pipeline. Always verify subagent is listed before starting.

## Parallel vs sequential

Call ALL task() invocations in ONE response turn to get true parallelism. If you call them one by one you lose the speed benefit — each video takes 1-2 minutes, so 3 sequential = 6 min vs 3 parallel = 2 min.

## Subagent response parsing

The video-processor subagent is instructed to return only a file path. If it returns extra prose, grep for the line starting with `/tmp`.

## Output directory collisions

Each video must get its own output dir (`/tmp/vmn_batch_1/`, `/tmp/vmn_batch_2/`, ...). If you reuse the same dir the frames from video 2 will overwrite video 1.

## YouTube URLs

If the user pastes a YouTube URL, the video-processor subagent handles the download. You do not need to download it yourself — just pass the URL as-is in the task() prompt.
