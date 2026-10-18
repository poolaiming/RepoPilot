import asyncio
import os
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

import app.db as db
import app.main as main
from app.security import MAX_BODY_BYTES, repository_root
from app.services import analyzer, search, testing


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite3")
    with TestClient(main.app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000)) as client:
        yield client


@pytest.mark.parametrize("headers", [
    {"Host": "attacker.example"},
    {"Origin": "https://attacker.example"},
    {"Origin": "null"},
    {"Sec-Fetch-Site": "cross-site"},
])
def test_rejects_untrusted_browser_origins(client, headers):
    response = client.get("/api/conversations", headers=headers)
    assert response.status_code == 403
    assert response.headers["X-Request-ID"]


def test_rejects_remote_clients(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.sqlite3")
    with TestClient(main.app, base_url="http://127.0.0.1", client=("192.0.2.1", 50000)) as remote:
        assert remote.get("/api/conversations").status_code == 403


def test_same_origin_works_and_form_posts_are_blocked(client, tmp_path):
    response = client.post("/api/conversations", headers={"Origin": "http://127.0.0.1"},
                           json={"repo_path": str(tmp_path)})
    assert response.status_code == 200
    assert client.post("/api/conversations", data={"repo_path": str(tmp_path)}).status_code == 403


def test_limits_body_without_trusting_content_length(client):
    response = client.post("/api/conversations", content=b"x" * (MAX_BODY_BYTES + 1),
                           headers={"content-type": "application/json", "content-length": "1"})
    assert response.status_code == 413


def test_resolves_roots_and_rejects_sibling_prefixes(monkeypatch, tmp_path):
    allowed = tmp_path / "repo"
    allowed.mkdir()
    sibling = tmp_path / "repo-other"
    sibling.mkdir()
    monkeypatch.setenv("REPOPILOT_REPO_ROOTS", str(allowed))
    assert repository_root(str(allowed / ".." / "repo")) == allowed
    with pytest.raises(ValueError, match="outside"):
        repository_root(str(sibling))
    monkeypatch.setenv("REPOPILOT_REPO_ROOTS", "")
    with pytest.raises(ValueError, match="Set REPOPILOT_REPO_ROOTS"):
        repository_root(str(allowed))


def test_junction_cannot_escape_allowed_roots(monkeypatch, tmp_path):
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    junction = allowed / "link"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], check=True, capture_output=True)
    else:
        junction.symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("REPOPILOT_REPO_ROOTS", str(allowed))
    with pytest.raises(ValueError, match="outside"):
        repository_root(str(junction))


@pytest.mark.parametrize("endpoint, payload", [
    ("/api/conversations", {}),
    ("/api/tasks", {"problem": "hello"}),
])
def test_both_creation_apis_enforce_root_allowlist(client, monkeypatch, tmp_path, endpoint, payload):
    monkeypatch.setenv("REPOPILOT_REPO_ROOTS", str(tmp_path / "trusted"))
    response = client.post(endpoint, json={"repo_path": str(tmp_path), **payload})
    assert response.status_code == 400


def test_existing_task_and_conversation_are_rechecked(client, monkeypatch, tmp_path):
    conversation = client.post("/api/conversations", json={"repo_path": str(tmp_path)}).json()["conversation"]["id"]
    task = client.post("/api/tasks", json={"repo_path": str(tmp_path), "problem": "hello"}).json()["task"]["id"]
    monkeypatch.setenv("REPOPILOT_REPO_ROOTS", str(tmp_path / "other"))
    assert client.post(f"/api/conversations/{conversation}/messages", json={"content": "hello"}).status_code == 400
    assert client.post(f"/api/tasks/{task}/analyze", json={"use_llm": False}).status_code == 400


def test_search_treats_dash_terms_as_literals_and_excludes_secrets(tmp_path):
    (tmp_path / "source.py").write_text('marker = "--pre"\n', encoding="utf-8")
    for filename in (".env", "credential.key", "private.pem", "store.sqlite3"):
        (tmp_path / filename).write_text("PRIVATE_MARKER", encoding="utf-8")
    results = search.search_repo(str(tmp_path), ["--pre"])
    assert len(results) == 1
    assert results[0]["file_path"].endswith("source.py")
    assert search.search_repo(str(tmp_path), ["PRIVATE_MARKER"]) == []


def test_search_fails_on_rg_errors_and_bounds_terms(monkeypatch, tmp_path):
    with pytest.raises(ValueError, match="up to 8"):
        search.search_repo(str(tmp_path), ["x"] * 9)
    monkeypatch.setattr(search.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess([], 2, "", "secret"))
    with pytest.raises(ValueError, match="search failed"):
        search.search_repo(str(tmp_path), ["hello"])


