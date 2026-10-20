(() => {
  if (window.__infostorageWatch) return;

  const isVisible = (element) => element.getClientRects().length > 0 && !element.disabled;
  let lastDetection = "";

  function formsWithPassword() {
    return Array.from(document.querySelectorAll('input[type="password"]'))
      .filter(isVisible)
      .map((input) => input.form)
      .filter(Boolean);
  }

  function inspect() {
    const forms = [...new Set(formsWithPassword())];
    if (!forms.length) {
      lastDetection = "";
      return;
    }
    const form = forms[0];
    const signature = `${location.href}:${forms.length}`;
    if (signature === lastDetection) return;
    lastDetection = signature;
    const passwords = Array.from(form.querySelectorAll('input[type="password"]')).filter(isVisible);
    const terms = `${location.pathname} ${form.innerText || ""}`.toLowerCase();
    const signup = passwords.some((field) => field.autocomplete === "new-password")
      || passwords.length > 1
      || /sign.?up|register|create account|cadastro|criar conta/.test(terms);
    chrome.runtime.sendMessage({
      type: "login-page-detected",
      page: { origin: location.origin, title: document.title || location.hostname, signup },
    }).catch(() => {});
  }

  function onSubmit(event) {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) return;
    const inputs = Array.from(form.querySelectorAll("input")).filter(isVisible);
    const passwordInputs = inputs.filter((field) => field.type === "password");
    const password = passwordInputs.find((field) => field.autocomplete === "new-password")
      || passwordInputs.find((field) => field.autocomplete === "current-password")
      || passwordInputs[0];
    if (!password?.value) return;

    const username = inputs.find((field) => field.autocomplete.toLowerCase().includes("username"))
      || inputs.find((field) => field.type === "email")
      || inputs.find((field) => ["text", "tel"].includes(field.type) && field !== password);
    chrome.runtime.sendMessage({
      type: "submitted-login",
      credentials: {
        origin: location.origin,
        title: document.title || location.hostname,
        username: username?.value || "",
        password: password.value,
      },
    }).catch(() => {});
  }

  document.addEventListener("submit", onSubmit, true);
  const observer = new MutationObserver(inspect);
  observer.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["type", "style", "class"] });
  inspect();

  const onMessage = (message, _sender, sendResponse) => {
    if (message?.type !== "stop-site-detection") return;
    document.removeEventListener("submit", onSubmit, true);
    observer.disconnect();
    chrome.runtime.onMessage.removeListener(onMessage);
    delete window.__infostorageWatch;
    sendResponse({ stopped: true });
  };
  chrome.runtime.onMessage.addListener(onMessage);
  window.__infostorageWatch = true;
})();
