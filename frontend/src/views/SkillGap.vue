<template>
  <div class="skill-gap-container">
    <header class="skill-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">&larr; Back</button>
        <h1>{{ agent?.name || 'Skill Gap Agent' }}</h1>
      </div>
      <button @click="handleLogout" class="btn-secondary">Logout</button>
    </header>

    <div class="skill-content">
      <aside :class="['skill-sidebar', { minimized: isChatMinimized }]">
        <div class="sidebar-header">
          <h2>Agent Chat</h2>
          <button @click="toggleChatMinimize" class="btn-minimize">{{ isChatMinimized ? '+' : '-' }}</button>
        </div>
        <div v-if="!isChatMinimized" class="sidebar-messages" ref="sidebarMessagesRef">
          <div v-for="message in sidebarMessages" :key="message.id" :class="['sidebar-message', message.role]">
            <div class="sidebar-message-content">
              <div class="sidebar-message-text" v-html="formatMessage(message.content)"></div>
              <div class="sidebar-message-time">{{ formatTime(message.created_at) }}</div>
            </div>
          </div>
          <div v-if="sidebarPending" class="sidebar-message assistant">
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
              placeholder="Ask explicit follow-up questions"
              :disabled="isBusy"
              class="sidebar-input-field"
            />
            <button type="submit" :disabled="!sidebarInput.trim() || isBusy" class="btn-send-small">Send</button>
          </form>
        </div>
      </aside>

      <button v-if="isChatMinimized" @click="toggleChatMinimize" class="chat-minimized-btn">Chat</button>

      <main class="skill-main">
        <section class="panel">
          <h2>1. Profile Baseline</h2>
          <p class="section-help">
            Start with minimal inputs. Provide your current role and target role, then use suggested learning capacity.
          </p>
          <div class="grid-2">
            <div class="field"><label>Current Role</label><input v-model="skillGapStore.currentRole" type="text" /></div>
            <div class="field"><label>Target Role</label><input v-model="skillGapStore.targetRole" type="text" /></div>
          </div>
          <div class="grid-3">
            <div class="field"><label>Years Experience</label><input v-model.number="skillGapStore.yearsExperience" type="number" min="0" max="50" /></div>
            <div class="field"><label>Weekly Learning Hours</label><input v-model.number="skillGapStore.weeklyLearningHours" type="number" min="1" max="80" /></div>
            <div class="field"><label>Timeline Weeks</label><input v-model.number="skillGapStore.timelineWeeks" type="number" min="2" max="104" /></div>
          </div>

          <div class="suggestion-block">
            <div class="suggestion-row">
              <span class="suggestion-label">Suggested weekly hours:</span>
              <button
                v-for="hours in suggestedLearningHours"
                :key="'sg-hours-' + hours"
                type="button"
                class="btn-suggestion"
                :class="{ active: skillGapStore.weeklyLearningHours === hours }"
                @click="skillGapStore.weeklyLearningHours = hours"
              >
                {{ hours }}h
              </button>
            </div>
            <div class="suggestion-row">
              <span class="suggestion-label">Suggested timeline:</span>
              <button
                v-for="weeks in suggestedTimelineWeeks"
                :key="'sg-weeks-' + weeks"
                type="button"
                class="btn-suggestion"
                :class="{ active: skillGapStore.timelineWeeks === weeks }"
                @click="skillGapStore.timelineWeeks = weeks"
              >
                {{ weeks }} weeks
              </button>
            </div>
          </div>

          <div class="action-row">
            <button class="btn-secondary-inline" @click="showAdvancedBaseline = !showAdvancedBaseline">
              {{ showAdvancedBaseline ? 'Hide Optional Profile Details' : 'Add Optional Profile Details' }}
            </button>
          </div>
          <div v-if="showAdvancedBaseline">
            <div class="field"><label>Department</label><input v-model="skillGapStore.department" type="text" /></div>
            <div class="field"><label>Current Skills (comma/newline separated)</label><textarea v-model="skillGapStore.currentSkillsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Target Skills</label><textarea v-model="skillGapStore.targetSkillsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Projects and Outcomes</label><textarea v-model="skillGapStore.projectsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Performance Notes</label><textarea v-model="skillGapStore.performanceNotes" class="input-textarea"></textarea></div>
            <div class="field"><label>Constraints</label><textarea v-model="skillGapStore.constraintsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Learning Preferences</label><textarea v-model="skillGapStore.learningPreferencesInput" class="input-textarea"></textarea></div>
          </div>

          <div class="action-row">
            <button class="btn-primary" :disabled="skillGapStore.loading" @click="runProfileBaseline">
              {{ skillGapStore.loading ? 'Analyzing...' : 'Generate Profile Baseline' }}
            </button>
          </div>

          <div v-if="skillGapStore.baselineReport && skillGapStore.baselineReport.status === 'ok'" class="report-block">
            <div class="score-card">
              <h3>Baseline Confidence</h3>
              <div class="score-value">{{ skillGapStore.baselineReport.confidence_score ?? 0 }}/100</div>
            </div>
            <div class="summary-card">
              <h3>Profile Summary</h3>
              <p>{{ skillGapStore.baselineReport.profile_summary }}</p>
            </div>
            <div class="list-card" v-if="skillGapStore.baselineReport.focus_areas?.length">
              <h3>Focus Areas</h3>
              <ul>
                <li v-for="(item, i) in skillGapStore.baselineReport.focus_areas" :key="'fa-' + i">{{ item }}</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="panel">
          <h2>2. Identify Skill Gaps</h2>
          <div class="field"><label>Role Expectations</label><textarea v-model="skillGapStore.roleExpectationsInput" class="input-textarea"></textarea></div>
          <div class="action-row">
            <button class="btn-secondary-inline" @click="showFeedbackInputs = !showFeedbackInputs">
              {{ showFeedbackInputs ? 'Hide Optional Feedback Inputs' : 'Add Optional Feedback Inputs' }}
            </button>
          </div>
          <div v-if="showFeedbackInputs">
            <div class="field"><label>Manager Feedback</label><textarea v-model="skillGapStore.managerFeedbackInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Peer Feedback</label><textarea v-model="skillGapStore.peerFeedbackInput" class="input-textarea"></textarea></div>
          </div>
          <div class="action-row">
            <button class="btn-primary" :disabled="skillGapStore.loading || !skillGapStore.targetRole.trim()" @click="runIdentifySkillGaps">
              {{ skillGapStore.loading ? 'Evaluating...' : 'Identify Skill Gaps' }}
            </button>
          </div>
          <div v-if="skillGapStore.gapReport && skillGapStore.gapReport.status === 'ok'" class="report-block">
            <div class="score-card">
              <h3>Overall Gap Score</h3>
              <div class="score-value">{{ skillGapStore.gapReport.overall_gap_score ?? 0 }}/100</div>
            </div>
            <div class="list-card" v-if="skillGapStore.gapReport.critical_skill_gaps?.length">
              <h3>Critical Gaps</h3>
              <div class="nested-card" v-for="(gap, i) in skillGapStore.gapReport.critical_skill_gaps" :key="'gap-' + i">
                <div class="nested-header">
                  <strong>{{ gap.skill }}</strong>
                  <span>{{ gap.priority }}</span>
                </div>
                <p>{{ gap.current_level }} to {{ gap.target_level }}</p>
                <p class="muted">{{ gap.business_impact }}</p>
              </div>
            </div>
          </div>
        </section>

        <section class="panel">
          <h2>3. Development Plan</h2>
          <div class="grid-2">
            <div class="field"><label>Timeline Weeks</label><input v-model.number="skillGapStore.timelineWeeks" type="number" min="2" max="104" /></div>
            <div class="field"><label>Weekly Learning Hours</label><input v-model.number="skillGapStore.weeklyLearningHours" type="number" min="1" max="80" /></div>
          </div>
          <div class="action-row">
            <button class="btn-primary" :disabled="skillGapStore.loading || !skillGapStore.targetRole.trim()" @click="runBuildDevelopmentPlan">
              {{ skillGapStore.loading ? 'Building...' : 'Build Development Plan' }}
            </button>
          </div>
          <div v-if="skillGapStore.planReport && skillGapStore.planReport.status === 'ok'" class="report-block">
            <div class="summary-card">
              <h3>Plan Summary</h3>
              <p>{{ skillGapStore.planReport.plan_summary }}</p>
            </div>
            <div class="list-card" v-if="skillGapStore.planReport.phases?.length">
              <h3>Phases</h3>
              <div class="nested-card" v-for="(phase, i) in skillGapStore.planReport.phases" :key="'phase-' + i">
                <div class="nested-header">
                  <strong>{{ phase.phase_name }}</strong>
                  <span>W{{ phase.start_week }}-{{ phase.end_week }}</span>
                </div>
                <p>{{ phase.goal }}</p>
              </div>
            </div>
          </div>
        </section>

        <section class="panel">
          <h2>4. Weekly Progress Check-In</h2>
          <div class="grid-2">
            <div class="field"><label>Week Number</label><input v-model.number="skillGapStore.weekNumber" type="number" min="1" max="520" /></div>
            <div class="field"><label>Learning Hours Spent</label><input v-model.number="skillGapStore.learningHoursSpent" type="number" min="0" max="120" /></div>
          </div>
          <div class="field"><label>Check-In Notes</label><textarea v-model="skillGapStore.checkinNotes" class="input-textarea"></textarea></div>
          <div class="action-row">
            <button class="btn-secondary-inline" @click="showDetailedCheckin = !showDetailedCheckin">
              {{ showDetailedCheckin ? 'Hide Optional Check-In Details' : 'Add Optional Check-In Details' }}
            </button>
          </div>
          <div v-if="showDetailedCheckin">
            <div class="field"><label>Completed Activities</label><textarea v-model="skillGapStore.completedActivitiesInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Blocked Activities</label><textarea v-model="skillGapStore.blockedActivitiesInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Wins</label><textarea v-model="skillGapStore.winsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Support Needed</label><textarea v-model="skillGapStore.supportNeededInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Evidence Links</label><textarea v-model="skillGapStore.evidenceLinksInput" class="input-textarea"></textarea></div>
          </div>
          <div class="action-row">
            <button class="btn-primary" :disabled="skillGapStore.loading" @click="runWeeklyProgressCheckin">
              {{ skillGapStore.loading ? 'Reviewing...' : 'Run Weekly Check-In' }}
            </button>
          </div>
          <div v-if="skillGapStore.weeklyCheckinReport && skillGapStore.weeklyCheckinReport.status === 'ok'" class="report-block">
            <div class="score-card">
              <h3>Progress Score</h3>
              <div class="score-value">{{ skillGapStore.weeklyCheckinReport.progress_score ?? 0 }}/100</div>
              <p class="score-caption">{{ skillGapStore.weeklyCheckinReport.trajectory }}</p>
            </div>
            <div class="list-card" v-if="skillGapStore.weeklyCheckinReport.next_week_priorities?.length">
              <h3>Next Week Priorities</h3>
              <ul>
                <li v-for="(item, i) in skillGapStore.weeklyCheckinReport.next_week_priorities" :key="'nwp-' + i">{{ item }}</li>
              </ul>
            </div>
          </div>
        </section>

        <section class="panel">
          <h2>5. Readiness Assessment</h2>
          <div class="action-row">
            <button class="btn-primary" :disabled="skillGapStore.loading || !skillGapStore.targetRole.trim()" @click="runReadinessAssessment">
              {{ skillGapStore.loading ? 'Assessing...' : 'Assess Readiness' }}
            </button>
          </div>
          <div v-if="skillGapStore.readinessReport && skillGapStore.readinessReport.status === 'ok'" class="report-block">
            <div class="score-card">
              <h3>Readiness Score</h3>
              <div class="score-value">{{ skillGapStore.readinessReport.readiness_score ?? 0 }}/100</div>
            </div>
            <div class="list-card" v-if="skillGapStore.readinessReport.competency_breakdown?.length">
              <h3>Competency Breakdown</h3>
              <div class="nested-card" v-for="(item, i) in skillGapStore.readinessReport.competency_breakdown" :key="'cb-' + i">
                <div class="nested-header">
                  <strong>{{ item.competency }}</strong>
                  <span>{{ item.score }}/100</span>
                </div>
                <p>{{ item.gap }}</p>
                <p class="muted">{{ item.evidence_needed }}</p>
              </div>
            </div>
          </div>
        </section>

        <p v-if="skillGapStore.error" class="error-text">{{ skillGapStore.error }}</p>
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
import { useSkillGapStore } from '@/stores/skillGap'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import type { Message } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const skillGapStore = useSkillGapStore()

