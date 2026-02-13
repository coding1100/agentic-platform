<template>
  <div class="resume-review-container">
    <header class="resume-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">&larr; Back</button>
        <h1>{{ agent?.name || 'Resume Review Agent' }}</h1>
      </div>
      <button @click="handleLogout" class="btn-secondary">Logout</button>
    </header>

    <div class="resume-content">
      <!-- Sidebar Chat (for optional follow-up questions) -->
      <aside :class="['resume-sidebar', { minimized: isChatMinimized }]">
        <div class="sidebar-header">
          <h2>Chat with Agent</h2>
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
              placeholder="Ask follow-up questions..."
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
        Chat
      </button>

      <!-- Main Resume Review Panel -->
      <main :class="['resume-main', { expanded: isChatMinimized }]">
        <section class="input-section">
          <h2>1. Paste Your Resume</h2>
          <p class="section-help">
            Paste your full resume text or upload a PDF. Avoid screenshots or images; plain text works best for ATS-style analysis.
          </p>
          <textarea
            v-model="resumeStore.resumeText"
            class="input-textarea resume-textarea"
            placeholder="Paste your resume here..."
          />
          <div class="upload-panel">
            <div class="upload-copy">
              <h3>Upload PDF (optional)</h3>
              <p>We will extract the text and populate the resume field above.</p>
            </div>
            <div class="upload-actions">
              <input
                ref="pdfInputRef"
                type="file"
                accept="application/pdf"
                class="file-input"
                @change="handlePdfUpload"
              />
              <button
                type="button"
                class="btn-secondary btn-upload"
                :disabled="pdfLoading"
                @click="triggerPdfPicker"
              >
                <span v-if="pdfLoading" class="spinner small"></span>
                <span v-if="pdfLoading">Extracting...</span>
                <span v-else>Choose PDF</span>
              </button>
            </div>
          </div>
          <div v-if="pdfFileName" class="upload-meta">
            <span class="file-name">{{ pdfFileName }}</span>
            <button type="button" class="link-button" @click="clearPdfSelection">Clear</button>
          </div>
          <p v-if="pdfError" class="error-text">
            {{ pdfError }}
          </p>
        </section>

        <section class="input-section">
          <h2>2. Target Role & Job Description</h2>
          <div class="two-column">
            <div class="field">
              <label for="target-role">Target Role</label>
              <input
                id="target-role"
                v-model="resumeStore.targetRole"
                type="text"
                placeholder="e.g., Senior Backend Engineer"
              />
            </div>
            <div class="field">
              <label for="seniority">Seniority</label>
              <select id="seniority" v-model="resumeStore.seniority">
                <option value="junior">Junior / Entry</option>
                <option value="mid">Mid-level</option>
                <option value="senior">Senior</option>
                <option value="lead">Lead</option>
              </select>
            </div>
          </div>
          <label for="job-description">Job Description (optional but recommended)</label>
          <textarea
            id="job-description"
            v-model="resumeStore.jobDescription"
            class="input-textarea"
            placeholder="Paste the job description here for a more accurate ATS match..."
          />
        </section>

        <section class="actions-section">
          <button
            class="btn-primary large"
            :disabled="!resumeStore.resumeText.trim() || resumeStore.loading"
            @click="runReview"
          >
            <span v-if="resumeStore.loading" class="spinner"></span>
            <span v-if="resumeStore.loading">Analyzing resume...</span>
            <span v-else>Run ATS Resume Review</span>
          </button>
          <p v-if="resumeStore.error" class="error-text">
            {{ resumeStore.error }}
          </p>
        </section>

        <section v-if="resumeStore.report" class="results-section">
          <h2>3. Review Results</h2>

          <div class="score-cards">
            <div class="score-card">
              <h3>Overall Score</h3>
              <div class="score-value">{{ resumeStore.report.overall_score ?? 0 }}/100</div>
              <p class="score-caption">Holistic quality for the target role</p>
            </div>
            <div class="score-card">
              <h3>ATS Match</h3>
              <div class="score-value">{{ resumeStore.report.ats_score ?? 0 }}/100</div>
              <p class="score-caption">Keyword and relevance score vs. job description</p>
            </div>
          </div>

          <div class="summary-card" v-if="resumeStore.report.match_summary">
            <h3>Match Summary</h3>
            <p>{{ resumeStore.report.match_summary }}</p>
          </div>

          <div class="grid-2">
            <div class="list-card" v-if="resumeStore.report.strengths?.length">
              <h3>Strengths</h3>
              <ul>
                <li v-for="(item, index) in resumeStore.report.strengths" :key="'s-' + index">
                  {{ item }}
                </li>
              </ul>
            </div>
            <div class="list-card" v-if="resumeStore.report.weaknesses?.length">
              <h3>Weaknesses</h3>
              <ul>
                <li v-for="(item, index) in resumeStore.report.weaknesses" :key="'w-' + index">
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>

          <div class="grid-2">
            <div class="list-card" v-if="resumeStore.report.missing_keywords?.length">
              <h3>Missing Keywords</h3>
              <p class="helper-text">Consider weaving these into your experience and skills sections when they are true for you.</p>
              <ul class="keyword-list">
                <li v-for="(kw, index) in resumeStore.report.missing_keywords" :key="'k-' + index">
                  {{ kw }}
                </li>
              </ul>
            </div>
            <div class="list-card" v-if="resumeStore.report.formatting_issues?.length">
              <h3>Formatting & ATS Issues</h3>
              <ul>
                <li v-for="(item, index) in resumeStore.report.formatting_issues" :key="'f-' + index">
                  {{ item }}
                </li>
              </ul>
            </div>
          </div>

          <div class="list-card" v-if="resumeStore.report.recommendations?.length">
            <h3>High-Impact Recommendations</h3>
            <ul>
              <li v-for="(item, index) in resumeStore.report.recommendations" :key="'r-' + index">
                {{ item }}
              </li>
            </ul>
          </div>

          <div class="improvements-section" v-if="resumeStore.report.sections_to_improve">
            <h3>Suggested Rewrites</h3>

            <div class="rewrite-card" v-if="resumeStore.report.sections_to_improve.summary">
              <h4>Professional Summary</h4>
              <div class="rewrite-grid">
                <div>
                  <h5>Current</h5>
                  <p>{{ resumeStore.report.sections_to_improve.summary.current }}</p>
                </div>
                <div>
                  <h5>Suggested</h5>
                  <p>{{ resumeStore.report.sections_to_improve.summary.suggested }}</p>
                </div>
              </div>
              <p class="reason" v-if="resumeStore.report.sections_to_improve.summary.reason">
                Why: {{ resumeStore.report.sections_to_improve.summary.reason }}
              </p>
            </div>

            <div
              class="rewrite-card"
              v-if="resumeStore.report.sections_to_improve.experience?.length"
            >
              <h4>Experience Bullets</h4>
              <div
                v-for="(exp, idx) in resumeStore.report.sections_to_improve.experience"
                :key="'exp-' + idx"
                class="rewrite-grid"
              >
                <div>
                  <h5>Current</h5>
                  <p>{{ exp.current }}</p>
                </div>
                <div>
                  <h5>Suggested</h5>
                  <p>{{ exp.suggested }}</p>
                  <p class="reason" v-if="exp.reason">Why: {{ exp.reason }}</p>
                </div>
              </div>
            </div>

            <div class="rewrite-card" v-if="resumeStore.report.sections_to_improve.skills">
              <h4>Skills Section</h4>
              <div class="rewrite-grid">
                <div>
                  <h5>Current</h5>
                  <p>{{ resumeStore.report.sections_to_improve.skills.current }}</p>
                </div>
                <div>
                  <h5>Suggested</h5>
                  <p>{{ resumeStore.report.sections_to_improve.skills.suggested }}</p>
                </div>
              </div>
              <p class="reason" v-if="resumeStore.report.sections_to_improve.skills.reason">
                Why: {{ resumeStore.report.sections_to_improve.skills.reason }}
              </p>
            </div>
          </div>
        </section>
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
import { useResumeReviewStore } from '@/stores/resumeReview'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import * as pdfjsLib from 'pdfjs-dist'

pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const resumeStore = useResumeReviewStore()

const agentId = route.params.agentId as string
const sidebarInput = ref('')
const sidebarMessagesRef = ref<HTMLElement | null>(null)
const isChatMinimized = ref(false)
const pdfInputRef = ref<HTMLInputElement | null>(null)
const pdfFileName = ref('')
const pdfLoading = ref(false)
const pdfError = ref<string | null>(null)

const agent = computed(() => agentsStore.selectedAgent)
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.sending || chatStore.loading)

onMounted(async () => {
  await agentsStore.fetchAgent(agentId)

  // Initialize or reuse conversation for this agent
  const urlConversationId = route.query.conversation_id as string
  const existing = urlConversationId || resumeStore.conversationId

  if (existing) {
    await chatStore.fetchConversation(existing)
    resumeStore.setConversationId(existing)
    if (!urlConversationId) {
      router.replace({
        path: route.path,
        query: { ...route.query, conversation_id: existing },
      })
    }
  } else {
    const result = await chatStore.createConversation(agentId)
    if (result.success && result.conversation) {
      await chatStore.fetchConversation(result.conversation.id)
      resumeStore.setConversationId(result.conversation.id)
      router.replace({
        path: route.path,
        query: { ...route.query, conversation_id: result.conversation.id },
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
    resumeStore.conversationId || chatStore.activeConversationId || undefined,
  )

  if (!result.success) {
    alert(result.error || 'Failed to send message')
    sidebarInput.value = message
  }
}

function triggerPdfPicker() {
  pdfInputRef.value?.click()
}

function clearPdfSelection() {
  pdfFileName.value = ''
  pdfError.value = null
  if (pdfInputRef.value) {
    pdfInputRef.value.value = ''
  }
}

async function handlePdfUpload(event: Event) {
  const input = event.target as HTMLInputElement | null
  const file = input?.files?.[0]
  if (!file) return

  pdfError.value = null
  pdfFileName.value = file.name

  if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
    pdfError.value = 'Please choose a valid PDF file.'
    return
  }

  const maxSizeMb = 10
  if (file.size > maxSizeMb * 1024 * 1024) {
    pdfError.value = `PDF is too large. Please upload a file under ${maxSizeMb}MB.`
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

    const normalized = extracted.trim()
    if (!normalized) {
      throw new Error('No text extracted from PDF.')
    }

    resumeStore.resumeText = normalized
  } catch (error) {
    console.error('Failed to extract PDF text:', error)
    pdfError.value = 'Could not extract text from this PDF. Please paste the resume text instead.'
  } finally {
    pdfLoading.value = false
  }
}

async function runReview() {
  if (!resumeStore.resumeText.trim()) return

  resumeStore.setError(null)
  resumeStore.setLoading(true)

  const payload = {
    action: 'review_resume',
    resume_text: resumeStore.resumeText,
    job_description: resumeStore.jobDescription,
    target_role: resumeStore.targetRole,
    seniority: resumeStore.seniority,
  }

  const messageContent = `RESUME_REVIEW_REQUEST\n${JSON.stringify(payload, null, 2)}`

  const result = await chatStore.sendMessage(
    agentId,
    messageContent,
    resumeStore.conversationId || chatStore.activeConversationId || undefined,
  )

  if (!result.success) {
    resumeStore.setError(result.error || 'Failed to run resume review')
    resumeStore.setLoading(false)
    return
  }

  // Refresh conversation and extract the latest assistant message as JSON
  const conversationId = resumeStore.conversationId || chatStore.activeConversationId
  if (conversationId) {
    await chatStore.fetchConversation(conversationId)
    const latestAssistant = [...chatStore.messages]
      .reverse()
      .find((m) => m.role === 'assistant' && !!m.content)

    if (latestAssistant) {
      try {
        const raw = latestAssistant.content.trim()
        let jsonStr = raw
        const firstBrace = raw.indexOf('{')
        const lastBrace = raw.lastIndexOf('}')
        if (firstBrace !== -1 && lastBrace !== -1 && lastBrace > firstBrace) {
          jsonStr = raw.slice(firstBrace, lastBrace + 1)
        }
        const parsed = JSON.parse(jsonStr)
        resumeStore.setReport(parsed)
        resumeStore.setError(parsed.error ? parsed.message || 'Resume review reported an error' : null)
      } catch (e) {
        console.error('Failed to parse resume review JSON:', e)
        resumeStore.setError('Could not parse resume review response. Please try again.')
      }
    }
  }

  resumeStore.setLoading(false)
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

function toggleChatMinimize() {
  isChatMinimized.value = !isChatMinimized.value
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
.resume-review-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #0b1220 0%, #0c1426 55%, #0a1122 100%);
  color: #e5e7eb;
  --panel: rgba(12, 18, 34, 0.92);
  --panel-strong: rgba(10, 16, 30, 0.98);
  --panel-border: rgba(84, 98, 128, 0.35);
  --input-bg: rgba(8, 14, 26, 0.9);
  --accent: #3b82f6;
  --accent-strong: #2563eb;
  --muted: #9aa5b5;
  --shadow: 0 12px 30px rgba(2, 6, 23, 0.45);
}

.resume-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 28px;
  border-bottom: 1px solid var(--panel-border);
  background: rgba(7, 12, 24, 0.92);
  backdrop-filter: blur(18px);
  box-shadow: 0 8px 24px rgba(2, 6, 23, 0.45);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-back {
  padding: 8px 14px;
  border-radius: 9999px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  background: rgba(12, 18, 34, 0.6);
  color: #e5e7eb;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary {
  padding: 8px 16px;
  border-radius: 9999px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: rgba(10, 16, 30, 0.9);
  color: #e5e7eb;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.resume-content {
  display: flex;
  position: relative;
  min-height: calc(100vh - 72px);
}

.resume-sidebar {
  width: 320px;
  max-width: 100%;
  border-right: 1px solid var(--panel-border);
  background: var(--panel-strong);
  display: flex;
  flex-direction: column;
}

.resume-sidebar.minimized {
  display: none;
}

.sidebar-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--panel-border);
}

.btn-minimize {
  border-radius: 9999px;
  border: 1px solid rgba(148, 163, 184, 0.4);
  background: rgba(12, 18, 34, 0.7);
  color: #e5e7eb;
  width: 32px;
  height: 32px;
  cursor: pointer;
}

.sidebar-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-message {
  display: flex;
}

.sidebar-message.user .sidebar-message-content {
  margin-left: auto;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: white;
}

.sidebar-message.assistant .sidebar-message-content {
  margin-right: auto;
  background: rgba(8, 14, 26, 0.95);
  border: 1px solid var(--panel-border);
}

.sidebar-message-content {
  max-width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.5;
}

.sidebar-message-time {
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.7;
}

.sidebar-input {
  border-top: 1px solid var(--panel-border);
  padding: 10px;
}

.sidebar-input-field {
  width: 100%;
  padding: 8px 10px;
  border-radius: 9999px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: var(--input-bg);
  color: #e5e7eb;
  font-size: 13px;
}

.sidebar-input-field:focus {
  outline: 2px solid rgba(59, 130, 246, 0.4);
  border-color: rgba(59, 130, 246, 0.8);
}

.btn-send-small {
  margin-top: 8px;
  width: 100%;
  padding: 8px;
  border-radius: 9999px;
  border: none;
  background: #2563eb;
  color: white;
  cursor: pointer;
  font-size: 13px;
}

.chat-minimized-btn {
  position: absolute;
  left: 16px;
  bottom: 16px;
  border-radius: 9999px;
  border: 1px solid rgba(59, 130, 246, 0.6);
  padding: 10px 16px;
  background: #2563eb;
  color: white;
  cursor: pointer;
  font-size: 13px;
}

.resume-main {
  flex: 1;
  padding: 26px 28px 40px;
  overflow-y: auto;
}

.resume-main.expanded {
  margin-left: 0;
}

.input-section {
  margin-bottom: 24px;
  padding: 20px;
  border-radius: 16px;
  background: var(--panel);
  border: 1px solid var(--panel-border);
  box-shadow: var(--shadow);
}

.input-section h2 {
  font-size: 18px;
  margin-bottom: 8px;
}

.section-help {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 12px;
}

.input-textarea {
  width: 100%;
  min-height: 120px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: var(--input-bg);
  color: #e5e7eb;
  font-size: 13px;
  resize: vertical;
}

.input-textarea:focus {
  outline: 2px solid rgba(59, 130, 246, 0.35);
  border-color: rgba(59, 130, 246, 0.8);
}

.resume-textarea {
  min-height: 200px;
}

.upload-panel {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(8, 14, 26, 0.7);
  border: 1px dashed rgba(90, 105, 130, 0.55);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.upload-copy h3 {
  font-size: 14px;
  margin-bottom: 4px;
}

.upload-copy p {
  font-size: 12px;
  color: var(--muted);
}

.upload-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-input {
  display: none;
}

.btn-upload {
  min-width: 140px;
  justify-content: center;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.upload-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: var(--muted);
}

.file-name {
  max-width: 420px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.link-button {
  border: none;
  background: transparent;
  color: var(--accent);
  cursor: pointer;
  font-size: 12px;
  padding: 0;
}

.two-column {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px 16px;
  margin-bottom: 12px;
}

.field label {
  display: block;
  font-size: 13px;
  margin-bottom: 4px;
}

.field input,
.field select {
  width: 100%;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.5);
  background: var(--input-bg);
  color: #e5e7eb;
  font-size: 13px;
}

.field input:focus,
.field select:focus {
  outline: 2px solid rgba(59, 130, 246, 0.35);
  border-color: rgba(59, 130, 246, 0.8);
}

.actions-section {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-primary.large {
  padding: 10px 22px;
  border-radius: 9999px;
  border: none;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: white;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.25);
}

.btn-primary.large:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.spinner {
  width: 16px;
  height: 16px;
  border-radius: 9999px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: white;
  animation: spin 0.8s linear infinite;
}

.spinner.small {
  width: 14px;
  height: 14px;
  border-width: 2px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-text {
  color: #fecaca;
  font-size: 13px;
}

.results-section {
  padding: 20px;
  border-radius: 16px;
  background: var(--panel);
  border: 1px solid var(--panel-border);
  margin-bottom: 24px;
  box-shadow: var(--shadow);
}

.score-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.score-card {
  padding: 12px 14px;
  border-radius: 14px;
  background: radial-gradient(circle at top left, rgba(59, 130, 246, 0.25), transparent),
    rgba(10, 16, 30, 0.92);
  border: 1px solid rgba(59, 130, 246, 0.45);
}

.score-card h3 {
  font-size: 14px;
  margin-bottom: 6px;
}

.score-value {
  font-size: 24px;
  font-weight: 700;
}

.score-caption {
  font-size: 12px;
  color: var(--muted);
}

.summary-card {
  margin-bottom: 16px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(10, 16, 30, 0.9);
  border: 1px solid var(--panel-border);
  font-size: 14px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.list-card {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(10, 16, 30, 0.9);
  border: 1px solid var(--panel-border);
  font-size: 13px;
}

.list-card h3 {
  margin-bottom: 8px;
  font-size: 14px;
}

.list-card ul {
  padding-left: 18px;
}

.list-card li {
  margin-bottom: 4px;
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-left: 0;
}

.keyword-list li {
  list-style: none;
  padding: 4px 8px;
  border-radius: 9999px;
  background: rgba(37, 99, 235, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.4);
  font-size: 12px;
}

.helper-text {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 6px;
}

.improvements-section {
  margin-top: 12px;
}

.rewrite-card {
  margin-bottom: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(10, 16, 30, 0.9);
  border: 1px solid var(--panel-border);
}

.rewrite-card h4 {
  margin-bottom: 8px;
  font-size: 14px;
}

.rewrite-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.rewrite-grid h5 {
  font-size: 13px;
  margin-bottom: 4px;
}

.rewrite-grid p {
  font-size: 13px;
}

.reason {
  margin-top: 6px;
  font-size: 12px;
  color: var(--muted);
}

@media (max-width: 900px) {
  .resume-content {
    flex-direction: column;
  }

  .resume-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--panel-border);
  }

  .resume-main {
    padding: 16px;
  }

  .upload-panel {
    flex-direction: column;
    align-items: flex-start;
  }

  .upload-actions {
    width: 100%;
  }

  .btn-upload {
    width: 100%;
  }
}
</style>

