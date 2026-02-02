<template>
  <div class="language-practice-container">
    <header class="language-practice-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>{{ agent?.name || 'Language Practice Agent' }}</h1>
      </div>
      <div class="header-right">
        <!-- Progress Stats Badge -->
        <div v-if="languagePracticeStore.progressStats.xp > 0" class="progress-badge">
          <span class="level-badge">Level {{ languagePracticeStore.progressStats.level }}</span>
          <span class="xp-badge">{{ languagePracticeStore.progressStats.xp }} XP</span>
          <span class="streak-badge" v-if="languagePracticeStore.progressStats.currentStreak > 0">
            🔥 {{ languagePracticeStore.progressStats.currentStreak }} day streak
          </span>
        </div>
        <button @click="handleLogout" class="btn-secondary">Logout</button>
      </div>
    </header>

    <div class="language-practice-content">
      <!-- Sidebar Chat -->
      <aside :class="['language-practice-sidebar', { minimized: isChatMinimized }]">
        <div class="sidebar-header">
          <h2>Chat with Tutor</h2>
          <button @click="toggleChatMinimize" class="btn-minimize" :title="isChatMinimized ? 'Expand Chat' : 'Minimize Chat'">
            <span v-if="!isChatMinimized">−</span>
            <span v-else>+</span>
          </button>
        </div>
        <div v-if="!isChatMinimized" class="sidebar-messages" ref="sidebarMessagesRef">
          <!-- AI Suggestions Card -->
          <div class="ai-suggestions-card">
            <div class="suggestions-header">
              <span class="ai-icon">🤖</span>
              <h3>Learning Tips</h3>
            </div>
            <div class="suggestions-content">
              <div v-for="(suggestion, index) in aiSuggestions" :key="index" class="suggestion-item">
                <div class="suggestion-icon">{{ suggestion.icon }}</div>
                <div class="suggestion-text">
                  <strong>{{ suggestion.title }}</strong>
                  <p>{{ suggestion.text }}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['sidebar-message', message.role]"
          >
            <div class="sidebar-message-content">
              <div class="sidebar-message-text" v-html="formatMessage(message.content)"></div>
              <div class="sidebar-message-time">
                {{ formatTime(message.created_at) }}
              </div>
            </div>
          </div>
          <div v-if="isLoading" class="sidebar-message assistant">
            <div class="sidebar-message-content">
              <div class="sidebar-message-text typing">Thinking...</div>
            </div>
          </div>
        </div>
        <div v-if="!isChatMinimized" class="sidebar-input">
          <form @submit.prevent="handleSidebarSend">
            <input
              v-model="sidebarInput"
              type="text"
              placeholder="Type your message..."
              :disabled="isLoading"
              class="sidebar-input-field"
            />
            <button
              type="submit"
              :disabled="!sidebarInput.trim() || isLoading"
              class="btn-send-small"
            >
              Send
            </button>
          </form>
        </div>
      </aside>

      <!-- Minimized Chat Button -->
      <button 
        v-if="isChatMinimized" 
        @click="toggleChatMinimize" 
        class="chat-minimized-btn"
        title="Expand Chat"
      >
        💬
      </button>

      <!-- Main Content Area -->
      <main :class="['language-practice-main', { expanded: isChatMinimized }]">
        <!-- Progress Indicator -->
        <div class="progress-indicator">
          <div 
            v-for="(step, index) in steps" 
            :key="step.id"
            :class="['progress-step', { 
              active: languagePracticeStore.currentStep === step.id,
              completed: isStepCompleted(step.id)
            }]"
            @click="navigateToStep(step.id)"
          >
            <div class="progress-step-number">{{ index + 1 }}</div>
            <div class="progress-step-label">{{ step.label }}</div>
          </div>
        </div>

        <!-- Step Components -->
        <div class="step-container">
          <!-- Language Selection Step -->
          <LanguageSelectionForm 
            v-if="languagePracticeStore.currentStep === 'language-selection'"
            @complete="handleLanguageSelectionComplete" 
          />

          <!-- Placement Test Step -->
          <PlacementTestForm 
            v-else-if="languagePracticeStore.currentStep === 'placement-test'"
            @complete="handlePlacementTestComplete" 
          />

          <!-- Learning Goals Step -->
          <LearningGoalsForm 
            v-else-if="languagePracticeStore.currentStep === 'learning-goals'"
            @complete="handleLearningGoalsComplete" 
          />

          <!-- Vocabulary Builder Step -->
          <VocabularyBuilderForm 
            v-else-if="languagePracticeStore.currentStep === 'vocabulary-builder'"
            @complete="handleVocabularyComplete" 
          />

          <!-- Grammar Practice Step -->
          <GrammarPracticeForm 
            v-else-if="languagePracticeStore.currentStep === 'grammar-practice'"
            @complete="handleGrammarComplete" 
          />

          <!-- Conversation Practice Step -->
          <ConversationPracticeForm 
            v-else-if="languagePracticeStore.currentStep === 'conversation-practice'"
            @complete="handleConversationComplete" 
          />

          <!-- Pronunciation Practice Step -->
          <PronunciationPracticeForm 
            v-else-if="languagePracticeStore.currentStep === 'pronunciation-practice'"
            @complete="handlePronunciationComplete" 
          />

          <!-- Progress Dashboard Step -->
          <ProgressDashboardForm 
            v-else-if="languagePracticeStore.currentStep === 'progress-dashboard'"
            @complete="handleDashboardComplete" 
          />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'
