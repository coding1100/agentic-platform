<template>
  <div class="tutor-container">
    <header class="tutor-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">&larr; Back</button>
        <div>
          <h1>{{ agent?.name || 'Tutor Tool' }}</h1>
          <p class="header-subtitle">AI-powered learning workspace with structured explanations, steps, and practice.</p>
        </div>
      </div>
      <button @click="handleLogout" class="btn-secondary">Logout</button>
    </header>

    <div class="tutor-content">
      <aside :class="['tutor-sidebar', { minimized: isChatMinimized }]">
        <div class="sidebar-header">
          <h2>Follow-Up Chat</h2>
          <button
            @click="toggleChatMinimize"
            class="btn-minimize"
            :title="isChatMinimized ? 'Expand Chat' : 'Minimize Chat'"
          >
            <span v-if="!isChatMinimized">-</span>
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
              <div class="sidebar-message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>

          <div v-if="pendingSidebarUser" class="sidebar-message user">
            <div class="sidebar-message-content">
              <div class="sidebar-message-text">{{ pendingSidebarUser.content }}</div>
              <div class="sidebar-message-time">{{ formatTime(pendingSidebarUser.created_at) }}</div>
            </div>
          </div>

          <div v-if="isStreamingSidebar" class="sidebar-message assistant">
            <div class="sidebar-message-content">
              <div class="sidebar-message-text" v-html="formatMessage(streamingAssistantText || 'Thinking...')"></div>
            </div>
          </div>
        </div>

        <div v-if="!isChatMinimized" class="sidebar-input">
          <form @submit.prevent="handleSidebarSend">
            <input
              v-model="sidebarInput"
              type="text"
              placeholder="Ask a follow-up question"
              :disabled="isSidebarBusy"
              class="sidebar-input-field"
            />
            <button type="submit" :disabled="!sidebarInput.trim() || isSidebarBusy" class="btn-send-small">
              Send
            </button>
          </form>
        </div>
      </aside>

      <button
        v-if="isChatMinimized"
        @click="toggleChatMinimize"
        class="chat-minimized-btn"
        title="Expand Chat"
      >
        Chat
      </button>

      <main :class="['tutor-main', { expanded: isChatMinimized }]">
        <div class="step-container">
          <section class="hero-card">
            <div>
              <span class="eyebrow">Tutor Tool</span>
              <h2>Structured AI learning for every session</h2>
              <p>
                Choose a subject, set the academic level, and use AI-powered actions for explanations,
                note-based study, and practice.
              </p>
            </div>
            <div class="feature-cloud">
              <span v-for="feature in featureBadges" :key="feature" class="feature-badge">{{ feature }}</span>
            </div>
          </section>

          <section v-if="tutorStore.currentStep === 'setup'" class="panel">
            <div class="panel-heading">
              <div>
                <h3>1. Setup Your Tutor Session</h3>
                <p>Start with the subject and academic level. Learner identity can be passed invisibly by the frontend when available.</p>
              </div>
            </div>

            <div class="field-group">
              <label for="subject-input">Subject</label>
              <input
                id="subject-input"
                v-model="subjectInput"
                type="text"
                placeholder="e.g., Calculus, Organic Chemistry, Political Theory"
                class="text-input"
              />
            </div>

            <div class="field-group">
              <label>Academic Level</label>
              <div class="choice-grid levels">
                <button
                  v-for="level in levelOptions"
                  :key="level.value"
                  type="button"
                  :class="['choice-card', { active: tutorStore.academicLevel === level.value }]"
                  @click="selectAcademicLevel(level.value)"
                >
                  <span class="choice-title">{{ level.label }}</span>
                  <span class="choice-description">{{ level.description }}</span>
                </button>
              </div>
            </div>

            <div class="panel-actions">
              <button class="btn-primary" :disabled="!canContinueSetup" @click="completeSetup">Continue</button>
            </div>
          </section>

          <section v-else-if="tutorStore.currentStep === 'action-selection'" class="panel">
            <div class="panel-heading split">
              <div>
                <h3>2. Choose Your Main Action</h3>
                <p>{{ tutorStore.subject }} at the {{ formatAcademicLevel(tutorStore.academicLevel) }} level is ready.</p>
              </div>
              <button class="btn-secondary-inline" type="button" @click="goToSetup">Edit setup</button>
            </div>

            <div class="choice-grid actions">
              <button
                v-for="action in actionOptions"
                :key="action.value"
                type="button"
                class="choice-card action-card"
                @click="selectAction(action.value)"
              >
                <span class="choice-title">{{ action.label }}</span>
                <span class="choice-description">{{ action.description }}</span>
              </button>
            </div>

            <section class="progress-panel compact">
              <div class="progress-card">
                <span class="progress-label">Sessions</span>
                <strong>{{ tutorStore.progress.sessions_completed }}</strong>
              </div>
              <div class="progress-card">
                <span class="progress-label">Practice Avg</span>
                <strong>{{ averageScoreLabel }}</strong>
              </div>
              <div class="progress-card wide">
                <span class="progress-label">Next Recommendation</span>
                <strong>{{ tutorStore.progress.next_recommended_action || 'Select an action to begin.' }}</strong>
              </div>
            </section>
          </section>

          <section v-else class="workspace-layout">
            <div class="workspace-main">
              <section class="panel">
                <div class="panel-heading split">
                  <div>
                    <h3>3. Results Workspace</h3>
                    <p>
                      {{ tutorStore.subject }} • {{ formatAcademicLevel(tutorStore.academicLevel) }} •
                      {{ currentActionLabel }}
                    </p>
                  </div>
                  <button class="btn-secondary-inline" type="button" @click="tutorStore.goToActionSelection()">
                    Change action
                  </button>
                </div>

                <div class="mode-section">
                  <label>Learning Mode</label>
                  <div class="mode-grid">
                    <button
                      v-for="mode in learningModes"
                      :key="mode.value"
                      type="button"
                      :class="['mode-pill', { active: tutorStore.selectedMode === mode.value }]"
                      @click="tutorStore.setSelectedMode(mode.value)"
                    >
                      <span>{{ mode.label }}</span>
                      <small>{{ mode.short }}</small>
                    </button>
                  </div>
                </div>

                <div v-if="tutorStore.selectedAction === 'ask_question'" class="composer-section">
                  <label for="question-prompt">Question or task</label>
                  <textarea
                    id="question-prompt"
                    v-model="questionPrompt"
                    class="text-area"
                    placeholder="Ask the AI tutor what you want explained, simplified, or broken into steps."
                  />
                </div>

                <div v-else-if="tutorStore.selectedAction === 'upload_notes'" class="composer-section">
                  <label for="notes-prompt">Optional instruction</label>
                  <textarea
                    id="notes-prompt"
                    v-model="notesPrompt"
                    class="text-area short"
                    placeholder="Tell the AI how to use these notes: summarize, simplify, prepare exam revision, etc."
                  />

                  <div class="grid-2">
                    <div class="field-group">
                      <label for="source-name">Source Name</label>
                      <input
                        id="source-name"
                        v-model="sourceName"
                        type="text"
                        placeholder="e.g., Week 4 lecture notes"
                        class="text-input"
                      />
                    </div>
                    <div class="field-group">
                      <label for="source-kind">Source Type</label>
                      <select id="source-kind" v-model="sourceKind" class="select-input">
                        <option value="notes">Notes</option>
                        <option value="pdf">PDF</option>
                        <option value="book">Book</option>
                      </select>
                    </div>
                  </div>

                  <div class="upload-panel">
                    <div>
                      <h4>Paste notes or extract from PDF</h4>
                      <p>Source text stays in the current session only. The workspace persists metadata, not the raw document.</p>
                    </div>
                    <div class="upload-actions">
                      <input
                        ref="pdfInputRef"
                        type="file"
                        accept="application/pdf"
                        class="file-input"
                        @change="handlePdfUpload"
                      />
                      <button type="button" class="btn-secondary-inline" :disabled="pdfLoading" @click="triggerPdfPicker">
                        <span v-if="pdfLoading">Extracting...</span>
                        <span v-else>Choose PDF</span>
                      </button>
                    </div>
                  </div>

                  <p v-if="pdfFileName" class="status-note">Loaded: {{ pdfFileName }}</p>
                  <p v-if="pdfError" class="error-text">{{ pdfError }}</p>
                  <p v-if="sourceTruncated" class="status-note">
                    The source text will be truncated to 20,000 characters when sent to the Tutor API.
                  </p>

                  <label for="source-text">Source Text</label>
                  <textarea
                    id="source-text"
                    v-model="sourceText"
                    class="text-area tall"
                    placeholder="Paste your notes here, or upload a PDF to populate this field."
                  />
                </div>

                <div v-else-if="tutorStore.selectedAction === 'practice'" class="composer-section">
                  <label for="practice-topic">Practice focus</label>
                  <textarea
                    id="practice-topic"
                    v-model="practicePrompt"
                    class="text-area short"
                    placeholder="Optional: specify the topic, chapter, or concept you want to practice."
                  />

                  <div class="grid-2">
                    <div class="field-group">
                      <label for="question-count">Question Count</label>
                      <select id="question-count" v-model.number="questionCount" class="select-input">
                        <option :value="3">3 Questions</option>
                        <option :value="5">5 Questions</option>
                        <option :value="7">7 Questions</option>
                      </select>
                    </div>
                    <div class="field-group">
                      <label for="practice-format">Practice Format</label>
                      <select id="practice-format" v-model="practiceFormat" class="select-input">
                        <option value="multiple_choice">Multiple Choice</option>
                        <option value="short_answer">Short Answer</option>
                        <option value="mixed">Mixed</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div class="panel-actions">
                  <button class="btn-primary" :disabled="!canRunTutorAction || tutorStore.loading" @click="runTutorAction">
                    <span v-if="tutorStore.loading">Generating...</span>
                    <span v-else>{{ currentRunLabel }}</span>
                  </button>
                </div>

                <p v-if="tutorStore.error" class="error-text">{{ tutorStore.error }}</p>
              </section>

              <section v-if="tutorStore.lastResult" class="results-stack">
                <section class="panel result-panel">
                  <div class="panel-heading">
                    <div>
                      <h3>AI Response</h3>
                      <p>Every Tutor action returns explanation, steps, and practice. Upload Notes also adds a summary.</p>
                    </div>
                  </div>

                  <div v-if="tutorStore.lastResult.summary" class="result-block">
                    <h4>Summary</h4>
                    <p>{{ tutorStore.lastResult.summary }}</p>
                  </div>

                  <div class="result-block">
                    <h4>Explanation</h4>
                    <p>{{ tutorStore.lastResult.explanation }}</p>
                  </div>

                  <div class="result-block">
                    <h4>Steps</h4>
                    <ol class="steps-list">
                      <li v-for="step in tutorStore.lastResult.steps" :key="step">{{ step }}</li>
                    </ol>
                  </div>

                  <div class="result-block">
                    <h4>Key Concepts</h4>
                    <div class="chip-group">
                      <span v-for="concept in tutorStore.lastResult.key_concepts" :key="concept" class="concept-chip">
                        {{ concept }}
                      </span>
                    </div>
                  </div>

                  <div class="result-block">
                    <h4>Suggested Next Actions</h4>
                    <ul class="plain-list">
                      <li v-for="item in tutorStore.lastResult.suggested_next_actions" :key="item">{{ item }}</li>
                    </ul>
                  </div>
                </section>

                <PracticeSetRenderer
                  :practice-set="tutorStore.lastResult.practice_set"
                  @completed="handlePracticeCompleted"
                />
              </section>
            </div>

            <aside class="workspace-sidebar">
              <section class="progress-panel">
                <div class="panel-heading">
                  <div>
                    <h3>Progress Tracking</h3>
                    <p>Persisted across refreshes for this Tutor workspace.</p>
                  </div>
                </div>

                <div class="progress-grid">
                  <div class="progress-card">
                    <span class="progress-label">Sessions</span>
                    <strong>{{ tutorStore.progress.sessions_completed }}</strong>
                  </div>
                  <div class="progress-card">
                    <span class="progress-label">Practice Attempts</span>
                    <strong>{{ tutorStore.progress.practice_sessions_attempted }}</strong>
                  </div>
                  <div class="progress-card">
                    <span class="progress-label">Sources Used</span>
                    <strong>{{ tutorStore.progress.source_sessions }}</strong>
                  </div>
                  <div class="progress-card">
                    <span class="progress-label">Average Score</span>
                    <strong>{{ averageScoreLabel }}</strong>
                  </div>
                </div>

                <div class="progress-section">
                  <h4>Weak Topics</h4>
                  <div class="chip-group">
                    <span
                      v-for="topic in tutorStore.progress.weak_topics"
                      :key="topic"
                      class="concept-chip weak"
                    >
                      {{ topic }}
                    </span>
                    <span v-if="tutorStore.progress.weak_topics.length === 0" class="empty-inline">
                      No weak topics recorded yet.
                    </span>
                  </div>
                </div>

                <div class="progress-section">
                  <h4>Recent Sources</h4>
                  <ul class="plain-list compact">
                    <li v-for="source in tutorStore.recentSources" :key="`${source.name}-${source.added_at}`">
                      {{ source.name }} • {{ source.kind }} • {{ source.char_count }} chars
                    </li>
                    <li v-if="tutorStore.recentSources.length === 0">No sources saved yet.</li>
                  </ul>
                </div>

                <div class="progress-section">
                  <h4>Recent Results</h4>
                  <ul class="plain-list compact">
                    <li v-for="result in tutorStore.recentResults" :key="`${result.title}-${result.created_at}`">
                      {{ result.title }}<span v-if="result.score !== null && result.score !== undefined"> • {{ result.score }}%</span>
                    </li>
                    <li v-if="tutorStore.recentResults.length === 0">No results yet.</li>
                  </ul>
                </div>
              </section>
            </aside>
          </section>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as pdfjsLib from 'pdfjs-dist'
