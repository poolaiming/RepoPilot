## 2026-07-06 - Task: Build RepoPilot MVP
### What was done
- Created a lightweight GitHub issue triage agent with issue ingestion, repository search, report generation, test execution, SQLite persistence, and a Web UI.
- Added project documentation for setup, safety boundaries, architecture, and resume positioning.

### Testing
- Pending local verification.

### Notes
- Changed files: `requirements.txt` defines runtime dependencies; `.env.example` documents optional tokens; `app/` contains the FastAPI app, services, and static UI; `tests/test_core.py` covers core parsing and fallback reporting; `README.md` and `docs/architecture.md` document usage and design.
- Rollback: delete the created project files in this directory, or restore from the filesystem snapshot before this task.

## 2026-07-06 - Task: Verify RepoPilot MVP
### What was done
- Verified the MVP core flow and started the local Web app for manual review.
- Added ignore rules for generated Python caches and the SQLite runtime database.

### Testing
- `python -m pip install -r requirements.txt`
- `python -m pytest -q` -> 3 passed.
- `python -m compileall app tests` -> completed successfully.
- FastAPI smoke test created task 1, scanned 4 repository matches, and generated a fallback bug report.
- Started local server at `http://127.0.0.1:8000/` with PID 8740; GET `/` returned HTTP 200.

### Notes
- Changed files: `.gitignore` ignores runtime/generated files; `README.md` adds a no-LLM smoke-test note; `progress.md` records verification evidence.
- Rollback: stop PID 8740, then delete the created files or restore the directory snapshot from before this task.

## 2026-07-06 - Task: Initialize CodeGraph index
### What was done
- Initialized CodeGraph for the new project and excluded the local index from source control.

### Testing
- `codegraph init` -> indexed 11 files.
- `python -m pytest -q` -> 3 passed.
- `Invoke-WebRequest http://127.0.0.1:8000/` -> HTTP 200.

### Notes
- Changed files: `.gitignore` now ignores `.codegraph/`; `progress.md` records the indexing and final checks.
- Rollback: delete `.codegraph/` and remove the `.codegraph/` ignore entry if the local index is not wanted.

## 2026-07-08 - Task: Add quick start script
### What was done
- Added a Windows double-click startup script that prepares `.env`, creates `.venv` when needed, installs dependencies, and starts RepoPilot on `127.0.0.1:8000`.
- Updated the README quick start entry to point to the script.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live check: `http://127.0.0.1:8000/` and `/settings` both returned HTTP 200.
- `codegraph sync` -> already up to date.

### Notes
- Changed files: `start-repopilot.cmd` adds the quick launcher; `README.md` documents it; `progress.md` records this task.
- Rollback: delete `start-repopilot.cmd` and remove the README quick-start sentence.

## 2026-07-08 - Task: Verify quick start script
### What was done
- Verified the quick start script creates the dependency stamp and launches RepoPilot.

### Testing
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 3 passed.
- `cmd /c "start-repopilot.cmd"` -> started the foreground server; the command timed out because the server kept running.
- `Invoke-WebRequest http://127.0.0.1:8000/` -> HTTP 200.

### Notes
- Changed files: `progress.md` records launcher verification.
- Runtime: server is listening on `127.0.0.1:8000` with owning PID 28976; related Python PIDs observed: 17992, 22260, 28976.
- Rollback: stop the listed PIDs and delete `start-repopilot.cmd` if the launcher is not wanted.

## 2026-07-08 - Task: Support configurable agent API endpoint
### What was done
- Added `OPENAI_BASE_URL` support so the agent can use an OpenAI-compatible custom endpoint.
- Documented how to change the agent API key, base URL, and model in `.env`.

### Testing
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 4 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.

### Notes
- Changed files: `app/services/analyzer.py` passes the optional base URL to the OpenAI client; `.env.example` and `README.md` document provider switching; `tests/test_core.py` covers the optional base URL setting.
- Rollback: remove `OPENAI_BASE_URL` from `.env.example` and README, revert the OpenAI client kwargs helper, and remove the related test.

## 2026-07-08 - Task: Update local env template fields
### What was done
- Added the blank `OPENAI_BASE_URL` field to the local `.env` file so the running project has the same provider-switch setting as `.env.example`.

### Testing
- `codegraph sync` -> already up to date.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 4 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Started RepoPilot with `.env`; `http://127.0.0.1:8000/` returned HTTP 200.

