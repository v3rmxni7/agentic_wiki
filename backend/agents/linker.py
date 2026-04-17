# Linker: scans a just-written note for mentions of other note titles and wraps them
# in [[wikilinks]]. Rule-based first; falls back to the model only if nothing matched.
# After that, mirrors the outgoing links as backlinks under each target's Related section.
from __future__ import annotations

import re

from backend.agents.base import HAIKU, call, is_mock
from backend.tools import notes as notes_tool


SYSTEM = """You are the LinkerAgent of a markdown wiki.

You will be given:
- the body of a note that was just created or updated
- a list of (slug, title) pairs for ALL other notes in the wiki

Your job: return the SAME body with `[[Title]]` wikilinks inserted where another note's title
appears naturally in prose. Rules:
- Only link concepts that match an existing title (case-insensitive, whole-word).
- Link each concept at most ONCE per note (first occurrence only).
- Do not link the note's own title.
- Do not change anything else: no rewording, no adding sentences, no removing content.
- Preserve all YAML/markdown formatting exactly.
- If nothing should be linked, return the body unchanged.

Return ONLY the resulting markdown body. No explanations, no code fences."""


def _rule_based_link(body: str, current_slug: str, others: list[tuple[str, str]]) -> str:
    result = body
    for slug, title in others:
        if slug == current_slug or not title:
            continue
        if f"[[{title}]]" in result:
            continue
        pattern = re.compile(rf"(?<!\[)(?<!\w){re.escape(title)}(?!\w)(?!\]\])", re.IGNORECASE)
        m = pattern.search(result)
        if m:
            start, end = m.span()
            result = result[:start] + f"[[{title}]]" + result[end:]
    return result


def link(current_slug: str, body: str) -> str:
    others = [(n.slug, n.title) for n in notes_tool.list_notes() if n.slug != current_slug]
    linked = _rule_based_link(body, current_slug, others)
    if is_mock():
        return linked
    # fall back to the model only if the rule pass found nothing
    if linked == body and others:
        pairs = "\n".join(f"- {s} | {t}" for s, t in others)
        user = f"Other notes:\n{pairs}\n\nNote body:\n{body}"
        try:
            out = call(SYSTEM, user, model=HAIKU, max_tokens=2000)
            if out and "##" in out:
                return out
        except Exception:
            return linked
    return linked


def mirror_backlinks(touched_slug: str, touched_title: str) -> list[str]:
    post = notes_tool.read_raw(touched_slug)
    if not post:
        return []
    mentioned_titles = set(notes_tool.extract_wikilinks(post.content))
    title_to_slug = {n.title.lower(): n.slug for n in notes_tool.list_notes()}
    updated: list[str] = []
    for title in mentioned_titles:
        target_slug = title_to_slug.get(title.lower())
        if not target_slug or target_slug == touched_slug:
            continue
        if notes_tool.append_backlink_note(target_slug, touched_title):
            updated.append(target_slug)
    return updated
