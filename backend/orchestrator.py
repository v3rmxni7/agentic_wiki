# Runs the agent pipeline end-to-end. Each step emits a TraceEvent so the UI can show
# progress over SSE. Validator failures trigger a single retry with issues fed back
# into the curator prompt.
from __future__ import annotations

from typing import Callable

from backend.agents import curator as curator_agent
from backend.agents import linker as linker_agent
from backend.agents import master as master_agent
from backend.agents import research as research_agent
from backend.agents import retrieval as retrieval_agent
from backend.agents import validator as validator_agent
from backend.agents import writer as writer_agent
from backend.schemas import (
    FileOperationPlan,
    Intent,
    IntentPlan,
    QueryResponse,
    TraceEvent,
    ValidationResult,
)
from backend.tools import notes as notes_tool


TraceFn = Callable[[TraceEvent], None]


def _emit(trace: list[TraceEvent], cb: TraceFn | None, event: TraceEvent) -> None:
    trace.append(event)
    if cb:
        try:
            cb(event)
        except Exception:
            pass


def _answer_from_operations(op_plan: FileOperationPlan, intent: Intent) -> str:
    lines = [f"**Intent:** {intent.value}  ", f"*{op_plan.rationale}*", ""]
    for op in op_plan.operations:
        if op.op == "create":
            lines.append(f"- Created note **{op.title or op.slug}** (`{op.slug}.md`) - {op.reason}")
        elif op.op == "patch":
            lines.append(f"- Updated section `{op.section or 'Details'}` in **{op.slug}.md** - {op.reason}")
        elif op.op == "merge":
            lines.append(f"- Merged {op.merge_with} into **{op.slug}.md** - {op.reason}")
        elif op.op == "skip":
            lines.append(f"- Skipped - {op.reason}")
    return "\n".join(lines)


