from __future__ import annotations

import re
import subprocess
from pathlib import Path
from time import perf_counter

from app.observability import record_event
from app.security import repository_root


STOP_WORDS = {
    "the", "and", "for", "with", "this", "that", "from", "have", "error",
    "issue", "bug", "when", "then", "than", "into", "does", "cannot",
}

INTENT_HINTS = (
    (("项目作用", "项目功能", "大概作用", "做什么", "用途", "overview", "purpose", "what does"),
     ("FastAPI", "conversation", "agent", "chat", "main", "service", "README")),
    (("入口", "启动", "怎么运行", "start", "startup", "entry point", "bootstrap"),
     ("__main__", "startup", "uvicorn", "main", "app")),
    (("登录", "认证", "鉴权", "账号", "login", "auth", "authentication"),
     ("login", "auth", "authenticate", "session", "token", "user")),
    (("配置", "设置", "环境变量", "config", "settings", "environment"),
     ("config", "settings", "dotenv", "environment", "base_url")),
    (("数据库", "存储", "记忆", "database", "storage", "memory"),
     ("database", "sqlite", "db", "memory", "model")),
    (("接口", "请求", "路由", "api", "endpoint", "request", "route"),
     ("api", "route", "endpoint", "request", "response")),
    (("搜索", "查找", "检索", "search", "find", "lookup"),
     ("search", "query", "filter", "index", "rg")),
    (("测试", "验证", "test", "verify"),
     ("test", "pytest", "assert", "check")),
    (("页面", "界面", "前端", "ui", "page", "frontend"),
     ("static", "html", "css", "javascript", "render")),
    (("支付", "订单", "账单", "payment", "order", "billing"),
     ("payment", "order", "billing", "invoice", "checkout")),
)


def extract_queries(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", text)
    seen: dict[str, int] = {}
    for word in words:
        key = word.lower()
        if key not in STOP_WORDS:
            seen[word] = seen.get(word, 0) + 1
    ranked = sorted(seen, key=lambda item: (-seen[item], -len(item), item.lower()))
    hints = [
        hint
        for phrases, hints in INTENT_HINTS
        if any(phrase in text.lower() for phrase in phrases)
        for hint in hints
    ]
    return _unique([*ranked, *hints], limit)


def search_repo(repo_path: str, queries: list[str], limit: int = 12) -> list[dict]:
    root = repository_root(repo_path)
    return _search_repository(root, queries, limit)


def _search_repository(root: Path, queries: list[str], limit: int = 12) -> list[dict]:
    started = perf_counter()
    if len(queries) > 8 or any(not query.strip() or len(query) > 200 for query in queries):
        raise ValueError("Provide up to 8 non-empty search terms of at most 200 characters.")
    if not queries:
        return []

    results: list[dict] = []
    seen: set[str] = set()
    for query in queries:
        query_results = 0
        proc = subprocess.run(
            ["rg", "--no-config", "--line-number", "--context", "2", "--fixed-strings",
             "--max-count", "8", "--max-filesize", "1M",
             "--glob", "!.env*", "--glob", "!*.pem", "--glob", "!*.key",
             "--glob", "!*.sqlite*", "--glob", "!*.db", "--glob", "!package-lock.json",
             "--glob", "!.git/**", "--", query, str(root)],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode not in {0, 1}:
            raise ValueError("Repository search failed. Check that rg is installed and the repository is readable.")
        for block in _split_rg_output(proc.stdout):
            file_path = _first_path(block)
            if file_path and file_path not in seen:
                seen.add(file_path)
                results.append(
                    {
                        "file_path": file_path,
                        "snippet": _trim(block),
                        "score": len(results),
                    }
                )
                query_results += 1
            if query_results >= 4:
                break
    ranked = sorted(results, key=lambda item: _result_sort_key(item, queries))[:limit]
    for score, item in enumerate(ranked):
        item["score"] = score
    record_event("search", query_count=len(queries), result_count=len(ranked),
                 duration_ms=round((perf_counter() - started) * 1000, 2))
    return ranked


def _split_rg_output(output: str) -> list[str]:
    blocks = re.split(r"\n--\n", output.strip())
    return [block for block in blocks if block.strip()]


def _first_path(block: str) -> str:
    first = block.splitlines()[0] if block.splitlines() else ""
    match = re.match(r"^(.*?)(?=:\d+:|-\d+-)", first)
    return match.group(1) if match else first


def _trim(text: str, max_chars: int = 1600) -> str:
    return text if len(text) <= max_chars else text[:max_chars] + "\n..."


def _unique(items: list[str], limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
        if len(result) >= limit:
            break
    return result


def _result_sort_key(item: dict, queries: list[str]) -> tuple[int, int, int]:
    path = item["file_path"].replace("\\", "/").lower()
    filename_hits = sum(query.lower() in path for query in queries)
    name = Path(path).name
    if name in {"progress.md", "changelog.md"}:
        path_priority = 4
    elif "/tests/" in path or name.startswith(("test_", "tests.")):
        path_priority = 3
    elif name == "readme.md":
        path_priority = 1
    elif Path(path).suffix in {".md", ".txt", ".rst"}:
        path_priority = 2
    else:
        path_priority = 0
    return -filename_hits, path_priority, item["score"]
