const I18N = {
  dict: {
    en: {
      settings: "Model Settings",
      tagline: "Evidence-first issue triage for local repositories.",
      issueUrl: "Issue URL",
      repoPath: "Local Repo Path",
      problem: "Local Problem",
      problemPlaceholder: "Use this when there is no GitHub issue.",
      createTask: "Create Task",
      scanRepo: "Scan Repo",
      analyze: "Analyze",
      issue: "Issue",
      evidence: "Evidence",
      report: "Report",
      testCommand: "Test Command",
      runTest: "Run Test",
      testResult: "Test Result",
      noTask: "No task yet.",
      noEvidence: "No evidence yet.",
      noReport: "No report yet.",
      noTest: "No test run yet.",
      taskCreated: "Task created.",
      back: "Back",
      provider: "Provider",
      apiKey: "API Key",
      baseUrl: "Base URL",
      model: "Model",
      keepKey: "Leave blank to keep existing key",
      fetchModels: "Fetch Models",
      save: "Save",
      loading: "Loading...",
      configured: "configured",
      missing: "missing",
      openaiKey: "OpenAI key",
      anthropicKey: "Anthropic key",
      fetchedModels: "Fetched {count} {provider} models.",
      savedConfig: "Saved. The running server can use this config now; restart only if you edited .env by hand.",
      language: "Language",
      command: "Command",
      exitCode: "Exit code",
      output: "Output",
      commandHelpEmpty: "Analyze first to get command suggestions.",
      commandHelpTitle: "Suggested command purpose:",
      explanation: "Plain-English explanation",
      testPassed: "Passed: exit code 0 means the command finished successfully.",
      testFailed: "Not passed: a non-zero exit code usually means tests failed, syntax is wrong, or the command errored. Read the output above first.",
    },
    zh: {
      settings: "模型设置",
      tagline: "面向本地仓库的证据优先 Issue 分诊。",
      issueUrl: "Issue 地址",
      repoPath: "本地仓库路径",
      problem: "本地问题",
      problemPlaceholder: "没有 GitHub Issue 时填写这里。",
      createTask: "创建任务",
      scanRepo: "扫描仓库",
      analyze: "分析",
      issue: "Issue",
      evidence: "证据",
      report: "报告",
      testCommand: "测试命令",
      runTest: "运行测试",
      testResult: "测试结果",
      noTask: "还没有任务。",
      noEvidence: "还没有证据。",
      noReport: "还没有报告。",
      noTest: "还没有测试结果。",
      taskCreated: "任务已创建。",
      back: "返回",
      provider: "接口类型",
      apiKey: "API Key",
      baseUrl: "Base URL",
      model: "模型",
      keepKey: "留空则保留现有 key",
      fetchModels: "拉取模型",
      save: "保存",
      loading: "加载中...",
      configured: "已配置",
      missing: "未配置",
      openaiKey: "OpenAI key",
      anthropicKey: "Anthropic key",
      fetchedModels: "已拉取 {count} 个 {provider} 模型。",
      savedConfig: "已保存。当前服务可直接使用；只有手动改 .env 后才需要重启。",
      language: "语言",
      command: "命令",
      exitCode: "退出码",
      output: "输出",
      commandHelpEmpty: "先分析，再自动生成测试命令建议。",
      commandHelpTitle: "建议命令作用：",
      explanation: "小白说明",
      testPassed: "通过：退出码 0 表示命令正常完成，当前检查没有发现失败。",
      testFailed: "未通过：退出码不是 0，通常表示测试失败、语法错误或命令运行出错。先看上面的输出。",
    },
  },
  lang() {
    return localStorage.getItem("repopilot_lang") || "zh";
  },
  t(key, vars = {}) {
    let text = (this.dict[this.lang()] || this.dict.zh)[key] || key;
    for (const [name, value] of Object.entries(vars)) text = text.replace(`{${name}}`, value);
    return text;
  },
  setLang(lang) {
    localStorage.setItem("repopilot_lang", lang);
    this.apply();
  },
  apply() {
    document.documentElement.lang = this.lang();
    document.querySelectorAll("[data-i18n]").forEach((node) => {
      node.textContent = this.t(node.dataset.i18n);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
      node.placeholder = this.t(node.dataset.i18nPlaceholder);
    });
    const toggle = document.getElementById("langToggle");
    if (toggle) toggle.textContent = this.lang() === "zh" ? "中文" : "EN";
  },
};

window.I18N = I18N;
document.addEventListener("DOMContentLoaded", () => {
  I18N.apply();
  const toggle = document.getElementById("langToggle");
  if (toggle) toggle.addEventListener("click", () => I18N.setLang(I18N.lang() === "zh" ? "en" : "zh"));
});
