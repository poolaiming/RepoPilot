# RepoPilot

RepoPilot is a small GitHub issue triage agent. It reads an issue or local
problem statement, searches a local repository with `rg`, produces a grounded
fix plan, and can run one verification command after human approval.

## Quick Start

Double-click `start-repopilot.cmd`, or run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --env-file .env
```

Open `http://127.0.0.1:8000`.

Open `http://127.0.0.1:8000/settings` to switch between OpenAI and Anthropic,
fetch model lists from the selected provider, save the active model to `.env`,
and switch the UI between Chinese and English.

For a no-LLM smoke test, create a task with a local problem, scan the current
repository path, and run analysis with `use_llm=false`.

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | No | Raises GitHub API limits and reads private issues if permitted. |
| `MODEL_PROVIDER` | No | `openai` or `anthropic`. Defaults to `openai`. |
| `OPENAI_API_KEY` | No | Enables LLM triage. Without it, RepoPilot uses a deterministic fallback report. |
| `OPENAI_BASE_URL` | No | OpenAI-compatible endpoint. Defaults to `https://api.openai.com/v1`. |
| `OPENAI_MODEL` | No | Defaults to `gpt-4.1-mini`. |
| `ANTHROPIC_API_KEY` | No | Enables Anthropic triage when `MODEL_PROVIDER=anthropic`. |
| `ANTHROPIC_BASE_URL` | No | Defaults to `https://api.anthropic.com/v1`. |
| `ANTHROPIC_MODEL` | No | Selected Claude model ID. |

To switch the agent provider manually, edit `.env`, then restart `start-repopilot.cmd`:

```text
MODEL_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://your-compatible-endpoint/v1
OPENAI_MODEL=your-model

MODEL_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
ANTHROPIC_MODEL=your-model
```

## Safety Boundary

RepoPilot does not edit files, commit, push, or merge code. It only reads issues,
searches local code, generates a report, and runs a single explicit test command.

## Resume Bullet

Built RepoPilot, an agentic GitHub issue triage assistant that ingests issues,
searches repository context with tool calls, generates grounded root-cause
hypotheses and fix plans, and runs verification commands with human approval.