const agentId = route.params.agentId as string
const sidebarInput = ref('')
const sidebarMessagesRef = ref<HTMLElement | null>(null)
const isChatMinimized = ref(false)
const sidebarPending = ref(false)
const showAdvancedBaseline = ref(false)
const showFeedbackInputs = ref(false)
const showDetailedCheckin = ref(false)

const agent = computed(() => agentsStore.selectedAgent)
const messages = computed(() => chatStore.messages)
const isBusy = computed(() => chatStore.sending || chatStore.loading || skillGapStore.loading)
const suggestedLearningHours = [4, 6, 8]
const suggestedTimelineWeeks = [8, 12, 16]

const structuredActions = new Set([
  'profile_baseline',
  'identify_skill_gaps',
  'build_development_plan',
  'weekly_progress_checkin',
  'readiness_assessment',
])

const sidebarMessages = computed(() => {
  const filtered: Message[] = []
  let explicitThread = false

  for (const message of messages.value) {
    if (message.role === 'user') {
      const explicit = !isStructuredSkillGapMessage(message)
      explicitThread = explicit
      if (explicit) filtered.push(message)
      continue
    }

    if (message.role === 'assistant') {
      if (isStructuredSkillGapMessage(message)) continue
      if (explicitThread) filtered.push(message)
    }
  }

  return filtered
})

