function originFrom(value) {
  const url = new URL(value);
  if (!(["http:", "https:"].includes(url.protocol))) throw new Error("Origem inválida.");
  return url.origin;
}

function scriptIdFor(origin) {
  return `infostorage_${origin.replace(/[^a-zA-Z0-9_-]/g, "_")}`;
}

async function setSiteDetection(origin, enabled) {
  const normalizedOrigin = originFrom(origin);
  const id = scriptIdFor(normalizedOrigin);
  if (enabled) {
    const allowed = await chrome.permissions.contains({ origins: [`${normalizedOrigin}/*`] });
    if (!allowed) throw new Error("Permissão do site não concedida.");
    const existing = await chrome.scripting.getRegisteredContentScripts({ ids: [id] });
    const script = {
      id,
      matches: [`${normalizedOrigin}/*`],
      js: ["content.js"],
      runAt: "document_idle",
      persistAcrossSessions: true,
    };
    if (existing.length) await chrome.scripting.updateContentScripts([script]);
    else await chrome.scripting.registerContentScripts([script]);
  } else {
    const existing = await chrome.scripting.getRegisteredContentScripts({ ids: [id] });
    if (existing.length) await chrome.scripting.unregisterContentScripts({ ids: [id] });
  }
  return { enabled, origin: normalizedOrigin };
}

async function siteDetectionStatus(origin) {
  const normalizedOrigin = originFrom(origin);
  const scripts = await chrome.scripting.getRegisteredContentScripts({ ids: [scriptIdFor(normalizedOrigin)] });
  return { enabled: scripts.length > 0, origin: normalizedOrigin };
}

async function apiRequest(path, token, options = {}) {
  const { apiUrl } = await chrome.storage.local.get("apiUrl");
  if (!apiUrl || !token) throw new Error("Entre na API pelo popup para salvar credenciais.");
  const response = await fetch(`${apiUrl}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      Authorization: `Bearer ${token}`,
    },
    cache: "no-store",
  });
  const payload = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(payload?.detail || "Não foi possível salvar a credencial.");
    error.status = response.status;
    throw error;
  }
  return payload;
}

async function saveSubmittedCredential(credentials, tabId) {
  const origin = originFrom(credentials.origin);
  const allowed = await chrome.permissions.contains({ origins: [`${origin}/*`] });
  if (!allowed) throw new Error("A permissão para este site foi removida.");
  const { accessToken } = await chrome.storage.session.get("accessToken");
  if (!accessToken) throw new Error("Entre na API pelo popup para salvar credenciais.");

  const hostname = new URL(origin).hostname.slice(0, 200);
  const username = (credentials.username || "").slice(0, 254);
  const password = (credentials.password || "").slice(0, 4096);
  if (!password) throw new Error("O formulário não continha uma senha.");

  const savedItems = await apiRequest("/api/v1/credentials", accessToken);
  const existing = savedItems.find((item) =>
    item.username === username && (item.title.toLowerCase() === hostname.toLowerCase() || (typeof item.notes === "string" && item.notes.includes(origin)))
  );
  const values = existing
    ? { title: existing.title, username, password, notes: existing.notes || `Salvo pela extensão para ${origin}` }
    : { title: hostname, username, password, notes: `Salvo pela extensão para ${origin}` };

  const result = existing
    ? await apiRequest(`/api/v1/credentials/${encodeURIComponent(existing.id)}`, accessToken, {
        method: "PUT",
        body: JSON.stringify(values),
      })
    : await apiRequest("/api/v1/credentials", accessToken, {
        method: "POST",
        body: JSON.stringify(values),
      });

  await chrome.storage.session.remove(`pendingLogin:${tabId}`);
  await chrome.storage.session.set({
    [`lastSavedLogin:${tabId}`]: { title: result.title, username: result.username, savedAt: Date.now() },
  });
  return result;
}

async function handleMessage(message, sender) {
  if (message?.type === "set-site-detection") {
    return setSiteDetection(message.origin, Boolean(message.enabled));
  }
  if (message?.type === "get-site-detection") {
    return siteDetectionStatus(message.origin);
  }
  if (message?.type === "login-page-detected") {
    if (sender.tab?.id != null) {
      await chrome.storage.session.set({ [`detectedLogin:${sender.tab.id}`]: message.page });
    }
    return { received: true };
  }
  if (message?.type === "submitted-login" && sender.tab?.id != null) {
    const tabId = sender.tab.id;
    const values = message.credentials;
    await chrome.storage.session.set({ [`pendingLogin:${tabId}`]: values });
    try {
      const result = await saveSubmittedCredential(values, tabId);
      return { saved: true, title: result.title };
    } catch (error) {
      return { saved: false, detail: error.message, status: error.status || null };
    }
  }
  if (message?.type === "retry-pending-login" && Number.isInteger(message.tabId)) {
    const tabId = message.tabId;
    const key = `pendingLogin:${tabId}`;
    const pending = (await chrome.storage.session.get(key))[key];
    if (!pending) return { saved: false, detail: "Não há credencial pendente." };
    try {
      const result = await saveSubmittedCredential(pending, tabId);
      return { saved: true, title: result.title, username: result.username };
    } catch (error) {
      return { saved: false, detail: error.message, status: error.status || null };
    }
  }
  return { received: false };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  handleMessage(message, sender)
    .then(sendResponse)
    .catch((error) => sendResponse({ error: error.message }));
  return true;
});

chrome.tabs.onRemoved.addListener((tabId) => {
  chrome.storage.session.remove([
    `pendingLogin:${tabId}`,
    `detectedLogin:${tabId}`,
    `lastSavedLogin:${tabId}`,
  ]);
});
