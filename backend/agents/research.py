# Research: produces structured findings on the topic, biased toward filling gaps
# in whatever the existing notes already say. No web search for now, just the model.
from __future__ import annotations

from backend.agents.base import HAIKU, call_json
from backend.schemas import Intent, ResearchFinding

SYSTEM = """You are the ResearchAgent of a knowledge wiki.

Given a topic, the user's query, the intent, and the bodies of existing related notes, produce
structured factual findings. Your job is to surface content worth writing, not to write the note.

Rules:
- Prioritize gap-filling: if existing notes already cover a point, do NOT repeat it verbatim. Add depth or adjacent facts.
- Use your internal knowledge; do not invent sources. Sources should be well-known references (paper titles, textbooks, canonical URLs) only if you are confident.
- 4-8 key_points, each a crisp factual sentence.
- gaps_filled: short phrases naming what's new vs. existing notes (empty list if no prior notes).

Output JSON:
{"topic": "...", "key_points": ["...", "..."], "sources": ["..."], "gaps_filled": ["..."]}
"""


def research(query: str, topic: str, intent: Intent, existing_notes: dict[str, str]) -> ResearchFinding:
    ctx = "\n\n".join(
        f"--- existing note: {slug} ---\n{body[:1500]}" for slug, body in existing_notes.items()
    ) or "(no existing notes)"
    user = (
        f"User query: {query}\n"
        f"Canonical topic: {topic}\n"
        f"Intent: {intent.value}\n\n"
        f"Existing related notes:\n{ctx}"
    )
    mock = ResearchFinding(
        topic=topic,
        key_points=[
            f"{topic} is a concept in the relevant domain.",
            f"Common applications of {topic} include several canonical use cases.",
            f"Core mechanism of {topic} involves a recognizable pattern.",
        ],
        sources=["Mock reference"],
        gaps_filled=["core definition"] if not existing_notes else ["new angle vs existing notes"],
    )
    return call_json(SYSTEM, user, ResearchFinding, model=HAIKU, max_tokens=1200, mock_instance=mock)
