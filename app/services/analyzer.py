from __future__ import annotations

import json
from typing import Any

import httpx

from app.models import Evidence, TriageReport
from app.services.config import (
    ANTHROPIC_DEFAULT_BASE_URL,
    ANTHROPIC_VERSION,
    OPENAI_DEFAULT_BASE_URL,
    config_value,
)


def build_context(task: dict, issue: dict | None, search_results: list[dict]) -> str:
    title = (issue or {}).get("title") or "Local problem"
    body = (issue or {}).get("body") or task.get("problem") or ""
    comments = (issue or {}).get("comments") or []
    snippets = "\n\n".join(
        f"FILE: {item['file_path']}\n{item['snippet']}" for item in search_results[:12]
    )
    return (
        f"TITLE:\n{title}\n\nBODY:\n{body}\n\nCOMMENTS:\n"
        f"{json.dumps(comments[:5], ensure_ascii=False)}\n\nCODE EVIDENCE:\n{snippets}"
    )


async def analyze(
    task: dict,
    issue: dict | None,
    search_results: list[dict],
    use_llm: bool = True,
    lang: str = "zh",
) -> TriageReport:
    lang = _lang(lang)
    if use_llm and _provider_has_key():
        try:
            return await _llm_analyze(build_context(task, issue, search_results), lang)
        except Exception:
            pass
    return _fallback_analyze(task, issue, search_results, lang)


async def _llm_analyze(context: str, lang: str) -> TriageReport:
    if config_value("MODEL_PROVIDER", "openai") == "anthropic":
        return await _anthropic_analyze(context, lang)
    return await _openai_analyze(context, lang)


async def _openai_analyze(context: str, lang: str) -> TriageReport:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(**_openai_client_kwargs())
    model = config_value("OPENAI_MODEL", "gpt-4.1-mini")
    prompt = _prompt(lang)
    resp = await client.responses.create(
        model=model,
        input=[{"role": "system", "content": prompt}, {"role": "user", "content": context}],
    )
    data = json.loads(resp.output_text)
    return TriageReport.model_validate(data)


async def _anthropic_analyze(context: str, lang: str) -> TriageReport:
    prompt = _prompt(lang)
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{config_value('ANTHROPIC_BASE_URL', ANTHROPIC_DEFAULT_BASE_URL).rstrip('/')}/messages",
            headers={
                "x-api-key": config_value("ANTHROPIC_API_KEY"),
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": config_value("ANTHROPIC_MODEL"),
                "max_tokens": 2000,
                "system": prompt,
                "messages": [{"role": "user", "content": context}],
            },
        )
        response.raise_for_status()
    return TriageReport.model_validate(json.loads(_anthropic_text(response.json())))


def _anthropic_text(payload: dict) -> str:
    return "\n".join(part.get("text", "") for part in payload.get("content", []) if part.get("type") == "text")


def _provider_has_key() -> bool:
    if config_value("MODEL_PROVIDER", "openai") == "anthropic":
        return bool(config_value("ANTHROPIC_API_KEY") and config_value("ANTHROPIC_MODEL"))
    return bool(config_value("OPENAI_API_KEY"))


def _openai_client_kwargs() -> dict[str, str]:
    base_url = config_value("OPENAI_BASE_URL", OPENAI_DEFAULT_BASE_URL)
    return {"api_key": config_value("OPENAI_API_KEY"), "base_url": base_url}


def _fallback_analyze(task: dict, issue: dict | None, search_results: list[dict], lang: str = "zh") -> TriageReport:
    lang = _lang(lang)
    title = (issue or {}).get("title") or task.get("problem") or "Local problem"
    body = (issue or {}).get("body") or task.get("problem") or ""
    zh = lang == "zh"
    evidence = [
        Evidence(
            file=item["file_path"],
            reason="命中问题关键词。" if zh else "Matched issue keywords in repository search.",
            snippet=item["snippet"],
        )
        for item in search_results[:5]
    ]
    root = "搜索证据不足，暂时无法判断单一根因。" if zh else "Search evidence is insufficient to name a single root cause."
    if evidence:
        root = (
            "问题可能涉及命中的代码路径；修改前先检查排在前面的证据文件。"
            if zh
            else "The issue likely touches the matched code paths; inspect the first evidence files before editing."
        )
    return TriageReport(
        summary=str(title)[:240],
        category=_guess_category(title, body),
        likely_root_cause=root,
        evidence=evidence,
        fix_plan=_fallback_fix_plan(lang),
        risk=_fallback_risk(lang),
        test_plan=_fallback_test_plan(lang),
    )


