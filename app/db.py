from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("repopilot.sqlite3")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            create table if not exists tasks (
                id integer primary key autoincrement,
                issue_url text,
                problem text,
                repo_path text not null,
                status text not null default 'created',
                created_at text not null default current_timestamp,
                updated_at text not null default current_timestamp
            );
            create table if not exists issues (
                task_id integer primary key,
                title text,
                body text,
                comments_json text not null default '[]'
            );
            create table if not exists search_results (
                id integer primary key autoincrement,
                task_id integer not null,
                file_path text not null,
                snippet text not null,
                score integer not null default 0
            );
            create table if not exists reports (
                task_id integer primary key,
                report_json text not null,
                report_markdown text not null
            );
            create table if not exists test_runs (
                id integer primary key autoincrement,
                task_id integer not null,
                command text not null,
                exit_code integer not null,
                output text not null,
                created_at text not null default current_timestamp
            );
            create table if not exists conversations (
                id integer primary key autoincrement,
                title text not null,
                repo_path text not null,
                issue_url text,
                issue_json text not null default '{}',
                lang text not null default 'zh',
                created_at text not null default current_timestamp,
                updated_at text not null default current_timestamp
            );
            create table if not exists messages (
                id integer primary key autoincrement,
                conversation_id integer not null,
                role text not null,
                content text not null,
                metadata_json text not null default '{}',
                created_at text not null default current_timestamp
            );
            create table if not exists memories (
                id integer primary key autoincrement,
                repo_path text not null,
                content text not null,
                source text not null default 'user',
                created_at text not null default current_timestamp,
                unique(repo_path, content)
            );
            create index if not exists idx_messages_conversation on messages(conversation_id, id);
            create index if not exists idx_memories_repo on memories(repo_path, id);
            """
        )


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def save_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def load_json(value: str) -> Any:
    return json.loads(value)
