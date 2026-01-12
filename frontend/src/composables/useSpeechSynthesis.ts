import { ref } from 'vue'

export interface SpeechSynthesisOptions {
  lang?: string
  pitch?: number
  rate?: number
  volume?: number
  voice?: SpeechSynthesisVoice | null
}

export function useSpeechSynthesis() {
  const isSupported = ref(false)
  const isSpeaking = ref(false)
  const voices = ref<SpeechSynthesisVoice[]>([])
  const error = ref<string | null>(null)

  // Check browser support
  const checkSupport = () => {
    isSupported.value = 'speechSynthesis' in window
    return isSupported.value
  }

  // Load available voices
  const loadVoices = () => {
    if (!checkSupport()) {
      return
    }

    const synth = window.speechSynthesis
    const availableVoices = synth.getVoices()
    voices.value = availableVoices

    // If voices aren't loaded yet, wait for them
    if (availableVoices.length === 0) {
      synth.onvoiceschanged = () => {
        voices.value = synth.getVoices()
      }
    }
  }

  // Get voice by language code
  const getVoiceByLang = (lang: string): SpeechSynthesisVoice | null => {
    if (voices.value.length === 0) {
      loadVoices()
    }

    // Try exact match first
    let voice = voices.value.find(v => v.lang === lang)
    
    // Try language code match (e.g., 'es' for 'es-ES')
    if (!voice) {
      const langCode = lang.split('-')[0]
      voice = voices.value.find(v => v.lang.startsWith(langCode))
    }

    // Fallback to any voice
    if (!voice && voices.value.length > 0) {
      voice = voices.value[0]
    }

    return voice || null
  }

  // Speak text
  const speak = (text: string, options: SpeechSynthesisOptions = {}) => {
    if (!checkSupport()) {
      error.value = 'Speech synthesis is not supported in this browser.'
      return Promise.reject(new Error('Speech synthesis not supported'))
    }

    return new Promise<void>((resolve, reject) => {
      const synth = window.speechSynthesis
      
      // Cancel any ongoing speech
      synth.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      
      utterance.lang = options.lang || 'en-US'
      utterance.pitch = options.pitch ?? 1
      utterance.rate = options.rate ?? 1
      utterance.volume = options.volume ?? 1

      if (options.voice) {
        utterance.voice = options.voice
      } else if (options.lang) {
        const voice = getVoiceByLang(options.lang)
        if (voice) {
          utterance.voice = voice
        }
      }

      utterance.onstart = () => {
        isSpeaking.value = true
        error.value = null
      }

      utterance.onend = () => {
        isSpeaking.value = false
        resolve()
      }

      utterance.onerror = (event) => {
        isSpeaking.value = false
        error.value = `Speech synthesis error: ${event.error}`
        reject(new Error(`Speech synthesis error: ${event.error}`))
      }

      synth.speak(utterance)
    })
  }

  // Stop speaking
  const stop = () => {
    if (checkSupport()) {
      window.speechSynthesis.cancel()
      isSpeaking.value = false
    }
  }

  // Pause speaking
  const pause = () => {
    if (checkSupport()) {
      window.speechSynthesis.pause()
    }
  }

  // Resume speaking
  const resume = () => {
    if (checkSupport()) {
      window.speechSynthesis.resume()
    }
  }

  // Initialize
  checkSupport()
  if (isSupported.value) {
    loadVoices()
  }

  return {
    isSupported,
    isSpeaking,
    voices,
    error,
    speak,
    stop,
    pause,
    resume,
    getVoiceByLang,
    loadVoices
  }
}





