/**
 * voice.js - Web Speech API: Speech-to-Text (STT) and Text-to-Speech (TTS)
 */

class VoiceAssistant {
  constructor() {
    this.recognition = null;
    this.isListening = false;
    this.isSpeaking = false;
    this.currentUtterance = null;
    this.initRecognition();
  }

  // Initialize Speech Recognition
  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('Web Speech Recognition API is not supported in this browser.');
      return;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-IN'; // Indian English default, also captures Hindi terms

      this.recognition.onstart = () => {
        this.isListening = true;
        this.updateMicUI(true);
        this.showSpeechStatusBar('Listening... Speak now into your microphone.');
      };

      this.recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        const chatInput = document.getElementById('chatInput');
        if (chatInput) {
          if (finalTranscript) {
            chatInput.value = (chatInput.value ? chatInput.value + ' ' : '') + finalTranscript;
          } else if (interimTranscript) {
            this.showSpeechStatusBar('Hearing: ' + interimTranscript);
          }
        }
      };

      this.recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        let msg = 'Speech recognition error: ' + event.error;
        if (event.error === 'not-allowed') {
          msg = 'Microphone access was denied. Please allow microphone permissions in your browser.';
        } else if (event.error === 'no-speech') {
          msg = 'No speech detected. Please try speaking again.';
        }
        showToast(msg, 'warning');
        this.stopListening();
      };

      this.recognition.onend = () => {
        this.stopListening();
      };
    } catch (e) {
      console.error('Failed to initialize speech recognition:', e);
    }
  }

  toggleListening() {
    if (!this.recognition) {
      showToast('Speech recognition is not supported in your browser. Please try Chrome, Edge, or Safari.', 'warning');
      return;
    }

    if (this.isListening) {
      this.recognition.stop();
      this.stopListening();
    } else {
      try {
        this.recognition.start();
      } catch (err) {
        console.error('Failed to start speech recognition:', err);
        this.stopListening();
      }
    }
  }

  stopListening() {
    this.isListening = false;
    this.updateMicUI(false);
    this.hideSpeechStatusBar();
  }

  updateMicUI(active) {
    const micBtn = document.getElementById('micBtn');
    if (micBtn) {
      if (active) {
        micBtn.classList.add('recording');
        micBtn.innerHTML = '<i class="bi bi-mic-fill"></i>';
        micBtn.setAttribute('title', 'Click to stop listening');
      } else {
        micBtn.classList.remove('recording');
        micBtn.innerHTML = '<i class="bi bi-mic"></i>';
        micBtn.setAttribute('title', 'Speak your question (Voice Input)');
      }
    }
  }

  showSpeechStatusBar(text) {
    let bar = document.getElementById('speechStatusBar');
    if (!bar) {
      const container = document.querySelector('.chat-input-area');
      if (container) {
        bar = document.createElement('div');
        bar.id = 'speechStatusBar';
        bar.className = 'speech-bar';
        container.insertBefore(bar, container.firstChild);
      }
    }
    if (bar) {
      bar.innerHTML = `<span><i class="bi bi-record-circle text-danger me-2"></i> ${escapeHTML(text)}</span>
                       <button type="button" class="btn btn-sm btn-link p-0 text-primary" onclick="voiceAssistant.toggleListening()">Done</button>`;
      bar.style.display = 'flex';
    }
  }

  hideSpeechStatusBar() {
    const bar = document.getElementById('speechStatusBar');
    if (bar) bar.style.display = 'none';
  }

  // Text to Speech
  speak(text, buttonElement = null) {
    if (!('speechSynthesis' in window)) {
      showToast('Text-to-speech is not supported in this browser.', 'warning');
      return;
    }

    // If currently speaking, stop
    if (this.isSpeaking) {
      window.speechSynthesis.cancel();
      this.isSpeaking = false;
      this.resetSpeakButtons();
      return;
    }

    window.speechSynthesis.cancel(); // Stop any pending speech

    // Clean markdown symbols for cleaner pronunciation
    const cleanText = text
      .replace(/[#*`_~\[\]\(\)>]/g, ' ')
      .replace(/https?:\/\/\S+/g, 'link')
      .replace(/\s+/g, ' ')
      .trim();

    this.currentUtterance = new SpeechSynthesisUtterance(cleanText);
    this.currentUtterance.rate = 1.0;
    this.currentUtterance.pitch = 1.0;

    // Pick an English or Indian English voice if available
    const voices = window.speechSynthesis.getVoices();
    const voice = voices.find(v => v.lang.includes('en-IN')) || voices.find(v => v.lang.includes('en'));
    if (voice) {
      this.currentUtterance.voice = voice;
    }

    this.currentUtterance.onstart = () => {
      this.isSpeaking = true;
      if (buttonElement) {
        buttonElement.innerHTML = '<i class="bi bi-stop-circle-fill text-danger"></i> Stop';
        buttonElement.classList.add('speaking');
      }
    };

    this.currentUtterance.onend = () => {
      this.isSpeaking = false;
      this.resetSpeakButtons();
    };

    this.currentUtterance.onerror = () => {
      this.isSpeaking = false;
      this.resetSpeakButtons();
    };

    window.speechSynthesis.speak(this.currentUtterance);
  }

  stopSpeaking() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      this.isSpeaking = false;
      this.resetSpeakButtons();
    }
  }

  resetSpeakButtons() {
    document.querySelectorAll('.btn-speak').forEach(btn => {
      btn.innerHTML = '<i class="bi bi-volume-up"></i> Listen';
      btn.classList.remove('speaking');
    });
  }
}

// Global voice instance
const voiceAssistant = new VoiceAssistant();
