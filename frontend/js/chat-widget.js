(function () {
  const API_BASE_URL = "http://127.0.0.1:8000";
  const WS_BASE_URL = "ws://127.0.0.1:8000";

  let currentUserId = Number(localStorage.getItem("vw_chat_user_id") || 1);
  let currentDialogId = null;
  let socket = null;

  const users = {
    1: "Иван Петров",
    2: "ООО АгроПлюс",
  };

  const styles = document.createElement("style");

  styles.textContent = `
    .vw-chat-launcher {
      position: fixed;
      right: 24px;
      bottom: 24px;
      z-index: 9999;
      width: 64px;
      height: 64px;
      border: none;
      border-radius: 22px;
      background: #256d3c;
      color: #fff;
      box-shadow: 0 18px 38px rgba(31, 47, 37, 0.24);
      cursor: pointer;
      font-size: 28px;
      display: grid;
      place-items: center;
      transition: 0.2s ease;
    }

    .vw-chat-launcher:hover {
      transform: translateY(-2px);
      box-shadow: 0 22px 44px rgba(31, 47, 37, 0.28);
    }

    .vw-chat-window {
      position: fixed;
      right: 24px;
      bottom: 102px;
      z-index: 9999;
      width: 380px;
      height: 520px;
      background: #ffffff;
      border: 1px solid #dce8df;
      border-radius: 24px;
      box-shadow: 0 24px 60px rgba(31, 47, 37, 0.22);
      display: none;
      overflow: hidden;
      font-family: Arial, sans-serif;
      color: #1f2f25;
    }

    .vw-chat-window.open {
      display: flex;
      flex-direction: column;
    }

    .vw-chat-head {
      padding: 16px;
      background: #256d3c;
      color: #ffffff;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }

    .vw-chat-head h3 {
      margin: 0;
      font-size: 18px;
    }

    .vw-chat-head p {
      margin: 4px 0 0;
      font-size: 12px;
      opacity: 0.85;
    }

    .vw-chat-actions {
      display: flex;
      gap: 6px;
    }

    .vw-chat-actions button {
      border: none;
      background: rgba(255, 255, 255, 0.16);
      color: #ffffff;
      border-radius: 10px;
      cursor: pointer;
      padding: 7px 9px;
      font-size: 12px;
    }

    .vw-chat-role {
      padding: 10px 12px;
      border-bottom: 1px solid #e6eee8;
      display: flex;
      gap: 8px;
      background: #f7fbf8;
    }

    .vw-chat-role button {
      flex: 1;
      border: none;
      padding: 8px;
      border-radius: 12px;
      cursor: pointer;
      background: #edf4ef;
      color: #256d3c;
      font-weight: 700;
      font-size: 12px;
    }

    .vw-chat-role button.active {
      background: #256d3c;
      color: #ffffff;
    }

    .vw-chat-messages {
      flex: 1;
      padding: 14px;
      overflow-y: auto;
      background: #f7fbf8;
    }

    .vw-chat-empty {
      margin: 60px auto;
      max-width: 250px;
      text-align: center;
      color: #6b7f70;
      font-size: 14px;
      line-height: 1.45;
    }

    .vw-msg {
      display: flex;
      margin-bottom: 10px;
    }

    .vw-msg.mine {
      justify-content: flex-end;
    }

    .vw-msg-bubble {
      max-width: 78%;
      padding: 10px 12px;
      border-radius: 16px;
      background: #ffffff;
      border: 1px solid #e1ebe4;
      font-size: 14px;
      line-height: 1.35;
      box-shadow: 0 6px 18px rgba(31, 47, 37, 0.06);
    }

    .vw-msg.mine .vw-msg-bubble {
      background: #256d3c;
      color: #ffffff;
      border-color: #256d3c;
    }

    .vw-msg-time {
      margin-top: 5px;
      font-size: 10px;
      opacity: 0.65;
      text-align: right;
    }

    .vw-chat-form {
      padding: 10px;
      border-top: 1px solid #e6eee8;
      display: flex;
      gap: 8px;
      background: #ffffff;
    }

    .vw-chat-form input {
      flex: 1;
      border: 1px solid #d6e2da;
      border-radius: 14px;
      padding: 11px 12px;
      outline: none;
      font-size: 14px;
    }

    .vw-chat-form button {
      border: none;
      border-radius: 14px;
      padding: 0 14px;
      background: #256d3c;
      color: #ffffff;
      cursor: pointer;
      font-weight: 700;
    }

    @media (max-width: 520px) {
      .vw-chat-window {
        width: calc(100vw - 24px);
        right: 12px;
        bottom: 88px;
      }

      .vw-chat-launcher {
        right: 14px;
        bottom: 14px;
      }
    }
  `;

  document.head.appendChild(styles);

  const launcher = document.createElement("button");
  launcher.className = "vw-chat-launcher";
  launcher.type = "button";
  launcher.title = "Открыть чат";
  launcher.innerHTML = "💬";

  const widget = document.createElement("div");
  widget.className = "vw-chat-window";

  widget.innerHTML = `
    <div class="vw-chat-head">
      <div>
        <h3>Чат</h3>
        <p id="vwChatSubtitle">Связь с работодателем</p>
      </div>

      <div class="vw-chat-actions">
        <button id="vwOpenMessengerBtn" type="button">Открыть</button>
        <button id="vwCloseChatBtn" type="button">×</button>
      </div>
    </div>

    <div class="vw-chat-role">
      <button id="vwApplicantBtn" type="button">Соискатель</button>
      <button id="vwEmployerBtn" type="button">Работодатель</button>
    </div>

    <div class="vw-chat-messages" id="vwChatMessages">
      <div class="vw-chat-empty">Загрузка переписки...</div>
    </div>

    <form class="vw-chat-form" id="vwChatForm">
      <input id="vwChatInput" type="text" placeholder="Сообщение..." />
      <button type="submit">➤</button>
    </form>
  `;

  document.body.appendChild(widget);
  document.body.appendChild(launcher);

  const closeBtn = widget.querySelector("#vwCloseChatBtn");
  const openMessengerBtn = widget.querySelector("#vwOpenMessengerBtn");
  const applicantBtn = widget.querySelector("#vwApplicantBtn");
  const employerBtn = widget.querySelector("#vwEmployerBtn");
  const messagesBox = widget.querySelector("#vwChatMessages");
  const form = widget.querySelector("#vwChatForm");
  const input = widget.querySelector("#vwChatInput");
  const subtitle = widget.querySelector("#vwChatSubtitle");

  launcher.addEventListener("click", async () => {
    widget.classList.toggle("open");

    if (widget.classList.contains("open")) {
      await initWidgetChat();
    }
  });

  closeBtn.addEventListener("click", () => {
    widget.classList.remove("open");
  });

  openMessengerBtn.addEventListener("click", () => {
    const chatPath = window.location.pathname.includes("/html/")
      ? `./chat.html?user_id=${currentUserId}`
      : `./html/chat.html?user_id=${currentUserId}`;

    window.open(
      chatPath,
      "VillageWorkerChat",
      "width=1000,height=720,resizable=yes,scrollbars=yes"
    );
  });

  applicantBtn.addEventListener("click", async () => {
    setRole(1);
    await initWidgetChat();
  });

  employerBtn.addEventListener("click", async () => {
    setRole(2);
    await initWidgetChat();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const text = input.value.trim();

    if (!text || !currentDialogId) {
      return;
    }

    input.value = "";

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ text }));
    } else {
      await fetch(`${API_BASE_URL}/api/chat/dialogs/${currentDialogId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sender_id: currentUserId,
          text,
        }),
      });

      await loadMessages();
    }
  });

  setRole(currentUserId);

  async function initWidgetChat() {
    await ensureDemoDialog();

    const dialogsResponse = await fetch(`${API_BASE_URL}/api/chat/dialogs?user_id=${currentUserId}`);
    const dialogsData = await dialogsResponse.json();
    const dialogs = dialogsData.items || [];

    if (!dialogs.length) {
      messagesBox.innerHTML = `<div class="vw-chat-empty">Диалогов пока нет</div>`;
      return;
    }

    currentDialogId = dialogs[0].id;

    subtitle.textContent = `${dialogs[0].companion_name} · ${dialogs[0].job_title}`;

    await loadMessages();
    connectSocket();
  }

  async function ensureDemoDialog() {
    await fetch(`${API_BASE_URL}/api/chat/dialogs/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        job_id: 1,
        job_title: "Рабочий на ферму",
        applicant_id: 1,
        applicant_name: "Иван Петров",
        employer_id: 2,
        employer_name: "ООО АгроПлюс",
      }),
    });
  }

  async function loadMessages() {
    if (!currentDialogId) {
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/chat/dialogs/${currentDialogId}/messages?user_id=${currentUserId}`);
    const data = await response.json();

    messagesBox.innerHTML = "";

    const messages = data.items || [];

    if (!messages.length) {
      messagesBox.innerHTML = `<div class="vw-chat-empty">Напишите первое сообщение.</div>`;
      return;
    }

    messages.forEach(renderMessage);

    scrollDown();
  }

  function connectSocket() {
    if (socket) {
      socket.close();
    }

    socket = new WebSocket(`${WS_BASE_URL}/api/chat/ws/${currentDialogId}?user_id=${currentUserId}`);

    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data);

      if (payload.type === "message") {
        renderMessage(payload.message);
        scrollDown();
      }
    };
  }

  function renderMessage(message) {
    const mine = Number(message.sender_id) === currentUserId;

    const row = document.createElement("div");
    row.className = `vw-msg ${mine ? "mine" : ""}`;

    row.innerHTML = `
      <div class="vw-msg-bubble">
        <div>${escapeHtml(message.text)}</div>
        <div class="vw-msg-time">${formatTime(message.created_at)}</div>
      </div>
    `;

    messagesBox.appendChild(row);
  }

  function setRole(userId) {
    currentUserId = userId;
    localStorage.setItem("vw_chat_user_id", String(userId));

    applicantBtn.classList.toggle("active", userId === 1);
    employerBtn.classList.toggle("active", userId === 2);
  }

  function scrollDown() {
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }

  function formatTime(value) {
    if (!value) {
      return "";
    }

    const date = new Date(String(value).replace(" ", "T"));

    return date.toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }
})();