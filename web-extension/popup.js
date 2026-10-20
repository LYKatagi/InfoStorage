const loginPanel = document.querySelector("#login-panel");
const generatorPanel = document.querySelector("#generator-panel");
const pageTools = document.querySelector("#page-tools");
const statusLine = document.querySelector("#status");
const resultBox = document.querySelector("#result-box");
let activeTabId = null;
let pageInfo = null;
let credentials = [];

function showStatus(message = "") {
  statusLine.textContent = message;
}

function normalizeApiUrl(value) {
  const url = new URL(value.trim());
  if (url.username || url.password || url.search || url.hash) {
    throw new Error("Use somente o endereço base da API, sem credenciais ou parâmetros.");
  }
  const isLocalHttp = url.protocol === "http:" && ["localhost", "127.0.0.1", "[::1]"].includes(url.hostname);
  if (url.protocol !== "https:" && !isLocalHttp) {
    throw new Error("Use HTTPS para acessar uma API fora do computador local.");
  }
  return url.href.replace(/\/$/, "");
}

async function allowApiHost(apiUrl) {
  const url = new URL(apiUrl);
  const granted = await chrome.permissions.request({ origins: [`${url.origin}/*`] });
  if (!granted) throw new Error("Permita o acesso à origem da API para continuar.");
}

