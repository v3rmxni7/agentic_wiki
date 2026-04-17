# Parse [[wikilinks]] across all notes to produce nodes + edges for the UI graph
# and a links_in count used in confidence scoring.
from __future__ import annotations

from backend.tools import notes as notes_tool
from backend.tools.notes import extract_wikilinks, slugify


def build_graph() -> dict:
    # pass 1: map title + slug -> slug so wikilinks can use either
    title_to_slug: dict[str, str] = {}
    raw: list[tuple[str, object]] = []
    for n in notes_tool.list_notes():
        post = notes_tool.read_raw(n.slug)
        if post is None:
            continue
        raw.append((n.slug, post))
        title_to_slug[n.title.lower()] = n.slug
        title_to_slug[n.slug.lower()] = n.slug

    edges: list[dict] = []
    links_in: dict[str, int] = {}
    for slug, post in raw:
        for link_text in set(extract_wikilinks(post.content)):
            target_slug = title_to_slug.get(link_text.lower()) or slugify(link_text)
            if target_slug == slug:
                continue
            edges.append({"from": slug, "to": target_slug, "label": link_text})
            links_in[target_slug] = links_in.get(target_slug, 0) + 1

    nodes: list[dict] = []
    for n in notes_tool.list_notes(links_in_map=links_in):
        nodes.append({
            "id": n.slug,
            "label": n.title,
            "tags": n.tags,
            "coverage": n.coverage,
            "confidence": n.confidence,
            "links_in": n.links_in,
            "links_out": n.links_out,
        })
    # add stubs for any link target that doesn't have a note yet
    known = {n["id"] for n in nodes}
    for e in edges:
        if e["to"] not in known:
            nodes.append({
                "id": e["to"],
                "label": e["label"],
                "tags": [],
                "coverage": "missing",
                "confidence": 0.0,
                "links_in": links_in.get(e["to"], 0),
                "links_out": 0,
                "missing": True,
            })
            known.add(e["to"])
    return {"nodes": nodes, "edges": edges, "links_in": links_in}


def links_in_map() -> dict[str, int]:
    return build_graph()["links_in"]
