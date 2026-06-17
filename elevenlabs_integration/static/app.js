/**
 * Movistar Sales Agent Frontend
 * Text chat + Voice chat using ElevenLabs Speech Engine + ADK multi-agent
 */

// ── State ──────────────────────────────────────────────────────────

const state = {
  messages: [],        // [{id, role, content, isVoice, timestamp}]
  voiceActive: false,
  conversation: null,
  messageCount: 0,
};

// ── DOM Elements ───────────────────────────────────────────────────

const messagesContainer = document.getElementById('messagesContainer');
const messageInput      = document.getElementById('messageInput');
const sendButton        = document.getElementById('sendButton');
const voiceButton       = document.getElementById('voiceButton');
const inputWrapper      = document.getElementById('inputWrapper');
const voiceBar          = document.getElementById('voiceBar');
const voiceOrb          = document.getElementById('voiceOrb');
const voiceStatus       = document.getElementById('voiceStatus');
const voiceTranscript   = document.getElementById('voiceTranscript');
const voiceBtnLabel     = voiceButton.querySelector('.voice-btn-label');
const iconMic           = voiceButton.querySelector('.icon-mic');
const iconStop          = voiceButton.querySelector('.icon-stop');

// ── Utilities ──────────────────────────────────────────────────────

function formatTimestamp(date) {
  return String(date.getHours()).padStart(2, '0') + ':' + String(date.getMinutes()).padStart(2, '0');
}

function generateMessageId() {
  return `msg-${++state.messageCount}`;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function scrollToBottom() {
  setTimeout(() => { messagesContainer.scrollTop = messagesContainer.scrollHeight; }, 0);
}

// ── Input bar mode switch ──────────────────────────────────────────

function setTextMode() {
  inputWrapper.style.display = '';
  voiceBar.classList.remove('active');
  voiceButton.classList.remove('active');
  iconMic.style.display  = '';
  iconStop.style.display = 'none';
  voiceBtnLabel.textContent = 'Voz';
  voiceButton.title = 'Iniciar llamada de voz';
}

function setVoiceMode() {
  inputWrapper.style.display = 'none';
  voiceBar.classList.add('active');
  voiceButton.classList.add('active');
  iconMic.style.display  = 'none';
  iconStop.style.display = '';
  voiceBtnLabel.textContent = 'Finalizar';
  voiceButton.title = 'Finalizar modo voz';
  setOrbState('connecting');
  voiceStatus.textContent    = 'Conectando...';
  voiceTranscript.textContent = '';
}

function setOrbState(newState) {
  voiceOrb.className = `voice-orb-mini ${newState}`;
}

// ── Text Chat ──────────────────────────────────────────────────────

async function sendMessage(text) {
  if (!text.trim()) return;

  const userMsg = { id: generateMessageId(), role: 'user', content: text, isVoice: false, timestamp: new Date() };
  state.messages.push(userMsg);
  messageInput.value = '';
  messageInput.style.height = 'auto';
  renderMessages();
  scrollToBottom();

  const typingId = 'typing-indicator';
  state.messages.push({ id: typingId, role: 'assistant', content: '...', timestamp: new Date() });
  renderMessages();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: 'default',
        history: state.messages
          .filter(m => m.id !== typingId)
          .slice(-20)
          .map(m => ({ role: m.role, content: m.content })),
      }),
    });
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    state.messages = state.messages.filter(m => m.id !== typingId);
    state.messages.push({ id: generateMessageId(), role: 'assistant', content: data.response, isVoice: false, timestamp: new Date() });
  } catch (err) {
    console.error('Chat error:', err);
    state.messages = state.messages.filter(m => m.id !== typingId);
    state.messages.push({ id: generateMessageId(), role: 'assistant', content: 'Lo siento, algo sali\u00f3 mal. Por favor intenta de nuevo.', isVoice: false, timestamp: new Date() });
  }

  renderMessages();
  scrollToBottom();
}

messageInput.addEventListener('input', () => {
  messageInput.style.height = 'auto';
  messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
});

messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(messageInput.value); }
});