import { useLanguagePracticeStore } from '@/stores/languagePractice'
import { usePersistedStore } from '@/composables/usePersistedStore'
import LanguageSelectionForm from '@/components/languagePractice/LanguageSelectionForm.vue'
import PlacementTestForm from '@/components/languagePractice/PlacementTestForm.vue'
import LearningGoalsForm from '@/components/languagePractice/LearningGoalsForm.vue'
import VocabularyBuilderForm from '@/components/languagePractice/VocabularyBuilderForm.vue'
import GrammarPracticeForm from '@/components/languagePractice/GrammarPracticeForm.vue'
import ConversationPracticeForm from '@/components/languagePractice/ConversationPracticeForm.vue'
import PronunciationPracticeForm from '@/components/languagePractice/PronunciationPracticeForm.vue'
import ProgressDashboardForm from '@/components/languagePractice/ProgressDashboardForm.vue'
import { sanitizeHtml } from '@/utils/sanitizeHtml'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const languagePracticeStore = useLanguagePracticeStore()

const agentId = route.params.agentId as string
const sidebarInput = ref('')
const sidebarMessagesRef = ref<HTMLElement | null>(null)
const isChatMinimized = ref(false)

const agent = computed(() => agentsStore.selectedAgent)
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.sending || chatStore.loading)

const { ready: languagePracticeReady } = usePersistedStore(
  `languagePractice:${agentId}`,
  () => languagePracticeStore.exportState(),
  (data) => languagePracticeStore.importState(data),
  () => languagePracticeStore.$state
)

const steps = [
  { id: 'language-selection', label: 'Language' },
  { id: 'placement-test', label: 'Assessment' },
  { id: 'learning-goals', label: 'Goals' },
  { id: 'vocabulary-builder', label: 'Vocabulary' },
  { id: 'grammar-practice', label: 'Grammar' },
  { id: 'conversation-practice', label: 'Conversation' },
  { id: 'pronunciation-practice', label: 'Pronunciation' },
  { id: 'progress-dashboard', label: 'Progress' }
]

function isStepCompleted(stepId: string): boolean {
  const stepIndex = steps.findIndex(s => s.id === stepId)
  const currentIndex = steps.findIndex(s => s.id === languagePracticeStore.currentStep)
  return stepIndex < currentIndex
}

function navigateToStep(stepId: string) {
  // Allow navigation to completed steps
  if (isStepCompleted(stepId) || stepId === languagePracticeStore.currentStep) {
    languagePracticeStore.setStep(stepId as any)
  }
}