import PracticeSetRenderer from '@/components/tutor/PracticeSetRenderer.vue'
import { useAgentsStore } from '@/stores/agents'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useTutorStore } from '@/stores/tutor'
import { tutorApi } from '@/services/api'
import { streamChatResponse } from '@/services/streaming'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import { debounce } from '@/utils/debounce'
import type { TutorAcademicLevel, TutorAction, TutorLearningMode, TutorPracticeFormat, TutorRecentSource } from '@/types'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

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
const isStreamingSidebar = ref(false)
const streamingAssistantText = ref('')
const pendingSidebarUser = ref<{ content: string; created_at: string } | null>(null)
const workspaceHydrated = ref(false)

const subjectInput = ref('')
const questionPrompt = ref('')
const notesPrompt = ref('')
const sourceText = ref('')
const sourceName = ref('')
const sourceKind = ref<'notes' | 'pdf' | 'book'>('notes')
const practicePrompt = ref('')
const questionCount = ref(5)
const practiceFormat = ref<TutorPracticeFormat>('multiple_choice')

const pdfInputRef = ref<HTMLInputElement | null>(null)
const pdfFileName = ref('')
const pdfLoading = ref(false)
const pdfError = ref<string | null>(null)

const levelOptions: Array<{ value: TutorAcademicLevel; label: string; description: string }> = [
  { value: 'high_school', label: 'High School', description: 'Foundational and school-level understanding.' },
  { value: 'college', label: 'College', description: 'Higher education depth with stronger terminology.' },
  { value: 'phd', label: 'PhD', description: 'Advanced academic rigor and research-level framing.' },
]

