from __future__ import annotations

import re
import subprocess
from pathlib import Path


STOP_WORDS = {
    "the", "and", "for", "with", "this", "that", "from", "have", "error",
    "issue", "bug", "when", "then", "than", "into", "does", "cannot",
}


def extract_queries(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}", text)
    seen: dict[str, int] = {}
    for word in words:
        key = word.lower()
        if key not in STOP_WORDS:
            seen[word] = seen.get(word, 0) + 1
    ranked = sorted(seen, key=lambda item: (-seen[item], -len(item), item.lower()))
    return ranked[:limit]


def search_repo(repo_path: str, queries: list[str], limit: int = 12) -> list[dict]:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Repository path does not exist: {root}")
    if not queries:
        return []

    results: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for query in queries:
        proc = subprocess.run(
            ["rg", "--line-number", "--context", "2", "--fixed-strings", query, str(root)],
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace",
        )
        for block in _split_rg_output(proc.stdout):
            file_path = _first_path(block)
            key = (file_path, block)
            if file_path and key not in seen:
                seen.add(key)
                results.append(
                    {
                        "file_path": file_path,
                        "snippet": _trim(block),
                        "score": len(results),
                    }
                )
            if len(results) >= limit:
                return results
    return results


def _split_rg_output(output: str) -> list[str]:
    blocks = re.split(r"\n--\n", output.strip())
    return [block for block in blocks if block.strip()]


def _first_path(block: str) -> str:
    first = block.splitlines()[0] if block.splitlines() else ""
    return first.split(":", 1)[0]


def _trim(text: str, max_chars: int = 1600) -> str:
    return text if len(text) <= max_chars else text[:max_chars] + "\n..."
