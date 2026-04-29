"""End-to-end test: ask the deep agent to run the video-meeting-notes skill.

Usage:
    OPENAI_API_KEY=sk-... .venv/bin/python test_video_skill.py [video-path-or-youtube-url]

If no argument is given, falls back to /tmp/vmn_test/input.mp4 (downloaded earlier).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.local_shell import LocalShellBackend
from langchain_core.callbacks import BaseCallbackHandler
from langchain_openai import ChatOpenAI


class SubagentTracer(BaseCallbackHandler):
    """Tag tool calls as [main] or [subagent].

    task() is synchronous — subagent runs between on_tool_start(task)
    and on_tool_end(task). Track open task run_ids to classify calls.
    """

    def __init__(self):
        super().__init__()
        self._open_tasks: set = set()   # run_ids of in-flight task() calls

    def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
        name = serialized.get("name", "?")
        if name == "task":
            self._open_tasks.add(run_id)
            tag = "[main]   "           # task() itself is a main-agent call
        else:
            tag = "[subagent]" if self._open_tasks else "[main]   "
        preview = str(input_str)[:100].replace("\n", " ")
        print(f"  {tag} {name}({preview}...)")

    def on_tool_end(self, output, *, run_id, **kwargs):
        self._open_tasks.discard(run_id)   # task() closed → back to main


PROJECT_ROOT = Path(__file__).parent.resolve()
SKILLS_DIR = PROJECT_ROOT / "skills"

DEFAULT_INPUT = "/tmp/vmn_test/input.mp4"


# Agent orchestrator. Cheap local model is fine — the heavy lifting is in scripts.
# Swap to ChatOpenAI(model="gpt-4o-mini") if LM Studio not running.
agent_model = ChatOpenAI(
    model="gpt-5.4-nano",
    temperature=0,
)

backend = LocalShellBackend(root_dir=str(PROJECT_ROOT), virtual_mode=False)

SYSTEM = """You are a helpful assistant. Before answering, ALWAYS check your
Available Skills list. If a skill matches, read its SKILL.md with `read_file`
and follow its instructions exactly, including running scripts via the
execute tool. Pass user-provided paths through to scripts verbatim — do not
invent or modify paths."""

agent = create_deep_agent(
    model=agent_model,
    system_prompt=SYSTEM,
    backend=backend,
    skills=[str(SKILLS_DIR)],
)


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("ERROR: OPENAI_API_KEY required (used by transcribe.py and compose_notes.py)")

    video = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    out_dir = "/tmp/vmn_run"

    prompt = (
        f"Please use the skill to turn the video at "
        f"`{video}` into illustrated markdown notes. "
        f"Save all outputs under `{out_dir}/`. "
        f"When done, print the final notes.md path and the first 30 lines of it."
    )

    print(f"=== running skill on {video} ===\n")
    print("--- tool call trace (main agent only) ---")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": prompt}]},
        config={"callbacks": [SubagentTracer()]},
    )

    print("\n--- final answer ---")
    print(result["messages"][-1].content)

    # Proof that subagent ran (written by SKILL.md instruction)
    log = Path("/tmp/vmn_subagent.log")
    if log.exists():
        print("\n--- subagent log (proof) ---")
        print(log.read_text())


if __name__ == "__main__":
    main()