const actionOptions: Array<{ value: TutorAction; label: string; description: string }> = [
  { value: 'ask_question', label: 'Ask Question', description: 'Get a direct explanation, breakdown, or solution path.' },
  { value: 'upload_notes', label: 'Upload Notes', description: 'Summarize and study from pasted notes or PDF text.' },
  { value: 'practice', label: 'Practice', description: 'Generate a focused practice set and grade it locally.' },
]

const learningModes: Array<{ value: TutorLearningMode; label: string; short: string }> = [
  { value: 'personalized_learning', label: 'Personalized Learning', short: 'Adaptive explanation' },
  { value: 'assignment_assistant', label: 'Assignment Assistant', short: 'Work through tasks' },
  { value: 'practice_quiz_generator', label: 'Practice + Quiz Generator', short: 'Generate drills' },
  { value: 'concept_simplifier', label: 'Concept Simplifier', short: 'Plain-language support' },
  { value: 'notes_summary', label: 'Notes + Summary', short: 'Condense source material' },
  { value: 'exam_mode', label: 'Exam Mode', short: 'Timed-style revision' },
  { value: 'source_based_learning', label: 'Source-Based Learning', short: 'Stay grounded in notes' },
]

const featureBadges = [
  'Personalized Learning Mode',
  'Assignment Assistant',
  'Practice + Quiz Generator',
  'Concept Simplifier',
  'Notes + Summary',
  'Progress Tracking',
  'Exam Mode',
  'Source-Based Learning (Book / PDF)',
]

