(function () {
  "use strict";

  const script = document.currentScript;
  const apiBase = (script && script.getAttribute("data-api")) || "http://localhost:8000";
  const clientId = (script && script.getAttribute("data-client-id")) || "default";

  const STORAGE_KEY = "pa_chat_conversation_id";

  function loadConversationId() {
    return localStorage.getItem(STORAGE_KEY);
  }

  function saveConversationId(id) {
    if (id) localStorage.setItem(STORAGE_KEY, id);
  }

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function injectStyles() {
    if (document.getElementById("pa-chat-styles")) return;
    const link = document.createElement("link");
    link.id = "pa-chat-styles";
    link.rel = "stylesheet";
    const base = apiBase.replace(/\/$/, "");
    link.href = base + "/widget/widget.css";
    document.head.appendChild(link);
  }

  function buildWidget() {
    const root = el("div");
    root.id = "pa-chat-root";

    const btn = el("button", null, "💬");
    btn.id = "pa-chat-button";
    btn.setAttribute("aria-label", "Open chat");

    const panel = el("div");
    panel.id = "pa-chat-panel";
    panel.innerHTML =
      '<div id="pa-chat-header">Chat Assistant</div>' +
      '<div id="pa-chat-messages"></div>' +
      '<div id="pa-chat-input-row">' +
      '<textarea id="pa-chat-input" rows="2" placeholder="Ihre Nachricht…"></textarea>' +
      '<button id="pa-chat-send">Senden</button>' +
      "</div>";

    root.appendChild(btn);
    root.appendChild(panel);
    document.body.appendChild(root);

    const messages = panel.querySelector("#pa-chat-messages");
    const input = panel.querySelector("#pa-chat-input");
    const send = panel.querySelector("#pa-chat-send");

    function appendMessage(role, text) {
      const m = el("div", "pa-msg " + (role === "user" ? "user" : "bot"), text);
      messages.appendChild(m);
      messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage() {
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      send.disabled = true;
      appendMessage("user", text);
      const bot = el("div", "pa-msg bot", "…");
      messages.appendChild(bot);

      try {
        const res = await fetch(apiBase.replace(/\/$/, "") + "/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: text,
            conversation_id: loadConversationId(),
            client_id: clientId,
            use_rag: true,
          }),
        });
        const data = await res.json();
        if (data.conversation_id) saveConversationId(data.conversation_id);
        bot.textContent = data.answer || "Keine Antwort.";
      } catch (err) {
        bot.textContent = "Verbindungsfehler. Ist die API erreichbar?";
      } finally {
        send.disabled = false;
        messages.scrollTop = messages.scrollHeight;
      }
    }

    btn.addEventListener("click", () => panel.classList.toggle("open"));
    send.addEventListener("click", sendMessage);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  injectStyles();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", buildWidget);
  } else {
    buildWidget();
  }
})();
