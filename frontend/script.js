const chatContainer = document.getElementById('chat-container');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const fileUpload = document.getElementById('file-upload');
const historyList = document.getElementById('history-list');

// State
let history = []; // Chat history for context

// Initialize
messageInput.focus();

// Auto-resize textarea
messageInput.addEventListener('input', function () {
    this.style.height = 'auto'; // Reset
    this.style.height = (this.scrollHeight) + 'px';
    if (this.value.trim().length > 0) {
        sendBtn.classList.add('active');
    } else {
        sendBtn.classList.remove('active');
    }
});

// Send Message
async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    // Clear and reset input
    messageInput.value = '';
    messageInput.style.height = '56px';
    sendBtn.classList.remove('active');

    // Add User Message
    addMessage(text, 'user');

    // Show loading
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch('http://localhost:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: text,
                history: history
            })
        });

        const data = await response.json();

        // Remove loading
        removeMessage(loadingId);

        // Add Bot Message
        addMessage(data.response, 'bot', data.sources);

        // Update History
        history.push({ role: "user", parts: [text] });
        history.push({ role: "model", parts: [data.response] });

    } catch (error) {
        removeMessage(loadingId);
        addMessage("Sorry, something went wrong. Is the backend running?", 'bot');
        console.error(error);
    }
}

// UI Helpers
function addMessage(text, type, sources = []) {
    const div = document.createElement('div');
    div.className = `message ${type}`;

    // Markdown parsing using marked.js
    const formattedText = marked.parse(text);

    let sourceHtml = '';
    if (sources && sources.length > 0) {
        sourceHtml = `
        <details class="sources-dropdown">
            <summary>View ${sources.length} Sources</summary>
            <div class="sources-list">
                ${sources.join('<br>')}
            </div>
        </details>`;
    }

    const avatarIcon = type === 'user' ? 'user' : 'bot';

    div.innerHTML = `
        <div class="avatar"><i data-lucide="${avatarIcon}" size="20"></i></div>
        <div class="message-content">
            ${formattedText}
            ${sourceHtml}
        </div>
    `;

    chatContainer.appendChild(div);
    lucide.createIcons({
        root: div
    });

    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return div;
}

function addLoadingMessage() {
    const id = 'loading-' + Date.now();
    const div = document.createElement('div');
    div.className = `message bot`;
    div.id = id;
    div.innerHTML = `
         <div class="avatar"><i data-lucide="bot" size="20"></i></div>
        <div class="message-content">
            Thinking...
        </div>
    `;
    chatContainer.appendChild(div);
    lucide.createIcons({ root: div });
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Event Listeners
sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// File Upload
fileUpload.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    addMessage(`Uploading ${file.name}...`, 'user');
    const loadingId = addLoadingMessage();

    try {
        const response = await fetch('http://localhost:8000/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        removeMessage(loadingId);
        addMessage(data.status, 'bot');
    } catch (error) {
        removeMessage(loadingId);
        addMessage("Upload failed.", 'bot');
    }
});
