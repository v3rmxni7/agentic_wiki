# Curator: decides what should change in the knowledge base. Outputs a
# FileOperationPlan (create/patch/merge/skip) that the writer executes verbatim.
# Keeping decide and do separate so we can audit what the model wanted to change.
from __future__ import annotations

from backend.agents.base import SONNET, call_json
from backend.schemas import FileOperation, FileOperationPlan, Intent, ResearchFinding
from backend.tools.notes import slugify

SYSTEM = """You are the CuratorAgent of a markdown knowledge wiki.

You decide how to mutate the knowledge base. You do NOT write prose. You produce a plan of file operations
that the WriterAgent will execute verbatim.

Operations (each `op`):
- "create": make a new note at `slug`. Required: title, content (markdown body), tags. Optional: parent.
- "patch": update ONE section of an existing note. Required: slug, section (e.g., "Key Ideas"), content. The content REPLACES that section, or is appended if the section is missing.
- "merge": fold `merge_with` slugs into `slug` and delete the others. Use ONLY if two notes have >80% overlap. Content should be the unified body.
- "skip": knowledge already well-covered; do nothing.

Hard rules:
- Match the `intent`:
  - NEW_TOPIC → exactly one "create"
  - EXTEND_TOPIC → one or more "patch" ops on the existing note; NEVER create a duplicate of an existing slug
  - COMPARE → one "create" for the comparison note + optional "patch" on each compared note's "Related" section
  - DEEP_DIVE → one parent "create" or "patch" + 2-4 "create" ops for sub-notes (set parent on sub-notes)
- Use ONLY kebab-case slugs derived from titles (lowercase, hyphens, no punctuation).
- Content should be clean markdown with section headings (## Summary, ## Key Ideas, ## Details, ## Related, ## Sources).
- Do NOT include YAML frontmatter. The Writer handles that.
- Keep each note focused; better to split into sub-notes than write one huge file.
- When patching a stub/partial note, expand the existing section rather than writing a new one if the topic fits.

Output JSON:
{
  "operations": [
    {"op": "create", "slug": "...", "title": "...", "content": "...", "tags": [...], "parent": null, "reason": "..."},
    ...
  ],
  "rationale": "one sentence on the overall decision"
}
"""


def plan(
    intent: Intent,
    topic: str,
    query: str,
    findings: ResearchFinding,
    existing_notes: dict[str, str],
    all_slugs: list[str],
) -> FileOperationPlan:
    ctx = "\n\n".join(
        f"--- existing note: {slug} ---\n{body[:1500]}" for slug, body in existing_notes.items()
    ) or "(no existing notes)"
    findings_str = "- " + "\n- ".join(findings.key_points)
    sources_str = ", ".join(findings.sources) if findings.sources else "(none)"
    index = ", ".join(all_slugs) if all_slugs else "(empty)"
    user = (
        f"Intent: {intent.value}\n"
        f"Canonical topic: {topic}\n"
        f"User query: {query}\n\n"
        f"All existing slugs: {index}\n\n"
        f"Research findings:\n{findings_str}\n\nSources: {sources_str}\n"
        f"Gaps filled: {', '.join(findings.gaps_filled) or '(none noted)'}\n\n"
        f"Bodies of related existing notes:\n{ctx}\n\n"
        f"Produce the FileOperationPlan JSON."
    )
    mock_slug = slugify(topic)
    mock_content = (
        f"## Summary\n{topic} - mock summary.\n\n"
        f"## Key Ideas\n" + "\n".join(f"- {p}" for p in findings.key_points) + "\n\n"
        f"## Sources\n" + "\n".join(f"- {s}" for s in findings.sources or ["Mock reference"]) + "\n"
    )
    mock = FileOperationPlan(
        operations=[FileOperation(op="create", slug=mock_slug, title=topic, content=mock_content, tags=["mock"], reason="mock mode")],
        rationale="mock curator decision",
    )
    return call_json(SYSTEM, user, FileOperationPlan, model=SONNET, max_tokens=3500, mock_instance=mock)