const agent = computed(() => agentsStore.selectedAgent)
const messages = computed(() => chatStore.messages)
const isSidebarBusy = computed(() => chatStore.loading || isStreamingSidebar.value)
const canContinueSetup = computed(() => subjectInput.value.trim().length > 0 && !!tutorStore.academicLevel)
const sourceTruncated = computed(() => sourceText.value.trim().length > 20000)
const averageScoreLabel = computed(() => {
  const value = tutorStore.progress.average_score
  return value === null || value === undefined ? 'N/A' : `${Math.round(value)}%`
})
const currentActionLabel = computed(() => {
  const action = actionOptions.find((item) => item.value === tutorStore.selectedAction)
  return action?.label || 'Tutor Action'
})
const currentRunLabel = computed(() => {
  switch (tutorStore.selectedAction) {
    case 'upload_notes':
      return 'Analyze Notes'
    case 'practice':
      return 'Generate Practice'
    default:
      return 'Generate Response'
  }
})
const canRunTutorAction = computed(() => {
  if (!tutorStore.subject || !tutorStore.academicLevel || !tutorStore.selectedAction || !tutorStore.selectedMode) {
    return false
  }
  if (tutorStore.selectedAction === 'ask_question') {
    return questionPrompt.value.trim().length > 0
  }
  if (tutorStore.selectedAction === 'upload_notes') {
    return sourceText.value.trim().length > 0
  }
  return questionCount.value > 0
})

