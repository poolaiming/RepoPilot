from __future__ import annotations

import subprocess
import json
import os
import shutil
import sys
from pathlib import Path
from time import perf_counter

from app.observability import record_event
from app.security import repository_root
from app.services.config import config_value


def suggest_test_commands(repo_path: str) -> list[str]:
    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return []

    commands: list[str] = []
    if any((root / name).exists() for name in ("pytest.ini", "pyproject.toml", "setup.cfg")) or (root / "tests").is_dir():
        commands.append("python -m pytest -q")
    if any((root / name).exists() for name in ("pyproject.toml", "setup.py", "requirements.txt")) or (root / "app").is_dir():
        commands.append("python -m compileall app tests" if (root / "app").is_dir() and (root / "tests").is_dir() else "python -m compileall .")
    commands.extend(_package_json_commands(root / "package.json"))
    if (root / "go.mod").exists():
        commands.append("go test ./...")
    if (root / "Cargo.toml").exists():
        commands.append("cargo test")
    if (root / "pom.xml").exists():
        commands.append("mvn test")
    return list(dict.fromkeys(commands))[:4]


def _package_json_commands(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        scripts = json.loads(path.read_text(encoding="utf-8")).get("scripts", {})
    except Exception:
        return []
    commands = []
    if "test" in scripts:
        commands.append("npm test")
    if "lint" in scripts:
        commands.append("npm run lint")
    return commands


def run_test_command(repo_path: str, command: str) -> dict:
    started = perf_counter()
    root = repository_root(repo_path)
    if config_value("REPOPILOT_ALLOW_TESTS", "false").lower() != "true":
        record_event("test", outcome="blocked")
        raise ValueError("Test execution is disabled. Set REPOPILOT_ALLOW_TESTS=true for trusted repositories, then retry.")
    if command not in suggest_test_commands(str(root)):
        record_event("test", outcome="blocked")
        raise ValueError("Select an exact command from the repository's suggested test commands.")
    args = command.split()
    executable = sys.executable if args[0] == "python" else None
    if not executable:
        # Absolute candidates avoid Windows which() implicitly searching the current directory.
        for part in os.get_exec_path():
            directory = Path(part)
            if directory.is_absolute() and not directory.resolve().is_relative_to(root):
                executable = shutil.which(str(directory / args[0]))
                if executable:
                    break
    if not executable:
        raise ValueError("Test executable is not installed on PATH.")
    args[0] = executable
    # shortcut: scripts retain OS user permissions; add process isolation before accepting untrusted code.
    try:
        proc = subprocess.run(
            args, cwd=root, capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace", shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        record_event("test", outcome="timeout", duration_ms=round((perf_counter() - started) * 1000, 2))
        raise ValueError("Test command exceeded the 120-second timeout.") from exc
    record_event("test", outcome="passed" if proc.returncode == 0 else "failed",
                 exit_code=proc.returncode, duration_ms=round((perf_counter() - started) * 1000, 2))
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return {"exit_code": proc.returncode, "output": output[-6000:]}
