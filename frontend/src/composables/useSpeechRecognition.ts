import { ref, onUnmounted } from 'vue'

export interface SpeechRecognitionOptions {
  lang?: string
  continuous?: boolean
  interimResults?: boolean
  maxAlternatives?: number
}

export interface SpeechRecognitionResult {
  transcript: string
  confidence: number
  isFinal: boolean
}

export function useSpeechRecognition(options: SpeechRecognitionOptions = {}) {
  const isSupported = ref(false)
  const isListening = ref(false)
  const transcript = ref('')
  const interimTranscript = ref('')
  const confidence = ref(0)
  const error = ref<string | null>(null)
  
  let recognition: any = null

  // Check browser support
  const checkSupport = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    isSupported.value = !!SpeechRecognition
    return isSupported.value
  }

  // Initialize recognition
  const initRecognition = () => {
    if (!checkSupport()) {
      error.value = 'Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.'
      return null
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    recognition = new SpeechRecognition()

    recognition.lang = options.lang || 'en-US'
    recognition.continuous = options.continuous ?? false
    recognition.interimResults = options.interimResults ?? true
    recognition.maxAlternatives = options.maxAlternatives ?? 1

    recognition.onstart = () => {
      isListening.value = true
      error.value = null
    }

    recognition.onresult = (event: any) => {
      let interim = ''
      let final = ''
      let maxConfidence = 0

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const transcript = result[0].transcript
        const conf = result[0].confidence || 0.8

        if (result.isFinal) {
          final += transcript
          maxConfidence = Math.max(maxConfidence, conf)
        } else {
          interim += transcript
        }
      }

      interimTranscript.value = interim
      if (final) {
        transcript.value += final + ' '
        confidence.value = maxConfidence
      }
    }

    recognition.onerror = (event: any) => {
      isListening.value = false
      let errorMessage = 'Speech recognition error occurred'
      
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try again.'
          break
        case 'audio-capture':
          errorMessage = 'No microphone found. Please check your microphone settings.'
          break
        case 'not-allowed':
          errorMessage = 'Microphone permission denied. Please allow microphone access.'
          break
        case 'network':
          errorMessage = 'Network error. Please check your internet connection.'
          break
        case 'aborted':
          errorMessage = 'Speech recognition aborted.'
          break
        default:
          errorMessage = `Speech recognition error: ${event.error}`
      }
      
      error.value = errorMessage
    }

    recognition.onend = () => {
      isListening.value = false
    }

    return recognition
  }

  // Start listening
  const start = (lang?: string) => {
    if (!recognition) {
      if (lang) {
        options.lang = lang
      }
      initRecognition()
    }
    
    if (recognition && !isListening.value) {
      transcript.value = ''
      interimTranscript.value = ''
      confidence.value = 0
      error.value = null
      
      try {
        if (lang) {
          recognition.lang = lang
        }
        recognition.start()
      } catch (e: any) {
        error.value = e.message || 'Failed to start speech recognition'
      }
    }
  }

  // Stop listening
  const stop = () => {
    if (recognition && isListening.value) {
      try {
        recognition.stop()
      } catch (e) {
        // Ignore errors when stopping
      }
    }
  }

  // Abort listening
  const abort = () => {
    if (recognition && isListening.value) {
      try {
        recognition.abort()
      } catch (e) {
        // Ignore errors when aborting
      }
    }
  }

  // Get full transcript (final + interim)
  const getFullTranscript = () => {
    return (transcript.value + interimTranscript.value).trim()
  }

  // Reset transcript
  const reset = () => {
    transcript.value = ''
    interimTranscript.value = ''
    confidence.value = 0
    error.value = null
  }

  // Cleanup on unmount
  onUnmounted(() => {
    if (recognition) {
      try {
        recognition.abort()
      } catch (e) {
        // Ignore errors
      }
    }
  })

  // Initialize on creation
  checkSupport()

  return {
    isSupported,
    isListening,
    transcript,
    interimTranscript,
    confidence,
    error,
    start,
    stop,
    abort,
    getFullTranscript,
    reset,
    checkSupport
  }
}