const saveWorkspace = debounce(async () => {
  if (!workspaceHydrated.value) return
  try {
    await tutorApi.saveWorkspace(agentId, tutorStore.exportWorkspaceState())
  } catch (error) {
    console.error('Failed to save tutor workspace:', error)
  }
}, 800)

onMounted(async () => {
  await agentsStore.fetchAgent(agentId)
  await initializeConversation()
  await hydrateWorkspace()
  workspaceHydrated.value = true
  syncInjectedLearnerName()
})

onBeforeUnmount(() => {
  saveWorkspace.flush()
})

watch(
  [
    () => tutorStore.subject,
    () => tutorStore.academicLevel,
    () => tutorStore.learnerName,
    () => tutorStore.selectedAction,
    () => tutorStore.selectedMode,
    () => tutorStore.progress,
    () => tutorStore.recentSources,
    () => tutorStore.recentResults,
  ],
  () => {
    if (workspaceHydrated.value) {
      saveWorkspace()
    }
  },
  { deep: true }
)

watch(
  [messages, pendingSidebarUser, streamingAssistantText],
  () => {
    nextTick(() => {
      scrollSidebarToBottom()
    })
  },
  { deep: true }
)

function scrollSidebarToBottom() {
  if (sidebarMessagesRef.value) {
    sidebarMessagesRef.value.scrollTop = sidebarMessagesRef.value.scrollHeight
  }
}

async function initializeConversation() {
  const urlConversationId = route.query.conversation_id as string
  const existing = urlConversationId || tutorStore.conversationId

  if (existing) {
    await chatStore.fetchConversation(existing, true)
    tutorStore.setConversationId(existing)
    if (!urlConversationId) {
      router.replace({
        path: route.path,
        query: { ...route.query, conversation_id: existing },
      })
    }
    return
  }

  const result = await chatStore.createConversation(agentId)
  if (result.success && result.conversation) {
    await chatStore.fetchConversation(result.conversation.id, true)
    tutorStore.setConversationId(result.conversation.id)
    router.replace({
      path: route.path,
      query: { ...route.query, conversation_id: result.conversation.id },
    })
  }
}

async function hydrateWorkspace() {
  try {
    const workspace = await tutorApi.getWorkspace(agentId)
    tutorStore.setWorkspaceState(workspace)
    subjectInput.value = tutorStore.subject
  } catch (error) {
    console.error('Failed to hydrate tutor workspace:', error)
  }
}

function syncInjectedLearnerName() {
  const raw = route.query.learner_name
  if (typeof raw === 'string' && raw.trim()) {
    tutorStore.setLearnerName(raw)
  }
}

function selectAcademicLevel(level: TutorAcademicLevel) {
  tutorStore.academicLevel = level
}

function completeSetup() {
  if (!subjectInput.value.trim() || !tutorStore.academicLevel) return
  tutorStore.setSetup(subjectInput.value.trim(), tutorStore.academicLevel)
}

