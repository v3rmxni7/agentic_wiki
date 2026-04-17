# Writer: applies a FileOperationPlan to disk. No LLM calls - the curator already
# decided what to do, this just does it.
from __future__ import annotations

import os
import re

from backend.schemas import FileOperation, FileOperationPlan
from backend.tools import notes as notes_tool


def _extract_summary(body: str) -> str:
    m = re.search(r"^##\s+Summary\s*\n(.+?)(?=\n##\s|\Z)", body, re.DOTALL | re.MULTILINE)
    if m:
        para = m.group(1).strip().split("\n\n")[0]
        return " ".join(para.split())[:240]
    return " ".join(body.strip().split())[:240]


def _execute_one(op: FileOperation, validator_passed: bool = False) -> list[str]:
    touched: list[str] = []
    if op.op == "skip":
        return touched
    if op.op == "create":
        title = op.title or op.slug.replace("-", " ").title()
        body = op.content.strip() + "\n"
        notes_tool.write_note(
            slug=op.slug,
            title=title,
            body=body,
            tags=op.tags or [],
            summary=_extract_summary(body),
            parent=op.parent,
            validator_passed=validator_passed,
        )
        touched.append(op.slug)
        return touched
    if op.op == "patch":
        post = notes_tool.read_raw(op.slug)
        if post is None:
            # the curator asked to patch a file that doesn't exist - just create it instead
            title = op.title or op.slug.replace("-", " ").title()
            body = op.content.strip() + "\n"
            notes_tool.write_note(
                slug=op.slug, title=title, body=body, tags=op.tags or [],
                summary=_extract_summary(body), parent=op.parent, validator_passed=validator_passed,
            )
            touched.append(op.slug)
            return touched
        section = op.section or "Details"
        new_body = notes_tool.upsert_section(post.content, section, op.content)
        title = post.metadata.get("title") or op.title or op.slug.replace("-", " ").title()
        existing_tags = post.metadata.get("tags") or []
        merged_tags = list(dict.fromkeys([*existing_tags, *(op.tags or [])]))
        notes_tool.write_note(
            slug=op.slug,
            title=str(title),
            body=new_body,
            tags=merged_tags,
            summary=_extract_summary(new_body),
            parent=op.parent or post.metadata.get("parent"),
            validator_passed=validator_passed,
        )
        touched.append(op.slug)
        return touched
    if op.op == "merge":
        title = op.title or op.slug.replace("-", " ").title()
        body = op.content.strip() + "\n"
        notes_tool.write_note(
            slug=op.slug, title=title, body=body, tags=op.tags or [],
            summary=_extract_summary(body), parent=op.parent, validator_passed=validator_passed,
        )
        touched.append(op.slug)
        for other in op.merge_with:
            if other == op.slug:
                continue
            p = notes_tool.path_for(other)
            if p.exists():
                try:
                    os.remove(p)
                except OSError:
                    pass
        return touched
    return touched


def execute(op_plan: FileOperationPlan, validator_passed: bool = False) -> list[str]:
    touched: list[str] = []
    for op in op_plan.operations:
        touched.extend(_execute_one(op, validator_passed=validator_passed))
    seen = set()
    out: list[str] = []
    for s in touched:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out