onMounted(async () => {
  await agentsStore.fetchAgent(agentId)

  const urlConversationId = route.query.conversation_id as string
  const existing = urlConversationId || skillGapStore.conversationId

  if (existing) {
    await chatStore.fetchConversation(existing, true)
    skillGapStore.setConversationId(existing)
    if (!urlConversationId) {
      router.replace({ path: route.path, query: { ...route.query, conversation_id: existing } })
    }
  } else {
    const result = await chatStore.createConversation(agentId)
    if (result.success && result.conversation) {
      await chatStore.fetchConversation(result.conversation.id, true)
      skillGapStore.setConversationId(result.conversation.id)
      router.replace({ path: route.path, query: { ...route.query, conversation_id: result.conversation.id } })
    }
  }
})

watch(messages, () => {
  nextTick(() => {
    if (sidebarMessagesRef.value) {
      sidebarMessagesRef.value.scrollTop = sidebarMessagesRef.value.scrollHeight
    }
  })
})

function parseListInput(input: string): string[] {
  return input
    .split(/[\n,;]/g)
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
}

function parseAssistantJson(raw: string): Record<string, unknown> | null {
  const trimmed = (raw || '').trim()
  const firstBrace = trimmed.indexOf('{')
  const lastBrace = trimmed.lastIndexOf('}')
  if (firstBrace === -1 || lastBrace === -1 || lastBrace <= firstBrace) return null
  try {
    return JSON.parse(trimmed.slice(firstBrace, lastBrace + 1))
  } catch {
    return null
  }
}