function goToSetup() {
  tutorStore.currentStep = 'setup'
}

function selectAction(action: TutorAction) {
  tutorStore.chooseAction(action)
  tutorStore.resetResult()

  if (action === 'upload_notes') {
    tutorStore.setSelectedMode('notes_summary')
  } else if (action === 'practice') {
    tutorStore.setSelectedMode('practice_quiz_generator')
  } else {
    tutorStore.setSelectedMode('personalized_learning')
  }
}

async function runTutorAction() {
  if (!tutorStore.selectedAction || !tutorStore.selectedMode || !tutorStore.academicLevel) return

  tutorStore.setLoading(true)
  tutorStore.setError(null)

  try {
    const sourcePayload = tutorStore.selectedAction === 'upload_notes'
      ? {
          source_text: sourceText.value.trim(),
          source_name: sourceName.value.trim() || `${tutorStore.subject} source`,
          source_kind: sourceKind.value,
          prompt: notesPrompt.value.trim() || null,
        }
      : {}

    const response = await tutorApi.execute(agentId, {
      action: tutorStore.selectedAction,
      learning_mode: tutorStore.selectedMode,
      subject: tutorStore.subject,
      academic_level: tutorStore.academicLevel,
      learner_name: tutorStore.learnerName,
      prompt:
        tutorStore.selectedAction === 'ask_question'
          ? questionPrompt.value.trim()
          : tutorStore.selectedAction === 'practice'
          ? (practicePrompt.value.trim() || `Generate practice for ${tutorStore.subject}.`)
          : undefined,
      question_count: tutorStore.selectedAction === 'practice' ? questionCount.value : 3,
      practice_format: tutorStore.selectedAction === 'practice' ? practiceFormat.value : undefined,
      ...sourcePayload,
    })

    tutorStore.applyExecuteResult(response)

    if (tutorStore.selectedAction === 'upload_notes') {
      const sourceMeta: TutorRecentSource = {
        name: sourceName.value.trim() || `${tutorStore.subject} source`,
        kind: sourceKind.value,
        char_count: Math.min(sourceText.value.trim().length, 20000),
        added_at: new Date().toISOString(),
      }
      tutorStore.addRecentSource(sourceMeta)
    }
  } catch (error: any) {
    tutorStore.setError(error.response?.data?.detail || 'Failed to run Tutor action.')
  } finally {
    tutorStore.setLoading(false)
  }
}

function handlePracticeCompleted(payload: { title: string; score: number; weakTopics: string[]; masteredTopics: string[] }) {
  tutorStore.recordPracticeResult(payload)
}

async function handleSidebarSend() {
  if (!sidebarInput.value.trim() || isSidebarBusy.value) return

  const message = sidebarInput.value.trim()
  sidebarInput.value = ''
  pendingSidebarUser.value = {
    content: message,
    created_at: new Date().toISOString(),
  }
  streamingAssistantText.value = ''
  isStreamingSidebar.value = true

  try {
    const stream = await streamChatResponse(
      agentId,
      message,
      tutorStore.conversationId || chatStore.activeConversationId || undefined,
    )

    for await (const chunk of stream) {
      streamingAssistantText.value += chunk
    }

    const conversationId = tutorStore.conversationId || chatStore.activeConversationId
    if (conversationId) {
      await chatStore.fetchConversation(conversationId, true)
    }
  } catch (error: any) {
    alert(error?.message || 'Streaming failed')
    sidebarInput.value = message
  } finally {
    pendingSidebarUser.value = null
    streamingAssistantText.value = ''
    isStreamingSidebar.value = false
  }
}

function triggerPdfPicker() {
  pdfInputRef.value?.click()
}

