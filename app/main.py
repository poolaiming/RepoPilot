from __future__ import annotations

from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.db import connect, init_db, load_json, row_to_dict, save_json
from app.observability import RequestTraceMiddleware, record_event
from app.security import LocalSecurityMiddleware, repository_root
from app.models import (
    AnalyzeRequest,
    ConversationCreate,
    MessageCreate,
    ModelConfigUpdate,
    ScanRequest,
    TaskCreate,
    TestRequest,
)
from app.services.analyzer import analyze, chat_reply, expand_search_queries, extract_memory, report_to_markdown
from app.services.config import fetch_model_ids, read_model_config, save_model_config
from app.services.github import fetch_issue
from app.services.search import extract_queries, search_repo
from app.services.testing import run_test_command, suggest_test_commands

app = FastAPI(title="RepoPilot")
app.add_middleware(LocalSecurityMiddleware)
app.add_middleware(RequestTraceMiddleware)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health():
    try:
        with connect() as conn:
            conn.execute("select 1").fetchone()
    except sqlite3.Error as exc:
        record_event("health", status="error", error_type=type(exc).__name__)
        return JSONResponse({"status": "error", "database": "error"}, status_code=503)
    return {"status": "ok", "database": "ok"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/settings")
def settings() -> FileResponse:
    return FileResponse(static_dir / "settings.html")


@app.get("/api/conversations")
def list_conversations() -> dict:
    with connect() as conn:
        items = [
            dict(row)
            for row in conn.execute(
                "select id, title, repo_path, issue_url, lang, created_at, updated_at "
                "from conversations order by updated_at desc, id desc limit 50"
            )
        ]
    return {"conversations": items}


@app.post("/api/conversations")
async def create_conversation(payload: ConversationCreate) -> dict:
    try:
        repo_path = str(repository_root(payload.repo_path))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    issue = {}
    if payload.issue_url:
        try:
            issue = await fetch_issue(payload.issue_url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            record_event("github", outcome="error", error_type=type(exc).__name__)
            raise HTTPException(status_code=502, detail="GitHub issue fetch failed. Check the URL and token, then retry.") from exc
    title = issue.get("title") or ("新对话" if payload.lang == "zh" else "New conversation")
    with connect() as conn:
        cur = conn.execute(
            "insert into conversations (title, repo_path, issue_url, issue_json, lang) values (?, ?, ?, ?, ?)",
            (title, repo_path, payload.issue_url, save_json(issue), payload.lang),
        )
        conversation_id = cur.lastrowid
    return get_conversation(conversation_id)


@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: int) -> dict:
    with connect() as conn:
        conversation = row_to_dict(
            conn.execute("select * from conversations where id = ?", (conversation_id,)).fetchone()
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        conversation["issue"] = load_json(conversation.pop("issue_json"))
        messages = []
        for row in conn.execute(
            "select id, role, content, metadata_json, created_at from messages "
            "where conversation_id = ? order by id",
            (conversation_id,),
        ):
            item = dict(row)
            item["metadata"] = load_json(item.pop("metadata_json"))
            messages.append(item)
        memories = [
            dict(row)
            for row in conn.execute(
                "select id, content, source, created_at from memories "
                "where repo_path = ? order by id desc limit 50",
                (conversation["repo_path"],),
            )
        ]
    return {"conversation": conversation, "messages": messages, "memories": memories}


@app.post("/api/conversations/{conversation_id}/messages")
async def send_message(conversation_id: int, payload: MessageCreate) -> dict:
    current = get_conversation(conversation_id)
    conversation = current["conversation"]
    try:
        repository_root(conversation["repo_path"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    user_message = _save_message(conversation_id, "user", payload.content)
    memory = extract_memory(payload.content)
    if memory:
        with connect() as conn:
            conn.execute(
                "insert or ignore into memories (repo_path, content) values (?, ?)",
                (conversation["repo_path"], memory),
            )
        reply = f"已记住：{memory}" if payload.lang == "zh" else f"Remembered: {memory}"
        commands = suggest_test_commands(conversation["repo_path"])
        assistant = _save_message(
            conversation_id,
            "assistant",
            reply,
            {"test_commands": commands},
        )
        _touch_conversation(conversation_id, payload.content, user_message["id"], payload.lang)
        return {
            "message": assistant,
            "evidence": [],
            "test_commands": commands,
            "memories": get_conversation(conversation_id)["memories"],
        }

    issue = conversation.get("issue") or {}
    query_text = "\n".join([payload.content, issue.get("title", ""), issue.get("body", "")])
    try:
        evidence = search_repo(conversation["repo_path"], extract_queries(query_text), 8)
        if not evidence:
            expanded_queries = await expand_search_queries(query_text)
            if expanded_queries:
                evidence = search_repo(conversation["repo_path"], expanded_queries, 8)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    history = get_conversation(conversation_id)
    reply = await chat_reply(
        conversation,
        history["messages"],
        history["memories"],
        evidence,
        payload.lang,
    )
    commands = suggest_test_commands(conversation["repo_path"])
    assistant = _save_message(
        conversation_id,
        "assistant",
        reply,
        {"evidence": evidence, "test_commands": commands},
    )
    _touch_conversation(conversation_id, payload.content, user_message["id"], payload.lang)
    return {
        "message": assistant,
        "evidence": evidence,
        "test_commands": commands,
        "memories": history["memories"],
    }


@app.post("/api/conversations/{conversation_id}/test")
def test_conversation(conversation_id: int, payload: TestRequest) -> dict:
    conversation = get_conversation(conversation_id)["conversation"]
    try:
        result = run_test_command(conversation["repo_path"], payload.command)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    passed = result["exit_code"] == 0
    if payload.lang == "zh":
        summary = "测试通过" if passed else "测试未通过"
        content = f"{summary}\n命令：{payload.command}\n退出码：{result['exit_code']}\n\n{result['output']}"
    else:
        summary = "Test passed" if passed else "Test did not pass"
        content = f"{summary}\nCommand: {payload.command}\nExit code: {result['exit_code']}\n\n{result['output']}"
    message = _save_message(conversation_id, "tool", content, {"test": result, "command": payload.command})
    _touch_conversation(conversation_id)
    return {"message": message, **result}


@app.delete("/api/memories/{memory_id}")
def delete_memory(memory_id: int) -> dict:
    with connect() as conn:
        deleted = conn.execute("delete from memories where id = ?", (memory_id,)).rowcount
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"deleted": True}


@app.get("/api/config")
def get_config() -> dict:
    return read_model_config()


@app.put("/api/config")
def update_config(payload: ModelConfigUpdate) -> dict:
    if payload.provider not in {"openai", "anthropic"}:
        raise HTTPException(status_code=400, detail="provider must be openai or anthropic.")
    return save_model_config(payload.model_dump())


@app.get("/api/config/models")
async def list_models(provider: str) -> dict:
    try:
        return {"models": await fetch_model_ids(provider)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        record_event("model_list", outcome="error", error_type=type(exc).__name__)
        raise HTTPException(status_code=502, detail="Model list request failed. Check provider settings and retry.") from exc


@app.post("/api/tasks")
async def create_task(payload: TaskCreate) -> dict:
    if not payload.issue_url and not payload.problem:
        raise HTTPException(status_code=400, detail="Provide issue_url or problem.")
    try:
        repo_path = str(repository_root(payload.repo_path))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    with connect() as conn:
        cur = conn.execute(
            "insert into tasks (issue_url, problem, repo_path) values (?, ?, ?)",
            (payload.issue_url, payload.problem, repo_path),
        )
        task_id = cur.lastrowid

    if payload.issue_url:
        try:
            issue = await fetch_issue(payload.issue_url)
            with connect() as conn:
                conn.execute(
                    "insert or replace into issues (task_id, title, body, comments_json) values (?, ?, ?, ?)",
                    (task_id, issue["title"], issue["body"], save_json(issue["comments"])),
                )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            record_event("github", outcome="error", error_type=type(exc).__name__)
            raise HTTPException(status_code=502, detail="GitHub issue fetch failed. Check the URL and token, then retry.") from exc
    return get_task(task_id)


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int) -> dict:
    with connect() as conn:
        task = row_to_dict(conn.execute("select * from tasks where id = ?", (task_id,)).fetchone())
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")
        issue = row_to_dict(conn.execute("select * from issues where task_id = ?", (task_id,)).fetchone())
        if issue:
            issue["comments"] = load_json(issue.pop("comments_json"))
        results = [
            dict(row)
            for row in conn.execute(
                "select file_path, snippet, score from search_results where task_id = ? order by id",
                (task_id,),
            )
        ]
        report = row_to_dict(conn.execute("select * from reports where task_id = ?", (task_id,)).fetchone())
        if report:
            report["report_json"] = load_json(report["report_json"])
        tests = [
            dict(row)
            for row in conn.execute(
                "select command, exit_code, output, created_at from test_runs where task_id = ? order by id desc",
                (task_id,),
            )
        ]
    return {"task": task, "issue": issue, "search_results": results, "report": report, "test_runs": tests}


@app.post("/api/tasks/{task_id}/scan")
def scan_task(task_id: int, payload: ScanRequest) -> dict:
    current = get_task(task_id)
    task = current["task"]
    issue = current["issue"] or {}
    text = "\n".join([issue.get("title", ""), issue.get("body", ""), task.get("problem") or ""])
    queries = payload.queries or extract_queries(text)
    try:
        results = search_repo(task["repo_path"], queries, payload.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    with connect() as conn:
        conn.execute("delete from search_results where task_id = ?", (task_id,))
        conn.executemany(
            "insert into search_results (task_id, file_path, snippet, score) values (?, ?, ?, ?)",
            [(task_id, item["file_path"], item["snippet"], item["score"]) for item in results],
        )
    return {"queries": queries, "results": results}


@app.post("/api/tasks/{task_id}/analyze")
async def analyze_task(task_id: int, payload: AnalyzeRequest) -> dict:
    current = get_task(task_id)
    try:
        repository_root(current["task"]["repo_path"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    report = await analyze(current["task"], current["issue"], current["search_results"], payload.use_llm, payload.lang)
    markdown = report_to_markdown(report, payload.lang)
    with connect() as conn:
        conn.execute(
            "insert or replace into reports (task_id, report_json, report_markdown) values (?, ?, ?)",
            (task_id, report.model_dump_json(), markdown),
        )
    return {"report": report.model_dump(), "markdown": markdown, "test_commands": suggest_test_commands(current["task"]["repo_path"])}


@app.post("/api/tasks/{task_id}/test")
def test_task(task_id: int, payload: TestRequest) -> dict:
    task = get_task(task_id)["task"]
    try:
        result = run_test_command(task["repo_path"], payload.command)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    with connect() as conn:
        conn.execute(
            "insert into test_runs (task_id, command, exit_code, output) values (?, ?, ?, ?)",
            (task_id, payload.command, result["exit_code"], result["output"]),
        )
    return result


@app.get("/api/tasks/{task_id}/report")
def report_markdown(task_id: int) -> PlainTextResponse:
    with connect() as conn:
        row = conn.execute("select report_markdown from reports where task_id = ?", (task_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found.")
    return PlainTextResponse(row["report_markdown"])


def _save_message(
    conversation_id: int,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> dict:
    with connect() as conn:
        cur = conn.execute(
            "insert into messages (conversation_id, role, content, metadata_json) values (?, ?, ?, ?)",
            (conversation_id, role, content, save_json(metadata or {})),
        )
        message_id = cur.lastrowid
        row = conn.execute(
            "select id, role, content, metadata_json, created_at from messages where id = ?",
            (message_id,),
        ).fetchone()
    item = dict(row)
    item["metadata"] = load_json(item.pop("metadata_json"))
    return item


def _touch_conversation(
    conversation_id: int,
    first_message: str | None = None,
    user_message_id: int | None = None,
    lang: str | None = None,
) -> None:
    with connect() as conn:
        if user_message_id:
            count = conn.execute(
                "select count(*) from messages where conversation_id = ? and role = 'user'",
                (conversation_id,),
            ).fetchone()[0]
            if count == 1 and first_message:
                conn.execute(
                    "update conversations set title = ?, lang = ?, updated_at = current_timestamp where id = ?",
                    (first_message.strip()[:48], lang or "zh", conversation_id),
                )
                return
        conn.execute(
            "update conversations set updated_at = current_timestamp where id = ?",
            (conversation_id,),
        )