function isLikelyStructuredAssistantJson(content: string): boolean {
  const normalized = (content || '').trim().toLowerCase()
  if (!normalized.startsWith('{')) return false
  if (normalized.includes('"action"') && normalized.includes('"status"')) return true
  return false
}

function isStructuredSkillGapMessage(message: Message): boolean {
  if (message.role === 'user' && message.content.startsWith('SKILL_GAP_REQUEST')) return true
  if (message.role === 'assistant') {
    const parsed = parseAssistantJson(message.content)
    const action = String((parsed?.['action'] as string) || '').toLowerCase()
    if (parsed && structuredActions.has(action)) return true
    if (isLikelyStructuredAssistantJson(message.content)) return true
  }
  return false
}

function buildProfilePayload() {
  const payload: Record<string, unknown> = {
    current_role: skillGapStore.currentRole,
    target_role: skillGapStore.targetRole,
    years_experience: skillGapStore.yearsExperience,
    weekly_learning_hours: skillGapStore.weeklyLearningHours,
    timeline_weeks: skillGapStore.timelineWeeks,
  }

  const department = skillGapStore.department.trim()
  if (department) payload.department = department

  const currentSkills = parseListInput(skillGapStore.currentSkillsInput)
  if (currentSkills.length > 0) payload.current_skills = currentSkills

  const targetSkills = parseListInput(skillGapStore.targetSkillsInput)
  if (targetSkills.length > 0) payload.target_skills = targetSkills

  const constraints = parseListInput(skillGapStore.constraintsInput)
  if (constraints.length > 0) payload.constraints = constraints

  const focusAreas = parseListInput(skillGapStore.focusAreasInput)
  if (focusAreas.length > 0) payload.focus_areas = focusAreas

  const projects = parseListInput(skillGapStore.projectsInput)
  if (projects.length > 0) payload.projects = projects

  const performanceNotes = skillGapStore.performanceNotes.trim()
  if (performanceNotes) payload.performance_notes = performanceNotes

  const roleExpectations = parseListInput(skillGapStore.roleExpectationsInput)
  if (roleExpectations.length > 0) payload.role_expectations = roleExpectations

  const learningPreferences = parseListInput(skillGapStore.learningPreferencesInput)
  if (learningPreferences.length > 0) payload.learning_preferences = learningPreferences

  const managerFeedback = parseListInput(skillGapStore.managerFeedbackInput)
  if (managerFeedback.length > 0) payload.manager_feedback = managerFeedback

  const peerFeedback = parseListInput(skillGapStore.peerFeedbackInput)
  if (peerFeedback.length > 0) payload.peer_feedback = peerFeedback

  return payload
}

