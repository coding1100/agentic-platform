<template>
  <div class="pronunciation-practice-form">
    <div class="form-card">
      <h2>Pronunciation Practice 🎤</h2>
      <p class="form-description">Improve your pronunciation with targeted practice and feedback.</p>
      
      <!-- Focus Selection -->
      <div v-if="!currentExercise" class="focus-selection">
        <h3>Choose a Focus Area</h3>
        <div class="focus-grid">
          <button
            v-for="focus in focusAreas"
            :key="focus.id"
            @click="selectFocus(focus)"
            :class="['focus-btn', { active: selectedFocus === focus.id }]"
          >
            <span class="focus-icon">{{ focus.icon }}</span>
            <div class="focus-info">
              <strong>{{ focus.name }}</strong>
              <p>{{ focus.description }}</p>
            </div>
          </button>
        </div>
      </div>

      <!-- Pronunciation Exercise -->
      <div v-else class="pronunciation-view">
        <div class="exercise-header">
          <button @click="backToFocus" class="btn-back-small">← Back to Focus Areas</button>
          <div class="exercise-progress">
            Word {{ currentWordIndex + 1 }} of {{ words.length }}
          </div>
        </div>

        <div class="pronunciation-card">
          <div class="word-display">
            <h3 class="target-word">{{ currentWord.word }}</h3>
            <p class="phonetic">{{ currentWord.phonetic }}</p>
          </div>

          <!-- Native Audio -->
          <div class="audio-section">
            <button @click="playNativeAudio" class="btn-audio-large">
              🔊 Play Native Pronunciation
            </button>
            <p class="audio-hint">Listen carefully to the native pronunciation</p>
          </div>

          <!-- User Recording -->
          <div class="recording-section">
            <div class="recording-status">
              <div v-if="isRecording" class="recording-indicator">
                <span class="pulse-dot"></span>
                Recording...
              </div>
              <div v-else-if="lastScore !== null" class="score-display">
                <span :class="['score-value', { good: lastScore >= 80, medium: lastScore >= 60 && lastScore < 80, poor: lastScore < 60 }]">
                  {{ lastScore }}%
                </span>
                <p class="score-feedback">{{ scoreFeedback }}</p>
              </div>
            </div>

            <button
              @click="toggleRecording"
              :class="['btn-record', { recording: isRecording }]"
              :disabled="!speechRecognition.isSupported || isAssessing"
            >
              <span v-if="isRecording">⏹️ Stop Recording</span>
              <span v-else-if="isAssessing">⏳ Assessing...</span>
              <span v-else>🎤 Record Your Pronunciation</span>
            </button>

            <div v-if="!speechRecognition.isSupported" class="browser-warning">
              <p>⚠️ Speech recognition is not supported in this browser.</p>
              <p>Please use Chrome, Edge, or Safari for voice features.</p>
            </div>

            <div v-if="isAssessing" class="assessing-indicator">
              <div class="spinner-medium"></div>
              <p class="loading-title">Assessing your pronunciation...</p>
              <p class="sub-text">Analyzing accuracy, fluency, and clarity</p>
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>

            <div v-if="lastScore !== null && !isAssessing" class="detailed-feedback">
              <div v-if="assessmentFeedback" class="feedback-text">
                <p><strong>Feedback:</strong> {{ assessmentFeedback }}</p>
              </div>
              
              <div class="feedback-item">
                <span>Overall Score:</span>
                <div class="feedback-bar">
                  <div class="feedback-fill" :style="{ width: `${lastScore}%` }"></div>
                </div>
                <span class="score-number">{{ lastScore }}%</span>
              </div>
              <div class="feedback-item">
                <span>Accuracy:</span>
                <div class="feedback-bar">
                  <div class="feedback-fill" :style="{ width: `${accuracyScore}%` }"></div>
                </div>
                <span class="score-number">{{ accuracyScore }}%</span>
              </div>
              <div class="feedback-item">
                <span>Fluency:</span>
                <div class="feedback-bar">
                  <div class="feedback-fill" :style="{ width: `${fluencyScore}%` }"></div>
                </div>
                <span class="score-number">{{ fluencyScore }}%</span>
              </div>
              <div class="feedback-item">
                <span>Intonation:</span>
                <div class="feedback-bar">
                  <div class="feedback-fill" :style="{ width: `${intonationScore}%` }"></div>
                </div>
                <span class="score-number">{{ intonationScore }}%</span>
              </div>
              <div class="feedback-item">
                <span>Stress:</span>
                <div class="feedback-bar">
                  <div class="feedback-fill" :style="{ width: `${stressScore}%` }"></div>
                </div>
                <span class="score-number">{{ stressScore }}%</span>
              </div>
              <div class="feedback-item">
                <span>Clarity:</span>
                <div class="feedback-bar">
                  <div class="feedback-fill" :style="{ width: `${clarityScore}%` }"></div>
                </div>
                <span class="score-number">{{ clarityScore }}%</span>
              </div>

              <div v-if="assessmentSuggestions.length > 0" class="suggestions-box">
                <h4>💡 Suggestions for Improvement:</h4>
                <ul>
                  <li v-for="(suggestion, index) in assessmentSuggestions" :key="index">
                    {{ suggestion }}
                  </li>
                </ul>
              </div>
            </div>

            <div v-if="speechRecognition.error" class="error-message">
              ⚠️ {{ speechRecognition.error }}
            </div>

            <div v-if="speechRecognition.interimTranscript && isRecording" class="interim-transcript">
              <p><em>Listening: {{ speechRecognition.interimTranscript }}</em></p>
            </div>
          </div>

          <!-- Practice Tips -->
          <div class="practice-tips">
            <h4>Practice Tips</h4>
            <ul>
              <li>{{ currentWord.tip1 }}</li>
              <li>{{ currentWord.tip2 }}</li>
              <li>{{ currentWord.commonMistake }}</li>
            </ul>
          </div>

          <div class="word-actions">
            <button @click="markDifficult" class="btn-difficult">😓 Too Difficult</button>
            <button @click="nextWord" class="btn-next" :disabled="lastScore === null">
              {{ currentWordIndex < words.length - 1 ? 'Next Word →' : 'Finish Practice' }}
            </button>
          </div>
        </div>
      </div>
        
      <div class="form-actions">
        <button @click="handleBack" class="btn-back">← Back</button>
        <button @click="handleContinue" class="btn-primary">
          View Progress Dashboard →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useLanguagePracticeStore } from '@/stores/languagePractice'
