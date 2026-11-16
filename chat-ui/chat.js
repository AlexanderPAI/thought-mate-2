const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const send = document.querySelector("#send");
const newChat = document.querySelector("#new-chat");
const conversation = document.querySelector("#conversation");
const messages = document.querySelector("#messages");
const welcome = document.querySelector("#welcome");
const statusMessage = document.querySelector("#status");

let sessionId = null;
let pending = false;

function addMessage(kind, author, text) {
    const message = document.createElement("article");
    message.className = `message ${kind}`;

    const heading = document.createElement("h2");
    heading.textContent = author;

    const body = document.createElement("p");
    body.textContent = text;
    message.append(heading, body);
    welcome.hidden = true;
    messages.append(message);
    conversation.scrollTop = conversation.scrollHeight;
}

function setPending(value) {
    pending = value;
    send.disabled = value;
    newChat.disabled = value;
    statusMessage.textContent = value ? "Агент обрабатывает запрос…" : "";
}

newChat.addEventListener("click", () => {
    sessionId = null;
    messages.replaceChildren();
    welcome.hidden = false;
    input.value = "";
    input.focus();
});

input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        if (!pending) form.requestSubmit();
    }
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (pending || !message) return;

    addMessage("user", "Ты", message);
    input.value = "";
    setPending(true);

    const query = new URLSearchParams({ message });
    if (sessionId) query.set("session_id", sessionId);

    try {
        const response = await fetch(`/api/v1/invoke?${query}`, { method: "POST" });

        if (!response.ok) {
            if (response.status === 404 && sessionId) {
                throw new Error("Сессия не найдена. Нажми «Новый чат», чтобы продолжить.");
            }
            if (response.status === 409) {
                throw new Error("Агент уже выполняет запрос в этом чате. Попробуй позже.");
            }
            throw new Error(`Ошибка запроса (HTTP ${response.status}).`);
        }

        const result = await response.json();
        if (result.status === "error") throw new Error(result.message);
        sessionId = result.session_id;

        if (result.status === "completed") {
            addMessage("assistant", "ThoughtMate", result.history.at(-1));
        } else if (result.status === "step_limit") {
            addMessage("error", "ThoughtMate", "Агент достиг лимита шагов и не успел дать финальный ответ.");
        } else {
            addMessage("error", "ThoughtMate", "Агент не вернул текст ответа.");
        }
    } catch (error) {
        const description = error instanceof TypeError
            ? "Не удалось связаться с сервисом чата."
            : error.message;
        addMessage("error", "Ошибка", description);
        if (!input.value) input.value = message;
    } finally {
        setPending(false);
    }
});