### Notes
- Changed files: `.env` now includes `OPENAI_BASE_URL`; `progress.md` records verification.
- Runtime: server is listening on `127.0.0.1:8000` with launcher PID 29000.
- Rollback: remove the `OPENAI_BASE_URL=` line from `.env`.

## 2026-07-08 - Task: Add model settings page
### What was done
- Added a standalone `/settings` page for switching OpenAI and Anthropic model providers, saving config to `.env`, and fetching model lists from the selected provider.
- Added backend config APIs and Anthropic Messages support for Agent analysis.
- Documented the new provider settings.

### Testing
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- TestClient smoke check: `/settings` returned 200, `/api/config` did not expose raw API keys, and invalid provider for model listing returned 400.
- Live check: `http://127.0.0.1:8000/settings` returned HTTP 200; `/api/config` returned provider/model fields with key presence booleans only.

### Notes
- Changed files: `app/services/config.py` handles `.env` config and model-list calls; `app/services/analyzer.py` supports OpenAI and Anthropic generation; `app/main.py` exposes settings/config APIs; `app/static/settings.*` adds the page; `.env.example`, `README.md`, and tests were updated.
- Rollback: remove the settings route/static files/config service, revert analyzer provider branching, and restore `.env.example`, README, and tests.

## 2026-07-08 - Task: Add Chinese and English UI switch
### What was done
- Added a shared language switch for the main page and model settings page.
- Localized static labels, placeholders, empty states, and common settings status messages in Chinese and English.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live check: `http://127.0.0.1:8000/` and `/settings` both returned HTTP 200.

### Notes
- Changed files: `app/static/i18n.js` adds the shared dictionary and localStorage language setting; `app/static/index.html`, `settings.html`, `app.js`, `settings.js`, and `styles.css` wire the switch into both pages; `README.md` documents the UI language switch.
- Runtime: server is listening on `127.0.0.1:8000` with owning PID 37256.
- Rollback: remove `i18n.js`, remove the language selectors and `data-i18n` attributes, and restore the previous static English labels.

## 2026-07-08 - Task: Refactor UI to Apple-style minimal design
### What was done
- Refined the main and settings screens toward a clean Apple-like interface with airy spacing, translucent panels, subtle borders, blue primary actions, and a quieter neutral background.
- Added a short localized product subtitle to both screens.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live check: `http://127.0.0.1:8000/` and `/settings` both returned HTTP 200.
- `codegraph sync` -> already up to date.

### Notes
- Changed files: `app/static/styles.css` updates the visual system; `index.html` and `settings.html` add subtitle structure; `i18n.js` adds localized subtitle copy.
- Runtime: server is listening on `127.0.0.1:8000` with owning PID 37256.
- Rollback: restore the previous CSS and remove the subtitle elements and `tagline` translations.

## 2026-07-08 - Task: Unify top navigation link style
### What was done
- Located the selected `Model Settings` link at `app/static/index.html` under `main > section.toolbar > div.topline > div.nav-actions > a`.
- Updated the real source node and matching settings-page back link to use a reusable `.nav-link` style consistent with the Apple-like top controls.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live check: `http://127.0.0.1:8000/` and `/settings` both returned HTTP 200.

### Notes
- Changed files: `app/static/index.html` and `settings.html` add the reusable nav-link class; `app/static/styles.css` defines the unified pill-style link; `progress.md` records the targeted UI fix.
- Rollback: remove the `nav-link` class from both anchors and delete the `.nav-link` CSS block.

## 2026-07-08 - Task: Replace language dropdown with compact toggle
### What was done
- Replaced the oversized language dropdown on the main and settings pages with a compact Chinese/English segmented button.
- Tightened the top navigation controls so language switching and navigation use the same compact Apple-style control family.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live check: `http://127.0.0.1:8000/` and `/settings` both returned HTTP 200.
- `codegraph sync` -> completed successfully.

### Notes
- Changed files: `app/static/index.html` and `settings.html` replace the language select markup; `app/static/i18n.js` switches language from buttons and marks the active language; `app/static/styles.css` adds segmented button styling and tightens top navigation.
- Rollback: restore the previous `select#langSelect` markup and the old `i18n.js` select handler, then remove `.segmented` CSS.

