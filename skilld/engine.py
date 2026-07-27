"""LLM engine abstraction.

Two backends, tried in order:
  1. Anthropic SDK — if the `anthropic` package is importable and credentials
     resolve (ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN / `ant auth login`).
  2. Claude Code CLI (`claude -p`) — uses the user's existing Claude Code
     login; no API key needed. This is the zero-config default for most users.

Set SKILLD_ENGINE=cli|api to force one.
"""

import json
import os
import shutil
import subprocess

CLI_MODEL = os.environ.get("SKILLD_MODEL", "opus")
API_MODEL = os.environ.get("SKILLD_API_MODEL", "claude-opus-5")


class EngineError(RuntimeError):
    pass


def _api_available() -> bool:
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False
    return bool(
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    )


def _complete_api(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=API_MODEL,
        max_tokens=32000,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    if message.stop_reason == "refusal":
        raise EngineError("Model refused the request.")
    return "".join(b.text for b in message.content if b.type == "text")


def _complete_cli(prompt: str) -> str:
    if not shutil.which("claude"):
        raise EngineError(
            "Neither the Anthropic SDK (with credentials) nor the `claude` CLI "
            "was found. Install Claude Code, or `pip install anthropic` and set "
            "ANTHROPIC_API_KEY."
        )
    proc = subprocess.run(
        ["claude", "-p", "--output-format", "json", "--model", CLI_MODEL],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    if proc.returncode != 0:
        raise EngineError(f"claude CLI failed: {proc.stderr.strip()[:500]}")
    try:
        return json.loads(proc.stdout).get("result", "")
    except json.JSONDecodeError:
        return proc.stdout


def complete(prompt: str) -> str:
    forced = os.environ.get("SKILLD_ENGINE")
    if forced == "api":
        return _complete_api(prompt)
    if forced == "cli":
        return _complete_cli(prompt)
    if _api_available():
        return _complete_api(prompt)
    return _complete_cli(prompt)


def extract_json(text: str) -> dict:
    """Pull the first top-level JSON object out of a model response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise EngineError(f"No JSON object in model output: {text[:200]}")
    return json.loads(text[start : end + 1])
