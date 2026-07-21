# RepoPilot

RepoPilot is a conversational engineering agent for local repositories. It
keeps recent conversation context, stores explicit repository memories, expands
Chinese or other natural-language questions into likely code terms, searches
with `rg`, explains relevant evidence, and runs one verification command after
human approval.

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

Create a conversation by selecting a local repository and optionally attaching
a GitHub Issue. Ask questions normally, or save durable repository knowledge
with:

```text
记住：这个项目使用 pytest
Remember: use npm test for this repository
```

Open `http://127.0.0.1:8000/settings` to switch between OpenAI and Anthropic,
fetch model lists from the selected provider, save the active model to `.env`,
and switch the UI between Chinese and English.

Without an LLM key, conversations still search the repository and return a
deterministic evidence summary. Common intents such as project overview,
startup, authentication, configuration, storage, API routes, search, tests,
frontend UI, and payments also have local query expansion. When a configured
model is available and the first search has no hits, RepoPilot asks the active
OpenAI or Anthropic model for additional source-code search terms.

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

RepoPilot does not edit files, commit, push, or merge code. It reads issues and
local code, stores conversation memory in SQLite, and runs only an explicit test
command selected by the user.

## Resume Bullet

Built RepoPilot, a conversational engineering agent with repository-scoped
long-term memory, evidence-grounded local code search, OpenAI/Anthropic support,
and human-approved verification commands.