async function sendSkillGapAction(action: string, payload: Record<string, unknown>) {
  skillGapStore.setError(null)
  skillGapStore.setLoading(true)
  try {
    const messageContent = `SKILL_GAP_REQUEST\n${JSON.stringify({ action, payload }, null, 2)}`
    const result = await chatStore.sendMessage(
      agentId,
      messageContent,
      skillGapStore.conversationId || chatStore.activeConversationId || undefined,
    )

    if (!result.success) {
      skillGapStore.setError(result.error || 'Failed to run skill gap action')
      return null
    }

    if (chatStore.activeConversationId && skillGapStore.conversationId !== chatStore.activeConversationId) {
      skillGapStore.setConversationId(chatStore.activeConversationId)
    }

    const conversationId = skillGapStore.conversationId || chatStore.activeConversationId
    if (!conversationId) {
      skillGapStore.setError('Conversation is not available.')
      return null
    }

    await chatStore.fetchConversation(conversationId, true)
    const latestAssistant = [...chatStore.messages].reverse().find((m) => m.role === 'assistant' && !!m.content)
    if (!latestAssistant) {
      skillGapStore.setError('No assistant response received.')
      return null
    }

    const parsed = parseAssistantJson(latestAssistant.content)
    if (!parsed) {
      skillGapStore.setError('Could not parse structured response from the Skill Gap Agent.')
      return null
    }

    if (parsed['status'] === 'error' || parsed['error']) {
      const message = String(parsed['message'] || parsed['error'] || 'Skill gap action failed.')
      skillGapStore.setError(message)
    }

    return parsed
  } finally {
    skillGapStore.setLoading(false)
  }
}

async function runProfileBaseline() {
  if (!skillGapStore.currentRole.trim() && !skillGapStore.targetRole.trim()) {
    skillGapStore.setError('Provide at least current role or target role to start.')
    return
  }
  const parsed = await sendSkillGapAction('profile_baseline', buildProfilePayload())
  if (parsed && parsed['action'] === 'profile_baseline') {
    skillGapStore.baselineReport = parsed as any
  }
}

async function runIdentifySkillGaps() {
  if (!skillGapStore.targetRole.trim()) {
    skillGapStore.setError('Target role is required for skill gap analysis.')
    return
  }
  const parsed = await sendSkillGapAction('identify_skill_gaps', {
    ...buildProfilePayload(),
    baseline_report: skillGapStore.baselineReport,
  })
  if (parsed && parsed['action'] === 'identify_skill_gaps') {
    skillGapStore.gapReport = parsed as any
  }
}

async function runBuildDevelopmentPlan() {
  if (!skillGapStore.targetRole.trim()) {
    skillGapStore.setError('Target role is required to build a development plan.')
    return
  }
  const parsed = await sendSkillGapAction('build_development_plan', {
    ...buildProfilePayload(),
    gap_report: skillGapStore.gapReport,
    timeline_weeks: skillGapStore.timelineWeeks,
    weekly_learning_hours: skillGapStore.weeklyLearningHours,
  })
  if (parsed && parsed['action'] === 'build_development_plan') {
    skillGapStore.planReport = parsed as any
  }
}

