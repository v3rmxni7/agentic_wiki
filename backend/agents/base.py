# Thin wrapper around the Groq client (OpenAI-compatible). call() returns text,
# call_json() forces JSON mode and validates against a Pydantic schema with one
# retry on parse failure. MOCK_MODE or a missing key skips the network.
from __future__ import annotations

import json
import os
import re
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

# model tiers - swapped in when we moved off Anthropic. Heavy goes to master +
# curator (JSON planning, reasoning). Light goes to research, linker, validator.
HEAVY = "llama-3.3-70b-versatile"
LIGHT = "llama-3.1-8b-instant"

# aliases so the agent files don't have to change
SONNET = HEAVY
HAIKU = LIGHT

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            api_key=os.environ.get("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


def is_mock() -> bool:
    return os.environ.get("MOCK_MODE", "0") == "1" or not os.environ.get("GROQ_API_KEY")


def call(
    system: str,
    user: str,
    model: str = LIGHT,
    max_tokens: int = 2000,
    cache_system: bool = True,  # groq has no prompt caching; flag kept for call sites
    mock_output: str = "",
) -> str:
    if is_mock():
        return mock_output
    resp = _get_client().chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


T = TypeVar("T", bound=BaseModel)


def _extract_json(text: str) -> str:
    # tolerant extractor for the fallback path (json mode should make this a no-op)
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    for opener, closer in [("{", "}"), ("[", "]")]:
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            c = text[i]
            if c == opener:
                depth += 1
            elif c == closer:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return text


def call_json(
    system: str,
    user: str,
    schema: Type[T],
    model: str = LIGHT,
    max_tokens: int = 2000,
    cache_system: bool = True,
    mock_instance: Optional[T] = None,
) -> T:
    if is_mock():
        if mock_instance is None:
            raise RuntimeError(f"MOCK_MODE: no mock_instance provided for {schema.__name__}")
        return mock_instance

    # groq's response_format=json_object requires the word "JSON" to appear in the prompt.
    # both conditions hold below, so JSON mode stays active.
    json_system = system + "\n\nReturn ONLY a single valid JSON object matching the schema. No prose, no code fences."
    raw = ""
    for attempt in range(2):
        try:
            resp = _get_client().chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": json_system},
                    {"role": "user", "content": user},
                ],
            )
            raw = (resp.choices[0].message.content or "").strip()
            payload = json.loads(_extract_json(raw))
            return schema.model_validate(payload)
        except Exception as e:
            if attempt == 1:
                raise RuntimeError(f"Failed to parse {schema.__name__}: {e}\nRaw: {raw[:500]}")
            user = f"{user}\n\nPrevious response could not be parsed. Error: {e}. Return a valid JSON object matching the schema."
    raise RuntimeError("unreachable")
