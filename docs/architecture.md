# RepoPilot Architecture

RepoPilot is a minimal closed-loop engineering agent:

```text
GitHub Issue / Local Problem
        |
        v
Issue Reader
        |
        v
Repo Search with rg
        |
        v
Context Builder
        |
        v
Agent Analyzer
        |
        v
Report + Optional Test Run
```

## Boundaries

- The app reads GitHub issues and local repositories.
- The app stores task history in SQLite.
- The app runs only one explicit command at a time and blocks shell control
  characters.
- The app does not write patches, commit code, push branches, or merge PRs.

## MVP Interfaces

| Endpoint | Purpose |
|---|---|
| `POST /api/tasks` | Create a triage task from an issue URL or local problem. |
| `POST /api/tasks/{id}/scan` | Search the repository with extracted keywords. |
| `POST /api/tasks/{id}/analyze` | Generate the triage report. |
| `POST /api/tasks/{id}/test` | Run one explicit verification command. |
| `GET /api/tasks/{id}/report` | Return the Markdown report. |
