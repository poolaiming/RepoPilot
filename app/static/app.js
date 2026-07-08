let taskId = null;

const $ = (id) => document.getElementById(id);
const show = (id, value) => {
  $(id).textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
};

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) throw new Error(data.detail || response.statusText);
  return data;
}

$("createBtn").addEventListener("click", async () => {
  try {
    const payload = {
      issue_url: $("issueUrl").value.trim() || null,
      problem: $("problem").value.trim() || null,
      repo_path: $("repoPath").value.trim(),
    };
    const data = await request("/api/tasks", { method: "POST", body: JSON.stringify(payload) });
    taskId = data.task.id;
    $("scanBtn").disabled = false;
    $("analyzeBtn").disabled = false;
    $("testBtn").disabled = false;
    show("issuePanel", data.issue || data.task.problem || I18N.t("taskCreated"));
  } catch (error) {
    show("issuePanel", error.message);
  }
});

$("scanBtn").addEventListener("click", async () => {
  try {
    const data = await request(`/api/tasks/${taskId}/scan`, { method: "POST", body: JSON.stringify({}) });
    show("evidencePanel", data);
  } catch (error) {
    show("evidencePanel", error.message);
  }
});

$("analyzeBtn").addEventListener("click", async () => {
  try {
    const data = await request(`/api/tasks/${taskId}/analyze`, {
      method: "POST",
      body: JSON.stringify({ use_llm: true, lang: I18N.lang() }),
    });
    show("reportPanel", data.markdown);
    setTestCommandOptions(data.test_commands || []);
  } catch (error) {
    show("reportPanel", error.message);
  }
});

$("testBtn").addEventListener("click", async () => {
  try {
    const data = await request(`/api/tasks/${taskId}/test`, {
      method: "POST",
      body: JSON.stringify({ command: $("testCommand").value.trim() }),
    });
    show("testPanel", formatTestResult($("testCommand").value.trim(), data));
  } catch (error) {
    show("testPanel", error.message);
  }
});

function setTestCommandOptions(commands) {
  $("testCommandOptions").innerHTML = "";
  for (const command of commands) {
    const option = document.createElement("option");
    option.value = command;
    option.label = commandDescription(command);
    $("testCommandOptions").appendChild(option);
  }
  if (!$("testCommand").value && commands.length) $("testCommand").value = commands[0];
  showCommandHelp(commands);
}

function formatTestResult(command, result) {
  const summary = result.exit_code === 0 ? I18N.t("testPassed") : I18N.t("testFailed");
  return `${I18N.t("command")}: ${command}\n${I18N.t("exitCode")}: ${result.exit_code}\n\n${I18N.t("output")}:\n${result.output || ""}\n\n${I18N.t("explanation")}:\n${summary}`;
}

function showCommandHelp(commands) {
  $("testCommandHelp").removeAttribute("data-i18n");
  if (!commands.length) {
    $("testCommandHelp").textContent = I18N.t("commandHelpEmpty");
    return;
  }
  $("testCommandHelp").textContent = `${I18N.t("commandHelpTitle")}\n${commands.map((command) => `${command}: ${commandDescription(command)}`).join("\n")}`;
}

function commandDescription(command) {
  const zh = I18N.lang() === "zh";
  if (command.includes("pytest")) return zh ? "运行 Python 自动测试，检查功能是否按预期通过。" : "Runs Python tests to check behavior.";
  if (command.includes("compileall")) return zh ? "检查 Python 文件有没有语法错误。" : "Checks Python files for syntax errors.";
  if (command === "npm test") return zh ? "运行前端或 Node 项目的测试脚本。" : "Runs the Node or frontend test script.";
  if (command === "npm run lint") return zh ? "检查前端或 Node 代码风格和常见问题。" : "Checks Node or frontend lint rules.";
  if (command.startsWith("go test")) return zh ? "运行 Go 项目的测试。" : "Runs Go tests.";
  if (command === "cargo test") return zh ? "运行 Rust 项目的测试。" : "Runs Rust tests.";
  if (command === "mvn test") return zh ? "运行 Java Maven 项目的测试。" : "Runs Java Maven tests.";
  return zh ? "运行项目验证命令。" : "Runs a project verification command.";
}