async function apiRequest(path, { token, ...options } = {}) {
  const { apiUrl } = await chrome.storage.local.get("apiUrl");
  const headers = { Accept: "application/json", ...(options.body ? { "Content-Type": "application/json" } : {}) };
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${apiUrl}${path}`, { ...options, headers: { ...headers, ...options.headers }, cache: "no-store" });
  const payload = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload?.detail || "Não foi possível concluir a solicitação.");
    error.status = response.status;
    throw error;
  }
  return payload;
}

async function requireToken() {
  const { accessToken } = await chrome.storage.session.get("accessToken");
  if (!accessToken) throw new Error("Entre na API novamente para continuar.");
  return accessToken;
}

async function showActionError(error) {
  if (error.status === 401) {
    await chrome.storage.session.remove(["accessToken", "username"]);
    generatorPanel.hidden = true;
    pageTools.hidden = true;
    loginPanel.hidden = false;
    showStatus("Sua sessão da API expirou. Entre novamente.");
    return;
  }
  showStatus(error.message || "Não foi possível concluir a operação.");
}

function detectLoginPage() {
  const visible = (element) => element.getClientRects().length > 0 && !element.disabled;
  const passwordInputs = Array.from(document.querySelectorAll('input[type="password"]')).filter(visible);
  if (!passwordInputs.length || !passwordInputs[0].form) {
    return { found: false, origin: location.origin, hostname: location.hostname, title: document.title || location.hostname };
  }

  const form = passwordInputs[0].form;
  const fields = Array.from(form.querySelectorAll("input")).filter(visible);
  const usernameField = fields.find((field) => field.type === "email" || field.autocomplete.toLowerCase().includes("username"))
    || fields.find((field) => ["text", "tel"].includes(field.type) && field !== passwordInputs[0]);
  const words = `${location.pathname} ${form.innerText || ""} ${Array.from(form.querySelectorAll("button, input[type=submit]")).map((node) => node.innerText || node.value).join(" ")}`.toLowerCase();
  const signup = passwordInputs.length > 1 || /sign.?up|register|create account|cadastro|criar conta/.test(words);

  return {
    found: true,
    origin: location.origin,
    hostname: location.hostname,
    title: document.title || location.hostname,
    signup,
    username: usernameField?.value || "",
    password: passwordInputs[0].value || "",
  };
}

function captureCurrentLogin() {
  const visible = (element) => element.getClientRects().length > 0 && !element.disabled;
  const password = Array.from(document.querySelectorAll('input[type="password"]')).find(visible);
  if (!password?.form || !password.value) return null;
  const fields = Array.from(password.form.querySelectorAll("input")).filter(visible);
  const user = fields.find((field) => field.type === "email" || field.autocomplete.toLowerCase().includes("username"))
    || fields.find((field) => ["text", "tel"].includes(field.type) && field !== password);
  return { origin: location.origin, title: document.title || location.hostname, username: user?.value || "", password: password.value };
}

function fillAndSubmitLogin(username, password) {
  const visible = (element) => element.getClientRects().length > 0 && !element.disabled;
  const passwordField = Array.from(document.querySelectorAll('input[type="password"]')).find(visible);
  if (!passwordField?.form) return false;
  const form = passwordField.form;
  const fields = Array.from(form.querySelectorAll("input")).filter(visible);
  const usernameField = fields.find((field) => field.type === "email" || field.autocomplete.toLowerCase().includes("username"))
    || fields.find((field) => ["text", "tel"].includes(field.type) && field !== passwordField);
  const setValue = (field, value) => {
    if (!field) return;
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
    setter.call(field, value);
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));
  };
  setValue(usernameField, username);
  setValue(passwordField, password);
  form.requestSubmit();
  return true;
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) throw new Error("Não consegui acessar a aba atual.");
  activeTabId = tab.id;
  return tab;
}

function setPendingSave(pending) {
  document.querySelector("#page-title").textContent = pending.title || new URL(pending.origin).hostname;
  document.querySelector("#page-origin").textContent = pending.origin;
  document.querySelector("#page-badge").textContent = "Login enviado";
  document.querySelector("#pending-username").textContent = pending.username || "Usuário não identificado";
  document.querySelector("#pending-save").hidden = false;
}

async function updateSiteDetectionStatus() {
  const title = document.querySelector("#watch-title");
  const description = document.querySelector("#watch-description");
  const enable = document.querySelector("#enable-site-watch");
  const disable = document.querySelector("#disable-site-watch");
  const url = new URL(pageInfo.origin);
  if (!["http:", "https:"].includes(url.protocol)) {
    title.textContent = "Detecção indisponível";
    description.textContent = "Abra um site HTTP ou HTTPS para ativar a detecção.";
    enable.hidden = true;
    disable.hidden = true;
    return;
  }
  const status = await chrome.runtime.sendMessage({ type: "get-site-detection", origin: url.origin });
  if (status?.error) throw new Error(status.error);
  title.textContent = status.enabled ? "Detecção ativa neste site" : "Detecção desligada";
  description.textContent = status.enabled
    ? "Formulários enviados neste site serão salvos como credenciais."
    : "Ative para detectar formulários de login e cadastro neste site.";
  enable.hidden = status.enabled;
  disable.hidden = !status.enabled;
}

async function inspectCurrentPage() {
  try {
    const tab = await getActiveTab();
    const pendingKey = `pendingLogin:${activeTabId}`;
    const pending = (await chrome.storage.session.get(pendingKey))[pendingKey];
    let injected;
    try {
      [injected] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: detectLoginPage });
    } catch (error) {
      if (!pending) throw error;
      pageTools.hidden = false;
      pageInfo = { found: false, origin: pending.origin, hostname: new URL(pending.origin).hostname, title: pending.title };
      setPendingSave(pending);
      document.querySelector("#login-actions").hidden = true;
      await updateSiteDetectionStatus();
      showStatus("");
      return;
    }
    pageInfo = injected?.result;
    if (pageInfo?.origin) {
      pageTools.hidden = false;
      document.querySelector("#page-title").textContent = pageInfo.title || pageInfo.hostname;
      document.querySelector("#page-origin").textContent = pageInfo.origin;
      document.querySelector("#login-actions").hidden = !pageInfo.found;
      if (!pageInfo.found) document.querySelector("#page-badge").textContent = "Página atual";
      await updateSiteDetectionStatus();
    }
    if (!pageInfo?.found) {
      if (pending) {
        setPendingSave(pending);
        document.querySelector("#login-actions").hidden = true;
        showStatus("");
        return;
      }
      showStatus("");
      return;
    }

    pageTools.hidden = false;
    document.querySelector("#page-title").textContent = pageInfo.title;
    document.querySelector("#page-origin").textContent = pageInfo.origin;
    document.querySelector("#page-badge").textContent = pageInfo.signup ? "Cadastro" : "Login";
    document.querySelector("#login-actions").hidden = false;
    await loadSavedCredentials();

    document.querySelector("#saved-credential").hidden = false;
    document.querySelector("#fill-login").hidden = false;
    document.querySelector("#save-current").hidden = false;
    if (pending) setPendingSave(pending);
    else document.querySelector("#pending-save").hidden = true;
    showStatus("");
  } catch (error) {
    if (error.status === 401) {
      await chrome.storage.session.remove(["accessToken", "username"]);
      generatorPanel.hidden = true;
      loginPanel.hidden = false;
      showStatus("Sua sessão da API expirou. Entre novamente.");
    } else {
      pageTools.hidden = true;
      showStatus("Não foi possível carregar a página ou as credenciais da API.");
    }
  }
}

async function loadSavedCredentials() {
  const token = await requireToken();
  credentials = await apiRequest("/api/v1/credentials", { token });
  const select = document.querySelector("#saved-credential");
  select.replaceChildren(new Option("Selecione uma credencial", ""));
  credentials.forEach((item, index) => {
    const option = new Option(`${item.title}${item.username ? ` · ${item.username}` : ""}`, String(index));
    select.add(option);
  });
  const matching = credentials.findIndex((item) => item.title.toLowerCase() === pageInfo.hostname.toLowerCase()
    || item.notes.includes(pageInfo.origin));
  if (matching >= 0) select.value = String(matching);
}

async function saveCredential(values) {
  if (!values?.password) throw new Error("Preencha a senha no formulário antes de salvar.");
  const token = await requireToken();
  await apiRequest("/api/v1/credentials", {
    method: "POST",
    token,
    body: JSON.stringify({
      title: new URL(values.origin || pageInfo.origin).hostname,
      username: values.username || "",
      password: values.password,
      notes: `Salvo pela extensão para ${values.origin || pageInfo.origin}`,
    }),
  });
  await loadSavedCredentials();
  showStatus("Credencial salva no InfoStorage.");
}

async function showGenerator() {
  const session = await chrome.storage.session.get(["accessToken", "username"]);
  if (!session.accessToken) return;
  loginPanel.hidden = true;
  generatorPanel.hidden = false;
  document.querySelector("#connected-user").textContent = `Conectado como ${session.username}`;
  await inspectCurrentPage();
  if (activeTabId != null) {
    const retried = await chrome.runtime.sendMessage({ type: "retry-pending-login", tabId: activeTabId }).catch(() => null);
    if (retried?.saved) dismissPendingPrompt();
    const key = `lastSavedLogin:${activeTabId}`;
    const notice = (await chrome.storage.session.get(key))[key];
    if (notice) {
      await chrome.storage.session.remove(key);
      showStatus(`Credencial salva no InfoStorage: ${notice.title}${notice.username ? ` (${notice.username})` : ""}.`);
    }
  }
}

document.querySelector("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showStatus("Conectando…");
  const loginForm = event.currentTarget;
  const form = new FormData(loginForm);
  try {
    const apiUrl = normalizeApiUrl(form.get("api-url"));
    await allowApiHost(apiUrl);
    await chrome.storage.local.set({ apiUrl });
    const response = await apiRequest("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: form.get("username"), password: form.get("password") }),
    });
    await chrome.storage.session.set({ accessToken: response.access_token, username: response.username });
    loginForm.reset();
    await showGenerator();
    showStatus("");
  } catch (error) {
    showStatus(error.message);
  }
});

document.querySelector("#enable-site-watch").addEventListener("click", async () => {
  try {
    if (!pageInfo?.origin || activeTabId == null) throw new Error("Abra um site HTTP ou HTTPS para ativar a detecção.");
    const url = new URL(pageInfo.origin);
    if (!["http:", "https:"].includes(url.protocol)) throw new Error("A detecção só funciona em sites HTTP ou HTTPS.");
    const origins = [`${url.origin}/*`];
    const granted = await chrome.permissions.request({ origins });
    if (!granted) throw new Error("Permita o acesso a este site para ativar a detecção.");
    const registration = await chrome.runtime.sendMessage({ type: "set-site-detection", origin: url.origin, enabled: true });
    if (registration?.error) throw new Error(registration.error);
    await chrome.scripting.executeScript({ target: { tabId: activeTabId }, files: ["content.js"] });
    await updateSiteDetectionStatus();
    showStatus("Detecção ativada. Formulários enviados neste site serão salvos como credenciais.");
  } catch (error) {
    showStatus(error.message || "Não foi possível ativar a detecção neste site.");
  }
});

document.querySelector("#disable-site-watch").addEventListener("click", async () => {
  try {
    const url = new URL(pageInfo.origin);
    const registration = await chrome.runtime.sendMessage({ type: "set-site-detection", origin: url.origin, enabled: false });
    if (registration?.error) throw new Error(registration.error);
    if (activeTabId != null) {
      try { await chrome.tabs.sendMessage(activeTabId, { type: "stop-site-detection" }); } catch { /* A aba pode não ter o script carregado. */ }
    }
    const { apiUrl } = await chrome.storage.local.get("apiUrl");
    if (apiUrl && new URL(apiUrl).origin !== url.origin) {
      await chrome.permissions.remove({ origins: [`${url.origin}/*`] });
    }
    await updateSiteDetectionStatus();
    showStatus("Detecção desativada neste site.");
  } catch (error) {
    showStatus(error.message || "Não foi possível desativar a detecção.");
  }
});

