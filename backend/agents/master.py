# Master agent: classifies the user query into one of four intents and picks a
# canonical topic name plus up to three already-existing slugs to bring along.
from __future__ import annotations

from backend.agents.base import SONNET, call_json
from backend.schemas import Intent, IntentPlan
from backend.tools import notes as notes_tool
from backend.tools.graph import links_in_map

SYSTEM = """You are the MasterAgent of a self-evolving markdown knowledge wiki.

Your job: classify a user query into ONE of four intents and pick the canonical topic name.

Intents:
- NEW_TOPIC: the query asks about something not yet covered by any existing note
- EXTEND_TOPIC: the query deepens or adds to a single existing note
- COMPARE: the query asks to compare/contrast TWO or more existing or related topics
- DEEP_DIVE: the query asks for a detailed exploration that should be split into sub-notes under a parent

You will be given the current notes index (slug | title | tags | coverage | summary). Use it.

Rules:
- If a note on the exact topic already exists and has coverage stub/partial, prefer EXTEND_TOPIC
- If the query explicitly compares ("vs", "difference between", "compare"), pick COMPARE
- If the query asks for a broad multi-faceted exploration ("everything about", "deep dive"), pick DEEP_DIVE
- Otherwise NEW_TOPIC
- Canonical topic name: Title Case, concise (max 5 words)
- related_slugs: up to 3 existing slugs from the index that are relevant; [] if none

Output JSON matching this schema:
{"intent": "NEW_TOPIC|EXTEND_TOPIC|COMPARE|DEEP_DIVE", "topic": "...", "related_slugs": [...], "rationale": "..."}
"""


def plan(query: str) -> IntentPlan:
    index = notes_tool.notes_index(links_in_map=links_in_map())
    user = f"Notes index:\n{index}\n\nUser query: {query}"
    mock = IntentPlan(intent=Intent.NEW_TOPIC, topic=query.strip().title()[:60], related_slugs=[], rationale="mock mode")
    return call_json(SYSTEM, user, IntentPlan, model=SONNET, max_tokens=600, mock_instance=mock)