async function runWeeklyProgressCheckin() {
  const parsed = await sendSkillGapAction('weekly_progress_checkin', {
    week_number: skillGapStore.weekNumber,
    target_role: skillGapStore.targetRole,
    learning_hours_spent: skillGapStore.learningHoursSpent,
    completed_activities: parseListInput(skillGapStore.completedActivitiesInput),
    blocked_activities: parseListInput(skillGapStore.blockedActivitiesInput),
    wins: parseListInput(skillGapStore.winsInput),
    support_needed: parseListInput(skillGapStore.supportNeededInput),
    evidence_links: parseListInput(skillGapStore.evidenceLinksInput),
    notes: skillGapStore.checkinNotes,
    plan_report: skillGapStore.planReport,
  })
  if (parsed && parsed['action'] === 'weekly_progress_checkin') {
    skillGapStore.weeklyCheckinReport = parsed as any
    if (parsed['status'] === 'ok') {
      skillGapStore.weekNumber += 1
    }
  }
}

async function runReadinessAssessment() {
  if (!skillGapStore.targetRole.trim()) {
    skillGapStore.setError('Target role is required for readiness assessment.')
    return
  }
  const parsed = await sendSkillGapAction('readiness_assessment', {
    ...buildProfilePayload(),
    baseline_report: skillGapStore.baselineReport,
    gap_report: skillGapStore.gapReport,
    plan_report: skillGapStore.planReport,
  })
  if (parsed && parsed['action'] === 'readiness_assessment') {
    skillGapStore.readinessReport = parsed as any
  }
}

