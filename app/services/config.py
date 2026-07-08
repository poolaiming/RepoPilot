from __future__ import annotations

import os
from pathlib import Path

import httpx
from dotenv import dotenv_values, set_key

ENV_PATH = Path(".env")
OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
ANTHROPIC_DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"


def config_value(key: str, default: str = "") -> str:
    values = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    value = values.get(key) or os.getenv(key) or default
    return str(value).strip()


def read_model_config() -> dict:
    return {
        "provider": config_value("MODEL_PROVIDER", "openai"),
        "openai_base_url": config_value("OPENAI_BASE_URL", OPENAI_DEFAULT_BASE_URL),
        "openai_model": config_value("OPENAI_MODEL", "gpt-4.1-mini"),
        "has_openai_key": bool(config_value("OPENAI_API_KEY")),
        "anthropic_base_url": config_value("ANTHROPIC_BASE_URL", ANTHROPIC_DEFAULT_BASE_URL),
        "anthropic_model": config_value("ANTHROPIC_MODEL"),
        "has_anthropic_key": bool(config_value("ANTHROPIC_API_KEY")),
    }


def save_model_config(payload: dict) -> dict:
    ENV_PATH.touch(exist_ok=True)
    updates = {
        "MODEL_PROVIDER": payload["provider"],
        "OPENAI_BASE_URL": payload.get("openai_base_url") or OPENAI_DEFAULT_BASE_URL,
        "OPENAI_MODEL": payload.get("openai_model") or "gpt-4.1-mini",
        "ANTHROPIC_BASE_URL": payload.get("anthropic_base_url") or ANTHROPIC_DEFAULT_BASE_URL,
        "ANTHROPIC_MODEL": payload.get("anthropic_model") or "",
    }
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        value = (payload.get(key.lower()) or "").strip()
        if value:
            updates[key] = value

    for key, value in updates.items():
        set_key(ENV_PATH, key, value)
        os.environ[key] = value
    return read_model_config()


async def fetch_model_ids(provider: str) -> list[str]:
    if provider == "openai":
        key = config_value("OPENAI_API_KEY")
        if not key:
            raise ValueError("OpenAI API key is not configured.")
        return _model_ids(
            await _get_json(
                f"{_trim_url(config_value('OPENAI_BASE_URL', OPENAI_DEFAULT_BASE_URL))}/models",
                {"Authorization": f"Bearer {key}"},
            )
        )
    if provider == "anthropic":
        key = config_value("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("Anthropic API key is not configured.")
        return _model_ids(
            await _get_json(
                f"{_trim_url(config_value('ANTHROPIC_BASE_URL', ANTHROPIC_DEFAULT_BASE_URL))}/models",
                {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION},
            )
        )
    raise ValueError("provider must be openai or anthropic.")


def _model_ids(payload: dict) -> list[str]:
    return [item["id"] for item in payload.get("data", []) if item.get("id")]


def _trim_url(url: str) -> str:
    return url.rstrip("/")


async def _get_json(url: str, headers: dict[str, str]) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
