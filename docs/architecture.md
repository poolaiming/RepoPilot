# RepoPilot Architecture

RepoPilot is a conversational, repository-scoped engineering agent:

```text
Conversation + Optional GitHub Issue
        |
        v
Recent Messages + Repository Memory
        |
        v
Natural-language Query Expansion
        |
        v
Local Code Search with rg
        |
        v
Conversation Context Builder
        |
        v
OpenAI / Anthropic / Rule Fallback
        |
        v
Assistant Reply + Evidence + Optional Test Run
```

## Boundaries

- The app reads GitHub issues and local repositories.
- The app stores conversations, messages, and explicit repository memories in SQLite.
- Recent messages provide short-term context; `记住：...` / `Remember: ...`
  creates long-term memory scoped to the current repository.
- Natural-language questions first use local intent hints; when no code matches
  and a model is configured, OpenAI or Anthropic generates additional literal
  source-code search terms before the second `rg` pass.
- HTTP requests pass through server-generated request tracing and then local
  connection/Host/origin checks and a 64 KiB body limit. Mutating JSON APIs require
  `application/json`. No CORS allowlist or multi-user authentication is introduced.
- `app/security.py` owns canonical repository-root validation against explicit
  `REPOPILOT_REPO_ROOTS`. Creation, search, analysis and tests recheck roots;
  existing database records retain their data and are checked when used.
- Tests default to disabled. `app/services/testing.py` requires
  `REPOPILOT_ALLOW_TESTS=true` and an exact entry from `suggest_test_commands`.
  Processes use `shell=False` and a 120-second timeout; scripts retain OS user
  permissions and may themselves spawn processes or access other files.
- Retrieval uses literal, bounded terms and ignores rg config and common secret
  filenames. Issue/code/memory content is treated as untrusted model input.
  Structured reports reject file references outside the supplied evidence.
- The app does not write patches, commit code, push branches, or merge PRs.

## MVP Interfaces

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Check SQLite connectivity; return 200 or 503 with a request ID. |
| `POST /api/conversations` | Create a repository-scoped conversation. |
| `GET /api/conversations/{id}` | Load messages and repository memories. |
| `POST /api/conversations/{id}/messages` | Search code and generate a contextual reply. |
| `POST /api/conversations/{id}/test` | Run one explicit verification command. |
| `DELETE /api/memories/{id}` | Remove a saved repository memory. |
| `POST /api/tasks` | Create a triage task from an issue URL or local problem. |
| `POST /api/tasks/{id}/scan` | Search the repository with extracted keywords. |
| `POST /api/tasks/{id}/analyze` | Generate the triage report. |
| `POST /api/tasks/{id}/test` | Run one explicit verification command. |
| `GET /api/tasks/{id}/report` | Return the Markdown report. |

## Evaluation and Observability

`python -m app.evaluation` applies production query extraction and retrieval to
fixed files under `tests/fixtures/retrieval_repo`. It bypasses deployment root
configuration only for this fixed internal fixture. Recall@5, MRR@5 and no-result
accuracy have versioned thresholds and a failing exit code. This evaluates
retrieval, with no provider calls or claim about generated-answer correctness.

`app/observability.py` owns request context and JSON events on `uvicorn.error`.
Every response receives a server-generated `X-Request-ID`. Search/model/test
events share it, including rule fallback after model errors. Events contain
operational metadata and exception types; they omit request bodies, query
strings, snippets, command output and exception messages. Unhandled request
errors return a generic 500. External loggers retain their own behavior.

See [quality-boundaries.md](quality-boundaries.md) for operating instructions,
metric definitions, trust assumptions and known limits.
