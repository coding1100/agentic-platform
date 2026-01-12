<template>
  <div class="conversation-practice-form">
    <div class="form-card">
      <h2>Conversation Practice 💬</h2>
      <p class="form-description">Practice real-world conversations in realistic scenarios.</p>
      
      <!-- Scenario Selection -->
      <div v-if="!currentScenario" class="scenario-selection">
        <h3>Choose a Conversation Scenario</h3>
        <div v-if="isGeneratingScenario" class="generating-scenario">
          <div class="spinner-large"></div>
          <p class="loading-title">Generating conversation scenario...</p>
          <p class="sub-text">Creating personalized dialogue for you</p>
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
        <div v-else class="scenario-grid">
          <button
            v-for="scenario in scenarios"
            :key="scenario.id"
            @click="selectScenario(scenario)"
            :class="['scenario-btn', { active: selectedScenario === scenario.id }]"
          >
            <span class="scenario-icon">{{ scenario.icon }}</span>
            <div class="scenario-info">
              <strong>{{ scenario.name }}</strong>
              <p>{{ scenario.description }}</p>
            </div>
          </button>
        </div>
      </div>

      <!-- Conversation Practice -->
      <div v-else class="conversation-view">
        <div class="conversation-header">
          <button @click="backToScenarios" class="btn-back-small">← Back to Scenarios</button>
          <h3>{{ currentScenario.title }}</h3>
        </div>

        <div class="scenario-context">
          <p><strong>Context:</strong> {{ currentScenario.context }}</p>
        </div>

        <div class="dialogue-container">
          <div
            v-for="(dialogue, index) in displayedDialogues"
            :key="dialogue.id"
            :class="['dialogue-message', dialogue.speaker]"
          >
            <div class="dialogue-avatar">
              {{ dialogue.speaker === 'native' ? '👤' : 'You' }}
            </div>
            <div class="dialogue-content">
              <div class="dialogue-text">{{ dialogue.text }}</div>
              <div class="dialogue-translation">{{ dialogue.translation }}</div>
              <button v-if="dialogue.audioUrl" @click="playAudio(dialogue)" class="btn-audio-small">🔊</button>
            </div>
          </div>
        </div>

        <div v-if="currentScenario && currentDialogueIndex < currentScenario.dialogues.length && currentScenario.dialogues[currentDialogueIndex].speaker === 'user'" class="user-response">
          <div class="response-prompt">
            <p><strong>Your turn:</strong> Respond naturally to the conversation</p>
          </div>

          <!-- Voice/Text Mode Toggle -->
          <div class="input-mode-toggle">
            <button
              @click="isVoiceMode = false"
              :class="['mode-btn', { active: !isVoiceMode }]"
            >
              ⌨️ Type
            </button>
            <button
              @click="isVoiceMode = true"
              :class="['mode-btn', { active: isVoiceMode }]"
              :disabled="!speechRecognition.isSupported"
            >
              🎤 Voice
            </button>
          </div>

          <!-- Text Input Mode -->
          <div v-if="!isVoiceMode" class="response-input">
            <input
              v-model="userResponse"
              type="text"
              class="form-input"
              :placeholder="`Type your response in ${languagePracticeStore.languageProfile.targetLanguage}...`"
              @keyup.enter="submitResponse"
              :disabled="isEvaluatingResponse"
            />
            <button @click="submitResponse" :disabled="!userResponse.trim() || isEvaluatingResponse" class="btn-send-response">
              <span v-if="isEvaluatingResponse">Evaluating...</span>
              <span v-else>Send</span>
            </button>
          </div>

          <!-- Voice Input Mode -->
          <div v-else class="voice-input">
            <div class="voice-controls">
              <button
                @click="toggleVoiceRecording"
                :class="['btn-voice-record', { recording: isListening }]"
                :disabled="!speechRecognition.isSupported || speechRecognition.isListening"
              >
                <span v-if="isListening">⏹️ Stop Recording</span>
                <span v-else>🎤 Tap to Speak</span>
              </button>
              
              <div v-if="speechRecognition.interimTranscript && isListening" class="interim-transcript">
                <p><em>{{ speechRecognition.interimTranscript }}</em></p>
              </div>

              <div v-if="speechRecognition.transcript && !isListening" class="final-transcript">
                <p><strong>You said:</strong> {{ speechRecognition.transcript }}</p>
                <div class="transcript-actions">
                  <button @click="useTranscript" class="btn-use-transcript">✓ Use This</button>
                  <button @click="clearTranscript" class="btn-clear-transcript">✗ Clear</button>
                </div>
              </div>

              <div v-if="speechRecognition.error" class="error-message">
                ⚠️ {{ speechRecognition.error }}
              </div>

              <div v-if="!speechRecognition.isSupported" class="browser-warning">
                <p>⚠️ Voice input is not supported in this browser.</p>
                <p>Please use Chrome, Edge, or Safari for voice features.</p>
              </div>
            </div>
          </div>

          <div class="response-hints" v-if="showHints">
            <p><strong>Hint:</strong> Try to respond naturally. Don't worry about being perfect!</p>
          </div>
          <button @click="showHints = !showHints" class="btn-hint">
            {{ showHints ? 'Hide' : 'Show' }} Hint
          </button>
        </div>

        <div v-else class="conversation-complete">
          <h3>🎉 Conversation Complete!</h3>
          <p>Great job practicing this scenario. Your score: {{ conversationScore }}%</p>
          <button @click="restartConversation" class="btn-primary">Practice Again</button>
        </div>

        <!-- Key Phrases -->
        <div v-if="selectedScenario === 'restaurant'" class="key-phrases">
          <h4>Key Phrases for This Scenario</h4>
          <div class="phrases-list">
            <div class="phrase-item">
              <strong>La cuenta, por favor</strong>
              <span>The check, please</span>
              <em>When asking for the bill</em>
            </div>
            <div class="phrase-item">
              <strong>¿Qué recomienda?</strong>
              <span>What do you recommend?</span>
              <em>Asking for recommendations</em>
            </div>
          </div>
        </div>
      </div>
        
      <div class="form-actions">
        <button @click="handleBack" class="btn-back">← Back</button>
        <button @click="handleContinue" class="btn-primary">
          Continue to Pronunciation →
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
import type { ConversationScenario } from '@/stores/languagePractice'

