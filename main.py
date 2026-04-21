from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.local_shell import LocalShellBackend
from deepagents.middleware.skills import _list_skills
from langchain_openai import ChatOpenAI


PROJECT_ROOT = Path(__file__).parent.resolve()
SKILLS_DIR = PROJECT_ROOT / "skills"


model = ChatOpenAI(model="openai/gpt-oss-20b", temperature=0, base_url="http://127.0.0.1:1234/v1", api_key="")

# LocalShellBackend = FilesystemBackend + execute tool. Required to run skill scripts.
backend = LocalShellBackend(root_dir=str(PROJECT_ROOT), virtual_mode=False)

agent = create_deep_agent(
    model=model,
    # system_prompt=(
    #     "You are a helpful assistant. Before answering any request, ALWAYS "
    #     "check your Available Skills list first. If a skill's description "
    #     "matches the user's task, you MUST read its SKILL.md with `read_file` "
    #     "and follow its instructions exactly, including running any scripts "
    #     "it tells you to run."
    # ),
    backend=backend,
    skills=[str(SKILLS_DIR)],
)


# Intentionally dense prose so the skill finds something to flag.
DEMO_TEXT = """
The newly architected platform leverages a microservices-based substrate
operating atop a polyglot persistence layer, facilitating extensible
heterogeneous workload orchestration while simultaneously maintaining
deterministic idempotency guarantees across downstream consumer services,
whose lifecycle events are propagated via an asynchronous event bus that
mediates backpressure through adaptive flow-control primitives. The
architecture additionally exposes observability hooks that surface latency
distributions and saturation indicators, enabling proactive capacity
rebalancing before degradation cascades manifest in user-facing surfaces.
""".strip()


def run(prompt: str) -> dict:
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    print("--- tool call trace ---")
    for msg in result["messages"]:
        for call in getattr(msg, "tool_calls", None) or []:
            args_preview = str(call.get("args", ""))[:80]
            print(f"  {call['name']}({args_preview}...)")
    print()
    return result


def verify(output: str) -> None:
    """Check the skill output follows the required structure."""
    checks = {
        "has Raw metrics header": "### Raw metrics" in output,
        "has Assessment header": "### Assessment" in output,
        "has Suggestions header": "### Suggestions" in output,
        "mentions words/sentence line": "words/sentence" in output,
        "mentions type-token ratio": "type-token ratio" in output,
        "uses OK / TOO HIGH / TOO LOW labels": any(
            tag in output for tag in ("OK", "TOO HIGH", "TOO LOW")
        ),
    }
    print()
    print("--- skill verification ---")
    for label, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    passed = sum(checks.values())
    print(f"  {passed}/{len(checks)} checks passed")


def main():
    print("=== skills discovered by backend ===")
    for skill in _list_skills(backend, str(SKILLS_DIR)):
        print(f"- {skill['name']}: {skill['description'][:80]}...")
    print()

    print("=== running text-stats demo ===")
    prompt = (
        "Please analyze the following text using the text-stats skill. "
        "Target content type: blog-post.\n\n"
        f"{DEMO_TEXT}"
    )
    result = run(prompt)
    answer = result["messages"][-1].content
    print(answer)
    verify(answer)


if __name__ == "__main__":
    main()
