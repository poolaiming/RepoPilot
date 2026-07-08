const $ = (id) => document.getElementById(id);

function status(value) {
  $("statusPanel").textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
}

async function api(path, options = {}) {
  const response = await fetch(path, { headers: { "Content-Type": "application/json" }, ...options });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok) throw new Error(data.detail || response.statusText);
  return data;
}

function setOptions(select, models, current) {
  select.innerHTML = "";
  for (const model of models) {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    select.appendChild(option);
  }
  if (current && !models.includes(current)) {
    const option = document.createElement("option");
    option.value = current;
    option.textContent = current;
    select.appendChild(option);
  }
  select.value = current || models[0] || "";
}

function activeProvider() {
  return $("provider").value;
}

function togglePanels() {
  $("openaiPanel").hidden = activeProvider() !== "openai";
  $("anthropicPanel").hidden = activeProvider() !== "anthropic";
}

async function loadConfig() {
  const config = await api("/api/config");
  $("provider").value = config.provider || "openai";
  $("openaiBaseUrl").value = config.openai_base_url || "";
  $("anthropicBaseUrl").value = config.anthropic_base_url || "";
  setOptions($("openaiModel"), [], config.openai_model);
  setOptions($("anthropicModel"), [], config.anthropic_model);
  togglePanels();
  status({
    [I18N.t("openaiKey")]: config.has_openai_key ? I18N.t("configured") : I18N.t("missing"),
    [I18N.t("anthropicKey")]: config.has_anthropic_key ? I18N.t("configured") : I18N.t("missing"),
  });
}

$("provider").addEventListener("change", togglePanels);

$("fetchModelsBtn").addEventListener("click", async () => {
  try {
    await saveConfig();
    const provider = activeProvider();
    const data = await api(`/api/config/models?provider=${encodeURIComponent(provider)}`);
    setOptions(provider === "openai" ? $("openaiModel") : $("anthropicModel"), data.models, "");
    status(I18N.t("fetchedModels", { count: data.models.length, provider }));
  } catch (error) {
    status(error.message);
  }
});

$("saveBtn").addEventListener("click", async () => {
  try {
    await saveConfig();
    status(I18N.t("savedConfig"));
  } catch (error) {
    status(error.message);
  }
});

async function saveConfig() {
  return api("/api/config", {
    method: "PUT",
    body: JSON.stringify({
      provider: activeProvider(),
      openai_api_key: $("openaiKey").value,
      openai_base_url: $("openaiBaseUrl").value,
      openai_model: $("openaiModel").value,
      anthropic_api_key: $("anthropicKey").value,
      anthropic_base_url: $("anthropicBaseUrl").value,
      anthropic_model: $("anthropicModel").value,
    }),
  });
}

loadConfig().catch((error) => status(error.message));