import { useSpeechRecognition } from '@/composables/useSpeechRecognition'
import { useSpeechSynthesis } from '@/composables/useSpeechSynthesis'
import { pronunciationApi } from '@/services/api'
import type { PronunciationAssessmentResponse } from '@/services/api'

const emit = defineEmits<{
  complete: []
}>()

const languagePracticeStore = useLanguagePracticeStore()

const selectedFocus = ref<string | null>(null)
const currentWordIndex = ref(0)
const isRecording = ref(false)
const lastScore = ref<number | null>(null)
const intonationScore = ref(0)
const stressScore = ref(0)
const clarityScore = ref(0)
const accuracyScore = ref(0)
const fluencyScore = ref(0)
const assessmentFeedback = ref('')
const assessmentSuggestions = ref<string[]>([])
const isAssessing = ref(false)

// Web Speech API composables
const speechRecognition = useSpeechRecognition({
  lang: getLanguageCode(languagePracticeStore.languageProfile.targetLanguage),
  continuous: false,
  interimResults: true
})

const speechSynthesis = useSpeechSynthesis()

// Get language code for speech recognition
function getLanguageCode(language: string | null): string {
  const languageMap: Record<string, string> = {
    'spanish': 'es-ES',
    'french': 'fr-FR',
    'german': 'de-DE',
    'italian': 'it-IT',
    'portuguese': 'pt-PT',
    'chinese': 'zh-CN',
    'japanese': 'ja-JP',
    'korean': 'ko-KR',
    'arabic': 'ar-SA',
    'hindi': 'hi-IN',
    'russian': 'ru-RU'
  }
  return languageMap[language || ''] || 'en-US'
}

interface FocusArea {
  id: string
  name: string
  description: string
  icon: string
}