const emit = defineEmits<{
  complete: []
}>()

const languagePracticeStore = useLanguagePracticeStore()

const selectedScenario = ref<string | null>(null)
const currentDialogueIndex = ref(0)
const userResponse = ref('')
const showHints = ref(false)
const conversationScore = ref(0)
const isVoiceMode = ref(false)
const isListening = ref(false)
const isGeneratingScenario = ref(false)
const isEvaluatingResponse = ref(false)

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

interface Scenario {
  id: string
  name: string
  description: string
  icon: string
}

const scenarios: Scenario[] = [
  { id: 'restaurant', name: 'Restaurant', description: 'Ordering food and drinks', icon: '🍽️' },
  { id: 'airport', name: 'Airport', description: 'Check-in, security, boarding', icon: '✈️' },
  { id: 'hotel', name: 'Hotel', description: 'Booking and checking in', icon: '🏨' },
  { id: 'shopping', name: 'Shopping', description: 'Buying items and asking prices', icon: '🛍️' },
  { id: 'taxi', name: 'Taxi/Uber', description: 'Giving directions and paying', icon: '🚕' },
  { id: 'doctor', name: 'Doctor Visit', description: 'Describing symptoms', icon: '🏥' }
]

const currentScenario = ref<ConversationScenario | null>(null)

async function selectScenario(scenario: Scenario) {
  selectedScenario.value = scenario.id
  isGeneratingScenario.value = true
  
  // In production, this would come from AI agent
  // Simulate AI generation delay
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  currentScenario.value = {
    id: scenario.id,
    title: `${scenario.name} Conversation`,
    description: scenario.description,
    context: `You are in a ${scenario.name.toLowerCase()} scenario. Practice having a conversation.`,
    dialogues: [
      {
        id: 'd1',
        speaker: 'native',
        text: scenario.id === 'restaurant' ? 'Buenas noches. ¿Tienen una mesa para dos?' : 'Hello, how can I help you?',
        translation: scenario.id === 'restaurant' ? 'Good evening. Do you have a table for two?' : 'Hello, how can I help you?'
      },
      {
        id: 'd2',
        speaker: 'user',
        text: '',
        translation: ''
      }
    ],
    difficulty: 2,
    completed: false,
    score: 0
  }
  currentDialogueIndex.value = 0
  userResponse.value = ''
  showHints.value = false
  isGeneratingScenario.value = false
}

