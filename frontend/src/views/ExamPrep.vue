<template>
  <div class="exam-prep-container">
    <header class="exam-prep-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>{{ agent?.name || 'Exam Prep Agent' }}</h1>
      </div>
      <div class="header-right">
        <div v-if="examPrepStore.examInfo.examDate" class="exam-date-badge">
          <span>📅 Exam: {{ formatDate(examPrepStore.examInfo.examDate) }}</span>
          <span v-if="daysRemaining >= 0" class="days-remaining">
            {{ daysRemaining }} days left
          </span>
        </div>
        <button @click="handleLogout" class="btn-secondary">Logout</button>
      </div>
    </header>

    <div class="exam-prep-content">
      <!-- Progress Indicator -->
      <div class="progress-indicator">
        <div 
          v-for="(step, index) in steps" 
          :key="step.id"
          :class="['progress-step', { 
            active: examPrepStore.currentStep === step.id,
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
        <!-- Exam Setup Step -->
        <ExamSetupForm 
          v-if="examPrepStore.currentStep === 'exam-setup'"
          @complete="handleExamSetupComplete" 
        />

        <!-- Study Schedule Step -->
        <StudyScheduleView 
          v-else-if="examPrepStore.currentStep === 'study-schedule'"
          @complete="handleScheduleComplete"
          @start-practice="handleStartPractice"
        />

        <!-- Practice Exam Step -->
        <PracticeExamView 
          v-else-if="examPrepStore.currentStep === 'practice-exam'"
          @complete="handlePracticeExamComplete"
        />

        <!-- Progress Dashboard Step -->
        <ProgressDashboard 
          v-else-if="examPrepStore.currentStep === 'progress-dashboard'"
          @view-weak-areas="handleViewWeakAreas"
          @review-topic="handleReviewTopic"
          @take-practice="handleStartPractice"
        />

        <!-- Weak Areas Step -->
        <WeakAreaAnalysis 
          v-else-if="examPrepStore.currentStep === 'weak-areas'"
          @complete="handleWeakAreasComplete"
          @review-topic="handleReviewTopic"
        />

        <!-- Topic Review Step -->
        <TopicReview 
          v-else-if="examPrepStore.currentStep === 'topic-review'"
          :topic="selectedTopic"
          @complete="handleTopicReviewComplete"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'
import { useExamPrepStore } from '@/stores/examPrep'
import { usePersistedStore } from '@/composables/usePersistedStore'
import ExamSetupForm from '@/components/examPrep/ExamSetupForm.vue'
import StudyScheduleView from '@/components/examPrep/StudyScheduleView.vue'
import PracticeExamView from '@/components/examPrep/PracticeExamView.vue'
import ProgressDashboard from '@/components/examPrep/ProgressDashboard.vue'
import WeakAreaAnalysis from '@/components/examPrep/WeakAreaAnalysis.vue'
import TopicReview from '@/components/examPrep/TopicReview.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const examPrepStore = useExamPrepStore()
const selectedTopic = ref('')

const agentId = route.params.agentId as string
const agent = computed(() => agentsStore.selectedAgent)

const { ready: examPrepReady } = usePersistedStore(
  `examPrep:${agentId}`,
  () => examPrepStore.exportState(),
  (data) => examPrepStore.importState(data),
  () => examPrepStore.$state
)

const steps = [
  { id: 'exam-setup', label: 'Setup' },
  { id: 'study-schedule', label: 'Schedule' },
  { id: 'practice-exam', label: 'Practice' },
  { id: 'progress-dashboard', label: 'Progress' },
  { id: 'weak-areas', label: 'Weak Areas' },
  { id: 'topic-review', label: 'Review' }
]

const daysRemaining = computed(() => {
  if (!examPrepStore.examInfo.examDate) return null
  const examDate = new Date(examPrepStore.examInfo.examDate)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  examDate.setHours(0, 0, 0, 0)
  const diff = Math.ceil((examDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  return diff
})

function isStepCompleted(stepId: string): boolean {
  const stepIndex = steps.findIndex(s => s.id === stepId)
  const currentIndex = steps.findIndex(s => s.id === examPrepStore.currentStep)
  return stepIndex < currentIndex
}

function navigateToStep(stepId: string) {
  if (isStepCompleted(stepId) || stepId === examPrepStore.currentStep) {
    examPrepStore.setStep(stepId as any)
  }
}

function formatDate(dateString: string | null): string {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(async () => {
  await examPrepReady
  await agentsStore.fetchAgent(agentId)
  
  // Initialize conversation if needed
  if (!examPrepStore.conversationId) {
    const result = await chatStore.createConversation(agentId, 'Exam Prep Session')
    if (result.success && result.conversation) {
      examPrepStore.setConversationId(result.conversation.id)
    }
  }

  // If exam info is already set, go to schedule step
  if (examPrepStore.examInfo.examType && examPrepStore.currentStep === 'exam-setup') {
    examPrepStore.setStep('study-schedule')
  }
})

function handleExamSetupComplete() {
  examPrepStore.setStep('study-schedule')
}

function handleScheduleComplete() {
  examPrepStore.setStep('progress-dashboard')
}

function handleStartPractice() {
  examPrepStore.setStep('practice-exam')
}

function handlePracticeExamComplete() {
  examPrepStore.setStep('progress-dashboard')
}

function handleViewResults() {
  // This is now handled directly in PracticeExamView by redirecting to progress-dashboard
  examPrepStore.setStep('progress-dashboard')
}

function handleViewWeakAreas() {
  examPrepStore.setStep('weak-areas')
}

function handleReviewTopic(topic: string) {
  selectedTopic.value = topic
  examPrepStore.setStep('topic-review')
}

function handleWeakAreasComplete() {
  examPrepStore.setStep('progress-dashboard')
}

function handleTopicReviewComplete() {
  examPrepStore.setStep('progress-dashboard')
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
.exam-prep-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  position: relative;
}

.exam-prep-header {
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

.exam-date-badge {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.days-remaining {
  font-size: 12px;
  opacity: 0.9;
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

.exam-prep-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
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
  .exam-prep-header {
    padding: 16px;
    flex-direction: column;
    gap: 12px;
  }

  .header-left,
  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .exam-prep-content {
    padding: 20px;
  }

  .progress-indicator {
    gap: 8px;
  }

  .progress-step-label {
    font-size: 10px;
  }
}
</style>