const focusAreas: FocusArea[] = [
  { id: 'vowels', name: 'Vowels', description: 'Master vowel sounds', icon: '🔤' },
  { id: 'consonants', name: 'Consonants', description: 'Perfect consonant pronunciation', icon: '🔠' },
  { id: 'stress', name: 'Word Stress', description: 'Learn stress patterns', icon: '⚡' },
  { id: 'intonation', name: 'Intonation', description: 'Sentence melody and tone', icon: '🎵' },
  { id: 'difficult-sounds', name: 'Difficult Sounds', description: 'Challenge sounds for your language', icon: '🎯' }
]

interface PronunciationWord {
  word: string
  phonetic: string
  tip1: string
  tip2: string
  commonMistake: string
}

const words = ref<PronunciationWord[]>([])
const currentWord = computed(() => words.value[currentWordIndex.value])

const scoreFeedback = computed(() => {
  if (lastScore.value === null) return ''
  if (lastScore.value >= 90) return 'Excellent! Your pronunciation is very clear.'
  if (lastScore.value >= 80) return 'Great job! Minor improvements needed.'
  if (lastScore.value >= 60) return 'Good attempt! Keep practicing.'
  return 'Keep trying! Focus on the tips below.'
})

function selectFocus(focus: FocusArea) {
  selectedFocus.value = focus.id
  generateWords(focus.id)
}

function generateWords(focusId: string) {
  // Sample words - in production, these would come from AI agent
  words.value = [
    {
      word: 'Hola',
      phonetic: '/ˈo.la/',
      tip1: 'The "H" is silent in Spanish',
      tip2: 'Emphasize the "o" sound',
      commonMistake: 'Avoid pronouncing the "H"'
    },
    {
      word: 'Gracias',
      phonetic: '/ˈɡɾa.sjas/',
      tip1: 'Roll the "r" sound',
      tip2: 'Stress on the first syllable',
      commonMistake: 'Don\'t pronounce it like "gracias" in English'
    }
  ]
  currentWordIndex.value = 0
  lastScore.value = null
}

async function playNativeAudio() {
  if (!currentWord.value) return
  
  if (!speechSynthesis.isSupported.value) {
    alert('Text-to-speech is not supported in this browser. Please use Chrome, Edge, or Safari.')
    return
  }

  try {
    const langCode = getLanguageCode(languagePracticeStore.languageProfile.targetLanguage)
    await speechSynthesis.speak(currentWord.value.word, {
      lang: langCode,
      rate: 0.9,
      pitch: 1,
      volume: 1
    })
  } catch (error: any) {
    console.error('Error playing audio:', error)
    alert('Failed to play audio. Please try again.')
  }
}

function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function startRecording() {
  if (!speechRecognition.isSupported.value) {
    alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.')
    return
  }

  if (!currentWord.value) {
    alert('Please select a word to practice first.')
    return
  }

  isRecording.value = true
  speechRecognition.reset()
  
  // Set language for recognition
  const langCode = getLanguageCode(languagePracticeStore.languageProfile.targetLanguage)
  speechRecognition.start(langCode)
}

async function stopRecording() {
  if (!isRecording.value) return

  speechRecognition.stop()
  isRecording.value = false

  // Wait a moment for final transcript
  await new Promise(resolve => setTimeout(resolve, 500))

  const transcript = speechRecognition.getFullTranscript().trim()
  
  if (!transcript) {
    alert('No speech detected. Please try again.')
    return
  }

  // Assess pronunciation
  await assessPronunciation(transcript)
}

