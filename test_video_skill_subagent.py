"""Subagent example: compare multiple videos in parallel.

Each video is handled by an isolated `video-processor` subagent that runs the
`video-meeting-notes` skill. The main agent only receives the resulting notes.md
paths, then synthesises a cross-video comparison without ever loading the full
transcripts into its own context.

Usage:
    OPENAI_API_KEY=sk-... .venv/bin/python test_video_skill_subagent.py \
        /tmp/vmn_test/input.mp4 \
        https://youtu.be/<another> \
        ...
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.local_shell import LocalShellBackend
from langchain_openai import ChatOpenAI


PROJECT_ROOT = Path(__file__).parent.resolve()
SKILLS_DIR = PROJECT_ROOT / "skills"


# --- model ---------------------------------------------------------------
agent_model = ChatOpenAI(model="gpt-5.4-nano", temperature=0)
backend = LocalShellBackend(root_dir=str(PROJECT_ROOT), virtual_mode=False)


# --- subagent ------------------------------------------------------------
# Description is what the main agent reads to decide when to delegate.
# Be concrete: input shape, output shape, scope.
video_processor = {
    "name": "video-processor",
    "description": (
        "Process ONE video (local path or YouTube URL) into illustrated "
        "markdown notes using the video-meeting-notes skill. "
        "Input: a single video path or URL plus an output directory. "
        "Returns: only the absolute path to the produced notes.md — "
        "NOT the markdown contents. Use this to keep the main agent's "
        "context free of long transcripts."
    ),
    "system_prompt": (
        "You are a single-video worker. Read the video-meeting-notes "
        "SKILL.md and follow it exactly: download (if URL), transcribe, "
        "extract frames, compose notes. When the pipeline finishes, "
        "respond with ONLY one line: the absolute path to notes.md. "
        "Do not paste the markdown content."
    ),
    "skills": [str(SKILLS_DIR)],   # subagent loads the same skill
}


# --- main agent ----------------------------------------------------------
# Orchestration logic lives in the skill (video-batch-compare/SKILL.md),
# not here. System prompt only needs to enforce skill-checking behaviour.
SYSTEM = """You are a helpful assistant. Before answering, ALWAYS check your
Available Skills list. If a skill matches the user's request, read its
SKILL.md and follow it exactly — including any instructions to delegate
work to subagents via the task() tool."""


agent = create_deep_agent(
    model=agent_model,
    system_prompt=SYSTEM,
    backend=backend,
    skills=[str(SKILLS_DIR)],          # main agent ALSO has the skill
    subagents=[video_processor],       # ...and can delegate via task()
)


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("ERROR: OPENAI_API_KEY required")
    if len(sys.argv) < 2:
        sys.exit("Usage: test_video_skill_subagent.py <video1> [video2] [...]")

    videos = sys.argv[1:]
    bullet_list = "\n".join(f"  {i+1}. {v}" for i, v in enumerate(videos))
    if len(videos) == 1:
        prompt = (
            f"Please process this video using the video-processor subagent "
            f"and produce illustrated meeting notes:\n  {videos[0]}\n\n"
            "Save outputs to /tmp/vmn_batch_1/ and return the notes.md path."
        )
    else:
        prompt = (
            f"Please process these {len(videos)} videos and write a comparison:\n"
            f"{bullet_list}\n\n"
            "Use the video-processor subagent for each (in parallel), then "
            "compare the resulting notes."
        )

    print(f"=== orchestrating {len(videos)} video(s) ===\n")
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})

    print("\n--- tool call trace ---")
    for msg in result["messages"]:
        for call in getattr(msg, "tool_calls", None) or []:
            args_preview = str(call.get("args", ""))[:120]
            print(f"  {call['name']}({args_preview}...)")

    print("\n--- final answer ---")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