def test_commands_default_disabled_and_arbitrary_commands_never_run(monkeypatch, tmp_path):
    (tmp_path / "tests").mkdir()
    def unexpected(*args, **kwargs):
        pytest.fail("A blocked command reached subprocess.run")
    monkeypatch.setattr(testing.subprocess, "run", unexpected)
    with pytest.raises(ValueError, match="disabled"):
        testing.run_test_command(str(tmp_path), "python -m pytest -q")
    monkeypatch.setenv("REPOPILOT_ALLOW_TESTS", "true")
    for command in ("python -c print(1)", "cmd /c echo hello", "python -m pytest -q --override-ini=x", "npm test && whoami"):
        with pytest.raises(ValueError, match="exact command"):
            testing.run_test_command(str(tmp_path), command)


def test_fixed_command_uses_trusted_python_and_preserves_failure(monkeypatch, tmp_path):
    (tmp_path / "tests").mkdir()
    monkeypatch.setenv("REPOPILOT_ALLOW_TESTS", "true")
    calls = []
    def run(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 7, "result", "error")
    monkeypatch.setattr(testing.subprocess, "run", run)
    result = testing.run_test_command(str(tmp_path), "python -m pytest -q")
    assert result == {"exit_code": 7, "output": "result\nerror"}
    assert calls[0][0] == [sys.executable, "-m", "pytest", "-q"]
    assert calls[0][1]["shell"] is False
    assert calls[0][1]["cwd"] == tmp_path
    assert calls[0][1]["timeout"] == 120


def test_test_timeout_returns_actionable_error(monkeypatch, tmp_path):
    (tmp_path / "tests").mkdir()
    monkeypatch.setenv("REPOPILOT_ALLOW_TESTS", "true")
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("test", 120)
    monkeypatch.setattr(testing.subprocess, "run", timeout)
    with pytest.raises(ValueError, match="120-second"):
        testing.run_test_command(str(tmp_path), "python -m pytest -q")


def test_tool_lookup_skips_repository_and_implicit_current_directory(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    trusted = tmp_path / "tools"
    local_bin = repo / "bin"
    local_bin.mkdir(parents=True)
    trusted.mkdir()
    (repo / "package.json").write_text('{"scripts":{"test":"echo test"}}', encoding="utf-8")
    filename = "npm.cmd" if os.name == "nt" else "npm"
    for directory in (repo, local_bin, trusted):
        tool = directory / filename
        tool.write_text("@exit /b 0\n" if os.name == "nt" else "#!/bin/sh\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("REPOPILOT_ALLOW_TESTS", "true")
    directories = [".", str(repo), str(local_bin), str(trusted)]
    monkeypatch.setattr(testing.os, "get_exec_path", lambda: directories)
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")
    monkeypatch.setattr(testing.subprocess, "run", run)
    assert testing.run_test_command(str(repo), "npm test")["exit_code"] == 0
    assert len(calls) == 1
    assert os.path.normcase(calls[0][0]) == os.path.normcase(str(trusted / filename))
    assert calls[0][1:] == ["test"]
    directories.pop()
    with pytest.raises(ValueError, match="not installed"):
        testing.run_test_command(str(repo), "npm test")
    assert len(calls) == 1


@pytest.mark.parametrize("kind", ["conversations", "tasks"])
def test_test_endpoints_enforce_disabled_execution(client, tmp_path, kind):
    response = client.post(f"/api/{kind}", json={"repo_path": str(tmp_path), "problem": "test"}).json()
    item = response["conversation" if kind == "conversations" else "task"]
    result = client.post(f"/api/{kind}/{item['id']}/test", json={"command": "python -c print(1)"})
    assert result.status_code == 400
    assert "disabled" in result.json()["detail"]


def test_model_list_errors_do_not_expose_provider_response(client, monkeypatch):
    async def broken(*args):
        raise RuntimeError("PRIVATE_PROVIDER_TOKEN")
    monkeypatch.setattr(main, "fetch_model_ids", broken)
    response = client.get("/api/config/models?provider=openai")
    assert response.status_code == 502
    assert "PRIVATE_PROVIDER_TOKEN" not in response.text


def test_unhandled_errors_are_traced_and_sanitized(client, monkeypatch):
    def broken():
        raise RuntimeError("PRIVATE_SERVER_TOKEN")
    monkeypatch.setattr(main, "read_model_config", broken)
    response = client.get("/api/config")
    assert response.status_code == 500
    assert response.headers["X-Request-ID"]
    assert "PRIVATE_SERVER_TOKEN" not in response.text


def test_report_citations_must_come_from_evidence(monkeypatch):
    monkeypatch.setattr(analyzer, "_provider_has_key", lambda: True)
    async def invented(*args):
        return analyzer.TriageReport(summary="x", category="x", likely_root_cause="x",
            evidence=[analyzer.Evidence(file="invented.py", reason="x", snippet="x")],
            fix_plan=[], risk=[], test_plan=[])
    monkeypatch.setattr(analyzer, "_llm_analyze", invented)
    report = asyncio.run(analyzer.analyze({"problem": "issue"}, None, [], True, "en"))
    assert report.evidence == []
