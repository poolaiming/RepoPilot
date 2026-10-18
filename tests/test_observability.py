import asyncio
import json
import logging
import sqlite3

from fastapi.testclient import TestClient

import app.db as db
import app.main as main
from app.observability import request_id
from app.services import analyzer


def events(caplog):
    return [json.loads(item.message) for item in caplog.records if item.message.startswith('{"event":')]


def test_request_trace_and_health_do_not_log_body(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite3")
    with caplog.at_level(logging.INFO), TestClient(main.app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        response = client.get("/api/health?secret=NEVER_LOG_ME", headers={"X-Request-ID": "untrusted"})
        failed = client.post("/api/conversations", json={"secret": "NEVER_LOG_ME"})
    assert response.json() == {"status": "ok", "database": "ok"}
    assert failed.status_code == 422
    assert len(response.headers["X-Request-ID"]) == 32
    assert response.headers["X-Request-ID"] != failed.headers["X-Request-ID"]
    records = events(caplog)
    assert records[0]["request_id"] == response.headers["X-Request-ID"]
    assert records[0]["duration_ms"] >= 0
    assert records[1]["status"] == 422
    assert "NEVER_LOG_ME" not in json.dumps(records)
    assert request_id.get() == "-"


def test_health_reports_database_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite3")
    with TestClient(main.app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        def broken():
            raise sqlite3.OperationalError("secret internal path")
        monkeypatch.setattr(main, "connect", broken)
        response = client.get("/api/health")
    assert response.status_code == 503
    assert "secret" not in response.text


def test_model_error_is_visible_without_exception_text(monkeypatch, caplog):
    monkeypatch.setattr(analyzer, "_provider_has_key", lambda: True)
    monkeypatch.setattr(analyzer, "config_value", lambda *args: "openai")
    async def broken(*args):
        raise RuntimeError("TOKEN_NEVER_LOG_ME")
    monkeypatch.setattr(analyzer, "_openai_chat", broken)
    token = request_id.set("test-model-trace")
    try:
        with caplog.at_level(logging.INFO):
            reply = asyncio.run(analyzer.chat_reply({"repo_path": "."}, [], [], [], "en"))
    finally:
        request_id.reset(token)
    assert reply
    record = events(caplog)[0]
    assert record["request_id"] == "test-model-trace"
    assert record["mode"] == "rules_after_error"
    assert record["error_type"] == "RuntimeError"
    assert "TOKEN_NEVER_LOG_ME" not in caplog.text


def test_local_workflows_keep_evidence_and_correlated_events(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite3")
    source = tmp_path / "auth.py"
    source.write_text("def login_user():\n    return True\n", encoding="utf-8")
    with caplog.at_level(logging.INFO), TestClient(main.app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        created = client.post("/api/conversations", json={"repo_path": str(tmp_path)}).json()
        conversation_id = created["conversation"]["id"]
        reply = client.post(f"/api/conversations/{conversation_id}/messages", json={"content": "login_user"})
        assert reply.status_code == 200
        assert reply.json()["evidence"][0]["file_path"] == str(source)
        history = client.get(f"/api/conversations/{conversation_id}").json()
        assert [item["role"] for item in history["messages"]] == ["user", "assistant"]

        created = client.post("/api/tasks", json={"repo_path": str(tmp_path), "problem": "login_user"}).json()
        task_id = created["task"]["id"]
        scanned = client.post(f"/api/tasks/{task_id}/scan", json={})
        assert scanned.status_code == 200
        analyzed = client.post(f"/api/tasks/{task_id}/analyze", json={"use_llm": False})
        assert analyzed.status_code == 200
        report = client.get(f"/api/tasks/{task_id}/report")
        assert str(source) in report.text
    records = [item for item in events(caplog) if item["request_id"] == reply.headers["X-Request-ID"]]
    assert {item["event"] for item in records} == {"search", "model", "request"}
    assert next(item for item in records if item["event"] == "model")["mode"] == "rules"
