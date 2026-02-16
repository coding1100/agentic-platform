<template>
  <Tutor v-if="isPersonalTutor" />
  <CourseCreation v-else-if="isCourseCreationAgent" />
  <LanguagePractice v-else-if="isLanguagePracticeAgent" />
  <MicroLearning v-else-if="isMicroLearningAgent" />
  <ExamPrep v-else-if="isExamPrepAgent" />
  <ResumeReview v-else-if="isResumeReviewAgent" />
  <CareerCoach v-else-if="isCareerCoachAgent" />
  <SkillGap v-else-if="isSkillGapAgent" />
  <div v-else class="chat-container">
    <header class="chat-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>{{ agent?.name || 'Chat' }}</h1>
      </div>
      <button @click="handleLogout" class="btn-secondary">Logout</button>
    </header>

    <div class="chat-content">
      <div v-if="chatStore.loading && messages.length === 0" class="loading">
        Loading conversation...
      </div>

      <div v-else class="chat-messages" ref="messagesContainer">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['message', message.role]"
        >
          <div class="message-content">
            <QuizRenderer
              v-if="isQuizMessage(message.content)"
              :content="message.content"
            />
            <div v-else class="message-text" v-html="formatMessage(message.content)"></div>
            <div class="message-time">
              {{ formatTime(message.created_at) }}
            </div>
          </div>
        </div>

        <div v-if="chatStore.sending" class="message assistant">
          <div class="message-content">
            <div class="message-text typing">Thinking...</div>
          </div>
        </div>
      </div>

      <div class="chat-input-container">
        <form @submit.prevent="handleSendMessage" class="chat-input-form">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="Type your message..."
            :disabled="chatStore.sending"
            class="chat-input"
          />
          <button
            type="submit"
            :disabled="!inputMessage.trim() || chatStore.sending"
            class="btn-send"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'
import { isQuizContent } from '@/utils/quizParser'
import QuizRenderer from '@/components/QuizRenderer.vue'
import Tutor from '@/views/Tutor.vue'
import CourseCreation from '@/views/CourseCreation.vue'
import LanguagePractice from '@/views/LanguagePractice.vue'
import MicroLearning from '@/views/MicroLearning.vue'
import ExamPrep from '@/views/ExamPrep.vue'
import ResumeReview from '@/views/ResumeReview.vue'
import CareerCoach from '@/views/CareerCoach.vue'
import SkillGap from '@/views/SkillGap.vue'
import { sanitizeHtml } from '@/utils/sanitizeHtml'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()

const agentId = route.params.agentId as string
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const agent = computed(() => agentsStore.selectedAgent)
const messages = computed(() => chatStore.messages)
const isPersonalTutor = computed(() => {
  const a = agent.value
  return a?.slug === 'education.personal_tutor' || 
         a?.name?.toLowerCase().includes('personal tutor')
})

const isCourseCreationAgent = computed(() => {
  const a = agent.value
  return a?.slug === 'education.course_creation_agent' || 
         a?.name?.toLowerCase().includes('course creation')
})

const isLanguagePracticeAgent = computed(() => {
  const a = agent.value
  return a?.slug === 'education.language_practice_agent' || 
         a?.name?.toLowerCase().includes('language practice')
})

const isMicroLearningAgent = computed(() => {
  const a = agent.value
  return a?.slug === 'education.micro_learning_agent' || 
         a?.name?.toLowerCase().includes('micro-learning') ||
         a?.name?.toLowerCase().includes('micro learning')
})

const isExamPrepAgent = computed(() => {
  const a = agent.value
  return a?.slug === 'education.exam_prep_agent' || 
         a?.name?.toLowerCase().includes('exam prep') ||
         a?.name?.toLowerCase().includes('exam preparation')
})

const isResumeReviewAgent = computed(() => {
  const a = agent.value
  return a?.slug === 'career.resume_review_agent' || 
         a?.name?.toLowerCase().includes('resume review') ||
         a?.name?.toLowerCase().includes('ats resume')
})

const isCareerCoachAgent = computed(() => {
  const a = agent.value
  return a?.slug === 'career.career_coach_agent' ||
         a?.name?.toLowerCase().includes('career coach')
})

const isSkillGapAgent = computed(() => {
  const a = agent.value
  return a?.slug === 'career.skill_gap_agent' ||
         a?.name?.toLowerCase().includes('skill gap')
})

onMounted(async () => {
  await agentsStore.fetchAgent(agentId)
  
  // Try to load existing conversation or create new one with greeting
  const conversationId = route.query.conversation_id as string
  if (conversationId) {
    await chatStore.fetchConversation(conversationId)
  } else {
    // No conversation ID - create a new conversation which will include the greeting message
    const result = await chatStore.createConversation(agentId)
    if (result.success && result.conversation) {
      // Fetch the conversation to get the greeting message
      await chatStore.fetchConversation(result.conversation.id)
      // Update URL to include conversation_id
      router.replace({ 
        path: route.path, 
        query: { ...route.query, conversation_id: result.conversation.id } 
      })
    }
  }
})

watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function handleSendMessage() {
  if (!inputMessage.value.trim() || chatStore.sending) return

  const message = inputMessage.value.trim()
  inputMessage.value = ''

  const result = await chatStore.sendMessage(
    agentId,
    message,
    chatStore.activeConversationId || undefined
  )

  if (!result.success) {
    alert(result.error || 'Failed to send message')
    inputMessage.value = message // Restore message on error
  }
}

function formatTime(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function isQuizMessage(content: string): boolean {
  return isQuizContent(content)
}

function formatMessage(content: string): string {
  // Basic markdown-like formatting
  const formatted = content
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
  return sanitizeHtml(formatted)
}

function goBack() {
  router.push('/dashboard')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  position: relative;
}

.chat-container::before {
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

.chat-header {
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

.chat-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  scroll-behavior: smooth;
}

.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 10px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}

.message {
  display: flex;
  margin-bottom: 8px;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 16px 20px;
  border-radius: 20px;
  word-wrap: break-word;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.message.user .message-content {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-bottom-right-radius: 6px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.message.assistant .message-content {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-bottom-left-radius: 6px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.message-text {
  margin-bottom: 4px;
  line-height: 1.5;
}

.message-content .quiz-container {
  width: 100%;
  max-width: 100%;
}

.message-time {
  font-size: 11px;
  opacity: 0.8;
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.9);
}

.message.user .message-time {
  text-align: right;
}

.typing {
  font-style: italic;
  opacity: 0.7;
}

.chat-input-container {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 20px 32px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 1;
}

.chat-input-form {
  display: flex;
  gap: 12px;
  max-width: 1200px;
  margin: 0 auto;
}

.chat-input {
  flex: 1;
  padding: 14px 20px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 25px;
  font-size: 16px;
  color: white;
  transition: all 0.3s ease;
}

.chat-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.chat-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-send {
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 25px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.btn-send:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  text-align: center;
  padding: 60px;
  color: white;
  font-size: 18px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

@media (max-width: 768px) {
  .message-content {
    max-width: 85%;
  }
}
</style>