async function assessPronunciation(userTranscript: string) {
  if (!currentWord.value) return

  isAssessing.value = true
  
  try {
    const language = languagePracticeStore.languageProfile.targetLanguage || 'english'
    const langCode = getLanguageCode(languagePracticeStore.languageProfile.targetLanguage)
    
    const assessment = await pronunciationApi.assess({
      word_or_phrase: currentWord.value.word,
      user_transcript: userTranscript,
      language: language,
      target_language_code: langCode
    })

    // Update scores
    lastScore.value = assessment.overall_score
    accuracyScore.value = assessment.accuracy_score
    fluencyScore.value = assessment.fluency_score
    intonationScore.value = assessment.intonation_score
    stressScore.value = assessment.stress_score
    clarityScore.value = assessment.clarity_score
    assessmentFeedback.value = assessment.feedback
    assessmentSuggestions.value = assessment.suggestions

    // Award XP based on score
    const xp = assessment.overall_score >= 90 ? 20 : 
               assessment.overall_score >= 80 ? 15 : 
               assessment.overall_score >= 60 ? 10 : 5
    languagePracticeStore.addXP(xp)

  } catch (error: any) {
    console.error('Error assessing pronunciation:', error)
    alert('Failed to assess pronunciation. Please try again.')
    
    // Fallback: use basic scoring based on transcript similarity
    const similarity = calculateSimilarity(
      currentWord.value.word.toLowerCase(),
      userTranscript.toLowerCase()
    )
    lastScore.value = Math.round(similarity * 100)
    accuracyScore.value = lastScore.value
    fluencyScore.value = lastScore.value
    intonationScore.value = lastScore.value
    stressScore.value = lastScore.value
    clarityScore.value = lastScore.value
    assessmentFeedback.value = 'Pronunciation assessment completed. Keep practicing!'
    assessmentSuggestions.value = ['Practice the word slowly', 'Focus on each sound', 'Listen to native pronunciation']
  } finally {
    isAssessing.value = false
  }
}

// Simple similarity calculation (Levenshtein distance based)
function calculateSimilarity(str1: string, str2: string): number {
  const longer = str1.length > str2.length ? str1 : str2
  const shorter = str1.length > str2.length ? str2 : str1
  
  if (longer.length === 0) return 1.0
  
  const distance = levenshteinDistance(longer, shorter)
  return (longer.length - distance) / longer.length
}

function levenshteinDistance(str1: string, str2: string): number {
  const matrix: number[][] = []
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i]
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1]
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        )
      }
    }
  }
  
  return matrix[str2.length][str1.length]
}

function markDifficult() {
  // Mark word for more practice
  if (currentWordIndex.value < words.value.length - 1) {
    nextWord()
  }
}

function nextWord() {
  if (currentWordIndex.value < words.value.length - 1) {
    currentWordIndex.value++
    lastScore.value = null
    accuracyScore.value = 0
    fluencyScore.value = 0
    intonationScore.value = 0
    stressScore.value = 0
    clarityScore.value = 0
    assessmentFeedback.value = ''
    assessmentSuggestions.value = []
    speechRecognition.reset()
  } else {
    // Practice complete
    selectedFocus.value = null
  }
}

// Cleanup on unmount
onUnmounted(() => {
  speechRecognition.abort()
  speechSynthesis.stop()
})

function backToFocus() {
  selectedFocus.value = null
  words.value = []
}

function handleBack() {
  languagePracticeStore.setStep('conversation-practice')
}

function handleContinue() {
  emit('complete')
}
</script>

<style scoped>
.pronunciation-practice-form {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  padding: 20px 0;
}

.form-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 700px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h2 {
  color: white;
  font-size: 28px;
  margin: 0 0 12px 0;
  font-weight: 700;
  text-align: center;
}

.form-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  text-align: center;
  margin-bottom: 32px;
  line-height: 1.6;
}

.focus-selection h3 {
  color: white;
  font-size: 20px;
  margin-bottom: 20px;
}