## 2026-07-08 - Task: Consolidate language toggle and top nav buttons
### What was done
- Replaced the two-button language segmented control with a single `中文` / `EN` toggle button.
- Unified the language toggle and `Model Settings` / `Back` controls under one `.nav-button` style and aligned the nav group to the toolbar's top-right.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live check: `http://127.0.0.1:8000/` and `/settings` both returned HTTP 200.

### Notes
- Changed files: `app/static/index.html` and `settings.html` use one language toggle and nav-button links; `app/static/i18n.js` toggles language from a single button; `app/static/styles.css` removes segmented styles and aligns nav actions to the top-right; `progress.md` records this targeted layout update.
- Rollback: restore the segmented language buttons and `.segmented` CSS, then remove `.nav-button` from the nav links.

## 2026-07-08 - Task: Push top nav controls to true top-right
### What was done
- Moved the top navigation group closer to the toolbar's upper-right edge using parent layout spacing instead of per-button transforms.
- Strengthened the `Model Settings` / `Back` link into a visible button that matches the language toggle.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live check: `http://127.0.0.1:8000/` and `/settings` both returned HTTP 200.

### Notes
- Changed files: `app/static/styles.css` adjusts `.topline`, `.nav-actions`, `.nav-button`, and `.nav-link` to fix placement and button consistency; `progress.md` records this correction.
- Rollback: remove the negative top/right margins and restore the previous `.nav-button` and `.nav-link` dimensions/colors.

## 2026-07-08 - Task: Put language toggle at far top-right and restyle model settings
### What was done
- Moved the language toggle to the far-right side of the top nav by changing DOM order inside `.nav-actions`.
- Restyled `Model Settings` / `Back` as the primary dark pill button, with the language toggle beside it as the secondary pill.
- Pushed the nav group closer to the toolbar's top-right edge through `.nav-actions` parent layout margins.

### Testing
- Pending verification.

### Notes
- Changed files: `app/static/index.html` and `settings.html` reorder nav controls; `app/static/styles.css` updates right-top placement and primary button styling; `progress.md` records the fix.
- Rollback: restore language button before the nav link and revert `.nav-actions`, `.nav-button`, and `.nav-link` styles.

## 2026-07-08 - Task: Force latest nav assets and tighten top spacing
### What was done
- Added cache-busting query strings to the CSS and JS assets so the browser loads the latest top-nav UI instead of stale styles.
- Tightened the page and toolbar top padding so the language toggle lands near the requested top-right position without absolute positioning.

### Testing
- Pending verification.

### Notes
- Changed files: `app/static/index.html` and `settings.html` version the static CSS/JS asset URLs; `app/static/styles.css` tightens top spacing; `progress.md` records this correction.
- Rollback: remove the version query strings and restore the previous `main`, `.toolbar`, and `.nav-actions` spacing.

## 2026-07-08 - Task: Match top-right nav target exactly
### What was done
- Moved the top navigation group to the requested top-right position using the parent `.nav-actions` layout.
- Fixed the language toggle to the selected 56px button size and made `Model Settings` / `Back` use a stronger button selector so they cannot fall back to naked link styling.
- Bumped static asset versions again so the browser loads the corrected nav CSS and scripts.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 5 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live HTTP check: `/` and `/settings` returned 200 and both pages include `20260708-nav4`.
- Browser visual check at 1280px viewport: `#langToggle` rendered at `x=1165.67`, `y=29.33`, `width=56`; `Model Settings` rendered as a dark pill button immediately beside it.

### Notes
- Changed files: `app/static/index.html` and `settings.html` bump asset versions; `app/static/styles.css` adjusts `.nav-actions`, `#langToggle`, and `.nav-button.nav-link`; `progress.md` records the verified correction.
- Rollback: restore the asset query strings to `20260708-nav3`, reset `.nav-actions` margins to the previous values, remove the `#langToggle` fixed width rule, and change `.nav-button.nav-link` selectors back to `.nav-link`.

## 2026-07-08 - Task: Support Chinese local problem keywords
### What was done
- Let local problem keyword extraction keep Chinese keyword groups, so inputs like `登录失败 支付回调` can drive repository scanning.

### Testing
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 6 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.

### Notes
- Changed files: `app/services/search.py` adds Chinese keyword extraction; `tests/test_core.py` covers Chinese terms; `progress.md` records the change.
- Rollback: restore the previous ASCII-only regex in `extract_queries` and remove `test_extract_queries_keeps_chinese_terms`.

