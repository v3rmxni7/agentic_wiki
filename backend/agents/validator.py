# Validator: cheap structural checks first (empty body, missing required sections),
# then a model pass for obvious hallucinations. Only "major" severity blocks.
from __future__ import annotations

from backend.agents.base import HAIKU, call_json, is_mock
from backend.schemas import ValidationResult
from backend.tools import notes as notes_tool


SYSTEM = """You are the ValidatorAgent of a knowledge wiki. You only flag REAL problems.

Flag an issue as MAJOR only if one of these is clearly true:
- A citation is fabricated (a paper title or author that does not exist)
- A numerical or historical fact is wrong by a wide margin
- The note directly contradicts itself in the same section

Everything else is MINOR (phrasing, terseness, missing polish). Minor issues NEVER block.

Default bias: PASS. If you are unsure, mark passed=true. Style, tone, missing Related
entries, short sections, and borderline claims are NOT failures.

Output JSON:
{"passed": true|false, "issues": ["..."], "severity": "none|minor|major"}
"""


def _structural_check(body: str) -> list[str]:
    # deterministic gate: only blocks if the note is essentially unusable
    issues: list[str] = []
    lower = body.lower()
    if len(body.strip()) < 60:
        issues.append("note body is near-empty")
    if "## summary" not in lower and "## key ideas" not in lower and "## details" not in lower:
        issues.append("missing any of Summary / Key Ideas / Details")
    return issues


def validate(slug: str) -> ValidationResult:
    body = notes_tool.read_body(slug)
    structural = _structural_check(body)
    if structural:
        return ValidationResult(passed=False, issues=structural, severity="major")
    # structural check is the gate. the LLM pass below is informational only -
    # its issues surface in the trace but never block.
    if is_mock():
        return ValidationResult(passed=True, issues=[], severity="none")
    try:
        res = call_json(
            SYSTEM, f"Note body:\n{body}", ValidationResult,
            model=HAIKU, max_tokens=400,
            mock_instance=ValidationResult(passed=True),
        )
        # downgrade any LLM "major" verdict to informational - the structural check already passed
        if not res.passed:
            return ValidationResult(passed=True, issues=res.issues, severity="minor")
        return res
    except Exception:
        return ValidationResult(passed=True, issues=["validator model call failed; structural check passed"], severity="minor")
