# Read/write markdown notes with YAML frontmatter. Also computes the derived
# metadata (confidence, coverage, source count) that the UI and curator rely on.
from __future__ import annotations

import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

import frontmatter

from backend.schemas import NoteMeta

KB_DIR = Path(os.environ.get("KB_DIR", "knowledge_base"))


def _kb() -> Path:
    KB_DIR.mkdir(parents=True, exist_ok=True)
    return KB_DIR


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"


def path_for(slug: str) -> Path:
    return _kb() / f"{slug}.md"


def exists(slug: str) -> bool:
    return path_for(slug).exists()


def read_raw(slug: str) -> Optional[frontmatter.Post]:
    p = path_for(slug)
    if not p.exists():
        return None
    return frontmatter.load(p)


def read_body(slug: str) -> str:
    post = read_raw(slug)
    return post.content if post else ""


def _count_sources(body: str) -> int:
    m = re.search(r"##\s+Sources?\b(.+?)(?=\n##\s|\Z)", body, re.DOTALL | re.IGNORECASE)
    if not m:
        return 0
    return len([ln for ln in m.group(1).splitlines() if ln.strip().startswith(("-", "*", "1", "2", "3", "4", "5", "6", "7", "8", "9"))])


def _section_count(body: str) -> int:
    return len(re.findall(r"^##\s+", body, re.MULTILINE))


def _coverage(body: str) -> str:
    words = len(body.split())
    sections = _section_count(body)
    if words < 80 or sections < 2:
        return "stub"
    if words < 300 or sections < 4:
        return "partial"
    return "comprehensive"


def _derive_confidence(sources: int, validator_passed: bool, coverage: str, links_in: int) -> float:
    src_score = min(sources / 3.0, 1.0) * 0.35
    val_score = (1.0 if validator_passed else 0.3) * 0.30
    cov_score = {"stub": 0.2, "partial": 0.6, "comprehensive": 1.0}[coverage] * 0.25
    link_score = min(links_in / 4.0, 1.0) * 0.10
    return round(src_score + val_score + cov_score + link_score, 2)


def extract_wikilinks(body: str) -> list[str]:
    # accepts both [[Target]] and Obsidian-style [[Target|display]]; we keep the target
    return [m.split("|", 1)[0].strip() for m in re.findall(r"\[\[([^\]]+)\]\]", body)]


def meta_from_post(slug: str, post: frontmatter.Post, links_in: int = 0) -> NoteMeta:
    body = post.content
    fm = post.metadata
    sources = _count_sources(body)
    coverage = _coverage(body)
    validator_passed = bool(fm.get("validator_passed", False))
    links_out = len(set(extract_wikilinks(body)))
    confidence = _derive_confidence(sources, validator_passed, coverage, links_in)
    return NoteMeta(
        slug=slug,
        title=str(fm.get("title", slug.replace("-", " ").title())),
        summary=str(fm.get("summary", ""))[:240],
        tags=list(fm.get("tags", []) or []),
        confidence=confidence,
        coverage=coverage,
        sources=sources,
        validator_passed=validator_passed,
        revision=int(fm.get("revision", 0) or 0),
        links_out=links_out,
        links_in=links_in,
        parent=fm.get("parent"),
        created=str(fm.get("created", "")) or None,
        updated=str(fm.get("updated", "")) or None,
    )


def list_notes(links_in_map: Optional[dict[str, int]] = None) -> list[NoteMeta]:
    out: list[NoteMeta] = []
    for p in sorted(_kb().glob("*.md")):
        slug = p.stem
        try:
            post = frontmatter.load(p)
        except Exception:
            continue
        li = (links_in_map or {}).get(slug, 0)
        out.append(meta_from_post(slug, post, links_in=li))
    return out


def notes_index(links_in_map: Optional[dict[str, int]] = None) -> str:
    # compact text index to inject into agent system prompts
    notes = list_notes(links_in_map=links_in_map)
    if not notes:
        return "(knowledge base is empty)"
    lines = []
    for n in notes:
        lines.append(f"- {n.slug} | {n.title} | tags={','.join(n.tags) or '-'} | coverage={n.coverage} | summary={n.summary or '(none)'}")
    return "\n".join(lines)


def upsert_section(body: str, section: str, new_content: str) -> str:
    # replace the body of `## {section}`, or append the section if missing
    pattern = re.compile(rf"(^##\s+{re.escape(section)}\s*\n)(.*?)(?=\n##\s|\Z)", re.DOTALL | re.MULTILINE)
    replacement = rf"\1{new_content.strip()}\n"
    new, n = pattern.subn(replacement, body)
    if n == 0:
        sep = "\n\n" if body and not body.endswith("\n\n") else ""
        new = body + sep + f"## {section}\n{new_content.strip()}\n"
    return new


def write_note(
    slug: str,
    title: str,
    body: str,
    tags: Optional[list[str]] = None,
    summary: str = "",
    parent: Optional[str] = None,
    validator_passed: bool = False,
    bump_revision: bool = True,
) -> NoteMeta:
    p = path_for(slug)
    existing = frontmatter.load(p) if p.exists() else None
    revision = int((existing.metadata.get("revision", 0) if existing else 0) or 0)
    if bump_revision:
        revision += 1
    created = (existing.metadata.get("created") if existing else None) or date.today().isoformat()
    meta = {
        "title": title,
        "summary": summary or (existing.metadata.get("summary", "") if existing else ""),
        "tags": tags if tags is not None else (existing.metadata.get("tags", []) if existing else []),
        "parent": parent or (existing.metadata.get("parent") if existing else None),
        "created": created,
        "updated": date.today().isoformat(),
        "revision": revision,
        "validator_passed": validator_passed,
    }
    post = frontmatter.Post(body, **{k: v for k, v in meta.items() if v is not None})
    with open(p, "wb") as f:
        frontmatter.dump(post, f)
    return meta_from_post(slug, post, links_in=0)


def append_backlink_note(slug: str, from_title: str) -> bool:
    # make sure the target note lists [[from_title]] under its Related section (idempotent)
    post = read_raw(slug)
    if not post:
        return False
    body = post.content
    link_token = f"[[{from_title}]]"
    if link_token in body:
        return False
    m = re.search(r"^##\s+Related\s*\n(.*?)(?=\n##\s|\Z)", body, re.DOTALL | re.MULTILINE)
    if m:
        section = m.group(1).rstrip() + f"\n- {link_token}\n"
        body = body[: m.start(1)] + section + body[m.end(1) :]
    else:
        sep = "\n\n" if body and not body.endswith("\n\n") else ""
        body = body + sep + f"## Related\n- {link_token}\n"
    post.content = body
    with open(path_for(slug), "wb") as f:
        frontmatter.dump(post, f)
    return True
