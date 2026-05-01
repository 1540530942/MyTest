const healthEl = document.querySelector("#health");
const providerForm = document.querySelector("#providerForm");
const providerList = document.querySelector("#providerList");
const providerSelect = document.querySelector("#providerSelect");
const modelInput = document.querySelector("#modelInput");
const messagesEl = document.querySelector("#messages");
const chatForm = document.querySelector("#chatForm");
const promptInput = document.querySelector("#promptInput");
const refreshProviders = document.querySelector("#refreshProviders");

let providers = [];
let messages = [
  { role: "assistant", content: "先配置一个兼容 OpenAI Chat Completions 的接口，然后就可以开始对话。" },
];

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function renderMessages() {
  messagesEl.innerHTML = messages
    .map((message) => `<article class="message ${message.role}">${escapeHtml(message.content)}</article>`)
    .join("");
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderProviders() {
  providerSelect.innerHTML = providers
    .map((provider) => `<option value="${provider.id}">${escapeHtml(provider.name)}</option>`)
    .join("");
  providerList.innerHTML = providers
    .map(
      (provider) => `
        <article class="provider-card">
          <div>
            <strong>${escapeHtml(provider.name)}</strong>
            <span>${escapeHtml(provider.id)}</span>
          </div>
          <p>${escapeHtml(provider.base_url)}${escapeHtml(provider.chat_path)}</p>
          <p>模型：${escapeHtml(provider.default_model)} · Key：${provider.api_key_masked || (provider.has_env_key ? "env" : "未配置")}</p>
          <button data-delete="${provider.id}">删除</button>
        </article>
      `,
    )
    .join("");

  const selected = providers.find((provider) => provider.id === providerSelect.value) || providers[0];
  if (selected) {
    providerSelect.value = selected.id;
    modelInput.value = selected.default_model;
  }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadHealth() {
  try {
    const data = await api("./api/health");
    healthEl.textContent = `正常 · ${data.providers} 个接口`;
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
        messages: messages.filter((message) => message.role !== "assistant" || message.content !== messages[0].content),
      }),
    });
    messages.push({ role: "assistant", content: data.content || "模型没有返回文本内容。" });
  } catch (error) {
    messages.push({ role: "assistant", content: `调用失败：${error.message}` });
  }
  renderMessages();
});

renderMessages();
loadProviders().catch((error) => {
  messages.push({ role: "assistant", content: `加载配置失败：${error.message}` });
  renderMessages();
});