def report_to_markdown(report: TriageReport, lang: str = "en") -> str:
    data: dict[str, Any] = report.model_dump()
    labels = _markdown_labels(lang)
    lines = [
        f"# {data['summary']}",
        "",
        f"- {labels['category']}: {data['category']}",
        f"- {labels['root']}: {data['likely_root_cause']}",
        "",
        f"## {labels['evidence']}",
    ]
    if report.evidence:
        for item in report.evidence:
            lines.append(f"- `{item.file}`: {item.reason}")
    else:
        lines.append(f"- {labels['no_evidence']}")
    lines.extend(["", f"## {labels['fix_plan']}"])
    lines.extend(f"- {step}" for step in report.fix_plan)
    lines.extend(["", f"## {labels['risk']}"])
    lines.extend(f"- {risk}" for risk in report.risk)
    lines.extend(["", f"## {labels['test_plan']}"])
    lines.extend(f"- {test}" for test in report.test_plan)
    return "\n".join(lines)


def _lang(lang: str) -> str:
    return lang if lang in {"zh", "en"} else "zh"


def _prompt(lang: str) -> str:
    language = "Simplified Chinese" if _lang(lang) == "zh" else "English"
    return (
        "You are RepoPilot, a conservative code issue triage agent. "
        "Return only JSON with keys: summary, category, likely_root_cause, "
        "evidence, fix_plan, risk, test_plan. evidence items need file, reason, snippet. "
        "Do not invent files. Say evidence is insufficient when it is. "
        f"Write all JSON string values in {language}."
    )


def _fallback_fix_plan(lang: str) -> list[str]:
    if _lang(lang) == "zh":
        return [
            "根据 GitHub 报告或本地问题复现现象。",
            "按顺序检查证据文件，找到能解释现象的共享路径。",
            "在共同根因处做最小修改，然后重新运行验证命令。",
        ]
    return [
        "Reproduce the issue from the GitHub report or local problem statement.",
        "Inspect the evidence files in order and find the shared path that explains the symptom.",
        "Apply the smallest fix at the shared root cause, then rerun the listed verification.",
    ]


def _fallback_risk(lang: str) -> list[str]:
    if _lang(lang) == "zh":
        return ["如果没有命中证据文件，判断可信度较低。", "不要因为文件相邻就修改无关代码。"]
    return ["Low confidence if no evidence file matched.", "Do not edit unrelated files just because they are near a search hit."]


def _fallback_test_plan(lang: str) -> list[str]:
    if _lang(lang) == "zh":
        return ["运行覆盖命中代码路径的最小现有测试。", "如果没有窄测试，运行项目默认测试命令。"]
    return ["Run the narrowest existing test that covers the matched code path.", "If no narrow test exists, run the project default test command."]


def _markdown_labels(lang: str) -> dict[str, str]:
    if _lang(lang) == "zh":
        return {
            "category": "分类",
            "root": "可能根因",
            "evidence": "证据",
            "no_evidence": "没有找到代码证据。",
            "fix_plan": "修复计划",
            "risk": "风险",
            "test_plan": "测试计划",
        }
    return {
        "category": "Category",
        "root": "Likely root cause",
        "evidence": "Evidence",
        "no_evidence": "No code evidence found.",
        "fix_plan": "Fix Plan",
        "risk": "Risk",
        "test_plan": "Test Plan",
    }


def _guess_category(title: str, body: str) -> str:
    text = f"{title} {body}".lower()
    if any(word in text for word in ["regression", "broke", "previously worked"]):
        return "regression"
    if any(word in text for word in ["bug", "error", "exception", "fail", "crash"]):
        return "bug"
    if any(word in text for word in ["doc", "readme"]):
        return "docs"
    if any(word in text for word in ["feature", "enhancement"]):
        return "enhancement"
    return "unknown"
