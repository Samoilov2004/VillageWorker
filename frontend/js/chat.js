const API_BASE_URL = "http://127.0.0.1:8000";
const WS_BASE_URL = "ws://127.0.0.1:8000";

const params = new URLSearchParams(window.location.search);

let currentUserId = Number(params.get("user_id") || localStorage.getItem("vw_chat_user_id") || 1);
let currentDialogId = null;
let currentDialog = null;
let socket = null;

const users = {
  1: {
    id: 1,
    name: "Иван Петров",
    role: "Соискатель",
  },
  2: {
    id: 2,
    name: "ООО АгроПлюс",
    role: "Работодатель",
  },
};

const dialogsList = document.getElementById("dialogsList");
const messagesList = document.getElementById("messagesList");
const chatHeader = document.getElementById("chatHeader");
const connectionStatus = document.getElementById("connectionStatus");
const messageForm = document.getElementById("messageForm");
const messageInput = document.getElementById("messageInput");
const sendMessageBtn = document.getElementById("sendMessageBtn");
const currentUserLabel = document.getElementById("currentUserLabel");
const applicantRoleBtn = document.getElementById("applicantRoleBtn");
const employerRoleBtn = document.getElementById("employerRoleBtn");
const createDemoDialogBtn = document.getElementById("createDemoDialogBtn");

document.addEventListener("DOMContentLoaded", async () => {
  setCurrentUser(currentUserId, false);
  bindEvents();

  await ensureDemoDialog();
  await loadDialogs();
});

function bindEvents() {
  applicantRoleBtn.addEventListener("click", () => setCurrentUser(1));
  employerRoleBtn.addEventListener("click", () => setCurrentUser(2));

  createDemoDialogBtn.addEventListener("click", async () => {
    await ensureDemoDialog();
    await loadDialogs();
  });

  messageForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await sendMessage();
  });

  messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = `${messageInput.scrollHeight}px`;
  });

  messageInput.addEventListener("keydown", async (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await sendMessage();
    }
  });
}

function setCurrentUser(userId, reload = true) {
  currentUserId = userId;
  localStorage.setItem("vw_chat_user_id", String(userId));

  const url = new URL(window.location.href);
  url.searchParams.set("user_id", String(userId));
  window.history.replaceState({}, "", url.toString());

  applicantRoleBtn.classList.toggle("active", userId === 1);
  employerRoleBtn.classList.toggle("active", userId === 2);

  currentUserLabel.textContent = `${users[userId].role}: ${users[userId].name}`;

  if (reload) {
    closeSocket();
    currentDialogId = null;
    currentDialog = null;
    loadDialogs();
    renderEmptyChat();
  }
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

async function loadDialogs() {
  dialogsList.innerHTML = `<div class="empty-state">Загрузка диалогов...</div>`;

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/dialogs?user_id=${currentUserId}`);
    const data = await response.json();

    const dialogs = data.items || [];

    if (!dialogs.length) {
      dialogsList.innerHTML = `<div class="empty-state">Диалогов пока нет</div>`;
      return;
    }

    renderDialogs(dialogs);

    if (!currentDialogId) {
      await selectDialog(dialogs[0].id, dialogs[0]);
    }
  } catch (error) {
    dialogsList.innerHTML = `
      <div class="empty-state">
        Не удалось загрузить диалоги. Проверьте, запущен ли backend.
      </div>
    `;

    console.error(error);
  }
}

function renderDialogs(dialogs) {
  dialogsList.innerHTML = "";

  dialogs.forEach((dialog) => {
    const button = document.createElement("button");
    button.className = "dialog-item";
    button.type = "button";
    button.dataset.dialogId = dialog.id;

    if (dialog.id === currentDialogId) {
      button.classList.add("active");
    }

    button.innerHTML = `
      <div class="dialog-top">
        <div class="dialog-name">${escapeHtml(dialog.companion_name)}</div>
        <div class="dialog-date">${formatShortDate(dialog.last_message_at || dialog.created_at)}</div>
      </div>

      <div class="dialog-job">${escapeHtml(dialog.job_title)}</div>

      <div class="dialog-last">
        ${escapeHtml(dialog.last_message || "Диалог создан. Можно начать переписку.")}
      </div>
    `;

    button.addEventListener("click", () => selectDialog(dialog.id, dialog));

    dialogsList.appendChild(button);
  });
}

async function selectDialog(dialogId, dialogData = null) {
  currentDialogId = dialogId;
  currentDialog = dialogData;

  document.querySelectorAll(".dialog-item").forEach((item) => {
    item.classList.toggle("active", Number(item.dataset.dialogId) === dialogId);
  });

  renderChatHeader(dialogData);
  await loadMessages(dialogId);
  connectSocket(dialogId);

  messageInput.disabled = false;
  sendMessageBtn.disabled = false;
  messageInput.focus();
}

function renderChatHeader(dialog) {
  const companionName = dialog?.companion_name || "Собеседник";
  const jobTitle = dialog?.job_title || "Вакансия";

  chatHeader.innerHTML = `
    <div>
      <h2>${escapeHtml(companionName)}</h2>
      <p>Переписка по вакансии: ${escapeHtml(jobTitle)}</p>
    </div>

    <span class="connection-status offline" id="connectionStatus">
      Подключение...
    </span>
  `;

  window.connectionStatus = document.getElementById("connectionStatus");
}

async function loadMessages(dialogId) {
  messagesList.innerHTML = `<div class="empty-state">Загрузка сообщений...</div>`;

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/dialogs/${dialogId}/messages?user_id=${currentUserId}`);

    if (!response.ok) {
      throw new Error("Нет доступа к диалогу");
    }

    const data = await response.json();
    const messages = data.items || [];

    renderMessages(messages);
  } catch (error) {
    messagesList.innerHTML = `
      <div class="empty-state">
        Не удалось загрузить сообщения.
      </div>
    `;

    console.error(error);
  }
}

