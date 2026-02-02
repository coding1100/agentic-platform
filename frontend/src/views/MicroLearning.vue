<template>
  <div class="micro-learning-container">
    <header class="ml-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>{{ agent?.name || 'Micro-Learning Agent' }}</h1>
      </div>
      <div class="header-right">
        <div class="streak-badge" v-if="microLearningStore.progress.currentStreak > 0">
          🔥 {{ microLearningStore.progress.currentStreak }} day streak
        </div>
        <button @click="handleLogout" class="btn-secondary">Logout</button>
      </div>
    </header>

    <div class="ml-content">
      <!-- Onboarding Flow -->
      <OnboardingFlow 
        v-if="microLearningStore.currentStep === 'onboarding'"
        @complete="handleOnboardingComplete"
      />

      <!-- Dashboard -->
      <ProgressDashboard 
        v-else-if="microLearningStore.currentStep === 'dashboard'"
        @start-lesson="handleStartLesson"
        @review-flashcards="handleReviewFlashcards"
        @view-progress="handleViewProgress"
      />

      <!-- Daily Lesson -->
      <DailyLesson 
        v-else-if="microLearningStore.currentStep === 'lesson'"
        @complete="handleLessonComplete"
        @request-quiz="handleRequestQuiz"
      />

      <!-- Quiz -->
      <MicroQuiz 
        v-else-if="microLearningStore.currentStep === 'quiz'"
        @complete="handleQuizComplete"
      />

      <!-- Flashcards -->
      <FlashcardSystem 
        v-else-if="microLearningStore.currentStep === 'flashcards'"
        @complete="handleFlashcardsComplete"
      />

      <!-- Review Session -->
      <ReviewSession 
        v-else-if="microLearningStore.currentStep === 'review'"
        @complete="handleReviewComplete"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'
import { useMicroLearningStore } from '@/stores/microLearning'
import { usePersistedStore } from '@/composables/usePersistedStore'
import OnboardingFlow from '@/components/microLearning/OnboardingFlow.vue'
import ProgressDashboard from '@/components/microLearning/ProgressDashboard.vue'
import DailyLesson from '@/components/microLearning/DailyLesson.vue'
import MicroQuiz from '@/components/microLearning/MicroQuiz.vue'
import FlashcardSystem from '@/components/microLearning/FlashcardSystem.vue'
import ReviewSession from '@/components/microLearning/ReviewSession.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const microLearningStore = useMicroLearningStore()

const agentId = route.params.agentId as string
const agent = computed(() => agentsStore.selectedAgent)

const { ready: microLearningReady } = usePersistedStore(
  `microLearning:${agentId}`,
  () => microLearningStore.exportState(),
  (data) => microLearningStore.importState(data),
  () => microLearningStore.$state
)

onMounted(async () => {
  await microLearningReady
  await agentsStore.fetchAgent(agentId)
  
  // Respect persisted step unless onboarding is incomplete or still on onboarding
  if (!microLearningStore.isOnboardingComplete) {
    microLearningStore.setCurrentStep('onboarding')
  } else if (microLearningStore.currentStep === 'onboarding') {
    microLearningStore.setCurrentStep('dashboard')
  }

  // Load or create conversation
  if (!microLearningStore.conversationId) {
    await initializeConversation()
  }
})

async function initializeConversation() {
  try {
    const result = await chatStore.createConversation(agentId, 'Micro-Learning Session')
    if (result.success && result.conversation) {
      microLearningStore.setConversationId(result.conversation.id)
    }
  } catch (error) {
    console.error('Error initializing conversation:', error)
  }
}

function handleOnboardingComplete() {
  microLearningStore.setCurrentStep('dashboard')
}

function handleStartLesson() {
  microLearningStore.setCurrentStep('lesson')
}

function handleRequestQuiz() {
  microLearningStore.setCurrentStep('quiz')
}

function handleLessonComplete() {
  microLearningStore.setCurrentStep('dashboard')
}

function handleQuizComplete() {
  microLearningStore.setCurrentStep('dashboard')
}

function handleReviewFlashcards() {
  microLearningStore.setCurrentStep('flashcards')
}

function handleFlashcardsComplete() {
  microLearningStore.setCurrentStep('dashboard')
}

function handleViewProgress() {
  // Already on dashboard
  microLearningStore.setCurrentStep('dashboard')
}

function handleReviewComplete() {
  microLearningStore.setCurrentStep('dashboard')
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
.micro-learning-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
}

.ml-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.streak-badge {
  background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
}

.btn-back {
  background: transparent;
  border: none;
  color: #667eea;
  font-size: 1rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.2s;
}

.btn-back:hover {
  background: rgba(102, 126, 234, 0.1);
}

.btn-secondary {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #5568d3;
}

.ml-content {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
}

h1 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
}

@media (max-width: 768px) {
  .ml-header {
    padding: 1rem;
    flex-direction: column;
    gap: 1rem;
  }

  .header-left,
  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .ml-content {
    padding: 1rem;
  }
}
</style>









