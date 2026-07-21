let currentConversationId = null;
let currentConversation = null;
let currentCommands = [];

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) throw new Error(data.detail || response.statusText);
  return data;
}

function showSetup() {
  currentConversationId = null;
  currentConversation = null;
  $("setupView").hidden = false;
  $("chatView").hidden = true;
  $("conversationTitle").textContent = I18N.t("welcomeTitle");
  $("repoLabel").textContent = I18N.t("welcomeSubtitle");
  renderMemories([]);
  renderEvidence([]);
  renderCommands([]);
  document.querySelectorAll(".conversation-item").forEach((node) => node.classList.remove("active"));
  $("repoPath").focus();
}

async function loadConversations(selectLatest = false) {
  const data = await api("/api/conversations");
  renderConversations(data.conversations);
  if ((selectLatest || !currentConversationId) && data.conversations.length) {
    await loadConversation(data.conversations[0].id);
  } else if (!data.conversations.length) {
    showSetup();
  }
}

function renderConversations(conversations) {
  $("conversationList").innerHTML = "";
  if (!conversations.length) {
    const empty = document.createElement("p");
    empty.className = "sidebar-empty";
    empty.textContent = I18N.t("noConversations");
    $("conversationList").appendChild(empty);
    return;
  }
  for (const conversation of conversations) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `conversation-item${conversation.id === currentConversationId ? " active" : ""}`;
    button.dataset.id = conversation.id;

    const title = document.createElement("strong");
    title.textContent = conversation.title;
    const repo = document.createElement("span");
    repo.textContent = conversation.repo_path.split(/[\\/]/).filter(Boolean).pop() || conversation.repo_path;
    button.append(title, repo);
    button.addEventListener("click", () => loadConversation(conversation.id));
    $("conversationList").appendChild(button);
  }
}

async function loadConversation(id) {
  const data = await api(`/api/conversations/${id}`);
  currentConversationId = id;
  currentConversation = data.conversation;
  $("setupView").hidden = true;
  $("chatView").hidden = false;
  $("conversationTitle").textContent = data.conversation.title;
  $("repoLabel").textContent = data.conversation.repo_path;
  renderMessages(data.messages);
  renderMemories(data.memories);

  const latestMetadata = [...data.messages].reverse().find((item) => item.metadata?.evidence || item.metadata?.test_commands)?.metadata || {};
  renderEvidence(latestMetadata.evidence || []);
  renderCommands(latestMetadata.test_commands || []);
  document.querySelectorAll(".conversation-item").forEach((node) => {
    node.classList.toggle("active", Number(node.dataset.id) === id);
  });
  $("messageInput").focus();
}

function renderMessages(messages) {
  $("messages").innerHTML = "";
  if (!messages.length) {
    appendMessage({
      role: "assistant",
      content: I18N.t("startPrompt"),
    });
    return;
  }
  messages.forEach(appendMessage);
  scrollMessages();
}

function appendMessage(message, extraClass = "") {
  const row = document.createElement("article");
  row.className = `message-row ${message.role} ${extraClass}`.trim();

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = message.role === "user" ? "U" : "R";

  const body = document.createElement("div");
  body.className = "message-body";
  const author = document.createElement("div");
  author.className = "message-author";
  author.textContent = message.role === "user" ? I18N.t("you") : message.role === "tool" ? I18N.t("toolResult") : "RepoPilot";
  const content = document.createElement("div");
  content.className = "message-content";
  content.textContent = message.content;
  body.append(author, content);
  row.append(message.role === "user" ? body : avatar, message.role === "user" ? avatar : body);
  $("messages").appendChild(row);
  scrollMessages();
  return row;
}

function renderMemories(memories) {
  $("memoryList").innerHTML = "";
  $("memoryCount").textContent = memories.length;
  if (!memories.length) {
    $("memoryList").appendChild(emptyCopy(I18N.t("noMemory")));
    return;
  }
  for (const memory of memories) {
    const card = document.createElement("div");
    card.className = "memory-card";
    const text = document.createElement("p");
    text.textContent = memory.content;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "icon-button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", I18N.t("deleteMemory"));
    remove.addEventListener("click", async () => {
      await api(`/api/memories/${memory.id}`, { method: "DELETE" });
      await loadConversation(currentConversationId);
    });
    card.append(text, remove);
    $("memoryList").appendChild(card);
  }
}

function renderEvidence(evidence) {
  $("evidenceList").innerHTML = "";
  $("evidenceCount").textContent = evidence.length;
  if (!evidence.length) {
    $("evidenceList").appendChild(emptyCopy(I18N.t("noEvidence")));
    return;
  }
  for (const item of evidence) {
    const card = document.createElement("div");
    card.className = "evidence-card";
    const path = document.createElement("strong");
    path.textContent = item.file_path;
    const snippet = document.createElement("p");
    snippet.textContent = item.snippet.split("\n").slice(0, 3).join("\n");
    card.append(path, snippet);
    $("evidenceList").appendChild(card);
  }
}