function renderMessages(messages) {
  messagesList.innerHTML = "";

  if (!messages.length) {
    messagesList.innerHTML = `
      <div class="welcome-card">
        <div class="welcome-icon">💬</div>
        <h3>Диалог создан</h3>
        <p>Напишите первое сообщение, чтобы начать общение.</p>
      </div>
    `;

    return;
  }

  messages.forEach((message) => renderMessage(message));

  scrollToBottom();
}

function renderMessage(message) {
  const isMine = Number(message.sender_id) === currentUserId;

  const row = document.createElement("div");
  row.className = `message-row ${isMine ? "mine" : ""}`;

  const author = isMine
    ? "Вы"
    : getCompanionName();

  row.innerHTML = `
    <div class="message-bubble">
      <div class="message-author">${escapeHtml(author)}</div>
      <div class="message-text">${escapeHtml(message.text)}</div>
      <div class="message-time">${formatFullDate(message.created_at)}</div>
    </div>
  `;

  messagesList.appendChild(row);
}

function connectSocket(dialogId) {
  closeSocket();
  setConnectionStatus("Подключение...", false);

  socket = new WebSocket(`${WS_BASE_URL}/api/chat/ws/${dialogId}?user_id=${currentUserId}`);

  socket.onopen = () => {
    setConnectionStatus("Онлайн", true);
  };

  socket.onmessage = (event) => {
    const payload = JSON.parse(event.data);

    if (payload.type === "message") {
      renderMessage(payload.message);
      scrollToBottom();
      loadDialogs();
    }

    if (payload.type === "error") {
      alert(payload.message || "Ошибка отправки сообщения");
    }
  };

  socket.onclose = () => {
    setConnectionStatus("Отключено", false);
  };

  socket.onerror = () => {
    setConnectionStatus("Ошибка соединения", false);
  };
}

function closeSocket() {
  if (socket) {
    socket.close();
    socket = null;
  }
}

async function sendMessage() {
  const text = messageInput.value.trim();

  if (!text || !currentDialogId) {
    return;
  }

  messageInput.value = "";
  messageInput.style.height = "auto";

  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ text }));
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/dialogs/${currentDialogId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sender_id: currentUserId,
        text,
      }),
    });

    const message = await response.json();

    renderMessage(message);
    scrollToBottom();
    await loadDialogs();
  } catch (error) {
    alert("Не удалось отправить сообщение");
    console.error(error);
  }
}

function renderEmptyChat() {
  chatHeader.innerHTML = `
    <div>
      <h2>Выберите диалог</h2>
      <p>История переписки появится здесь</p>
    </div>

    <span class="connection-status" id="connectionStatus">
      Не подключено
    </span>
  `;

  messagesList.innerHTML = `
    <div class="welcome-card">
      <div class="welcome-icon">💬</div>
      <h3>Коммуникационный модуль</h3>
      <p>
        Здесь соискатель и работодатель могут обмениваться сообщениями,
        уточнять условия вакансии и сохранять историю переписки.
      </p>
    </div>
  `;

  messageInput.disabled = true;
  sendMessageBtn.disabled = true;
}

function setConnectionStatus(text, online) {
  const status = document.getElementById("connectionStatus");

  if (!status) {
    return;
  }

  status.textContent = text;
  status.classList.toggle("online", online);
  status.classList.toggle("offline", !online);
}

function getCompanionName() {
  if (!currentDialog) {
    return "Собеседник";
  }

  return currentDialog.companion_name || "Собеседник";
}

function formatShortDate(value) {
  if (!value) {
    return "";
  }

  const date = parseDate(value);

  return date.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
  });
}

function formatFullDate(value) {
  if (!value) {
    return "";
  }

  const date = parseDate(value);

  return date.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function parseDate(value) {
  return new Date(String(value).replace(" ", "T"));
}

function scrollToBottom() {
  messagesList.scrollTop = messagesList.scrollHeight;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}