.focus-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.focus-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.focus-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.focus-btn.active {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.focus-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.focus-info {
  flex: 1;
}

.focus-info strong {
  display: block;
  font-size: 16px;
  margin-bottom: 4px;
}

.focus-info p {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.pronunciation-view {
  margin-bottom: 32px;
}

.exercise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.exercise-progress {
  color: white;
  font-size: 14px;
}

.pronunciation-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
}

.word-display {
  text-align: center;
  margin-bottom: 32px;
}

.target-word {
  font-size: 64px;
  font-weight: 700;
  color: white;
  margin: 0 0 12px 0;
}

.phonetic {
  font-size: 24px;
  color: rgba(255, 255, 255, 0.8);
  font-family: monospace;
}

.audio-section {
  text-align: center;
  margin-bottom: 32px;
}

.btn-audio-large {
  padding: 16px 32px;
  background: rgba(102, 126, 234, 0.4);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-audio-large:hover {
  background: rgba(102, 126, 234, 0.5);
  transform: scale(1.05);
}

.audio-hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  margin-top: 8px;
}

.recording-section {
  margin-bottom: 32px;
}

.recording-status {
  text-align: center;
  margin-bottom: 20px;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #ff5722;
  font-weight: 600;
}

.pulse-dot {
  width: 12px;
  height: 12px;
  background: #ff5722;
  border-radius: 50%;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-value {
  font-size: 48px;
  font-weight: 700;
}

.score-value.good {
  color: #4caf50;
}

.score-value.medium {
  color: #ffc107;
}

.score-value.poor {
  color: #ff5722;
}

.score-feedback {
  color: white;
  font-size: 14px;
  margin: 0;
}

.btn-record {
  width: 100%;
  padding: 20px;
  background: rgba(255, 87, 34, 0.3);
  color: white;
  border: 3px solid rgba(255, 87, 34, 0.5);
  border-radius: 16px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-record:hover {
  background: rgba(255, 87, 34, 0.4);
}

.btn-record.recording {
  background: rgba(255, 87, 34, 0.6);
  animation: pulse-border 1s infinite;
}

@keyframes pulse-border {
  0%, 100% { border-color: rgba(255, 87, 34, 0.5); }
  50% { border-color: rgba(255, 87, 34, 0.8); }
}

.detailed-feedback {
  margin-top: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.feedback-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.feedback-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.feedback-item span:first-child {
  color: white;
  font-size: 14px;
  min-width: 100px;
}

.score-number {
  color: white;
  font-size: 14px;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.feedback-bar {
  flex: 1;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.feedback-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(76, 175, 80, 0.8), rgba(102, 126, 234, 0.8));
  transition: width 0.3s ease;
}

.practice-tips {
  background: rgba(255, 193, 7, 0.2);
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.practice-tips h4 {
  color: white;
  font-size: 16px;
  margin-bottom: 12px;
}

.practice-tips ul {
  color: white;
  font-size: 14px;
  line-height: 1.8;
  margin: 0;
  padding-left: 20px;
}

.word-actions {
  display: flex;
  gap: 12px;
}

.btn-difficult {
  flex: 1;
  padding: 12px 20px;
  background: rgba(255, 87, 34, 0.3);
  color: white;
  border: 1px solid rgba(255, 87, 34, 0.5);
  border-radius: 12px;
  cursor: pointer;
}

.btn-next {
  flex: 2;
  padding: 12px 20px;
  background: rgba(255, 255, 255, 0.25);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

.btn-next:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-back-small {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-back {
  flex: 1;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  cursor: pointer;
}

.btn-primary {
  flex: 2;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.25);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.assessing-indicator {
  text-align: center;
  padding: 32px 20px;
  color: white;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  margin: 16px 0;
}

.spinner-medium {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: rgba(102, 126, 234, 1);
  border-right-color: rgba(102, 126, 234, 0.8);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-title {
  color: white;
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.sub-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  margin: 0 0 16px 0;
}

.loading-dots {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: rgba(102, 126, 234, 0.8);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

.feedback-text {
  background: rgba(255, 255, 255, 0.1);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  color: white;
  font-size: 14px;
  line-height: 1.6;
}

.suggestions-box {
  margin-top: 20px;
  padding: 16px;
  background: rgba(255, 193, 7, 0.2);
  border-radius: 8px;
}

.suggestions-box h4 {
  color: white;
  font-size: 16px;
  margin-bottom: 12px;
}

.suggestions-box ul {
  color: white;
  font-size: 14px;
  line-height: 1.8;
  margin: 0;
  padding-left: 20px;
}

.error-message {
  background: rgba(255, 87, 34, 0.3);
  color: white;
  padding: 12px;
  border-radius: 8px;
  margin-top: 12px;
  font-size: 14px;
}

.interim-transcript {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-style: italic;
}

.browser-warning {
  margin-top: 16px;
  padding: 16px;
  background: rgba(255, 193, 7, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 14px;
  text-align: center;
}

.btn-record:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