def run(query: str, trace_cb: TraceFn | None = None) -> QueryResponse:
    trace: list[TraceEvent] = []

    # 1. master: intent + routing
    _emit(trace, trace_cb, TraceEvent(agent="master", phase="start", detail="classifying intent"))
    intent_plan: IntentPlan = master_agent.plan(query)
    _emit(trace, trace_cb, TraceEvent(
        agent="master", phase="end",
        detail=f"intent={intent_plan.intent.value} topic='{intent_plan.topic}'",
        data={"intent": intent_plan.intent.value, "topic": intent_plan.topic, "related": intent_plan.related_slugs, "rationale": intent_plan.rationale},
    ))

    # 2. retrieval: pull bodies of likely relevant existing notes
    _emit(trace, trace_cb, TraceEvent(agent="retrieval", phase="start", detail="inspecting existing notes"))
    existing = retrieval_agent.retrieve(query, intent_plan.related_slugs)
    _emit(trace, trace_cb, TraceEvent(
        agent="retrieval", phase="end",
        detail=f"{len(existing)} relevant notes loaded",
        data={"slugs": list(existing.keys())},
    ))

    # 3. research: gap-aware findings
    _emit(trace, trace_cb, TraceEvent(agent="research", phase="start", detail="gathering findings"))
    findings = research_agent.research(query, intent_plan.topic, intent_plan.intent, existing)
    _emit(trace, trace_cb, TraceEvent(
        agent="research", phase="end",
        detail=f"{len(findings.key_points)} key points, {len(findings.sources)} sources",
        data={"key_points": findings.key_points[:3], "gaps_filled": findings.gaps_filled},
    ))

    # 4. curator: decide file ops
    _emit(trace, trace_cb, TraceEvent(agent="curator", phase="start", detail="planning file operations"))
    all_slugs = [n.slug for n in notes_tool.list_notes()]
    op_plan = curator_agent.plan(intent_plan.intent, intent_plan.topic, query, findings, existing, all_slugs)
    _emit(trace, trace_cb, TraceEvent(
        agent="curator", phase="end",
        detail=f"{len(op_plan.operations)} operation(s): {', '.join(o.op for o in op_plan.operations)}",
        data={"rationale": op_plan.rationale, "ops": [{"op": o.op, "slug": o.slug, "section": o.section, "reason": o.reason} for o in op_plan.operations]},
    ))

    # 5. writer: apply the plan
    _emit(trace, trace_cb, TraceEvent(agent="writer", phase="start", detail="applying operations"))
    touched = writer_agent.execute(op_plan, validator_passed=False)
    _emit(trace, trace_cb, TraceEvent(
        agent="writer", phase="end",
        detail=f"touched {len(touched)} note(s)",
        data={"slugs": touched},
    ))

    # 6. linker: wikilinks + backlinks
    _emit(trace, trace_cb, TraceEvent(agent="linker", phase="start", detail="adding wikilinks + backlinks"))
    backlinks_updated: list[str] = []
    for slug in touched:
        post = notes_tool.read_raw(slug)
        if not post:
            continue
        new_body = linker_agent.link(slug, post.content)
        if new_body != post.content:
            notes_tool.write_note(
                slug=slug,
                title=str(post.metadata.get("title", slug)),
                body=new_body,
                tags=list(post.metadata.get("tags") or []),
                summary=str(post.metadata.get("summary", "")),
                parent=post.metadata.get("parent"),
                validator_passed=bool(post.metadata.get("validator_passed", False)),
                bump_revision=False,
            )
        # mirror backlinks
        title = str(post.metadata.get("title", slug))
        backlinks_updated.extend(linker_agent.mirror_backlinks(slug, title))
    _emit(trace, trace_cb, TraceEvent(
        agent="linker", phase="end",
        detail=f"mirrored backlinks into {len(backlinks_updated)} note(s)",
        data={"backlinks_updated": backlinks_updated},
    ))

    # 7. validator: gate with one retry
    _emit(trace, trace_cb, TraceEvent(agent="validator", phase="start", detail="checking touched notes"))
    aggregate: ValidationResult = ValidationResult(passed=True)
    for slug in touched:
        res = validator_agent.validate(slug)
        if not res.passed and res.severity == "major":
            aggregate = ValidationResult(passed=False, issues=[f"{slug}: {i}" for i in res.issues], severity="major")
            break
        if res.issues:
            aggregate.issues.extend(f"{slug}: {i}" for i in res.issues)

    if not aggregate.passed:
        # retry once: feed the issues back into the curator prompt
        _emit(trace, trace_cb, TraceEvent(
            agent="validator", phase="end",
            detail=f"FAILED: {'; '.join(aggregate.issues)} - retrying once",
            data={"issues": aggregate.issues},
        ))
        retry_query = f"{query}\n\n[Previous attempt failed validation: {'; '.join(aggregate.issues)}. Fix these issues.]"
        op_plan = curator_agent.plan(intent_plan.intent, intent_plan.topic, retry_query, findings, existing, all_slugs)
        touched = writer_agent.execute(op_plan, validator_passed=False)
        for slug in touched:
            post = notes_tool.read_raw(slug)
            if post:
                new_body = linker_agent.link(slug, post.content)
                if new_body != post.content:
                    notes_tool.write_note(
                        slug=slug, title=str(post.metadata.get("title", slug)),
                        body=new_body, tags=list(post.metadata.get("tags") or []),
                        summary=str(post.metadata.get("summary", "")),
                        parent=post.metadata.get("parent"),
                        validator_passed=False, bump_revision=False,
                    )
        aggregate = ValidationResult(passed=True, issues=["retry applied"], severity="minor")
        for slug in touched:
            res = validator_agent.validate(slug)
            if not res.passed and res.severity == "major":
                aggregate = ValidationResult(passed=False, issues=[f"{slug}: {i}" for i in res.issues], severity="major")
                break

    # stamp validator_passed into frontmatter so confidence picks it up next read
    for slug in touched:
        post = notes_tool.read_raw(slug)
        if post:
            notes_tool.write_note(
                slug=slug, title=str(post.metadata.get("title", slug)),
                body=post.content, tags=list(post.metadata.get("tags") or []),
                summary=str(post.metadata.get("summary", "")),
                parent=post.metadata.get("parent"),
                validator_passed=aggregate.passed, bump_revision=False,
            )

    _emit(trace, trace_cb, TraceEvent(
        agent="validator", phase="end",
        detail=("passed" if aggregate.passed else "failed after retry"),
        data={"issues": aggregate.issues, "severity": aggregate.severity},
    ))

    answer = _answer_from_operations(op_plan, intent_plan.intent)
    return QueryResponse(
        intent=intent_plan.intent,
        answer=answer,
        operations=op_plan.operations,
        notes_touched=touched,
        trace=trace,
        validator=aggregate,
    )
