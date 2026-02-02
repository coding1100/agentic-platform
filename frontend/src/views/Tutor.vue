<template>
  <div class="tutor-container">
    <header class="tutor-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>{{ agent?.name || 'Personal Tutor' }}</h1>
      </div>
      <button @click="handleLogout" class="btn-secondary">Logout</button>
    </header>

    <div class="tutor-content">
      <!-- Sidebar Chat -->
      <aside :class="['tutor-sidebar', { minimized: isChatMinimized }]">
        <div class="sidebar-header">
          <h2>Chat with Tutor</h2>
          <button @click="toggleChatMinimize" class="btn-minimize" :title="isChatMinimized ? 'Expand Chat' : 'Minimize Chat'">
            <span v-if="!isChatMinimized">−</span>
            <span v-else>+</span>
          </button>
        </div>
        <div v-if="!isChatMinimized" class="sidebar-messages" ref="sidebarMessagesRef">
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

      <!-- Minimized Chat Button (when minimized) -->
      <button 
        v-if="isChatMinimized" 
        @click="toggleChatMinimize" 
        class="chat-minimized-btn"
        title="Expand Chat"
      >
        💬
      </button>

      <!-- Main Content Area -->
      <main :class="['tutor-main', { expanded: isChatMinimized }]">
        <!-- Child Details Step -->
        <div v-if="tutorStore.currentStep === 'child-details'" class="step-container">
          <ChildDetailsForm @complete="handleChildDetailsComplete" />
        </div>

        <!-- Subject Selection Step -->
        <div v-else-if="tutorStore.currentStep === 'subject-selection'" class="step-container">
          <SubjectSelectionForm @complete="handleSubjectComplete" />
        </div>

        <!-- Skill Assessment Step -->
        <div v-else-if="tutorStore.currentStep === 'skill-assessment'" class="step-container">
          <SkillAssessmentForm 
            v-if="tutorStore.selectedSubject"
            :subject="tutorStore.selectedSubject"
            @complete="handleSkillAssessmentComplete" 
          />
        </div>

        <!-- Focus Areas Step -->
        <div v-else-if="tutorStore.currentStep === 'focus-areas'" class="step-container">
          <FocusAreasForm @complete="handleFocusAreasComplete" />
        </div>

        <!-- Topic Menu Step -->
        <div v-else-if="tutorStore.currentStep === 'topic-menu'" class="step-container">
          <TopicMenu @select-topic="handleTopicSelect" />
        </div>

        <!-- Learning Step -->
        <div v-else-if="tutorStore.currentStep === 'learning'" class="step-container">
          <LearningArea
            :topic="tutorStore.selectedTopic"
            :child-name="tutorStore.childDetails.name"
            @quiz-complete="handleQuizComplete"
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
import { useTutorStore } from '@/stores/tutor'
import { usePersistedStore } from '@/composables/usePersistedStore'
import ChildDetailsForm from '@/components/tutor/ChildDetailsForm.vue'
import SubjectSelectionForm from '@/components/tutor/SubjectSelectionForm.vue'
import SkillAssessmentForm from '@/components/tutor/SkillAssessmentForm.vue'
import FocusAreasForm from '@/components/tutor/FocusAreasForm.vue'
import TopicMenu from '@/components/tutor/TopicMenu.vue'
import LearningArea from '@/components/tutor/LearningArea.vue'
import { sanitizeHtml } from '@/utils/sanitizeHtml'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const tutorStore = useTutorStore()

const agentId = route.params.agentId as string
const sidebarInput = ref('')
const sidebarMessagesRef = ref<HTMLElement | null>(null)
const isChatMinimized = ref(false)

const agent = computed(() => agentsStore.selectedAgent)
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.sending || chatStore.loading)

const { ready: tutorReady } = usePersistedStore(
  `tutor:${agentId}`,
  () => tutorStore.exportState(),
  (data) => tutorStore.importState(data),
  () => tutorStore.$state
)

onMounted(async () => {
  await tutorReady
  await agentsStore.fetchAgent(agentId)
  
  // Initialize conversation
  const conversationId = (route.query.conversation_id as string) || tutorStore.conversationId
  if (conversationId) {
    await chatStore.fetchConversation(conversationId)
    tutorStore.setConversationId(conversationId)
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
      tutorStore.setConversationId(result.conversation.id)
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
    tutorStore.conversationId || undefined
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

function handleChildDetailsComplete(details: { name: string }) {
  tutorStore.setChildDetails(details)
  tutorStore.setStep('subject-selection')
}

function handleSubjectComplete(subject: any) {
  tutorStore.setSelectedSubject(subject)
  tutorStore.setStep('skill-assessment')
}

function handleSkillAssessmentComplete(assessment: { proficiency: 'beginner' | 'intermediate' | 'advanced'; subject: any }) {
  tutorStore.setSkillAssessment(assessment)
  if (tutorStore.focusAreas.length === 0) {
    tutorStore.setStep('topic-menu')
  } else {
    tutorStore.setStep('focus-areas')
  }
}

function handleFocusAreasComplete() {
  tutorStore.setStep('topic-menu')
}

function handleTopicSelect(topic: any) {
  // Topic selection already moves to learning step in TopicMenu component
  // This is just a handler for the event
  tutorStore.setSelectedTopic(topic)
}

function handleQuizComplete(results: any) {
  tutorStore.setQuizResults(results)
  // Handle quiz completion - either show more questions or move to next topic
  if (results.percentage >= 100) {
    // Perfect score - provide further assessment
    setTimeout(() => {
      tutorStore.setStep('topic-menu')
    }, 2000)
  } else {
    // Focus on weak areas
    setTimeout(() => {
      tutorStore.setStep('learning')
    }, 2000)
  }
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
.tutor-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  position: relative;
}

.tutor-container::before {
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

.tutor-header {
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

.tutor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.tutor-sidebar {
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

.tutor-sidebar.minimized {
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
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
  -webkit-appearance: none;
  appearance: none;
}

.btn-minimize::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transform: translate(-50%, -50%);
  transition: width 0.4s ease, height 0.4s ease;
}

.btn-minimize:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.btn-minimize:hover::before {
  width: 100px;
  height: 100px;
}

.btn-minimize:active {
  transform: scale(0.95);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.btn-minimize:focus {
  outline: none;
  border: none;
}

.btn-minimize:focus-visible {
  outline: none;
  border: none;
}

.btn-minimize span {
  position: relative;
  z-index: 1;
  line-height: 1;
  transition: transform 0.3s ease;
}

.btn-minimize:hover span {
  transform: scale(1.1);
}

.sidebar-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.tutor-main {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  transition: width 0.3s ease;
}

.tutor-main.expanded {
  width: 100%;
}

.step-container {
  width: 100%;
  max-width: 900px;
}

@media (max-width: 768px) {
  .tutor-sidebar {
    width: 100%;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10;
    display: none;
  }

  .tutor-main {
    padding: 20px;
  }
}
</style>