## 2026-07-08 - Task: Generate task outputs in execution language
### What was done
- Analysis now receives the current page language, so Chinese pages generate Chinese reports and English pages generate English reports.
- Existing report and test result text no longer changes when the UI language is switched later.
- Analysis returns detected test command suggestions and the test command input now exposes them through a native browser datalist.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 8 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live HTTP check: `/` and `/settings` returned 200 and both pages include `20260708-nav5`.

### Notes
- Changed files: `app/models.py` adds analysis language; `app/services/analyzer.py` renders reports by execution language; `app/services/testing.py` suggests test commands; `app/main.py` returns suggestions after analysis; `app/static/index.html`, `app/static/app.js`, `app/static/i18n.js`, and `settings.html` wire the UI; `tests/test_core.py` covers the new behavior.
- Rollback: remove `AnalyzeRequest.lang`, call `analyze` and `report_to_markdown` without language, remove `suggest_test_commands`, remove `testCommandOptions`, and restore asset versions.

## 2026-07-08 - Task: Explain test commands and test results
### What was done
- Added plain-language descriptions under the test command input after analysis suggests commands.
- Added a beginner-friendly pass/fail explanation at the end of each test result while preserving the raw command output.
- Bumped static asset versions so the browser loads the updated UI scripts and styles.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 8 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live HTTP check: `/` and `/settings` returned 200 and both pages include `20260708-nav6`.

### Notes
- Changed files: `app/static/index.html` adds the command help line; `app/static/app.js` renders command descriptions and test explanations; `app/static/i18n.js` adds Chinese/English wording; `app/static/styles.css` styles the helper text; `settings.html` bumps static asset versions; `progress.md` records the update.
- Rollback: remove `testCommandHelp`, delete the command description and explanation helpers from `app.js`, remove the added i18n keys and `.command-help` style, then restore static asset versions.

## 2026-07-19 - Task: Convert RepoPilot into a conversational agent with repository memory
### What was done
- Replaced the linear task screen with a modern responsive conversation workspace containing conversation history, repository setup, chat messages, code evidence, long-term memory, and test command panels.
- Added repository-scoped conversations, persistent messages, explicit `记住：...` / `Remember: ...` long-term memory, memory deletion, code search for each question, and OpenAI/Anthropic conversational replies with rule fallback.
- Preserved human-approved test execution and displayed test results as conversation tool messages.
- Updated project documentation for the conversational workflow and memory model.

### Testing
- `node --check app\\static\\i18n.js; node --check app\\static\\app.js; node --check app\\static\\settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 9 passed.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live HTTP check: `/`, `/settings`, and `/api/conversations` returned 200; static pages include `20260719-chat4`.
- Browser QA at 1440x900: created a conversation for `F:\\AI project\\ai agent`, saved two repository memories, received test command suggestions, and ran `python -m pytest -q` successfully.
- Browser QA at 375x812: conversation history, new conversation, settings, language control, message input, and send action remained accessible without horizontal overflow.

### Notes
- Changed files: `app/db.py` adds conversation, message, and memory tables; `app/models.py`, `app/main.py`, and `app/services/analyzer.py` add conversational APIs and model/fallback replies; `app/static/index.html`, `app/static/app.js`, `app/static/i18n.js`, `app/static/styles.css`, and `settings.html` provide the new responsive UI; `tests/test_core.py` covers persistent memory; `README.md` and `docs/architecture.md` document the workflow.
- Rollback: revert this task's changed files, restart the service, and remove the `conversations`, `messages`, and `memories` tables only if their stored data is no longer needed.

## 2026-07-19 - Task: Unify model settings UI and move user avatars right
### What was done
- Rebuilt the model settings page with the same modern sidebar, header, cards, controls, color tokens, and responsive behavior as the conversation workspace.
- Moved each user avatar to the right of its message bubble while keeping RepoPilot and tool avatars on the left.
- Added static asset cache busting and an empty favicon to prevent stale styling and console noise.

### Testing
- `node --check app/static/i18n.js; node --check app/static/app.js; node --check app/static/settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 9 passed, 3 existing deprecation warnings.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live HTTP checks: `/` and `/settings` returned 200 and included `20260719-chat5`.
- Browser QA at `1440x900`: settings layout rendered without horizontal overflow; provider switching, language switching, and back navigation target worked; browser console had no errors.
- Browser QA at `375x812`: settings page had no horizontal overflow and kept the back and language controls visible.
- Message geometry check confirmed the user avatar starts after the user bubble's right edge.
- `design-qa.md` -> `final result: passed`.

