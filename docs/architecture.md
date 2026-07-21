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
- The app runs only one explicit command at a time and blocks shell control
  characters.
- The app does not write patches, commit code, push branches, or merge PRs.

## MVP Interfaces

| Endpoint | Purpose |
|---|---|
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