document.querySelector("#length").addEventListener("input", (event) => {
  document.querySelector("#length-value").value = event.target.value;
});

document.querySelector("#generator-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showStatus("Gerando…");
  resultBox.hidden = true;
  try {
    const token = await requireToken();
    const response = await apiRequest("/api/v1/passwords/generate", {
      method: "POST",
      token,
      body: JSON.stringify({
        length: Number(document.querySelector("#length").value),
        lowercase: document.querySelector("#lowercase").checked,
        uppercase: document.querySelector("#uppercase").checked,
        digits: document.querySelector("#digits").checked,
        symbols: document.querySelector("#symbols").checked,
      }),
    });
    document.querySelector("#password-result").textContent = response.password;
    resultBox.hidden = false;
    showStatus("");
  } catch (error) {
    await showActionError(error);
  }
});

document.querySelector("#copy-password").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(document.querySelector("#password-result").textContent);
    showStatus("Senha copiada.");
  } catch {
    showStatus("Não foi possível copiar a senha.");
  }
});

document.querySelector("#fill-login").addEventListener("click", async () => {
  const index = Number(document.querySelector("#saved-credential").value);
  const item = credentials[index];
  if (!item) return showStatus("Escolha uma credencial salva.");
  try {
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: activeTabId }, func: fillAndSubmitLogin, args: [item.username, item.password],
    });
    if (!result?.result) throw new Error("Não encontrei um formulário compatível nesta página.");
    showStatus("Credencial preenchida; formulário enviado.");
  } catch (error) {
    await showActionError(error);
  }
});

