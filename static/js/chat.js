/**
 * chat.js - Government Job Guide AI Chat Controller
 * Handles conversation state, markdown rendering, error recovery, and message saving.
 */

class ChatController {
  constructor() {
    this.history = []; // [{role: 'user', text: '...'}, {role: 'model', text: '...'}]
    this.isRequestActive = false;
    this.lastFailedMessage = null;
    this.requestTimeoutMs = 35000; // 35 seconds

    this.messagesContainer = document.getElementById('chatMessages');
    this.chatInput = document.getElementById('chatInput');
    this.sendBtn = document.getElementById('sendBtn');
    this.micBtn = document.getElementById('micBtn');
    this.clearChatBtn = document.getElementById('clearChatBtn');

    this.init();
  }

  init() {
    // Configure Marked.js options
    if (typeof marked !== 'undefined') {
      marked.setOptions({
        breaks: true,
        gfm: true
      });
    }

    // Bind event listeners
    if (this.sendBtn) {
      this.sendBtn.addEventListener('click', () => this.handleSend());
    }

    if (this.chatInput) {
      this.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSend();
        }
      });

      // Auto-resize textarea
      this.chatInput.addEventListener('input', () => {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
      });
    }

    if (this.micBtn) {
      this.micBtn.addEventListener('click', () => {
        if (typeof voiceAssistant !== 'undefined') {
          voiceAssistant.toggleListening();
        }
      });
    }

    // Suggested prompt chips
    document.querySelectorAll('.prompt-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        const promptText = e.currentTarget.getAttribute('data-prompt') || e.currentTarget.textContent.trim();
        this.sendPrompt(promptText);
      });
    });

    // Clear chat button
    if (this.clearChatBtn) {
      this.clearChatBtn.addEventListener('click', () => this.confirmClearChat());
    }
  }

  confirmClearChat() {
    const modalEl = document.getElementById('clearConfirmModal');
    if (modalEl && typeof bootstrap !== 'undefined') {
      const modal = new bootstrap.Modal(modalEl);
      modal.show();

      const confirmBtn = document.getElementById('btnConfirmClear');
      if (confirmBtn) {
        confirmBtn.onclick = () => {
          this.clearChat();
          modal.hide();
        };
      }
    } else {
      if (confirm("Are you sure you want to clear the conversation history?")) {
        this.clearChat();
      }
    }
  }

  clearChat() {
    this.history = [];
    if (this.messagesContainer) {
      this.messagesContainer.innerHTML = '';
      this.renderWelcomeMessage();
    }
    showToast('Conversation cleared.', 'info');
  }

  renderWelcomeMessage() {
    const welcomeHTML = `
      <div class="message-row ai">
        <div class="avatar-bubble ai"><i class="bi bi-robot"></i></div>
        <div class="bubble-content">
          <h4 class="mb-2">Namaste! I am Government Job Guide.</h4>
          <p class="mb-2">I can help you explore verified central and state government career paths based on your qualification, age, and field of interest.</p>
          <p class="text-muted small mb-0">Select a suggested topic on the left or type your query below.</p>
        </div>
      </div>
    `;
    this.messagesContainer.insertAdjacentHTML('beforeend', welcomeHTML);
  }

  sendPrompt(text) {
    if (this.isRequestActive) return;
    if (this.chatInput) {
      this.chatInput.value = text;
      this.handleSend();
    }
  }

  async handleSend() {
    if (this.isRequestActive) return;

    const message = this.chatInput.value.trim();
    if (!message) return;

    // Reset textarea
    this.chatInput.value = '';
    this.chatInput.style.height = 'auto';

    // Render User Message
    this.appendUserMessage(message);

    // Render Thinking Indicator
    const thinkingId = this.appendThinkingIndicator();

    // Disable inputs
    this.setRequestState(true);
    this.lastFailedMessage = null;

    // Prepare AbortController for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.requestTimeoutMs);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: message,
          history: this.history
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      this.removeThinkingIndicator(thinkingId);

      const data = await response.json().catch(() => null);

      if (response.ok && data && data.reply) {
        // Successful response
        this.appendAIMessage(data.reply);
        // Track history
        this.history.push({ role: 'user', text: message });
        this.history.push({ role: 'model', text: data.reply });
      } else {
        // Server returned an error
        const errorMsg = (data && data.error) ? data.error : `Server responded with status ${response.status}`;
        this.lastFailedMessage = message;
        this.appendErrorMessage(errorMsg, true);
      }

    } catch (err) {
      clearTimeout(timeoutId);
      this.removeThinkingIndicator(thinkingId);

      let errorMsg = 'Failed to connect to the AI assistant. Please check your network connection.';
      if (err.name === 'AbortError') {
        errorMsg = 'Request timed out after 35 seconds. The server may be busy or rate-limited. Please retry.';
      }
      this.lastFailedMessage = message;
      this.appendErrorMessage(errorMsg, true);
    } finally {
      // ALWAYS re-enable UI state
      this.setRequestState(false);
      this.scrollToBottom();
    }
  }

  appendUserMessage(text) {
    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `
      <div class="avatar-bubble user"><i class="bi bi-person-fill"></i></div>
      <div class="bubble-content">
        <p class="mb-0">${escapeHTML(text).replace(/\n/g, '<br>')}</p>
      </div>
    `;
    this.messagesContainer.appendChild(row);
    this.scrollToBottom();
  }

  appendThinkingIndicator() {
    const id = 'thinking-' + Date.now();
    const row = document.createElement('div');
    row.id = id;
    row.className = 'message-row ai';
    row.innerHTML = `
      <div class="avatar-bubble ai"><i class="bi bi-robot"></i></div>
      <div class="bubble-content">
        <div class="thinking-indicator">
          <span>Thinking</span>
          <span class="dot-pulse"></span>
          <span class="dot-pulse"></span>
          <span class="dot-pulse"></span>
        </div>
      </div>
    `;
    this.messagesContainer.appendChild(row);
    this.scrollToBottom();
    return id;
  }

  removeThinkingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  appendAIMessage(rawMarkdown) {
    let sanitizedHtml = '';
    if (typeof marked !== 'undefined' && typeof DOMPurify !== 'undefined') {
      const parsed = marked.parse(rawMarkdown);
      sanitizedHtml = DOMPurify.sanitize(parsed);
    } else {
      sanitizedHtml = escapeHTML(rawMarkdown).replace(/\n/g, '<br>');
    }

    const row = document.createElement('div');
    row.className = 'message-row ai';

    const messageId = 'ai-msg-' + Date.now();
    row.innerHTML = `
      <div class="avatar-bubble ai"><i class="bi bi-robot"></i></div>
      <div class="bubble-content" id="${messageId}">
        <div class="markdown-body">${sanitizedHtml}</div>
        <div class="bubble-actions">
          <button type="button" class="btn-action-sm btn-copy" title="Copy response to clipboard">
            <i class="bi bi-clipboard"></i> Copy
          </button>
          <button type="button" class="btn-action-sm btn-speak" title="Listen to response">
            <i class="bi bi-volume-up"></i> Listen
          </button>
          <button type="button" class="btn-action-sm btn-save" title="Save this guidance to your profile">
            <i class="bi bi-bookmark"></i> Save
          </button>
        </div>
      </div>
    `;

    this.messagesContainer.appendChild(row);

    // Attach actions
    const copyBtn = row.querySelector('.btn-copy');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => copyToClipboard(rawMarkdown, copyBtn));
    }

    const speakBtn = row.querySelector('.btn-speak');
    if (speakBtn) {
      speakBtn.addEventListener('click', () => {
        if (typeof voiceAssistant !== 'undefined') {
          voiceAssistant.speak(rawMarkdown, speakBtn);
        }
      });
    }

    const saveBtn = row.querySelector('.btn-save');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        // Derive title from first line or default
        const firstLine = rawMarkdown.split('\n').find(l => l.trim().length > 0) || 'Career Guidance';
        const title = firstLine.replace(/^[#\*\s\-]+/, '').substring(0, 60);
        saveGuidanceItem(title, 'AI Chat', rawMarkdown, saveBtn);
      });
    }

    this.scrollToBottom();
  }

  appendErrorMessage(errorMsg, canRetry = false) {
    const row = document.createElement('div');
    row.className = 'message-row ai';
    row.innerHTML = `
      <div class="avatar-bubble ai" style="background: #ef4444;"><i class="bi bi-exclamation-triangle-fill"></i></div>
      <div class="bubble-content" style="border-left: 4px solid #ef4444; background: #fff5f5;">
        <p class="text-danger fw-semibold mb-2"><i class="bi bi-x-circle me-1"></i> ${escapeHTML(errorMsg)}</p>
        ${canRetry && this.lastFailedMessage ? `
          <button type="button" class="btn btn-sm btn-outline-danger mt-1 btn-retry">
            <i class="bi bi-arrow-clockwise me-1"></i> Retry Message
          </button>
        ` : ''}
      </div>
    `;

    this.messagesContainer.appendChild(row);

    if (canRetry && this.lastFailedMessage) {
      const retryBtn = row.querySelector('.btn-retry');
      if (retryBtn) {
        retryBtn.addEventListener('click', () => {
          row.remove();
          this.chatInput.value = this.lastFailedMessage;
          this.handleSend();
        });
      }
    }

    this.scrollToBottom();
  }

  setRequestState(active) {
    this.isRequestActive = active;
    if (this.sendBtn) this.sendBtn.disabled = active;
    if (this.chatInput) this.chatInput.disabled = active;
    if (this.micBtn) this.micBtn.disabled = active;
  }

  scrollToBottom() {
    if (this.messagesContainer) {
      this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
  }
}

// Instantiate on chat page
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('chatMessages')) {
    window.chatController = new ChatController();
  }
});
