from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    issue_url: str | None = None
    problem: str | None = None
    repo_path: str


class ScanRequest(BaseModel):
    queries: list[str] | None = None
    limit: int = Field(default=12, ge=1, le=30)


class AnalyzeRequest(BaseModel):
    use_llm: bool = True
    lang: Literal["zh", "en"] = "zh"


class ModelConfigUpdate(BaseModel):
    provider: str
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None
    anthropic_api_key: str | None = None
    anthropic_base_url: str | None = None
    anthropic_model: str | None = None


class TestRequest(BaseModel):
    command: str


class Evidence(BaseModel):
    file: str
    reason: str
    snippet: str


class TriageReport(BaseModel):
    summary: str
    category: str
    likely_root_cause: str
    evidence: list[Evidence]
    fix_plan: list[str]
    risk: list[str]
    test_plan: list[str]
