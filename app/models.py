from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    issue_url: str | None = Field(default=None, max_length=2048)
    problem: str | None = Field(default=None, max_length=8000)
    repo_path: str = Field(min_length=1, max_length=4096)


class ScanRequest(BaseModel):
    queries: list[str] | None = Field(default=None, max_length=8)
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
    command: str = Field(min_length=1, max_length=200)
    lang: Literal["zh", "en"] = "zh"


class ConversationCreate(BaseModel):
    repo_path: str = Field(min_length=1, max_length=4096)
    issue_url: str | None = Field(default=None, max_length=2048)
    lang: Literal["zh", "en"] = "zh"


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    lang: Literal["zh", "en"] = "zh"


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