function renderCommands(commands) {
  currentCommands = commands;
  $("commandChips").innerHTML = "";
  $("runTestBtn").disabled = !currentConversationId;
  if (!commands.length) {
    $("commandChips").appendChild(emptyCopy(I18N.t("noTestCommands")));
    return;
  }
  for (const command of commands) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "command-chip";
    const code = document.createElement("strong");
    code.textContent = command;
    const description = document.createElement("span");
    description.textContent = commandDescription(command);
    button.append(code, description);
    button.addEventListener("click", () => {
      $("testCommand").value = command;
      $("testCommand").focus();
    });
    $("commandChips").appendChild(button);
  }
  if (!$("testCommand").value) $("testCommand").value = commands[0];
}

function commandDescription(command) {
  const zh = I18N.lang() === "zh";
  if (command.includes("pytest")) return zh ? "运行 Python 自动测试" : "Run Python tests";
  if (command.includes("compileall")) return zh ? "检查 Python 语法" : "Check Python syntax";
  if (command === "npm test") return zh ? "运行 Node 测试" : "Run Node tests";
  if (command === "npm run lint") return zh ? "检查代码规范" : "Check lint rules";
  if (command.startsWith("go test")) return zh ? "运行 Go 测试" : "Run Go tests";
  if (command === "cargo test") return zh ? "运行 Rust 测试" : "Run Rust tests";
  if (command === "mvn test") return zh ? "运行 Maven 测试" : "Run Maven tests";
  return zh ? "运行项目验证" : "Run project verification";
}

function emptyCopy(text) {
  const empty = document.createElement("p");
  empty.className = "empty-copy";
  empty.textContent = text;
  return empty;
}

function scrollMessages() {
  requestAnimationFrame(() => {
    $("messages").scrollTop = $("messages").scrollHeight;
  });
}

function setSending(sending) {
  $("sendBtn").disabled = sending;
  $("messageInput").disabled = sending;
}

$("workspaceForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("setupError").textContent = "";
  $("createConversationBtn").disabled = true;
  try {
    const data = await api("/api/conversations", {
      method: "POST",
      body: JSON.stringify({
        repo_path: $("repoPath").value.trim(),
        issue_url: $("issueUrl").value.trim() || null,
        lang: I18N.lang(),
      }),
    });
    await loadConversation(data.conversation.id);
    await loadConversations();
  } catch (error) {
    $("setupError").textContent = error.message;
  } finally {
    $("createConversationBtn").disabled = false;
  }
});

$("messageForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = $("messageInput").value.trim();
  if (!content || !currentConversationId) return;
  $("messageInput").value = "";
  autoResizeMessageInput();
  appendMessage({ role: "user", content });
  const pending = appendMessage({ role: "assistant", content: I18N.t("thinking") }, "pending");
  setSending(true);
  try {
    const data = await api(`/api/conversations/${currentConversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content, lang: I18N.lang() }),
    });
    pending.remove();
    appendMessage(data.message);
    renderEvidence(data.evidence || []);
    renderCommands(data.test_commands || []);
    renderMemories(data.memories || []);
    if (currentConversation && ["新对话", "New conversation"].includes(currentConversation.title)) {
      currentConversation.title = content.slice(0, 48);
      $("conversationTitle").textContent = currentConversation.title;
    }
    await loadConversations();
  } catch (error) {
    pending.remove();
    appendMessage({ role: "assistant", content: error.message }, "error");
  } finally {
    setSending(false);
    $("messageInput").focus();
  }
});

$("messageInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    $("messageForm").requestSubmit();
  }
});

$("messageInput").addEventListener("input", autoResizeMessageInput);

function autoResizeMessageInput() {
  $("messageInput").style.height = "auto";
  $("messageInput").style.height = `${Math.min($("messageInput").scrollHeight, 180)}px`;
}

$("runTestBtn").addEventListener("click", async () => {
  const command = $("testCommand").value.trim();
  if (!command || !currentConversationId) {
    $("testError").textContent = I18N.t("enterTestCommand");
    return;
  }
  $("testError").textContent = "";
  $("runTestBtn").disabled = true;
  try {
    const data = await api(`/api/conversations/${currentConversationId}/test`, {
      method: "POST",
      body: JSON.stringify({ command, lang: I18N.lang() }),
    });
    appendMessage(data.message);
  } catch (error) {
    $("testError").textContent = error.message;
  } finally {
    $("runTestBtn").disabled = false;
  }
});

$("newChatBtn").addEventListener("click", showSetup);

loadConversations(true).catch((error) => {
  showSetup();
  $("setupError").textContent = error.message;
});
