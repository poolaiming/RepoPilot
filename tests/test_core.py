from fastapi.testclient import TestClient

import app.db as db
from app.main import app
from app.models import TriageReport
from app.services.analyzer import (
    _anthropic_text,
    _fallback_analyze,
    _openai_client_kwargs,
    _parse_search_queries,
    extract_memory,
    report_to_markdown,
)
from app.services.config import _model_ids, _trim_url
from app.services.github import parse_issue_url
from app.services.search import extract_queries, search_repo
from app.services.testing import suggest_test_commands


def test_parse_issue_url():
    ref = parse_issue_url("https://github.com/openai/openai-python/issues/123")
    assert ref.owner == "openai"
    assert ref.repo == "openai-python"
    assert ref.number == 123


def test_extract_queries_keeps_code_terms():
    queries = extract_queries("Parser crashes when ResponseServiceTier is priority")
    assert "ResponseServiceTier" in queries
    assert "Parser" in queries


def test_extract_queries_keeps_chinese_terms():
    queries = extract_queries("登录失败 支付回调")
    assert "登录失败" in queries
    assert "支付回调" in queries


def test_natural_language_search_expands_to_related_code(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
    queries = extract_queries("查一下这个项目大概作用")
    results = search_repo(str(tmp_path), queries)
    assert "FastAPI" in queries
    assert results[0]["file_path"] == str(source)


def test_parse_search_queries_accepts_model_json():
    queries = _parse_search_queries('["authentication", "session token", "login_user"]')
    assert {"authentication", "login_user", "session", "token"}.issubset(queries)


def test_conversation_saves_repository_memory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite3")
    repo = tmp_path / "repo"
    repo.mkdir()

    with TestClient(app) as client:
        created = client.post(
            "/api/conversations",
            json={"repo_path": str(repo), "lang": "zh"},
        ).json()
        conversation_id = created["conversation"]["id"]
        response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": "记住：这个项目使用 pytest", "lang": "zh"},
        )

    assert response.status_code == 200
    assert response.json()["memories"][0]["content"] == "这个项目使用 pytest"
    assert response.json()["test_commands"] == []
    assert extract_memory("remember: use npm test") == "use npm test"


def test_fallback_report_mentions_evidence_file():
    report = _fallback_analyze(
        {"problem": "Parser crashes", "repo_path": "."},
        None,
        [{"file_path": "src/parser.py", "snippet": "raise ValueError", "score": 0}],
    )
    markdown = report_to_markdown(report)
    assert isinstance(report, TriageReport)
    assert "`src/parser.py`" in markdown


def test_fallback_report_uses_requested_language():
    report = _fallback_analyze({"problem": "登录失败", "repo_path": "."}, None, [], lang="zh")
    markdown = report_to_markdown(report, "zh")
    assert "## 证据" in markdown
    assert "搜索证据不足" in markdown


def test_suggest_test_commands_detects_python_project(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
    commands = suggest_test_commands(str(tmp_path))
    assert commands[:2] == ["python -m pytest -q", "python -m compileall app tests"]


def test_openai_base_url_is_optional(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert _openai_client_kwargs() == {"api_key": "", "base_url": "https://api.openai.com/v1"}
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.example.com/v1")
    assert _openai_client_kwargs() == {"api_key": "", "base_url": "https://api.example.com/v1"}


def test_model_helpers_parse_provider_responses():
    assert _trim_url("https://api.example.com/v1/") == "https://api.example.com/v1"
    assert _model_ids({"data": [{"id": "gpt-test"}, {"name": "ignored"}]}) == ["gpt-test"]
    assert _anthropic_text({"content": [{"type": "text", "text": '{"summary":"ok"}'}]}) == '{"summary":"ok"}'
