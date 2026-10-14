(() => {
  "use strict";

  const $ = id => document.getElementById(id);
  let sending = false;

  function waitUntilEnabled(button, timeout = 10000) {
    return new Promise((resolve, reject) => {
      if (!button?.disabled) return resolve();
      const observer = new MutationObserver(() => {
        if (!button.disabled) {
          observer.disconnect();
          resolve();
        }
      });
      observer.observe(button, { attributes: true, attributeFilter: ["disabled"] });
      window.setTimeout(() => {
        observer.disconnect();
        reject(new Error("Hermès n’a pas pu préparer la demande."));
      }, timeout);
    });
  }

  async function send() {
    if (sending) return;
    const question = $("v2-handoff-question")?.value?.trim() || "";
    const message = $("v2-handoff-message");
    const sendButton = $("v2-handoff-send");
    const prepareButton = $("v2-handoff-prepare");
    const submitButton = $("v2-handoff-submit");

    if (question.length < 3) {
      if (message) message.textContent = "Décrivez votre demande.";
      return;
    }

    sending = true;
    if (sendButton) sendButton.disabled = true;
    try {
      prepareButton?.click();
      await waitUntilEnabled(submitButton);
      submitButton.click();
    } catch (error) {
      if (message) message.textContent = error.message || String(error);
    } finally {
      sending = false;
      if (sendButton) sendButton.disabled = false;
    }
  }

  function install() {
    $("v2-handoff-send")?.addEventListener("click", () => void send());
    $("v2-handoff-question")?.addEventListener("keydown", event => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault();
        void send();
      }
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install, { once: true });
  else install();
})();