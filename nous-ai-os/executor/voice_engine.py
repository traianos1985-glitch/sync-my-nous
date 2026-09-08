"""Voice Engine — φωνητική αλληλεπίδραση για τον NOUS.

Browser-side: Web Speech API (SpeechRecognition + SpeechSynthesis) — δεν χρειάζεται backend.
Server-side: προετοιμασία κειμένου για TTS + status endpoint.
"""
import re, time

VOICE_ENABLED  = True
VOICE_LANG     = "el-GR"
VOICE_RATE     = 0.9   # speaking rate
VOICE_PITCH    = 1.0


def voice_status() -> dict:
    return {
        "enabled":  VOICE_ENABLED,
        "mode":     "web_speech_api",
        "lang":     VOICE_LANG,
        "features": ["speech_to_text", "text_to_speech"],
        "note":     "Φωνητική I/O μέσω Web Speech API — λειτουργεί εξ ολοκλήρου στο browser",
    }


def prepare_tts(text: str, lang: str = None) -> dict:
    """Καθαρίζει κείμενο για καλύτερη φωνητική απόδοση."""
    # Strip emojis and markdown
    clean = re.sub(r'[^\w\s.,;:!?()\'\"«»\-–—\n]', '', text, flags=re.UNICODE)
    clean = re.sub(r'\*+', '', clean)
    clean = re.sub(r'`+', '', clean)
    clean = clean.strip()
    return {
        "ok":   True,
        "text": clean,
        "lang": lang or VOICE_LANG,
        "rate": VOICE_RATE,
        "pitch": VOICE_PITCH,
    }


def get_voice_js() -> str:
    """Επιστρέφει JS snippet για voice input/output στον browser."""
    return """
// NOUS Voice Engine — Web Speech API
const nousVoice = {
  recognition: null,
  synthesis: window.speechSynthesis,

  startListening(onResult, onError) {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { if(onError) onError('not_supported'); return false; }
    this.recognition = new SR();
    this.recognition.lang = 'el-GR';
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.onresult = e => onResult(e.results[0][0].transcript);
    this.recognition.onerror  = e => { if(onError) onError(e.error); };
    this.recognition.start();
    return true;
  },

  stopListening() {
    if (this.recognition) { this.recognition.stop(); this.recognition = null; }
  },

  speak(text, lang) {
    if (!this.synthesis) return;
    this.synthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang  = lang || 'el-GR';
    u.rate  = 0.9;
    u.pitch = 1.0;
    this.synthesis.speak(u);
  },

  stop() { if (this.synthesis) this.synthesis.cancel(); this.stopListening(); }
};
"""