sendButton.addEventListener('click', () => sendMessage(messageInput.value));

// ── Voice Chat ─────────────────────────────────────────────────────

async function startVoiceChat() {
  state.voiceActive = true;
  setVoiceMode();

  try {
    // Share current text chat history with the voice LLM before connecting
    if (state.messages.length > 0) {
      await fetch('/api/set-voice-context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          history: state.messages.slice(-30).map(m => ({ role: m.role, content: m.content })),
        }),
      });
    }

    const urlRes = await fetch('/api/signed-url');
    if (!urlRes.ok) throw new Error('Failed to get signed URL');
    const { token: conversationToken } = await urlRes.json();

    const ElevenLabsClient = window.ElevenLabsClient;
    if (!ElevenLabsClient) throw new Error('ElevenLabs SDK not loaded');

    voiceStatus.textContent = 'Iniciando...';

    state.conversation = await ElevenLabsClient.Conversation.startSession({
      conversationToken,
      overrides: {
        agent: {
          firstMessage: "¡Hola! Soy Natalie, llamando de Movistar. ¿Estoy hablando con Mauricio Ortiz?",
        },
      },
      onConnect: () => {
        setOrbState('listening');
        voiceStatus.textContent    = 'Escuchando';
        voiceTranscript.textContent = 'Habla con naturalidad…';
      },
      onModeChange: ({ mode }) => {
        if (mode === 'speaking') {
          setOrbState('speaking');
          voiceStatus.textContent = 'Natalie habla';
        } else {
          setOrbState('listening');
          voiceStatus.textContent = 'Escuchando';
        }
      },
      onMessage: ({ message, source }) => {
        voiceTranscript.textContent = `"${message}"`;
        state.messages.push({
          id: generateMessageId(),
          role: source === 'user' ? 'user' : 'assistant',
          content: message,
          isVoice: true,
          timestamp: new Date(),
        });
        renderMessages();
        scrollToBottom();
      },
      onDisconnect: () => endVoiceMode(),
      onError: (error) => {
        console.error('Voice error:', error);
        const text = typeof error === 'string' ? error : (error && error.message) || '';
        // Quota/rate-limit is surfaced by the backend as a flat error frame
        // (normalized into onError by elevenlabs-error-shim.js).
        if (/quota|rate.?limit|exceeds/i.test(text)) {
          voiceStatus.textContent = 'Servicio no disponible (cuota agotada)';
        } else {
          voiceStatus.textContent = 'Error — intenta de nuevo';
        }
        setOrbState('connecting');
      },
    });
  } catch (err) {
    console.error('Failed to start voice:', err);
    voiceStatus.textContent = 'Error: ' + err.message;
    setOrbState('connecting');
  }
}

async function endVoiceMode() {
  if (state.conversation) {
    try { await state.conversation.endSession(); } catch (e) { console.warn(e); }
  }
  state.voiceActive  = false;
  state.conversation = null;
  setTextMode();
  renderMessages();
}

// Toggle: if voice is active, end it; if not, start it
voiceButton.addEventListener('click', () => {
  if (state.voiceActive) endVoiceMode();
  else startVoiceChat();
});

// ── Rendering ──────────────────────────────────────────────────────

function renderMessages() {
  if (state.messages.length === 0) {
    messagesContainer.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📞</div>
        <div class="empty-state-text">Inicia una conversación escribiendo abajo o presiona el botón de voz para hablar con Natalie.</div>
      </div>`;
    return;
  }

  messagesContainer.innerHTML = state.messages.map(msg => {
    const avatarLetter = msg.role === 'user' ? 'P' : 'N';
    return `
    <div class="message-group ${msg.role}">
      <div class="message-avatar">${avatarLetter}</div>
      <div class="message-body">
        <div class="message-bubble">${escapeHtml(msg.content)}</div>
        <div class="message-info">
          ${formatTimestamp(msg.timestamp)}
          ${msg.isVoice ? '<span class="voice-badge">voz</span>' : ''}
        </div>
      </div>
    </div>`;
  }).join('');
}

// ── Initialize ─────────────────────────────────────────────────────

renderMessages();
