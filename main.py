"""Deep Agent with skills loaded from the local skills/ directory."""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

ROOT_DIR = Path(__file__).parent
SKILLS_PATH = "/skills/"
LOG_DIR = ROOT_DIR / "logs"


def _env_str(name: str) -> str:
    return os.getenv(name, "").strip()


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _lm_studio_model_name() -> str:
    return _env_str("LM_STUDIO_MODEL")


def _anthropic_model_name() -> str:
    return _env_str("ANTHROPIC_MODEL")


def _openai_model_name() -> str:
    return _env_str("OPENAI_MODEL")


def _looks_like_anthropic_model(model_name: str) -> bool:
    normalized = model_name.strip().lower()
    return normalized.startswith("claude") or normalized.startswith("anthropic:")


def _anthropic_base_url() -> str:
    return os.getenv(
        "ANTHROPIC_BASE_URL",
        os.getenv("LM_STUDIO_ANTHROPIC_BASE_URL", "http://127.0.0.1:3456"),
    ).strip()


def _openai_base_url() -> str:
    explicit = _env_str("OPENAI_BASE_URL")
    lm_studio_base = _env_str("LM_STUDIO_BASE_URL")
    if explicit:
        return explicit
    if lm_studio_base:
        return lm_studio_base

    # LM Studio's OpenAI-compatible server is separate from its Anthropic bridge.
    # Do not derive the /v1 base URL from ANTHROPIC_BASE_URL, or fallback will hit
    # the wrong port for local models such as gemma.
    if _lm_studio_model_name():
        return "http://127.0.0.1:1234/v1"

    return "http://127.0.0.1:1234/v1"


def _make_anthropic_model(preferred_model: str | None = None):
    model_name = preferred_model or _anthropic_model_name() or _lm_studio_model_name()
    if not model_name:
        raise ValueError("ANTHROPIC_MODEL or LM_STUDIO_MODEL is required when using ChatAnthropic.")

    return ChatAnthropic(
        model_name=model_name,
        base_url=_anthropic_base_url(),
        api_key=os.getenv(
            "ANTHROPIC_API_KEY",
            os.getenv("ANTHROPIC_AUTH_TOKEN", os.getenv("LM_STUDIO_API_KEY", "lmstudio")),
        ),
        temperature=0,
        streaming=True,
    )


def _make_openai_model(preferred_model: str | None = None):
    model_name = preferred_model or _openai_model_name() or _lm_studio_model_name() or _anthropic_model_name()
    if not model_name:
        raise ValueError("OPENAI_MODEL, LM_STUDIO_MODEL, or ANTHROPIC_MODEL is required when using ChatOpenAI.")

    return ChatOpenAI(
        model=model_name,
        base_url=_openai_base_url(),
        api_key=os.getenv("OPENAI_API_KEY", os.getenv("LM_STUDIO_API_KEY", "lm-studio")),
        temperature=0,
        streaming=True,
        use_responses_api=False,
    )


def _make_model():
    provider = _env_str("MODEL_PROVIDER").lower() or "auto"
    anthropic_model = _anthropic_model_name()
    lm_studio_model = _lm_studio_model_name()
    openai_model = _openai_model_name()

    if provider in {"anthropic", "lmstudio-anthropic"}:
        return _make_anthropic_model(preferred_model=anthropic_model or lm_studio_model)

    if provider == "lmstudio-openai":
        return _make_openai_model(preferred_model=lm_studio_model or openai_model or anthropic_model)

    if provider == "openai":
        if _env_str("OPENAI_BASE_URL"):
            return _make_openai_model(preferred_model=openai_model or lm_studio_model or anthropic_model)
        return openai_model or "openai:gpt-5.4-nano"

    if lm_studio_model:
        if _looks_like_anthropic_model(lm_studio_model):
            return _make_anthropic_model(preferred_model=lm_studio_model)
        return _make_openai_model(preferred_model=lm_studio_model)

    if anthropic_model:
        return _make_anthropic_model(preferred_model=anthropic_model)

    if openai_model and _env_str("OPENAI_BASE_URL"):
        return _make_openai_model(preferred_model=openai_model)

    return openai_model or "openai:gpt-5.4-nano"


def _model_label(model) -> str:
    if isinstance(model, str):
        return model

    model_name = getattr(model, "model_name", None) or getattr(model, "model", "unknown-model")
    base_url = (
        getattr(model, "base_url", None)
        or getattr(model, "anthropic_api_url", None)
        or getattr(model, "openai_api_base", None)
        or "default-base-url"
    )
    return f"{model_name} via {base_url}"


def _is_lm_studio_template_error(exc: Exception) -> bool:
    text = str(exc)
    return (
        "Error rendering prompt with jinja template" in text
        or "Cannot call something that is not a function: got UndefinedValue" in text
    )


def _should_fallback_to_openai(exc: Exception, model) -> bool:
    return (
        isinstance(model, ChatAnthropic)
        and bool(_lm_studio_model_name())
        and _env_flag("LM_STUDIO_FALLBACK_TO_OPENAI", True)
        and _is_lm_studio_template_error(exc)
    )