async function handlePdfUpload(event: Event) {
  const input = event.target as HTMLInputElement | null
  const file = input?.files?.[0]
  if (!file) return

  pdfError.value = null
  pdfFileName.value = file.name
  sourceKind.value = 'pdf'
  sourceName.value = file.name

  if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
    pdfError.value = 'Please choose a valid PDF file.'
    return
  }

  pdfLoading.value = true
  try {
    const arrayBuffer = await file.arrayBuffer()
    const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
    const pdf = await loadingTask.promise

    let extracted = ''
    for (let pageNum = 1; pageNum <= pdf.numPages; pageNum += 1) {
      const page = await pdf.getPage(pageNum)
      const content = await page.getTextContent()
      const pageText = content.items
        .map((item: any) => ('str' in item ? item.str : ''))
        .filter(Boolean)
        .join(' ')
      extracted += `${pageText}\n`
    }

    sourceText.value = extracted.trim()
  } catch (error) {
    console.error('Failed to extract Tutor PDF:', error)
    pdfError.value = 'Could not extract text from this PDF. Please paste the notes instead.'
  } finally {
    pdfLoading.value = false
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

function formatAcademicLevel(level: TutorAcademicLevel | null | undefined) {
  if (!level) return 'Not set'
  const match = levelOptions.find((item) => item.value === level)
  return match?.label || level.replace('_', ' ')
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
  min-height: 100vh;
  background:
    radial-gradient(circle at top left, rgba(255, 236, 179, 0.75), transparent 28%),
    radial-gradient(circle at bottom right, rgba(251, 191, 114, 0.55), transparent 26%),
    linear-gradient(160deg, #0f172a 0%, #12243b 46%, #16304d 100%);
}

.tutor-header {
  padding: 20px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(8, 15, 30, 0.72);
  backdrop-filter: blur(18px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  color: white;
  margin: 0;
  font-size: 28px;
}

.header-subtitle {
  margin: 4px 0 0 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 13px;
}

.btn-back,
.btn-secondary,
.btn-send-small,
.btn-minimize,
.chat-minimized-btn {
  border-radius: 999px;
  cursor: pointer;
}

.btn-back {
  padding: 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.btn-secondary {
  padding: 10px 18px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.tutor-content {
  display: flex;
  flex: 1;
  min-height: calc(100vh - 81px);
}

.tutor-sidebar {
  width: 330px;
  background: rgba(8, 15, 30, 0.84);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
}

.tutor-sidebar.minimized {
  display: none;
}

.sidebar-header {
  padding: 18px 18px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-header h2 {
  margin: 0;
  color: white;
  font-size: 18px;
}

.btn-minimize {
  width: 34px;
  height: 34px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.sidebar-messages {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
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
  max-width: 92%;
  padding: 12px 14px;
  border-radius: 14px;
  color: white;
  line-height: 1.6;
}

.sidebar-message.user .sidebar-message-content {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(29, 78, 216, 0.95));
}

.sidebar-message.assistant .sidebar-message-content {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-message-time {
  font-size: 11px;
  margin-top: 6px;
  opacity: 0.72;
}

.sidebar-input {
  padding: 14px 18px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.sidebar-input form {
  display: flex;
  gap: 10px;
}

.sidebar-input-field {
  flex: 1;
  padding: 11px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: white;
}

.sidebar-input-field::placeholder {
  color: rgba(255, 255, 255, 0.58);
}

.btn-send-small {
  padding: 10px 16px;
  border: none;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  font-weight: 700;
}

.btn-send-small:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-minimized-btn {
  position: fixed;
  left: 18px;
  bottom: 18px;
  border: 1px solid rgba(245, 158, 11, 0.5);
  background: #d97706;
  color: white;
  padding: 12px 18px;
}

.tutor-main {
  flex: 1;
  padding: 28px;
  overflow-y: auto;
}

.tutor-main.expanded {
  width: 100%;
}

.step-container {
  max-width: 1320px;
  margin: 0 auto;
}

.hero-card,
.panel,
.progress-panel,
.practice-panel {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.22);
}

.hero-card {
  padding: 26px;
  border-radius: 22px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 24px;
}

.eyebrow {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.16);
  color: #fde68a;
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.hero-card h2 {
  color: white;
  margin: 10px 0 10px 0;
  font-size: 34px;
  max-width: 640px;
}

.hero-card p {
  color: rgba(255, 255, 255, 0.78);
  margin: 0;
  max-width: 720px;
  line-height: 1.7;
}

.feature-cloud {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  max-width: 440px;
}

.feature-badge {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: white;
  font-size: 13px;
  white-space: nowrap;
}

.panel,
.progress-panel {
  border-radius: 22px;
  padding: 24px;
}

.panel-heading {
  margin-bottom: 18px;
}

.panel-heading.split {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.panel-heading h3 {
  color: white;
  margin: 0 0 8px 0;
  font-size: 24px;
}

.panel-heading p {
  margin: 0;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.6;
}

.field-group {
  margin-bottom: 18px;
}

.field-group label,
.mode-section label,
.composer-section label {
  display: block;
  color: white;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 700;
}

.text-input,
.select-input,
.text-area {
  width: 100%;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(8, 15, 30, 0.36);
  color: white;
  padding: 14px 16px;
  font-size: 15px;
}

.text-area {
  min-height: 124px;
  resize: vertical;
}

.text-area.short {
  min-height: 92px;
}

.text-area.tall {
  min-height: 240px;
}

.text-input::placeholder,
.text-area::placeholder {
  color: rgba(255, 255, 255, 0.54);
}

.choice-grid {
  display: grid;
  gap: 16px;
}

.choice-grid.levels {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.choice-grid.actions {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.choice-card {
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 18px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.06);
  color: white;
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.choice-card:hover,
.choice-card.active {
  transform: translateY(-2px);
  border-color: rgba(245, 158, 11, 0.55);
  background: rgba(245, 158, 11, 0.12);
}

.choice-title {
  display: block;
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 8px;
}

.choice-description {
  display: block;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.6;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.btn-primary,
.btn-secondary-inline {
  border-radius: 999px;
  cursor: pointer;
}

.btn-primary {
  border: none;
  padding: 12px 20px;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  font-size: 14px;
  font-weight: 800;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary-inline {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.08);
  color: white;
  padding: 10px 16px;
}

.workspace-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 24px;
}

.workspace-main {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.workspace-sidebar {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.mode-pill {
  padding: 14px 14px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.05);
  color: white;
  text-align: left;
  cursor: pointer;
}

.mode-pill span {
  display: block;
  font-weight: 700;
  margin-bottom: 4px;
}

.mode-pill small {
  display: block;
  color: rgba(255, 255, 255, 0.64);
}

.mode-pill.active {
  border-color: rgba(59, 130, 246, 0.55);
  background: rgba(59, 130, 246, 0.14);
}

.composer-section {
  margin-top: 8px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.upload-panel {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px dashed rgba(255, 255, 255, 0.18);
  margin: 14px 0 12px;
}

.upload-panel h4 {
  margin: 0 0 6px 0;
  color: white;
}

.upload-panel p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
  line-height: 1.6;
}

.upload-actions {
  display: flex;
  align-items: center;
}

.file-input {
  display: none;
}

.results-stack {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.result-panel .result-block + .result-block {
  margin-top: 18px;
}

.result-block h4,
.progress-section h4 {
  margin: 0 0 10px 0;
  color: white;
  font-size: 16px;
}

.result-block p,
.plain-list li,
.status-note,
.empty-inline {
  color: rgba(255, 255, 255, 0.78);
  line-height: 1.7;
}

.steps-list,
.plain-list {
  margin: 0;
  padding-left: 20px;
}

.plain-list.compact {
  padding-left: 18px;
}

.chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.concept-chip {
  padding: 7px 11px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 13px;
}

.concept-chip.weak {
  background: rgba(239, 68, 68, 0.16);
}

.progress-panel.compact {
  margin-top: 18px;
}

.progress-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.progress-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.progress-card.wide {
  grid-column: span 2;
}

.progress-label {
  display: block;
  color: rgba(255, 255, 255, 0.62);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.progress-card strong {
  display: block;
  margin-top: 6px;
  color: white;
  font-size: 24px;
}

.progress-section {
  margin-top: 18px;
}

.error-text {
  margin-top: 12px;
  color: #fecaca;
  background: rgba(127, 29, 29, 0.25);
  border: 1px solid rgba(248, 113, 113, 0.4);
  border-radius: 14px;
  padding: 12px 14px;
}

@media (max-width: 1180px) {
  .workspace-layout {
    grid-template-columns: 1fr;
  }

  .workspace-sidebar {
    order: -1;
  }
}

@media (max-width: 980px) {
  .tutor-content {
    flex-direction: column;
  }

  .tutor-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    max-height: 320px;
  }

  .choice-grid.levels,
  .choice-grid.actions,
  .mode-grid,
  .grid-2,
  .progress-grid {
    grid-template-columns: 1fr;
  }

  .hero-card {
    flex-direction: column;
  }

  .feature-cloud {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .tutor-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .tutor-main {
    padding: 18px 16px 30px;
  }

  .panel-heading.split {
    flex-direction: column;
  }

  .sidebar-input form,
  .upload-panel {
    flex-direction: column;
  }
}
</style>