### Notes
- Changed files: `app/static/app.js` changes user message element order; `app/static/index.html` and `app/static/settings.html` update assets and page structure; `app/static/styles.css` adds the unified settings layout and right-side user message grid; `design-qa.md` records visual evidence; `progress.md` records this task.
- Rollback: restore the previous settings markup and settings CSS block, restore `row.append(avatar, body)` in `appendMessage`, remove the user-specific grid override, and revert the static asset query strings.

## 2026-07-19 - Task: Change the shared sidebar to a white theme
### What was done
- Changed the shared main/settings sidebar from dark navy to a translucent white surface that matches the rest of the interface.
- Updated sidebar text, conversation states, empty text, borders, and footer buttons for readable contrast and a consistent indigo active state.
- Bumped the shared stylesheet version so both pages load the new sidebar immediately.

### Testing
- `node --check app/static/i18n.js; node --check app/static/app.js; node --check app/static/settings.js` -> completed successfully.
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 9 passed, 3 existing deprecation warnings.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Live HTTP checks: `/` and `/settings` returned 200 and included `20260719-chat6`.
- Browser QA at `1440x900`: both pages rendered the shared sidebar as `rgba(255, 255, 255, 0.94)` with no horizontal overflow or console errors.
- Browser QA at `375x812`: the white mobile navigation rendered without horizontal overflow.

### Notes
- Changed files: `app/static/styles.css` updates the shared sidebar palette and interaction states; `app/static/index.html` and `app/static/settings.html` bump the stylesheet version; `progress.md` records this task.
- Rollback: restore the previous dark `.sidebar`, conversation, and `.sidebar-link` color rules, then change the stylesheet query string back to `20260719-chat5`.

## 2026-07-19 - Task: Search approximate code from natural-language questions
### What was done
- Added local intent expansion so Chinese and English questions about project purpose, startup, authentication, configuration, storage, APIs, search, tests, UI, and payments produce likely source-code terms.
- Added a second model-assisted query expansion pass through the active OpenAI or Anthropic provider only when the first local search returns no evidence.
- Improved evidence quality by returning unique files, prioritizing source files and filename matches, and correctly parsing absolute Windows paths from `rg`.
- Updated fallback wording and project documentation to describe natural-language code search.

### Testing
- `.\\.venv\\Scripts\\python.exe -m pytest -q` -> 11 passed, 3 existing deprecation warnings.
- `.\\.venv\\Scripts\\python.exe -m compileall app tests` -> completed successfully.
- Manual search for `查一下这个项目大概作用` returned `app/main.py`, `app/services/search.py`, `app/services/analyzer.py`, and `README.md`.
- Manual search for `记忆相关的` returned `app/db.py`, `app/models.py`, `app/services/search.py`, and `app/main.py`.
- Endpoint-level TestClient verification returned HTTP 200 and ranked `app/main.py` first for the Chinese project-purpose question.
- Restarted the local service and verified `GET /api/conversations` returned HTTP 200 on PID `52776`.

### Notes
- Changed files: `app/services/search.py` adds local intent expansion, ranking, unique-file results, and Windows path parsing; `app/services/analyzer.py` adds provider-assisted query expansion; `app/main.py` runs the second search pass when needed; `tests/test_core.py` covers natural-language search and model query parsing; `README.md` and `docs/architecture.md` document the new flow; `progress.md` records this task.
- Rollback: remove `INTENT_HINTS`, `expand_search_queries`, the second search pass, the new ranking helpers and tests, then restore the previous README and architecture wording.

## 2026-07-21 - Task: Add Chinese README
### What was done
- Changed the project README into a bilingual document with Chinese first and English retained below.
- Added Chinese descriptions for features, startup, usage, configuration, safety boundaries, and the resume summary.
- Added language navigation at the top of the README.

### Testing
- Read `README.md` as UTF-8 and verified the Chinese text and required bilingual headings.
- `git diff --check` completed successfully.

### Notes
- Changed files: `README.md` adds the Chinese documentation and keeps the English version; `progress.md` records this task.
- Rollback: restore `README.md` and remove this final progress entry.

## 2026-10-18 - Task: Add an offline retrieval evaluation baseline
### What was done
- Added a fixed bilingual retrieval suite with positive and no-result cases, Recall@5/MRR@5/no-result metrics, per-case evidence, and a failing exit code below quality thresholds.
- Recorded the approved local-single-user scope and ordered implementation in the existing docs directory.