const displayedDialogues = computed(() => {
  if (!currentScenario.value) return []
  const dialogues = [...currentScenario.value.dialogues]
  // Add user response if provided
  if (currentDialogueIndex.value < dialogues.length && dialogues[currentDialogueIndex.value].speaker === 'user') {
    if (userResponse.value && currentDialogueIndex.value > 0) {
      dialogues[currentDialogueIndex.value].text = userResponse.value
    }
  }
  return dialogues.slice(0, currentDialogueIndex.value + 1)
})


async function submitResponse() {
  if (!userResponse.value.trim() || !currentScenario.value) return
  
  isEvaluatingResponse.value = true
  
  // Add user response to dialogue
  if (currentDialogueIndex.value < currentScenario.value.dialogues.length) {
    const dialogue = currentScenario.value.dialogues[currentDialogueIndex.value]
    if (dialogue.speaker === 'user') {
      dialogue.text = userResponse.value
    }
  }
  
  // Simulate AI evaluation delay
  await new Promise(resolve => setTimeout(resolve, 800))
  
  // In production, AI would evaluate the response
  conversationScore.value += 10
  
  currentDialogueIndex.value++
  userResponse.value = ''
  showHints.value = false
  isEvaluatingResponse.value = false
  
  languagePracticeStore.addXP(20)
  
  // Check if conversation is complete
  if (currentScenario.value && currentDialogueIndex.value >= currentScenario.value.dialogues.length) {
    currentScenario.value.completed = true
    currentScenario.value.score = conversationScore.value
  }
}

