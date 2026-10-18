# RepoPilot

[中文](#中文) | [English](#english)

<a id="中文"></a>

## 中文

RepoPilot 是一个面向本地代码仓库的对话式工程 Agent。它能够保存对话上下文和仓库长期记忆，将中文、英文等自然语言问题扩展为可能的代码关键词，通过 `rg` 搜索源码，展示相关代码证据，并在用户确认后执行一条验证命令。

### 核心能力

- 使用自然语言查询仓库中的近似功能代码。
- 分析 GitHub Issue 或直接描述的本地工程问题。
- 保存仓库级长期记忆，在后续对话中复用。
- 支持 OpenAI Responses API 和 Anthropic Messages API。
- 展示代码证据、分析结论和测试命令建议。
- 测试命令必须经过用户确认后才会执行。
- 提供离线检索评估、请求追踪、模型失败记录及健康检查。
- 支持中文和英文界面，新任务按执行时语言生成结果。

### 快速开始

首次使用先将 `.env.example` 复制为 `.env`，设置允许访问的仓库根目录（包含其子目录）：

```dotenv
REPOPILOT_REPO_ROOTS='F:/AI project/ai agent'
REPOPILOT_ALLOW_TESTS=false
```

多个根目录在 Windows 上用 `;` 分隔，在 Linux/macOS 上用 `:` 分隔。根目录留空时，仓库操作会被阻止。
完成配置后双击 `start-repopilot.cmd`，或者运行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --env-file .env
```

浏览器打开 `http://127.0.0.1:8000`。

### 使用方法

1. 新建对话并选择一个本地代码仓库。
2. 直接用自然语言提问，也可以附加 GitHub Issue。
3. 查看 Agent 找到的源码证据、分析结果和测试建议。
4. 如需执行测试，先对可信仓库设置 `REPOPILOT_ALLOW_TESTS=true`，然后确认并执行建议列表中的原样命令。

示例问题：

```text
这个项目的登录功能在哪里实现？
查找和模型配置相关的代码
分析这个报错可能涉及哪些文件
记住：这个项目使用 pytest
```

打开 `http://127.0.0.1:8000/settings` 可以切换 OpenAI 或 Anthropic、获取模型列表、保存当前模型配置，并切换中文或英文界面。

未配置模型 API Key 时，RepoPilot 仍然可以搜索本地代码，并返回基于规则的代码证据摘要。如果首次搜索没有结果且模型已经配置，RepoPilot 会调用当前模型补充源码搜索词，再进行一次检索。

### 配置

| 环境变量 | 必填 | 作用 |
|---|---|---|
| `REPOPILOT_REPO_ROOTS` | 是 | 允许操作的本地仓库根目录；留空时阻止仓库操作。 |
| `REPOPILOT_ALLOW_TESTS` | 否 | 默认 `false`；设为 `true` 后允许执行检测到的固定测试命令。 |
| `GITHUB_TOKEN` | 否 | 提高 GitHub API 请求额度，并在权限允许时读取私有 Issue。 |
| `MODEL_PROVIDER` | 否 | 使用 `openai` 或 `anthropic`，默认 `openai`。 |
| `OPENAI_API_KEY` | 否 | 启用 OpenAI 分析；未配置时使用规则分析。 |
| `OPENAI_BASE_URL` | 否 | OpenAI 兼容接口地址，默认 `https://api.openai.com/v1`。 |
| `OPENAI_MODEL` | 否 | OpenAI 模型名称，默认 `gpt-4.1-mini`。 |
| `ANTHROPIC_API_KEY` | 否 | 当 Provider 为 Anthropic 时启用模型分析。 |
| `ANTHROPIC_BASE_URL` | 否 | Anthropic 接口地址，默认 `https://api.anthropic.com/v1`。 |
| `ANTHROPIC_MODEL` | 否 | Claude 模型 ID。 |

也可以手动编辑 `.env`，然后重启 `start-repopilot.cmd`：

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

### 安全边界

RepoPilot 面向本地单人使用，校验本机连接、Host 和同源请求，限制请求体为 64 KiB，并在每次仓库操作时校验配置的根目录。测试默认关闭，启用后仅执行检测到的固定命令，使用当前 Python 或 PATH 中的工具，以 120 秒超时启动进程。项目测试脚本拥有当前用户权限；开启前应确认仓库可信。

源码检索排除 `.env*`、密钥及数据库等常见文件；配置模型后，对话、记忆、Issue 和代码证据会发送到所选 Provider。文件名过滤及提示词约束覆盖有限，源码中的硬编码秘密仍需自行检查。项目保持人工确认测试流程，不自动修改、提交、推送或合并代码。

### 评估与运行检查

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m app.evaluation
curl.exe -i http://127.0.0.1:8000/api/health
```

离线评估包含 10 个中英检索案例，输出 Recall@5、MRR@5、空结果准确率，低于阈值时退出码为 1。
响应头 `X-Request-ID` 可关联终端中的 JSON 请求、检索、模型及测试事件；模型失败会记录错误类型和规则降级模式。
健康检查检测 SQLite 连通性，成功为 200，数据库异常为 503。
配置说明、指标定义、日志范围和回滚步骤见 [质量与本地边界](docs/quality-boundaries.md)。

### 简历描述

开发 RepoPilot 对话式工程 Agent，实现仓库级长期记忆、自然语言源码检索、代码证据分析、OpenAI/Anthropic 双模型接入和人工确认测试流程。

---

<a id="english"></a>

## English

RepoPilot is a conversational engineering agent for local repositories. It keeps recent conversation context, stores explicit repository memories, expands natural-language questions into likely code terms, searches with `rg`, explains relevant evidence, and runs one verification command after human approval.

### Features

- Search for approximate code functionality with natural-language questions.
- Analyze a GitHub Issue or a directly described local engineering problem.
- Store repository-scoped long-term memory for future conversations.
- Support the OpenAI Responses API and Anthropic Messages API.
- Present source evidence, analysis, and suggested test commands.
- Run a test command only after explicit user confirmation.
- Run offline retrieval evaluations, trace requests and model failures, and check database health.
- Support Chinese and English UI and execution-language-specific results.

### Quick Start

First copy `.env.example` to `.env` and set trusted repository roots (including their subdirectories):

```dotenv
REPOPILOT_REPO_ROOTS='F:/AI project/ai agent'
REPOPILOT_ALLOW_TESTS=false
```

Separate multiple roots with `;` on Windows or `:` on Linux/macOS. Empty roots block repository operations.
Then double-click `start-repopilot.cmd`, or run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --env-file .env
```

Open `http://127.0.0.1:8000`.

### Usage

1. Create a conversation and select a local repository.
2. Ask a question normally, with an optional GitHub Issue.
3. Review the source evidence, analysis, and suggested tests.
4. To run tests in trusted repositories, set `REPOPILOT_ALLOW_TESTS=true`, then confirm an exact suggested command.

Example prompts:

```text
Where is authentication implemented?
Find code related to model configuration
Which files may be involved in this error?
Remember: use npm test for this repository
```

Open `http://127.0.0.1:8000/settings` to switch between OpenAI and Anthropic, fetch model lists, save the active model configuration, and switch the UI language.

Without an LLM API key, RepoPilot still searches the repository and returns a deterministic evidence summary. When a model is configured and the first search has no hits, RepoPilot asks the active model for additional source-code search terms and searches again.

### Configuration

| Variable | Required | Purpose |
|---|---|---|
| `REPOPILOT_REPO_ROOTS` | Yes | Trusted local repository roots; empty roots block repository operations. |
| `REPOPILOT_ALLOW_TESTS` | No | Defaults to `false`; `true` enables detected, fixed test commands. |
| `GITHUB_TOKEN` | No | Raises GitHub API limits and reads private issues if permitted. |
| `MODEL_PROVIDER` | No | Uses `openai` or `anthropic`; defaults to `openai`. |
| `OPENAI_API_KEY` | No | Enables OpenAI analysis; otherwise RepoPilot uses deterministic fallback analysis. |
| `OPENAI_BASE_URL` | No | OpenAI-compatible endpoint; defaults to `https://api.openai.com/v1`. |
| `OPENAI_MODEL` | No | OpenAI model name; defaults to `gpt-4.1-mini`. |
| `ANTHROPIC_API_KEY` | No | Enables Anthropic analysis when the provider is Anthropic. |
| `ANTHROPIC_BASE_URL` | No | Anthropic endpoint; defaults to `https://api.anthropic.com/v1`. |
| `ANTHROPIC_MODEL` | No | Claude model ID. |

You can also edit `.env` manually and restart `start-repopilot.cmd`:

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

### Safety Boundary

RepoPilot targets local, single-user operation. It checks loopback connections, Host and same-origin requests, caps request bodies at 64 KiB, and checks configured roots on every repository operation. Test execution defaults to disabled; enabling it permits exact detected commands using the current Python or PATH tools, with a 120-second process timeout. Repository scripts retain your OS user permissions, so only enable them for trusted code.

Search excludes common `.env*`, key and database files. Configured providers receive conversation context, memories, issues and source evidence. Filename filters and prompt instructions have limited coverage; review hardcoded source secrets yourself. Test execution remains human-approved; RepoPilot does not automatically edit, commit, push, or merge code.

### Evaluation and Operations

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m app.evaluation
curl.exe -i http://127.0.0.1:8000/api/health
```

The offline suite contains 10 bilingual retrieval cases and reports Recall@5, MRR@5 and no-result accuracy. A failed threshold returns exit code 1.
Use the response `X-Request-ID` to correlate JSON request, search, model and test events in the server terminal. Model errors record their type and rule-fallback mode.
The health endpoint checks SQLite connectivity: 200 on success, 503 on database errors.
See [Quality and Local Boundaries](docs/quality-boundaries.md) for configuration, metric definitions, logging limits and rollback steps.

### Resume Bullet

Built RepoPilot, a conversational engineering agent with repository-scoped long-term memory, evidence-grounded natural-language code search, OpenAI/Anthropic support, and human-approved verification commands.
