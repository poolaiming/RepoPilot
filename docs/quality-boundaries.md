# RepoPilot 质量与本地边界

## 本轮范围与实施顺序

目标：为现有本地单人 Agent 补充可重复的评估、可定位的运行记录及实际执行的安全边界。
用户已选择本地单人方案。以 `README.md`、`docs/architecture.md` 和现有服务为基线；
沿用 FastAPI、SQLite、rg、pytest 和 Python 标准库，不新增基础设施或依赖。
现有文档声明的人工确认和 shell 字符过滤不足以约束 HTTP 调用和任意可执行程序，必须补代码。

| 顺序 | Owner 与落点 | 验收 |
|---|---|---|
| 1 评估 | `app/evaluation.py`、固定检索样本、评估测试 | 离线输出 Recall@5、MRR@5、空结果准确率，低于阈值返回非零退出码 |
| 2 可观测性 | `app/observability.py`、HTTP 中间件、现有 analyzer/search/testing | 请求 ID、状态、耗时、模型模式/错误类型可关联；健康检查检测 SQLite；日志不记录正文、密钥、命令输出 |
| 3 安全边界 | `app/security.py`、现有 search/testing、API 入口及 models | 本机/同源校验、仓库根目录限制、默认关闭执行、固定命令白名单、秘密文件排除、参数边界和回归 |
| 4 收口 | README、architecture、progress | 全量 pytest、离线评估、compileall、diff/编码检查通过，记录回滚及未覆盖项 |

兼容：保留现有响应字段、界面和数据库结构。安全策略会收紧过去允许的任意路径与命令；
部署者通过 `.env` 明确设置可信仓库根目录及执行开关。历史任务在使用时重新校验路径。
评估仅衡量固定样本上的本地检索，不宣称代表模型回答质量或真实仓库泛化能力。

TDD Route：off / skipped；不采用严格 test-first，实施后补行为回归与故障注入。
执行方式：inline；共享入口改动串行，无 commit、push 或服务重启。
起点：`e02d8b17a8d6eeec95c90056e6bc79a01abad87e`，main 与 origin/main 对齐；
已有 `progress.md` 改动、`.serena/`、`design-qa.md` 保留。

风险：可信测试脚本仍拥有当前用户权限；模型开启后上下文会发送到配置的 Provider；
日志为进程输出，由运行环境负责留存；不引入多人鉴权或 OS 级沙箱。

## 配置与启动

在项目 `.env` 中设置实际可信目录；示例允许当前项目及其子目录：

```dotenv
REPOPILOT_REPO_ROOTS='F:/AI project/ai agent'
REPOPILOT_ALLOW_TESTS=false
```

Windows 多目录示例：`REPOPILOT_REPO_ROOTS='F:/projects;D:/work'`；Linux/macOS 用 `:` 分隔。
目录会先解析为规范路径，根目录自身及子目录允许，兄弟路径和解析后越界的链接被阻止。
未配置 roots 时，新建对话、创建任务及历史任务的仓库操作返回 400；历史记录继续保留。
本轮保留现有 `.env` 与数据库，部署者应补 roots 后重启原服务加载新代码。

按既有方式启动 `start-repopilot.cmd`，使用 `http://127.0.0.1:8000` 或 `http://localhost:8000`。
保持绑定回环地址，不通过远程代理暴露。HTTP 入口同时验证连接来源及 Host，浏览器 Origin 必须
与打开的地址（包括端口）一致；无 Origin 的本机 CLI 可访问。跨站请求、非 JSON 写入返回 403，
实际请求体超过 64 KiB 返回 413。请求 ID 同样附加到这些响应中。

测试执行默认关闭。确认仓库可信后才设置 `REPOPILOT_ALLOW_TESTS=true`；界面原样选择检测出的命令。
命令之外的参数、拼接命令及任意可执行文件会被阻止。Python 命令使用 RepoPilot 当前解释器，
其他工具需安装在 PATH。测试结果保留真实退出码，展示最后 6000 字符；超时为 120 秒。
工具查找逐个检查 PATH 中的绝对目录，跳过目标仓库及其子目录，避免 Windows 隐式查找当前目录中的同名程序。
测试事件记录结果、耗时及退出码，不把命令输出写入事件日志。

