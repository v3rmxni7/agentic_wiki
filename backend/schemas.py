# Pydantic schemas shared across agents.
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Intent(str, Enum):
    NEW_TOPIC = "NEW_TOPIC"
    EXTEND_TOPIC = "EXTEND_TOPIC"
    COMPARE = "COMPARE"
    DEEP_DIVE = "DEEP_DIVE"


class IntentPlan(BaseModel):
    intent: Intent
    topic: str = Field(..., description="Canonical topic name (Title Case)")
    related_slugs: list[str] = Field(default_factory=list, description="Existing note slugs likely relevant")
    rationale: str = ""


class NoteMeta(BaseModel):
    slug: str
    title: str
    summary: str = ""
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    coverage: Literal["stub", "partial", "comprehensive"] = "stub"
    sources: int = 0
    validator_passed: bool = False
    revision: int = 0
    links_out: int = 0
    links_in: int = 0
    parent: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class ResearchFinding(BaseModel):
    topic: str
    key_points: list[str]
    sources: list[str] = Field(default_factory=list)
    gaps_filled: list[str] = Field(default_factory=list, description="What this adds beyond existing notes")


class FileOperation(BaseModel):
    op: Literal["create", "patch", "merge", "skip"]
    slug: str = Field(..., description="Target note slug (without .md)")
    title: Optional[str] = None
    section: Optional[str] = Field(None, description="For patch: which section heading to update")
    content: str = Field("", description="Markdown body to insert/replace")
    merge_with: list[str] = Field(default_factory=list, description="For merge op: other slugs to fold in")
    parent: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    reason: str = ""


class FileOperationPlan(BaseModel):
    operations: list[FileOperation]
    rationale: str = ""


class ValidationResult(BaseModel):
    passed: bool
    issues: list[str] = Field(default_factory=list)
    severity: Literal["none", "minor", "major"] = "none"


class TraceEvent(BaseModel):
    agent: str
    phase: Literal["start", "end", "error"]
    detail: str = ""
    data: dict = Field(default_factory=dict)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    intent: Intent
    answer: str
    operations: list[FileOperation]
    notes_touched: list[str]
    trace: list[TraceEvent]
    validator: ValidationResult