document.querySelector("#save-current").addEventListener("click", async () => {
  try {
    const [result] = await chrome.scripting.executeScript({ target: { tabId: activeTabId }, func: captureCurrentLogin });
    await saveCredential(result?.result);
  } catch (error) {
    await showActionError(error);
  }
});

document.querySelector("#save-pending").addEventListener("click", async () => {
  try {
    const result = await chrome.runtime.sendMessage({ type: "retry-pending-login", tabId: activeTabId });
    if (!result?.saved) {
      const error = new Error(result?.detail || "Não foi possível salvar a credencial.");
      error.status = result?.status;
      throw error;
    }
    dismissPendingPrompt();
    showStatus(`Credencial salva no InfoStorage: ${result.title}${result.username ? ` (${result.username})` : ""}.`);
  } catch (error) {
    await showActionError(error);
  }
});

document.querySelector("#discard-pending").addEventListener("click", async () => {
  await chrome.storage.session.remove(`pendingLogin:${activeTabId}`);
  dismissPendingPrompt();
});

function dismissPendingPrompt() {
  document.querySelector("#pending-save").hidden = true;
  document.querySelector("#page-title").textContent = pageInfo?.title || pageInfo?.hostname || "Página atual";
  document.querySelector("#page-origin").textContent = pageInfo?.origin || "";
  document.querySelector("#page-badge").textContent = pageInfo?.found
    ? (pageInfo.signup ? "Cadastro" : "Login")
    : "Página atual";
}

document.querySelector("#logout").addEventListener("click", async () => {
  const { accessToken } = await chrome.storage.session.get("accessToken");
  try { await apiRequest("/api/v1/auth/logout", { method: "POST", token: accessToken }); } catch { /* A sessão pode já ter expirado. */ }
  await chrome.storage.session.remove(["accessToken", "username"]);
  resultBox.hidden = true;
  pageTools.hidden = true;
  generatorPanel.hidden = true;
  loginPanel.hidden = false;
  showStatus("Sessão encerrada.");
});

chrome.storage.local.get("apiUrl").then(({ apiUrl }) => {
  if (apiUrl) document.querySelector("#api-url").value = apiUrl;
});
showGenerator();