## 离线评估与质量门

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m app.evaluation
```

评估输出 JSON，包含每个案例的实际词条、文件排序、得分、整体指标和阈值；通过返回 0，
任一阈值未达返回 1。固定仓库与标注一同提交，避免依赖当前业务仓库或真实模型配置。

| 指标 | 计算与验收 |
|---|---|
| Recall@5 | 每个正例前 5 个结果命中的期望文件比例，再对正例取平均；至少 0.90 |
| MRR@5 | 每个正例前 5 个结果中首个相关文件排名的倒数，未命中记 0，再取平均；至少 0.80 |
| 空结果准确率 | 负例实际返回空结果的比例；必须为 1.00 |

当前样本版本为 `offline-retrieval-v1`：8 个正例、2 个空结果案例，覆盖中英文问题。
回归还将检索器替换为空结果，确认质量门确实失败。该小样本仅用于发现已知检索退化；
模型生成质量、提示注入鲁棒性、真实大仓库召回和延迟预算尚未量化。

## 请求追踪与故障定位

```powershell
curl.exe -i http://127.0.0.1:8000/api/health
```

正常响应为 `{"status":"ok","database":"ok"}`；SQLite 连接或查询错误返回 503。
该接口检测连通性，未执行完整性检查、写入检查或外部模型探测。

从响应头复制 `X-Request-ID`，在启动终端的 JSON 事件中查找同值：

```json
{"event":"model","request_id":"<response-id>","operation":"chat","mode":"rules_after_error","error_type":"TimeoutError","duration_ms":30001.2}
{"event":"request","request_id":"<response-id>","method":"POST","route":"/api/conversations/{conversation_id}/messages","status":200,"duration_ms":30008.4,"error_type":null}
```

| 事件 | 含义 |
|---|---|
| `request` | 方法、路由模板、HTTP 状态、响应创建耗时、异常类型；未匹配路由记 `unmatched` |
| `search` | 词条数量、结果数量、检索耗时 |
| `model` | 操作 `chat` / `analyze` / `query_expansion`、模式、耗时与错误类型 |
| `test` | `blocked` / `passed` / `failed` / `timeout`，执行结束时含退出码与耗时 |
| `health` / `github` / `model_list` | 对应依赖失败的类型 |

模型模式：`llm` 表示调用和解析成功，`rules` 表示直接规则处理，`rules_after_error` 表示模型异常后
沿用规则结果，`skipped` 表示未配置模型而跳过扩词。请求 200 本身不代表调用过模型。
服务端生成 ID，忽略客户端传来的 ID；跨请求会清理上下文。未处理异常返回通用 500 和 ID。

应用事件只记录元数据，排除正文、源码、密钥、URL 查询参数、异常文本和命令输出。
Uvicorn access log、HTTP 客户端等第三方日志独立配置；应用事件脱敏规则不替代它们的日志策略。
事件输出到 `uvicorn.error` 的 INFO 级别，调高日志等级会隐藏这些记录。部署环境负责留存、轮转和访问权限；
当前未增加日志平台、token/费用统计或流式响应全程计时。

## 明确的使用边界

- 本机单人规则约束 HTTP 与操作入口，本机其他进程仍可调用接口；不用于多人或公网部署。
- 固定命令白名单限制命令入口，项目自身的测试、构建钩子仍有当前用户权限。直接进程有超时，
  子进程树未做隔离；输出在返回前全量捕获，6000 字符限制仅作用于展示。
- `.env*`、`*.pem`、`*.key`、`*.sqlite*`、`*.db`、`package-lock.json`、`.git` 从检索中排除。
  这些模式覆盖常见文件，用户输入、历史消息和普通源码中的秘密仍可能进入模型上下文。
- 模型开启后，对话、记忆、Issue 和代码证据发送至配置的 Provider；API Key 仍由既有 `.env` 保存机制管理。
  提示词要求将外部内容当作数据，结构化报告文件引用另有校验；自由文本答案仍需人工核对。
- 本轮保持数据库结构及现有响应字段，未执行数据迁移、服务重启、真实 Provider 调用或生产切换。

## 回滚

以下命令仅针对本轮修改、且施工前干净的 tracked 文件；执行前确认这些文件没有后续工作：

```powershell
git restore --source=e02d8b17a8d6eeec95c90056e6bc79a01abad87e -- .env.example README.md docs/architecture.md app/main.py app/models.py app/services/analyzer.py app/services/search.py app/services/testing.py tests/test_core.py
```

然后仅删除本轮新增的 `app/evaluation.py`、`app/observability.py`、`app/security.py`、
`tests/conftest.py`、`tests/test_evaluation.py`、`tests/test_observability.py`、`tests/test_security.py`、
`tests/fixtures/` 和本文档。保留原有 `.serena/`、`design-qa.md`、`.env` 和数据库。
`progress.md` 有施工前改动，应只移除本轮追加段落；原始完整备份位于
`C:\Users\lpc\AppData\Local\Temp\repopilot-quality-wxpnmy7x\progress.md`，先比较再恢复，保留后续新增记录。
回滚后重启原服务加载旧代码。