### Testing
- `.\.venv\Scripts\python.exe -m pytest tests/test_evaluation.py -q` -> 2 passed, including a deliberately broken retriever failing the gate.
- `.\.venv\Scripts\python.exe -m app.evaluation` -> 10 cases; all three metrics 1.0, quality gate passed.

### Notes
- Files: `app/evaluation.py` runs evaluation; `tests/fixtures/retrieval.json` defines expectations; `tests/fixtures/retrieval_repo/*.py` provides fixed source samples; `tests/test_evaluation.py` checks pass/fail behavior; `docs/quality-boundaries.md` records approved scope; `progress.md` appends this entry.
- Rollback: remove only these new evaluation files and this entry. Pre-task progress backup: `C:\Users\lpc\AppData\Local\Temp\repopilot-quality-wxpnmy7x\progress.md`.
- Limits: synthetic retrieval baseline only; no external model calls or answer-quality claim.

## 2026-10-18 - Task: Add request and model observability
### What was done
- Added server-generated request IDs, structured request status/duration and model mode/error-type events, including formerly silent model errors.
- Added SQLite connectivity health checks and generic traced server errors without exception contents.

### Testing
- `.\.venv\Scripts\python.exe -m pytest tests/test_observability.py tests/test_core.py -q` -> 14 passed, 3 pre-existing deprecation warnings.
- Verified fresh request IDs, 422 tracing, healthy/failed database responses, model-error visibility, and exclusion of sensitive values from application events.

### Notes
- Files: `app/observability.py` owns operational event logging and HTTP tracing; `app/main.py` wires tracing and health; `app/services/analyzer.py` reports model outcomes; `tests/test_observability.py` covers tracing, health and failure behavior; `progress.md` appends this entry.
- Rollback: restore the task-owned edits in main/analyzer, remove observability and its tests, and remove this entry; keep the preceding evaluation task and pre-existing work.
- Limits: JSON events use the Uvicorn error logger; external access/HTTP client loggers retain their own formatting and retention settings.

## 2026-10-18 - Task: Enforce approved local-single-user boundaries and close quality verification
### What was done
- Enforced loopback/Host/same-origin access, JSON writes, an actual 64 KiB request-body ceiling, and canonical repository roots on creation and later operations.
- Disabled tests by default and restricted enabled execution to exact detected commands; bounded literal rg search, excluded common secret files, constrained model instructions and checked structured report citations.
- Added operational search/test events, normal workflow and boundary regressions; synchronized bilingual setup, architecture, diagnostics, quality thresholds, limitations and rollback instructions.

### Testing
- `.\.venv\Scripts\python.exe -m pytest -q` -> 39 passed, 3 pre-existing deprecation warnings. Covers both task/conversation APIs, same-origin success, remote/cross-site/Host rejection, actual body size, roots including Windows junctions, disabled/arbitrary commands, timeout, sanitized failures and normal search/report persistence.
- `.\.venv\Scripts\python.exe -m app.evaluation` -> 10 cases; Recall@5=1.0, MRR@5=1.0, no-result accuracy=1.0; exit 0. Broken-retriever regression confirms a failed gate returns nonzero.
- `.\.venv\Scripts\python.exe -m compileall -q app tests` -> exit 0; `git diff --check` -> exit 0. All 25 task-owned text files decode as UTF-8 without BOM. The original progress backup remains an exact byte prefix.
- `.\.venv\Scripts\python.exe C:/Users/lpc/AppData/Local/Temp/repopilot-quality-wxpnmy7x/http_smoke.py` -> real Uvicorn/HTTP on an ephemeral loopback port and temporary SQLite: pages/health 200, cross-origin and untrusted Host 403, outside root 400, normal chat evidence and correlated search/model/request events, disabled tests 400, enabled fixed compile command exit 0. Temporary server shut down; existing service untouched.
- Smoke harness initially expected an incorrect nested test-result field; corrected it to the existing top-level response contract and reran successfully. SQLite handles in the temporary harness required garbage collection before Windows cleanup; no database code changed.

