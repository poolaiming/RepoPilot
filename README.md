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
- 支持中文和英文界面，新任务按执行时语言生成结果。

### 快速开始

双击 `start-repopilot.cmd`，或者运行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --env-file .env
```

浏览器打开 `http://127.0.0.1:8000`。

### 使用方法

1. 新建对话并选择一个本地代码仓库。
2. 直接用自然语言提问，也可以附加 GitHub Issue。
3. 查看 Agent 找到的源码证据、分析结果和测试建议。
4. 确认测试命令后执行验证。

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

RepoPilot 只读取 Issue 和本地代码，将对话记忆保存在 SQLite 中，并且只执行用户明确确认的一条测试命令。它不会自动修改、提交、推送或合并代码。

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
- Support Chinese and English UI and execution-language-specific results.

### Quick Start

Double-click `start-repopilot.cmd`, or run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --env-file .env
```

Open `http://127.0.0.1:8000`.

### Usage

1. Create a conversation and select a local repository.
2. Ask a question normally, with an optional GitHub Issue.
3. Review the source evidence, analysis, and suggested tests.
4. Confirm a test command before running verification.

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

RepoPilot reads issues and local code, stores conversation memory in SQLite, and runs only one test command explicitly approved by the user. It does not automatically edit, commit, push, or merge code.

### Resume Bullet

Built RepoPilot, a conversational engineering agent with repository-scoped long-term memory, evidence-grounded natural-language code search, OpenAI/Anthropic support, and human-approved verification commands.
