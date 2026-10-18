import pytest

from app.services import config


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch, tmp_path):
    """Tests never consume host credentials or the real model configuration."""
    monkeypatch.setattr(config, "ENV_PATH", tmp_path / ".env")
    monkeypatch.setenv("REPOPILOT_REPO_ROOTS", str(tmp_path))
    monkeypatch.setenv("REPOPILOT_ALLOW_TESTS", "false")
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "GITHUB_TOKEN"):
        monkeypatch.delenv(key, raising=False)