async function playAudio(dialogue: any) {
  if (!speechSynthesis.isSupported.value) {
    alert('Text-to-speech is not supported in this browser.')
    return
  }

  try {
    const langCode = getLanguageCode(languagePracticeStore.languageProfile.targetLanguage)
    await speechSynthesis.speak(dialogue.text, {
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

function toggleVoiceRecording() {
  if (isListening.value) {
    stopVoiceRecording()
  } else {
    startVoiceRecording()
  }
}

function startVoiceRecording() {
  if (!speechRecognition.isSupported.value) {
    alert('Speech recognition is not supported in this browser.')
    return
  }

  isListening.value = true
  speechRecognition.reset()
  
  const langCode = getLanguageCode(languagePracticeStore.languageProfile.targetLanguage)
  speechRecognition.start(langCode)
}

async function stopVoiceRecording() {
  speechRecognition.stop()
  isListening.value = false

  // Wait for final transcript
  await new Promise(resolve => setTimeout(resolve, 500))
}

function useTranscript() {
  const transcript = speechRecognition.getFullTranscript().trim()
  if (transcript) {
    userResponse.value = transcript
    submitResponse()
  }
}

function clearTranscript() {
  speechRecognition.reset()
  userResponse.value = ''
}

// Watch for transcript changes to auto-submit if desired
// (optional: can be enabled for auto-submit on voice input)

function restartConversation() {
  currentDialogueIndex.value = 0
  userResponse.value = ''
  showHints.value = false
  conversationScore.value = 0
}

function backToScenarios() {
  selectedScenario.value = null
}

function handleBack() {
  languagePracticeStore.setStep('grammar-practice')
}

function handleContinue() {
  emit('complete')
}

// Cleanup on unmount
onUnmounted(() => {
  speechRecognition.abort()
  speechSynthesis.stop()
})
</script>

<style scoped>
.conversation-practice-form {
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

.scenario-selection h3 {
  color: white;
  font-size: 20px;
  margin-bottom: 20px;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.scenario-btn {
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

.scenario-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.scenario-btn.active {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.scenario-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.scenario-info {
  flex: 1;
}

.scenario-info strong {
  display: block;
  font-size: 16px;
  margin-bottom: 4px;
}

.scenario-info p {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.conversation-view {
  margin-bottom: 32px;
}

.conversation-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.conversation-header h3 {
  color: white;
  font-size: 22px;
  margin: 0;
  flex: 1;
}

.scenario-context {
  background: rgba(255, 255, 255, 0.1);
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 24px;
  color: white;
}

.dialogue-container {
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 24px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.dialogue-message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.dialogue-message.user {
  flex-direction: row-reverse;
}

.dialogue-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.dialogue-content {
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  padding: 12px 16px;
  border-radius: 12px;
}

.dialogue-message.user .dialogue-content {
  background: rgba(102, 126, 234, 0.3);
}

.dialogue-text {
  color: white;
  font-size: 16px;
  margin-bottom: 6px;
}

.dialogue-translation {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  font-style: italic;
}

.btn-audio-small {
  margin-top: 8px;
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
  cursor: pointer;
}

.user-response {
  background: rgba(255, 255, 255, 0.1);
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.response-prompt {
  color: white;
  margin-bottom: 12px;
}

.response-input {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.response-input .form-input {
  flex: 1;
}

.btn-send-response {
  padding: 12px 24px;
  background: rgba(102, 126, 234, 0.4);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
}

.response-hints {
  background: rgba(255, 193, 7, 0.2);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  color: white;
  font-size: 14px;
}

.btn-hint {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
}

.conversation-complete {
  text-align: center;
  padding: 32px;
  background: rgba(76, 175, 80, 0.2);
  border-radius: 12px;
  margin-bottom: 24px;
}

.conversation-complete h3 {
  color: white;
  font-size: 24px;
  margin-bottom: 12px;
}

.conversation-complete p {
  color: white;
  margin-bottom: 20px;
}

.key-phrases {
  background: rgba(255, 255, 255, 0.1);
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.key-phrases h4 {
  color: white;
  font-size: 18px;
  margin-bottom: 16px;
}

.phrases-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.phrase-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.phrase-item strong {
  color: white;
  font-size: 16px;
}

.phrase-item span {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.phrase-item em {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
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

.input-mode-toggle {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.mode-btn {
  flex: 1;
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.mode-btn.active {
  background: rgba(102, 126, 234, 0.4);
  border-color: rgba(102, 126, 234, 0.6);
}

.mode-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.voice-input {
  margin-bottom: 16px;
}

.voice-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-voice-record {
  width: 100%;
  padding: 20px;
  background: rgba(102, 126, 234, 0.4);
  color: white;
  border: 3px solid rgba(102, 126, 234, 0.6);
  border-radius: 16px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-voice-record:hover {
  background: rgba(102, 126, 234, 0.5);
}

.btn-voice-record.recording {
  background: rgba(255, 87, 34, 0.4);
  border-color: rgba(255, 87, 34, 0.6);
  animation: pulse-border 1s infinite;
}

.btn-voice-record:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.interim-transcript {
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  font-style: italic;
  text-align: center;
}

.final-transcript {
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: white;
}

.final-transcript p {
  margin-bottom: 12px;
  font-size: 16px;
}

.transcript-actions {
  display: flex;
  gap: 8px;
}

.btn-use-transcript {
  flex: 1;
  padding: 10px;
  background: rgba(76, 175, 80, 0.4);
  color: white;
  border: 1px solid rgba(76, 175, 80, 0.6);
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.btn-use-transcript:hover {
  background: rgba(76, 175, 80, 0.5);
}

.btn-clear-transcript {
  flex: 1;
  padding: 10px;
  background: rgba(255, 87, 34, 0.4);
  color: white;
  border: 1px solid rgba(255, 87, 34, 0.6);
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.btn-clear-transcript:hover {
  background: rgba(255, 87, 34, 0.5);
}

.error-message {
  background: rgba(255, 87, 34, 0.3);
  color: white;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
}

.browser-warning {
  padding: 16px;
  background: rgba(255, 193, 7, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 14px;
  text-align: center;
}

@keyframes pulse-border {
  0%, 100% { border-color: rgba(255, 87, 34, 0.6); }
  50% { border-color: rgba(255, 87, 34, 0.9); }
}

.generating-scenario {
  text-align: center;
  padding: 60px 20px;
}

.generating-scenario {
  text-align: center;
  padding: 80px 20px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.spinner-large {
  width: 60px;
  height: 60px;
  border: 5px solid rgba(255, 255, 255, 0.2);
  border-top-color: rgba(102, 126, 234, 1);
  border-right-color: rgba(102, 126, 234, 0.8);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 32px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-title {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.loading-dots {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 16px;
}

.loading-dots span {
  width: 10px;
  height: 10px;
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

.form-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