def _make_log_path() -> Path:
    LOG_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"session_{ts}.jsonl"


def _json_default(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return str(obj)


def _log(log_file: Path, record: dict) -> None:
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, default=_json_default) + "\n")


_agent_stack: list[str] = ["main"]

_CHAIN_NOISE = {"", "LangGraph", "tools", "agent"}


def _print_event(event: dict) -> None:
    kind = event.get("event")
    name = event.get("name", "")
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")

    if kind == "on_chain_start" and name not in _CHAIN_NOISE:
        _agent_stack.append(name)
        print(f"\n[{ts}] >> {name}", flush=True)

    elif kind == "on_chain_end" and name not in _CHAIN_NOISE:
        if len(_agent_stack) > 1:
            _agent_stack.pop()

    elif kind == "on_chat_model_stream":
        chunk = event.get("data", {}).get("chunk")
        if chunk:
            for block in getattr(chunk, "content", []):
                if isinstance(block, dict) and block.get("type") == "text":
                    print(block["text"], end="", flush=True)
            if isinstance(getattr(chunk, "content", None), str):
                print(chunk.content, end="", flush=True)

    elif kind == "on_tool_start":
        agent = _agent_stack[-1]
        inputs = event.get("data", {}).get("input", {})
        print(f"\n[{ts}] [{agent}] TOOL {name} ← {json.dumps(inputs, ensure_ascii=False)}", flush=True)

    elif kind == "on_tool_end":
        agent = _agent_stack[-1]
        output = event.get("data", {}).get("output")
        preview = str(output)[:200].replace("\n", " ")
        print(f"[{ts}] [{agent}] TOOL {name} → {preview}", flush=True)


_RETRYABLE = ("rate limit", "rate_limit", "429", "overloaded", "timeout", "connection")
_MAX_RETRIES = 15


def _is_retryable(exc: Exception) -> float | None:
    """Return seconds to wait if exception is retryable, else None."""
    import re

    # Unwrap ExceptionGroup (asyncio TaskGroup wraps exceptions this way)
    candidates = [exc]
    if isinstance(exc, BaseExceptionGroup):
        candidates.extend(exc.exceptions)

    for e in candidates:
        msg = str(e).lower()
        if any(k in msg for k in _RETRYABLE):
            m = re.search(r"try again in ([0-9.]+)s", msg)
            return float(m.group(1)) + 0.5 if m else 5.0
    return None


async def run_turn(agent, user_input: str, config: dict, log_file: Path) -> None:
    _log(log_file, {"ts": datetime.now(timezone.utc).isoformat(), "role": "user", "content": user_input})

    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            print("\nAgent: ", end="", flush=True)
            async for event in agent.astream_events(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config,
                version="v2",
            ):
                _print_event(event)
                if event.get("event") != "on_chat_model_stream":
                    _log(log_file, {"ts": datetime.now(timezone.utc).isoformat(), "event": event})
            print()
            return
        except Exception as exc:
            wait = _is_retryable(exc)
            if wait is None or attempt == _MAX_RETRIES:
                print(f"\n[error] {exc}", flush=True)
                raise
            print(f"\n[retry {attempt}/{_MAX_RETRIES}] {exc.__class__.__name__}: {exc} — waiting {wait:.1f}s", flush=True)
            await asyncio.sleep(wait)


def _build_agent(model):
    backend = LocalShellBackend(root_dir=ROOT_DIR, virtual_mode=False, inherit_env=True)
    return create_deep_agent(
        model=model,
        backend=backend,
        skills=[SKILLS_PATH],
    )


async def main() -> None:
    model = "openai:gpt-5.4-mini" #_make_model() #
    agent = _build_agent(model)

    config = {"configurable": {"thread_id": "main"}, "recursion_limit": 1000}
    log_file = _make_log_path()
    print(f"Logging to {log_file}\n")
    print(f"Using model: {_model_label(model)}\n")

    task = (
        "Read all files /data, understand their content, "
        "then create a polished presentation and save it as /temp/output.pptx."
    )
    try:
        await run_turn(agent, task, config, log_file)
    except Exception as exc:
        if not _should_fallback_to_openai(exc, model):
            raise

        fallback_model = _make_openai_model(preferred_model=_lm_studio_model_name())
        print(
            "\nLM Studio Anthropic endpoint failed with a prompt-template error. "
            f"Retrying via OpenAI-compatible endpoint: {_model_label(fallback_model)}\n",
            flush=True,
        )
        await run_turn(_build_agent(fallback_model), task, config, log_file)


if __name__ == "__main__":
    asyncio.run(main())


# Command line: uv run main.py > all_output.txt 2>&1
# export MODEL_PROVIDER="lmstudio-openai"
# export LM_STUDIO_MODEL="gemma-4-26b-a4b-it"
# export LM_STUDIO_BASE_URL="http://127.0.0.1:1234/v1"
# export LM_STUDIO_API_KEY="lm-studio"
# uv run main.py