### Notes
- Files: `.env.example` documents roots and execution switches; `app/security.py` owns HTTP/repository boundaries; `app/models.py` bounds inputs; `app/main.py` enforces entry checks and sanitized dependency errors; `app/services/search.py` bounds and filters rg; `app/services/testing.py` enforces execution policy; `app/services/analyzer.py` constrains prompts and report citations; `tests/conftest.py` isolates runtime config and credentials; `tests/test_core.py` uses a loopback client; `tests/test_security.py` covers boundary/failure behavior; `tests/test_observability.py` adds normal correlated API workflows; `README.md` and `docs/architecture.md` document final behavior; `docs/quality-boundaries.md` holds operating/rollback details; `progress.md` appends this entry. Earlier entries list the new evaluation/observability modules and fixtures.
- Rollback: follow the exact tracked-file allowlist and new-file list in `docs/quality-boundaries.md`, using source `e02d8b17a8d6eeec95c90056e6bc79a01abad87e`. Preserve pre-existing `.serena/`, `design-qa.md`, `.env`, runtime database and pre-task progress content. Pre-task progress backup: `C:\Users\lpc\AppData\Local\Temp\repopilot-quality-wxpnmy7x\progress.md`.
- Activation: real `.env` remains unchanged; set `REPOPILOT_REPO_ROOTS` to intended trusted roots before restarting the existing service. Tests remain off unless explicitly enabled in configuration. No commit or push.
- Limits: fixed synthetic retrieval suite, no real OpenAI/Anthropic/GitHub calls or browser UI session; npm/go/cargo/mvn execution was not exercised. Test scripts keep OS user permissions; child-process isolation and full-output memory limits remain outside this implementation. Existing SQLite connection lifecycle and third-party logging behavior were preserved.

## 2026-10-18 - Task: Close Windows executable lookup boundary
### What was done
- Reproduced Python 3.12 Windows `shutil.which` implicitly selecting a working-directory `npm.cmd` despite an explicit filtered PATH.
- Changed test-tool lookup to absolute candidates in PATH directories outside the repository tree; added a regression with competing repository/current-directory/trusted tools and a missing trusted tool.

### Testing
- `.\.venv\Scripts\python.exe -m pytest -q` -> 40 passed, 3 pre-existing deprecation warnings. The added regression confirms only the external trusted tool reaches subprocess; removing it blocks execution.
- `.\.venv\Scripts\python.exe -m compileall -q app tests` -> exit 0.
- Reran the real-HTTP temporary-server smoke harness -> all checks passed, including enabled fixed Python compile exit 0 and request/search/model event correlation.
- Initial regression assertion differed only in Windows PATHEXT suffix casing; changed the assertion to compare normalized OS paths and reran successfully.

### Notes
- Files: `app/services/testing.py` resolves absolute executable candidates; `tests/test_security.py` covers Windows current-directory precedence and repository PATH entries; `docs/quality-boundaries.md` documents lookup semantics; `progress.md` appends this evidence.
- Rollback: restore the preceding test-tool lookup lines and remove this added regression/document sentence; full-task rollback remains in `docs/quality-boundaries.md`.
- No dependency, real configuration, database, existing service, commit or remote change.

## 2026-10-18 - Task: Prepare verified quality changes for repository upload
### What was done
- Prepared the completed evaluation, observability and local-single-user boundary changes for the user-requested commit and push to `poolaiming/RepoPilot`, branch `main`.
- Limited the submission to the 25 task-owned files, including only this task's progress additions; preserved the pre-existing interview-document entry, `.serena/` and `design-qa.md` locally.

### Testing
- `.\.venv\Scripts\python.exe -m pytest -q` -> 40 passed, 3 pre-existing deprecation warnings.
- `.\.venv\Scripts\python.exe -m app.evaluation` -> 10 cases, all three metrics 1.0, quality gate passed.
- `.\.venv\Scripts\python.exe -m compileall -q app tests` and `git diff --check` -> exit 0.
- `git fetch origin main` and `git rev-list --left-right --count HEAD...origin/main` -> remote checked, 0 ahead / 0 behind before commit.
- All 25 task-owned text files decode as UTF-8 without BOM; credential-pattern scan found no matches. The pre-task progress backup remains an exact byte prefix.

### Notes
- Files: the existing task-owned source, tests, fixtures, config example and docs are submitted together; `progress.md` appends this upload-preparation evidence.
- Rollback after upload: use `git revert` on the quality-change commit; keep local unrelated files and the pre-existing progress entry. No history rewrite is required.
- Runtime activation remains separate: configure trusted repository roots and restart the existing service. Real provider calls and browser UI verification remain outside this upload check.
