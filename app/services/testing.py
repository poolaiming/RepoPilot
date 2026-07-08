from __future__ import annotations

import subprocess
import json
from pathlib import Path


BLOCKED_TOKENS = {";", "&&", "||", "|", ">", "<", "`"}


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
    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Repository path does not exist: {root}")
    if any(token in command for token in BLOCKED_TOKENS):
        raise ValueError("Command contains shell control characters; run one command at a time.")

    proc = subprocess.run(
        command.split(),
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return {"exit_code": proc.returncode, "output": output[-6000:]}
