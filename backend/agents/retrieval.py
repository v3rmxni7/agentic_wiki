# Retrieval: pulls full bodies for notes the master agent flagged plus any whose
# title words overlap the query. No LLM call, just string matching.
from __future__ import annotations

from backend.tools import notes as notes_tool


def retrieve(query: str, related_slugs: list[str], limit: int = 5) -> dict[str, str]:
    query_words = {w.lower() for w in query.replace("?", "").split() if len(w) > 3}
    chosen: list[str] = list(dict.fromkeys(related_slugs))
    for n in notes_tool.list_notes():
        if n.slug in chosen:
            continue
        title_words = {w.lower() for w in n.title.split()}
        if query_words & title_words:
            chosen.append(n.slug)
    chosen = chosen[:limit]
    out: dict[str, str] = {}
    for slug in chosen:
        body = notes_tool.read_body(slug)
        if body:
            out[slug] = body
    return out