// AI Suggestions based on current step
const aiSuggestions = computed(() => {
  const step = languagePracticeStore.currentStep
  const suggestions: Array<{ icon: string; title: string; text: string }> = []
  
  switch (step) {
    case 'language-selection':
      suggestions.push({
        icon: '🌍',
        title: 'Choose Your Language',
        text: 'Select a language you\'re passionate about. Motivation is key to consistent learning!'
      })
      break
    case 'placement-test':
      suggestions.push({
        icon: '📊',
        title: 'Honest Assessment',
        text: 'Answer honestly to get the most accurate level. This helps create the perfect learning path for you.'
      })
      break
    case 'vocabulary-builder':
      suggestions.push({
        icon: '📚',
        title: 'Spaced Repetition',
        text: 'Review words regularly. The system will remind you when it\'s time to review for maximum retention.'
      })
      break
    case 'grammar-practice':
      suggestions.push({
        icon: '📝',
        title: 'Practice Makes Perfect',
        text: 'Don\'t worry about mistakes. Each error is a learning opportunity!'
      })
      break
    case 'conversation-practice':
      suggestions.push({
        icon: '💬',
        title: 'Real-World Practice',
        text: 'Practice conversations in realistic scenarios. This builds confidence for real-life situations.'
      })
      break
    case 'pronunciation-practice':
      suggestions.push({
        icon: '🎤',
        title: 'Speak Out Loud',
        text: 'Practice pronunciation regularly. Even 5 minutes daily makes a huge difference!'
      })
      break
  }
  
  return suggestions
})

onMounted(async () => {
  await languagePracticeReady
  await agentsStore.fetchAgent(agentId)
  
  // Initialize conversation
  const conversationId = (route.query.conversation_id as string) || languagePracticeStore.conversationId
  if (conversationId) {
    await chatStore.fetchConversation(conversationId)
    languagePracticeStore.setConversationId(conversationId)
    if (!route.query.conversation_id) {
      router.replace({
        path: route.path,
        query: { ...route.query, conversation_id: conversationId }
      })
    }
  } else {
    const result = await chatStore.createConversation(agentId)
    if (result.success && result.conversation) {
      await chatStore.fetchConversation(result.conversation.id)
      languagePracticeStore.setConversationId(result.conversation.id)
      router.replace({ 
        path: route.path, 
        query: { ...route.query, conversation_id: result.conversation.id } 
      })
    }
  }
})

watch(messages, () => {
  nextTick(() => {
    scrollSidebarToBottom()
  })
})

function scrollSidebarToBottom() {
  if (sidebarMessagesRef.value) {
    sidebarMessagesRef.value.scrollTop = sidebarMessagesRef.value.scrollHeight
  }
}

async function handleSidebarSend() {
  if (!sidebarInput.value.trim() || isLoading.value) return

  const message = sidebarInput.value.trim()
  sidebarInput.value = ''

  const result = await chatStore.sendMessage(
    agentId,
    message,
    languagePracticeStore.conversationId || undefined
  )

  if (!result.success) {
    alert(result.error || 'Failed to send message')
    sidebarInput.value = message
  }
}

function formatTime(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatMessage(content: string): string {
  const formatted = content
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
  return sanitizeHtml(formatted)
}

function handleLanguageSelectionComplete(profile: any) {
  languagePracticeStore.setLanguageProfile(profile)
  languagePracticeStore.setStep('placement-test')
}

function handlePlacementTestComplete(level: any) {
  languagePracticeStore.setLanguageProfile({
    ...languagePracticeStore.languageProfile,
    proficiencyLevel: level.proficiencyLevel,
    cefrLevel: level.cefrLevel
  })
  languagePracticeStore.setStep('learning-goals')
}

function handleLearningGoalsComplete(goals: any) {
  languagePracticeStore.setLearningGoals(goals)
  languagePracticeStore.setStep('vocabulary-builder')
}

function handleVocabularyComplete() {
  languagePracticeStore.setStep('grammar-practice')
}

function handleGrammarComplete() {
  languagePracticeStore.setStep('conversation-practice')
}

function handleConversationComplete() {
  languagePracticeStore.setStep('pronunciation-practice')
}

function handlePronunciationComplete() {
  languagePracticeStore.setStep('progress-dashboard')
}

function handleDashboardComplete() {
  // Could cycle back to vocabulary or show completion
  languagePracticeStore.setStep('vocabulary-builder')
}

function goBack() {
  router.push('/dashboard')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function toggleChatMinimize() {
  isChatMinimized.value = !isChatMinimized.value
}
</script>

<style scoped>
.language-practice-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  position: relative;
}

.language-practice-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.3) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.language-practice-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.progress-badge {
  display: flex;
  align-items: center;
  gap: 12px;
}