async function handleSidebarSend() {
  if (!sidebarInput.value.trim() || isBusy.value) return
  const message = sidebarInput.value.trim()
  sidebarInput.value = ''
  sidebarPending.value = true

  try {
    const result = await chatStore.sendMessage(
      agentId,
      message,
      skillGapStore.conversationId || chatStore.activeConversationId || undefined,
    )

    if (!result.success) {
      alert(result.error || 'Failed to send message')
      sidebarInput.value = message
      return
    }

    if (chatStore.activeConversationId && skillGapStore.conversationId !== chatStore.activeConversationId) {
      skillGapStore.setConversationId(chatStore.activeConversationId)
    }
  } finally {
    sidebarPending.value = false
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
.skill-gap-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #141f38 0%, #1e3a5f 52%, #224766 100%);
  color: #ecf5ff;
  --panel: rgba(22, 34, 59, 0.9);
  --panel-strong: rgba(16, 28, 51, 0.96);
  --panel-border: rgba(140, 170, 214, 0.34);
  --input-bg: rgba(12, 24, 43, 0.9);
  --muted: #aec6e6;
  --shadow: 0 16px 38px rgba(6, 12, 26, 0.42);
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 28px;
  border-bottom: 1px solid var(--panel-border);
  background: rgba(16, 28, 48, 0.92);
  backdrop-filter: blur(16px);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-back,
.btn-secondary,
.btn-primary,
.btn-send-small,
.btn-minimize,
.chat-minimized-btn {
  border-radius: 9999px;
  cursor: pointer;
}

.btn-back {
  padding: 8px 14px;
  border: 1px solid rgba(140, 170, 214, 0.5);
  background: rgba(22, 35, 61, 0.66);
  color: #ecf5ff;
  font-size: 14px;
}

.btn-secondary {
  padding: 8px 16px;
  border: 1px solid rgba(140, 170, 214, 0.5);
  background: rgba(17, 30, 52, 0.96);
  color: #ecf5ff;
  font-size: 14px;
}

.skill-content {
  display: flex;
  position: relative;
  min-height: calc(100vh - 72px);
}

.skill-sidebar {
  width: 320px;
  border-right: 1px solid var(--panel-border);
  background: var(--panel-strong);
  display: flex;
  flex-direction: column;
}

.skill-sidebar.minimized {
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
  border: 1px solid rgba(140, 170, 214, 0.46);
  background: rgba(20, 35, 60, 0.75);
  color: #ecf5ff;
  width: 32px;
  height: 32px;
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
  background: linear-gradient(135deg, #0b84ff, #4f46e5);
  color: #ffffff;
}

.sidebar-message.assistant .sidebar-message-content {
  margin-right: auto;
  background: rgba(11, 22, 40, 0.95);
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
  opacity: 0.72;
}

.sidebar-input {
  border-top: 1px solid var(--panel-border);
  padding: 10px;
}

.sidebar-input-field {
  width: 100%;
  padding: 8px 10px;
  border-radius: 9999px;
  border: 1px solid rgba(140, 170, 214, 0.54);
  background: var(--input-bg);
  color: #ecf5ff;
  font-size: 13px;
}

.btn-send-small {
  margin-top: 8px;
  width: 100%;
  padding: 8px;
  border: none;
  background: #4f46e5;
  color: #ffffff;
}

.chat-minimized-btn {
  position: absolute;
  left: 16px;
  bottom: 16px;
  border: 1px solid rgba(129, 140, 248, 0.75);
  padding: 10px 16px;
  background: #4f46e5;
  color: #ffffff;
}

.skill-main {
  flex: 1;
  padding: 26px 28px 40px;
  overflow-y: auto;
}

.panel {
  margin-bottom: 24px;
  padding: 20px;
  border-radius: 16px;
  background: var(--panel);
  border: 1px solid var(--panel-border);
  box-shadow: var(--shadow);
}

.section-help {
  margin: 0 0 14px;
  color: #cfddf3;
  font-size: 13px;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.field {
  margin-bottom: 14px;
}

.field label {
  display: block;
  font-size: 12px;
  margin-bottom: 6px;
  color: #d0def5;
}

.field input,
.field textarea {
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(140, 170, 214, 0.5);
  background: var(--input-bg);
  color: #ecf5ff;
  font-size: 13px;
}

.input-textarea {
  min-height: 88px;
  resize: vertical;
}

.suggestion-block {
  margin-top: 4px;
  margin-bottom: 10px;
}

.suggestion-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.suggestion-label {
  font-size: 12px;
  color: #d0def5;
}

.btn-suggestion {
  border: 1px solid rgba(140, 170, 214, 0.52);
  background: rgba(20, 35, 60, 0.72);
  color: #ecf5ff;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 9999px;
  cursor: pointer;
}

.btn-suggestion.active {
  background: rgba(99, 102, 241, 0.28);
  border-color: rgba(129, 140, 248, 0.75);
}

.action-row {
  display: flex;
  margin-top: 6px;
}

.btn-secondary-inline {
  border: 1px solid rgba(140, 170, 214, 0.52);
  background: rgba(17, 30, 52, 0.76);
  color: #d6e4fa;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 12px;
  cursor: pointer;
}

.btn-primary {
  border: none;
  padding: 11px 18px;
  background: linear-gradient(135deg, #0b84ff, #4f46e5);
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
}

.btn-primary:disabled,
.btn-send-small:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.report-block {
  margin-top: 20px;
}

.score-card,
.summary-card,
.list-card {
  margin-bottom: 14px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(15, 29, 51, 0.78);
  border: 1px solid var(--panel-border);
}

.score-value {
  font-size: 28px;
  font-weight: 800;
  color: #8bb5ff;
}

.score-caption,
.muted {
  color: var(--muted);
  font-size: 12px;
}

.list-card ul {
  margin: 8px 0 0;
  padding-left: 18px;
}

.list-card li {
  margin-bottom: 6px;
}

.nested-card {
  margin-top: 10px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(140, 170, 214, 0.28);
  background: rgba(10, 21, 37, 0.84);
}

.nested-header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.typing {
  opacity: 0.82;
}

.error-text {
  margin-top: 10px;
  color: #fecaca;
  background: rgba(127, 29, 29, 0.32);
  border: 1px solid rgba(248, 113, 113, 0.45);
  padding: 10px 12px;
  border-radius: 10px;
}

@media (max-width: 1200px) {
  .grid-3 {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .skill-content {
    flex-direction: column;
  }

  .skill-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--panel-border);
    max-height: 320px;
  }

  .skill-main {
    padding: 18px 16px 28px;
  }

  .grid-2 {
    grid-template-columns: 1fr;
  }

  .skill-header {
    padding: 14px 16px;
  }
}
</style>
