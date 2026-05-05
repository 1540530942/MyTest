const healthEl = document.querySelector("#health");
const tabs = document.querySelectorAll("[data-view]");
const views = {
  modules: document.querySelector("#modulesView"),
  llm: document.querySelector("#llmView"),
};
const moduleMetrics = document.querySelector("#moduleMetrics");
const moduleList = document.querySelector("#moduleList");
const refreshModules = document.querySelector("#refreshModules");
const providerForm = document.querySelector("#providerForm");
const providerList = document.querySelector("#providerList");
const providerSelect = document.querySelector("#providerSelect");
const modelInput = document.querySelector("#modelInput");
const messagesEl = document.querySelector("#messages");
const chatForm = document.querySelector("#chatForm");
const promptInput = document.querySelector("#promptInput");
const refreshProviders = document.querySelector("#refreshProviders");

const initialAssistantMessage = {
  role: "assistant",
  content: "先配置一个兼容 OpenAI Chat Completions 的接口，然后就可以开始对话。",
};

let modules = [];
let providers = [];
let messages = [initialAssistantMessage];

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(readableError(text) || response.statusText);
  }
  return response.json();
}

function readableError(text) {
  try {
    const data = JSON.parse(text);
    return data.detail || text;
  } catch {
    return text;
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setView(name) {
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.view === name));
  Object.entries(views).forEach(([viewName, view]) => view.classList.toggle("active", viewName === name));
}

function statusLabel(status) {
  const labels = {
    ready: "就绪",
    integration: "集成中",
    scaffold: "骨架",
    "extension-point": "扩展入口",
  };
  return labels[status] || status || "未标注";
}

function connectionLabel(state) {
  const labels = {
    online: "在线",
    offline: "离线",
    unknown: "未知",
    not_configured: "未配置",
  };
  return labels[state] || state;
}

function renderModuleMetrics() {
  const total = modules.length;
  const online = modules.filter((module) => module.connection_state === "online").length;
  const ready = modules.filter((module) => module.status === "ready").length;
  const developing = modules.filter((module) => ["integration", "scaffold"].includes(module.status)).length;
  moduleMetrics.innerHTML = [
    ["模块总数", total],
    ["连接正常", online],
    ["已就绪", ready],
    ["开发中", developing],
  ]
    .map(([label, value]) => `<article class="metric"><span>${label}</span><strong>${value}</strong></article>`)
    .join("");
}

function renderModules() {
  renderModuleMetrics();
  moduleList.innerHTML = modules.length
    ? modules
        .map(
          (module) => `
            <article class="module-card ${escapeHtml(module.connection_state)}">
              <div class="module-main">
                <div>
                  <div class="module-title">
                    <h3>${escapeHtml(module.name)}</h3>
                    <span>${escapeHtml(module.id)}</span>
                  </div>
                  <p>${escapeHtml(module.summary)}</p>
                </div>
                <div class="module-state">
                  <strong>${connectionLabel(module.connection_state)}</strong>
                  <span>${statusLabel(module.status)}</span>
                </div>
              </div>
              <div class="module-grid">
                <div>
                  <span>当前进展</span>
                  <p>${escapeHtml(module.current_progress)}</p>
                </div>
                <div>
                  <span>下一步</span>
                  <p>${escapeHtml(module.next_step)}</p>
                </div>
                <div>
                  <span>连接状态</span>
                  <p>${escapeHtml(module.connection_detail)}</p>
                </div>
                <div>
                  <span>访问入口</span>
                  <p>${module.local_url ? `<a href="${escapeHtml(module.local_url)}" target="_blank" rel="noreferrer">本地</a>` : "本地未配置"}${module.public_url ? ` · <a href="${escapeHtml(module.public_url)}" target="_blank" rel="noreferrer">公网</a>` : ""}</p>
                </div>
              </div>
              <div class="capabilities">
                ${(module.capabilities || []).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
              </div>
            </article>
          `,
        )
        .join("")
    : '<p class="empty-state">还没有读取到模块注册信息。</p>';
}

async function loadModules() {
  moduleList.innerHTML = '<p class="empty-state">正在检查模块状态...</p>';
  modules = await api("./api/modules");
  renderModules();
  await loadHealth();
}