.level-badge, .xp-badge, .streak-badge {
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

.btn-back {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 16px;
  cursor: pointer;
  padding: 10px 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateX(-4px);
}

h1 {
  color: white;
  font-size: 24px;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.btn-secondary {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.language-practice-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.language-practice-sidebar {
  width: 350px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease, width 0.3s ease;
  overflow: hidden;
}

.language-practice-sidebar.minimized {
  width: 0;
  transform: translateX(-100%);
  border: none;
}

.chat-minimized-btn {
  position: fixed;
  left: 20px;
  bottom: 20px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.chat-minimized-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h2 {
  color: white;
  font-size: 18px;
  margin: 0;
  font-weight: 600;
  flex: 1;
}

.btn-minimize {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: none;
  outline: none;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-minimize:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
}

.sidebar-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-suggestions-card {
  background: rgba(102, 126, 234, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.suggestions-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.ai-icon {
  font-size: 20px;
}

.suggestions-header h3 {
  color: white;
  font-size: 14px;
  margin: 0;
  font-weight: 600;
}

.suggestions-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.suggestion-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.suggestion-text {
  flex: 1;
}

.suggestion-text strong {
  color: white;
  font-size: 12px;
  display: block;
  margin-bottom: 4px;
}

.suggestion-text p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 11px;
  margin: 0;
  line-height: 1.4;
}

.sidebar-message {
  display: flex;
}

.sidebar-message.user {
  justify-content: flex-end;
}

.sidebar-message.assistant {
  justify-content: flex-start;
}

.sidebar-message-content {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.sidebar-message.user .sidebar-message-content {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.sidebar-message.assistant .sidebar-message-content {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-message-text {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 4px;
}

.sidebar-message-time {
  font-size: 11px;
  opacity: 0.7;
  margin-top: 4px;
}

.typing {
  font-style: italic;
  opacity: 0.7;
}

.sidebar-input {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-input form {
  display: flex;
  gap: 8px;
}

.sidebar-input-field {
  flex: 1;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  font-size: 14px;
  color: white;
}

.sidebar-input-field::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.sidebar-input-field:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.25);
}

.btn-send-small {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-send-small:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
}

.btn-send-small:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.language-practice-main {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: width 0.3s ease;
}

.language-practice-main.expanded {
  width: 100%;
}

.progress-indicator {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.5;
  transition: opacity 0.3s ease;
  cursor: pointer;
}

.progress-step.active {
  opacity: 1;
}

.progress-step.completed {
  opacity: 0.8;
}

.progress-step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.3s ease;
}

.progress-step.active .progress-step-number {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.1);
}

.progress-step.completed .progress-step-number {
  background: rgba(76, 175, 80, 0.3);
  border-color: rgba(76, 175, 80, 0.5);
}

.progress-step-label {
  color: white;
  font-size: 11px;
  font-weight: 500;
  text-align: center;
  max-width: 80px;
}

.step-container {
  width: 100%;
  max-width: 900px;
}

@media (max-width: 768px) {
  .language-practice-sidebar {
    width: 100%;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10;
    display: none;
  }

  .language-practice-main {
    padding: 20px;
  }

  .progress-indicator {
    gap: 8px;
  }

  .progress-step-label {
    font-size: 10px;
  }
  
  .header-right {
    flex-direction: column;
    gap: 8px;
  }
  
  .progress-badge {
    flex-direction: column;
    gap: 6px;
  }
}
</style>





