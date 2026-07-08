from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.db import connect, init_db, load_json, row_to_dict, save_json
from app.models import AnalyzeRequest, ModelConfigUpdate, ScanRequest, TaskCreate, TestRequest
from app.services.analyzer import analyze, report_to_markdown
from app.services.config import fetch_model_ids, read_model_config, save_model_config
from app.services.github import fetch_issue
from app.services.search import extract_queries, search_repo
from app.services.testing import run_test_command, suggest_test_commands

app = FastAPI(title="RepoPilot")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/settings")
def settings() -> FileResponse:
    return FileResponse(static_dir / "settings.html")


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
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/tasks")
async def create_task(payload: TaskCreate) -> dict:
    if not payload.issue_url and not payload.problem:
        raise HTTPException(status_code=400, detail="Provide issue_url or problem.")
    with connect() as conn:
        cur = conn.execute(
            "insert into tasks (issue_url, problem, repo_path) values (?, ?, ?)",
            (payload.issue_url, payload.problem, payload.repo_path),
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
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"GitHub issue fetch failed: {exc}") from exc
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
    except Exception as exc:
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
    except Exception as exc:
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