function renderMessages() {
  messagesEl.innerHTML = messages
    .map((message) => `<article class="message ${message.role}">${escapeHtml(message.content)}</article>`)
    .join("");
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function providerKeyStatus(provider) {
  if (provider.api_key_masked) return provider.api_key_masked;
  if (provider.has_env_key) return `${provider.api_key_env} 已读取`;
  if (provider.api_key_env) return `${provider.api_key_env} 未读取`;
  return "未配置";
}

function renderProviders() {
  providerSelect.innerHTML = providers.length
    ? providers.map((provider) => `<option value="${provider.id}">${escapeHtml(provider.name)}</option>`).join("")
    : '<option value="">暂无接口</option>';

  providerList.innerHTML = providers.length
    ? providers
        .map(
          (provider) => `
            <article class="provider-card">
              <div>
                <strong>${escapeHtml(provider.name)}</strong>
                <span>${escapeHtml(provider.id)}</span>
              </div>
              <p>${escapeHtml(provider.base_url)}${escapeHtml(provider.chat_path)}</p>
              <p>模型：${escapeHtml(provider.default_model)} · Key：${escapeHtml(providerKeyStatus(provider))}</p>
              <p>状态：${provider.enabled ? "启用" : "停用"}</p>
              <button type="button" data-delete="${escapeHtml(provider.id)}">删除</button>
            </article>
          `,
        )
        .join("")
    : '<p class="empty-state">还没有配置接口。</p>';

  const selected = providers.find((provider) => provider.id === providerSelect.value) || providers[0];
  if (selected) {
    providerSelect.value = selected.id;
    modelInput.value = selected.default_model;
  } else {
    modelInput.value = "";
  }
}

async function loadHealth() {
  try {
    const data = await api("./api/health");
    healthEl.textContent = `正常 · ${data.modules} 个模块 · ${data.providers} 个大模型接口`;
    healthEl.classList.add("ok");
  } catch (error) {
    healthEl.textContent = "异常";
    healthEl.classList.remove("ok");
  }
}

async function loadProviders() {
  providers = await api("./api/providers");
  renderProviders();
  await loadHealth();
}

tabs.forEach((tab) => tab.addEventListener("click", () => setView(tab.dataset.view)));

refreshModules.addEventListener("click", loadModules);

providerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(providerForm);
  const payload = Object.fromEntries(form.entries());
  payload.enabled = form.get("enabled") === "on";
  if (!payload.id) delete payload.id;
  if (!payload.api_key) delete payload.api_key;
  if (!payload.api_key_env) delete payload.api_key_env;

  await api("./api/providers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  providerForm.reset();
  providerForm.elements.chat_path.value = "/chat/completions";
  providerForm.elements.enabled.checked = true;
  await loadProviders();
});

providerSelect.addEventListener("change", () => {
  const provider = providers.find((item) => item.id === providerSelect.value);
  if (provider) modelInput.value = provider.default_model;
});

providerList.addEventListener("click", async (event) => {
  const target = event.target.closest("[data-delete]");
  if (!target) return;
  await api(`./api/providers/${target.dataset.delete}`, { method: "DELETE" });
  await loadProviders();
});

refreshProviders.addEventListener("click", loadProviders);

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const content = promptInput.value.trim();
  if (!content) return;

  messages.push({ role: "user", content });
  promptInput.value = "";
  renderMessages();

  try {
    const data = await api("./api/chat", {
      method: "POST",
      body: JSON.stringify({
        provider_id: providerSelect.value || null,
        model: modelInput.value || null,
        messages: messages.filter((message) => message !== initialAssistantMessage),
      }),
    });
    messages.push({ role: "assistant", content: data.content || "模型没有返回文本内容。" });
  } catch (error) {
    messages.push({ role: "assistant", content: `调用失败：${error.message}` });
  }
  renderMessages();
});

renderMessages();
Promise.all([loadHealth(), loadModules(), loadProviders()]).catch((error) => {
  moduleList.innerHTML = `<p class="empty-state">加载模块状态失败：${escapeHtml(error.message)}</p>`;
  messages.push({ role: "assistant", content: `加载配置失败：${error.message}` });
  renderMessages();
});
