<template>
  <div class="career-coach-container">
    <header class="career-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">&larr; Back</button>
        <h1>{{ agent?.name || 'Career Coach Agent' }}</h1>
      </div>
      <button @click="handleLogout" class="btn-secondary">Logout</button>
    </header>

    <div class="career-content">
      <aside :class="['coach-sidebar', { minimized: isChatMinimized }]">
        <div class="sidebar-header">
          <h2>Coach Chat</h2>
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
              <div class="sidebar-message-content"><div class="sidebar-message-text typing">Thinking...</div></div>
            </div>
          </div>
        <div v-if="!isChatMinimized" class="sidebar-input">
          <form @submit.prevent="handleSidebarSend">
            <input
              v-model="sidebarInput"
              type="text"
              placeholder="Ask follow-up coaching questions"
              :disabled="isBusy"
              class="sidebar-input-field"
            />
            <button type="submit" :disabled="!sidebarInput.trim() || isBusy" class="btn-send-small">Send</button>
          </form>
        </div>
      </aside>

      <button v-if="isChatMinimized" @click="toggleChatMinimize" class="chat-minimized-btn">Chat</button>

      <main class="coach-main">
        <section class="panel">
          <h2>1. Career Intake</h2>
          <p class="section-help">
            Start with minimal inputs. You only need your current role and target role. Everything else is optional.
          </p>
          <div class="grid-2">
            <div class="field"><label>Current Role</label><input v-model="careerCoachStore.currentRole" type="text" /></div>
            <div class="field"><label>Target Role</label><input v-model="careerCoachStore.targetRole" type="text" /></div>
          </div>
          <div class="grid-3">
            <div class="field"><label>Years Experience</label><input v-model.number="careerCoachStore.yearsExperience" type="number" min="0" max="50" /></div>
            <div class="field"><label>Weekly Hours</label><input v-model.number="careerCoachStore.weeklyHours" type="number" min="1" max="80" /></div>
            <div class="field"><label>Timeline Weeks</label><input v-model.number="careerCoachStore.timelineWeeks" type="number" min="2" max="104" /></div>
          </div>

          <div class="suggestion-block">
            <div class="suggestion-row">
              <span class="suggestion-label">Suggested weekly hours:</span>
              <button
                v-for="hours in suggestedWeeklyHours"
                :key="'hrs-' + hours"
                type="button"
                class="btn-suggestion"
                :class="{ active: careerCoachStore.weeklyHours === hours }"
                @click="careerCoachStore.weeklyHours = hours"
              >
                {{ hours }}h
              </button>
            </div>
            <div class="suggestion-row">
              <span class="suggestion-label">Suggested timeline:</span>
              <button
                v-for="weeks in suggestedTimelineWeeks"
                :key="'weeks-' + weeks"
                type="button"
                class="btn-suggestion"
                :class="{ active: careerCoachStore.timelineWeeks === weeks }"
                @click="careerCoachStore.timelineWeeks = weeks"
              >
                {{ weeks }} weeks
              </button>
            </div>
          </div>

          <div class="action-row">
            <button class="btn-secondary-inline" @click="showAdvancedIntake = !showAdvancedIntake">
              {{ showAdvancedIntake ? 'Hide Optional Profile Details' : 'Add Optional Profile Details' }}
            </button>
          </div>

          <div v-if="showAdvancedIntake">
            <div class="field"><label>Current Skills (comma/newline separated)</label><textarea v-model="careerCoachStore.currentSkillsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Achievements</label><textarea v-model="careerCoachStore.achievementsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Constraints</label><textarea v-model="careerCoachStore.constraintsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Career Interests</label><textarea v-model="careerCoachStore.careerInterestsInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Target Job Description</label><textarea v-model="careerCoachStore.targetJobDescription" class="input-textarea"></textarea></div>
          </div>
          <div class="action-row"><button class="btn-primary" :disabled="careerCoachStore.loading" @click="runIntakeAssessment">{{ careerCoachStore.loading ? 'Generating...' : 'Generate Intake Assessment' }}</button></div>

          <div v-if="careerCoachStore.intakeReport && careerCoachStore.intakeReport.status === 'ok'" class="report-block">
            <div class="score-card"><h3>Confidence</h3><div class="score-value">{{ careerCoachStore.intakeReport.confidence_score ?? 0 }}/100</div></div>
            <div class="summary-card"><h3>Profile Summary</h3><p>{{ careerCoachStore.intakeReport.profile_summary }}</p></div>
            <div class="list-card" v-if="careerCoachStore.intakeReport.immediate_priorities?.length"><h3>Immediate Priorities</h3><ul><li v-for="(item, i) in careerCoachStore.intakeReport.immediate_priorities" :key="'ip-' + i">{{ item }}</li></ul></div>
          </div>
        </section>

        <section class="panel">
          <h2>2. Opportunity Strategy</h2>
          <div class="action-row"><button class="btn-primary" :disabled="careerCoachStore.loading || !careerCoachStore.targetRole.trim()" @click="runOpportunityStrategy">{{ careerCoachStore.loading ? 'Analyzing...' : 'Build Opportunity Strategy' }}</button></div>
          <div v-if="careerCoachStore.opportunityStrategyReport && careerCoachStore.opportunityStrategyReport.status === 'ok'" class="report-block">
            <div class="score-card"><h3>Market Fit</h3><div class="score-value">{{ careerCoachStore.opportunityStrategyReport.market_fit_score ?? 0 }}/100</div></div>
            <div class="summary-card"><h3>Strategy Summary</h3><p>{{ careerCoachStore.opportunityStrategyReport.strategy_summary }}</p></div>
            <div class="summary-card"><h3>Positioning Statement</h3><p>{{ careerCoachStore.opportunityStrategyReport.positioning_statement }}</p></div>
            <div class="list-card" v-if="careerCoachStore.opportunityStrategyReport.top_role_tracks?.length">
              <h3>Top Role Tracks</h3>
              <div class="nested-card" v-for="(track, i) in careerCoachStore.opportunityStrategyReport.top_role_tracks" :key="'track-' + i">
                <div class="nested-header"><strong>{{ track.role_title }}</strong><span>{{ track.fit_score }}/100</span></div>
                <p>{{ track.why_fit }}</p>
              </div>
            </div>
            <div class="list-card" v-if="careerCoachStore.opportunityStrategyReport.networking_plan?.length"><h3>Networking Plan</h3><ul><li v-for="(item, i) in careerCoachStore.opportunityStrategyReport.networking_plan" :key="'network-' + i">{{ item }}</li></ul></div>
          </div>
        </section>

        <section class="panel">
          <h2>3. Roadmap</h2>
          <div class="grid-2">
            <div class="field"><label>Timeline Weeks</label><input v-model.number="careerCoachStore.timelineWeeks" type="number" min="2" max="104" /></div>
            <div class="field"><label>Weekly Hours</label><input v-model.number="careerCoachStore.weeklyHours" type="number" min="1" max="80" /></div>
          </div>
          <div class="action-row"><button class="btn-primary" :disabled="careerCoachStore.loading || !careerCoachStore.targetRole.trim()" @click="runRoadmap">{{ careerCoachStore.loading ? 'Building...' : 'Build Roadmap' }}</button></div>
          <div v-if="careerCoachStore.roadmapReport && careerCoachStore.roadmapReport.status === 'ok'" class="report-block">
            <div class="summary-card"><h3>Summary</h3><p>{{ careerCoachStore.roadmapReport.roadmap_summary }}</p></div>
            <div class="stats-grid">
              <div class="stat-card"><span>Timeline</span><strong>{{ careerCoachStore.roadmapReport.timeline_weeks }} weeks</strong></div>
              <div class="stat-card"><span>Phases</span><strong>{{ careerCoachStore.roadmapReport.phases?.length || 0 }}</strong></div>
              <div class="stat-card"><span>Weekly Outputs</span><strong>{{ careerCoachStore.roadmapReport.weekly_plan?.length || 0 }}</strong></div>
            </div>
            <div class="list-card" v-if="currentWeekRoadmapTopics.length">
              <h3>Current Week Topics (W{{ careerCoachStore.weekNumber }})</h3>
              <div class="topic-chip-group">
                <span v-for="(topic, i) in currentWeekRoadmapTopics" :key="'curr-topic-' + i" class="topic-chip">{{ topic }}</span>
              </div>
            </div>
            <div class="action-row">
              <button class="btn-secondary-inline" :disabled="isGeneratingRoadmapPdf" @click="downloadRoadmapPdf">
                {{ isGeneratingRoadmapPdf ? 'Preparing PDF...' : 'Download Detailed Roadmap (PDF)' }}
              </button>
            </div>
          </div>
        </section>

        <section class="panel">
          <h2>4. Weekly Check-In</h2>
          <p class="section-help">
            Weekly check-in requires completed topics from your roadmap for this week.
          </p>
          <div class="grid-2">
            <div class="field"><label>Week Number</label><input v-model.number="careerCoachStore.weekNumber" type="number" min="1" max="520" /></div>
            <div class="field"><label>Hours Spent</label><input v-model.number="careerCoachStore.timeSpentHours" type="number" min="0" max="100" /></div>
          </div>
          <div v-if="currentWeekRoadmapTopics.length" class="suggestion-row">
            <span class="suggestion-label">Week {{ careerCoachStore.weekNumber }} topics:</span>
            <button
              v-for="topic in currentWeekRoadmapTopics"
              :key="'wk-topic-' + topic"
              type="button"
              class="btn-suggestion"
              @click="toggleCompletedTopic(topic)"
            >
              {{ topic }}
            </button>
          </div>
          <div class="field">
            <label>Completed Topics (required)</label>
            <textarea
              v-model="careerCoachStore.completedTopicsInput"
              class="input-textarea"
              placeholder="List the roadmap topics you completed this week"
            ></textarea>
          </div>
          <div class="field"><label>Context Notes</label><textarea v-model="careerCoachStore.checkinNotes" class="input-textarea"></textarea></div>
          <div class="action-row">
            <button class="btn-secondary-inline" @click="showDetailedCheckin = !showDetailedCheckin">
              {{ showDetailedCheckin ? 'Hide Optional Check-In Details' : 'Add Optional Check-In Details' }}
            </button>
          </div>
          <div v-if="showDetailedCheckin">
            <div class="field"><label>Completed Tasks</label><textarea v-model="careerCoachStore.completedTasksInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Blocked Tasks</label><textarea v-model="careerCoachStore.blockedTasksInput" class="input-textarea"></textarea></div>
            <div class="field"><label>Wins</label><textarea v-model="careerCoachStore.winsInput" class="input-textarea"></textarea></div>
          </div>
          <div class="action-row"><button class="btn-primary" :disabled="careerCoachStore.loading" @click="runWeeklyCheckin">{{ careerCoachStore.loading ? 'Evaluating...' : 'Run Weekly Check-In' }}</button></div>
          <div v-if="careerCoachStore.weeklyCheckinReport && careerCoachStore.weeklyCheckinReport.status === 'ok'" class="report-block">
            <div class="score-card"><h3>Progress</h3><div class="score-value">{{ careerCoachStore.weeklyCheckinReport.progress_score ?? 0 }}/100</div><p class="score-caption">{{ careerCoachStore.weeklyCheckinReport.progress_status }}</p></div>
            <div class="list-card" v-if="careerCoachStore.weeklyCheckinReport.next_week_plan?.length"><h3>Next Week Plan</h3><ul><li v-for="(item, i) in careerCoachStore.weeklyCheckinReport.next_week_plan" :key="'nwp-' + i">{{ item }}</li></ul></div>
          </div>
        </section>

        <section class="panel">
          <h2>5. Interview Readiness</h2>
          <p class="section-help">Use suggested interview tracks if you don't want to type.</p>
          <div class="suggestion-row">
            <span class="suggestion-label">Suggested tracks:</span>
            <button
              v-for="interviewType in suggestedInterviewTypes"
              :key="'it-' + interviewType"
              type="button"
              class="btn-suggestion"
              @click="toggleInterviewType(interviewType)"
            >
              {{ interviewType }}
            </button>
          </div>
          <div class="field"><label>Interview Types</label><input v-model="careerCoachStore.interviewTypesInput" type="text" placeholder="behavioral, technical" /></div>
          <div class="action-row">
            <button class="btn-secondary-inline" @click="showInterviewContext = !showInterviewContext">
              {{ showInterviewContext ? 'Hide Optional Interview Context' : 'Add Optional Interview Context' }}
            </button>
          </div>
          <div v-if="showInterviewContext" class="field"><label>Upcoming Interview Context</label><textarea v-model="careerCoachStore.upcomingInterviewContext" class="input-textarea"></textarea></div>
          <div class="action-row"><button class="btn-primary" :disabled="careerCoachStore.loading || !careerCoachStore.targetRole.trim()" @click="runInterviewReadiness">{{ careerCoachStore.loading ? 'Assessing...' : 'Assess Interview Readiness' }}</button></div>
          <div v-if="careerCoachStore.interviewReadinessReport && careerCoachStore.interviewReadinessReport.status === 'ok'" class="report-block">
            <div class="score-card"><h3>Readiness</h3><div class="score-value">{{ careerCoachStore.interviewReadinessReport.readiness_score ?? 0 }}/100</div></div>
            <div class="list-card" v-if="careerCoachStore.interviewReadinessReport.behavioral_round_plan?.length"><h3>Behavioral Plan</h3><ul><li v-for="(item, i) in careerCoachStore.interviewReadinessReport.behavioral_round_plan" :key="'bp-' + i">{{ item }}</li></ul></div>
          </div>
        </section>

        <p v-if="careerCoachStore.error" class="error-text">{{ careerCoachStore.error }}</p>
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
import { useCareerCoachStore } from '@/stores/careerCoach'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import type { Message } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const careerCoachStore = useCareerCoachStore()

const agentId = route.params.agentId as string
const sidebarInput = ref('')
const sidebarMessagesRef = ref<HTMLElement | null>(null)
const isChatMinimized = ref(false)
const sidebarPending = ref(false)
const showAdvancedIntake = ref(false)
const showDetailedCheckin = ref(false)
const showInterviewContext = ref(false)
const isGeneratingRoadmapPdf = ref(false)

const agent = computed(() => agentsStore.selectedAgent)
const messages = computed(() => chatStore.messages)
const isBusy = computed(() => chatStore.sending || chatStore.loading || careerCoachStore.loading)
const suggestedWeeklyHours = [4, 6, 8]
const suggestedTimelineWeeks = [8, 12, 16]
const suggestedInterviewTypes = ['behavioral', 'technical', 'system_design']

const structuredActions = new Set([
  'intake_assessment',
  'opportunity_strategy',
  'build_roadmap',
  'weekly_checkin',
  'interview_readiness',
])

const sidebarMessages = computed(() => {
  const filtered: Message[] = []
  let explicitThread = false

  for (const message of messages.value) {
    if (message.role === 'user') {
      const explicit = !isStructuredCareerMessage(message)
      explicitThread = explicit
      if (explicit) filtered.push(message)
      continue
    }

    if (message.role === 'assistant') {
      if (isStructuredCareerMessage(message)) continue
      if (explicitThread) filtered.push(message)
    }
  }

  return filtered
})

const currentWeekRoadmapTopics = computed(() => {
  return getRoadmapTopicsForWeek(careerCoachStore.weekNumber)
})

onMounted(async () => {
  await agentsStore.fetchAgent(agentId)

  const urlConversationId = route.query.conversation_id as string
  const existing = urlConversationId || careerCoachStore.conversationId

  if (existing) {
    await chatStore.fetchConversation(existing, true)
    careerCoachStore.setConversationId(existing)
    if (!urlConversationId) {
      router.replace({ path: route.path, query: { ...route.query, conversation_id: existing } })
    }
  } else {
    const result = await chatStore.createConversation(agentId)
    if (result.success && result.conversation) {
      await chatStore.fetchConversation(result.conversation.id, true)
      careerCoachStore.setConversationId(result.conversation.id)
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

function parseAssistantJson(raw: string): Record<string, any> | null {
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

function isStructuredCareerMessage(message: Message): boolean {
  if (message.role === 'user' && message.content.startsWith('CAREER_COACH_REQUEST')) return true
  if (message.role === 'assistant') {
    const parsed = parseAssistantJson(message.content)
    if (parsed && structuredActions.has(String(parsed.action || '').toLowerCase())) {
      return true
    }
    if (isLikelyStructuredAssistantJson(message.content)) {
      return true
    }
  }
  return false
}

function buildProfilePayload() {
  const payload: Record<string, unknown> = {
    current_role: careerCoachStore.currentRole,
    target_role: careerCoachStore.targetRole,
    years_experience: Math.max(0, careerCoachStore.yearsExperience || 0),
    weekly_hours: Math.max(1, careerCoachStore.weeklyHours || 6),
    timeline_weeks: Math.max(2, careerCoachStore.timelineWeeks || 12),
  }

  const currentSkills = parseListInput(careerCoachStore.currentSkillsInput)
  if (currentSkills.length > 0) payload.current_skills = currentSkills

  const achievements = parseListInput(careerCoachStore.achievementsInput)
  if (achievements.length > 0) payload.achievements = achievements

  const constraints = parseListInput(careerCoachStore.constraintsInput)
  if (constraints.length > 0) payload.constraints = constraints

  const careerInterests = parseListInput(careerCoachStore.careerInterestsInput)
  if (careerInterests.length > 0) payload.career_interests = careerInterests

  const targetJobDescription = careerCoachStore.targetJobDescription.trim()
  if (targetJobDescription) payload.job_description = targetJobDescription

  const primaryIndustry = careerCoachStore.primaryIndustry.trim()
  if (primaryIndustry) payload.primary_industry = primaryIndustry

  const locationPreference = careerCoachStore.locationPreference.trim()
  if (locationPreference) payload.location_preference = locationPreference

  const preferredWorkModel = careerCoachStore.preferredWorkModel.trim()
  if (preferredWorkModel) payload.preferred_work_model = preferredWorkModel

  const compensationGoal = careerCoachStore.compensationGoal.trim()
  if (compensationGoal) payload.compensation_goal = compensationGoal

  return payload
}

function normalizeTopic(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function getRoadmapTopicsForWeek(weekNumber: number): string[] {
  const report = careerCoachStore.roadmapReport
  if (!report?.weekly_plan?.length) return []

  const weekPlan = report.weekly_plan.find((item) => Number(item?.week) === Number(weekNumber))
  if (!weekPlan) return []

  const topics = Array.isArray(weekPlan.topics) ? weekPlan.topics : []
  const tasks = Array.isArray(weekPlan.tasks) ? weekPlan.tasks : []
  const fallbackTopics = topics.length > 0 ? topics : tasks.slice(0, 3)
  const deduped: string[] = []
  const seen = new Set<string>()
  for (const topic of fallbackTopics) {
    const cleaned = String(topic || '').trim()
    const normalized = normalizeTopic(cleaned)
    if (!cleaned || !normalized || seen.has(normalized)) continue
    seen.add(normalized)
    deduped.push(cleaned)
  }
  return deduped
}

function topicMatchesRoadmap(topic: string, expectedTopics: string[]): boolean {
  const normalizedTopic = normalizeTopic(topic)
  if (!normalizedTopic) return false

  return expectedTopics.some((expected) => {
    const normalizedExpected = normalizeTopic(expected)
    if (!normalizedExpected) return false
    return normalizedTopic.includes(normalizedExpected) || normalizedExpected.includes(normalizedTopic)
  })
}

function toggleCompletedTopic(topic: string) {
  const existing = new Set(parseListInput(careerCoachStore.completedTopicsInput).map((item) => item.toLowerCase()))
  const normalized = topic.toLowerCase()
  if (existing.has(normalized)) {
    existing.delete(normalized)
  } else {
    existing.add(normalized)
  }
  careerCoachStore.completedTopicsInput = Array.from(existing).join(', ')
}

function escapeHtml(value: string): string {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function renderPdfList(items: string[]): string {
  if (!items.length) return '<p style="margin:0;color:#425466;">-</p>'
  return `<ul style="margin:8px 0 0 18px;">${items.map((item) => `<li style="margin:4px 0;">${escapeHtml(item)}</li>`).join('')}</ul>`
}

function buildRoadmapPdfHtml() {
  const report = careerCoachStore.roadmapReport
  if (!report) return ''

  const now = new Date().toLocaleString()
  const phasesHtml = (report.phases || [])
    .map((phase) => {
      const keyTopics = Array.isArray((phase as any).key_topics) ? (phase as any).key_topics : []
      return `
        <div style="border:1px solid #d9e2ec;border-radius:8px;padding:10px;margin:10px 0;">
          <div style="display:flex;justify-content:space-between;gap:10px;">
            <strong>${escapeHtml(phase.phase_name)}</strong>
            <span>Week ${phase.start_week} - ${phase.end_week}</span>
          </div>
          <p style="margin:8px 0 0 0;">${escapeHtml(phase.goal)}</p>
          <p style="margin:8px 0 0 0;"><strong>Key topics:</strong></p>
          ${renderPdfList(keyTopics)}
          <p style="margin:8px 0 0 0;"><strong>Milestones:</strong></p>
          ${renderPdfList(phase.milestones || [])}
          <p style="margin:8px 0 0 0;"><strong>Deliverables:</strong></p>
          ${renderPdfList(phase.deliverables || [])}
        </div>
      `
    })
    .join('')

  const weeklyHtml = (report.weekly_plan || [])
    .map((week) => {
      const topics = Array.isArray((week as any).topics) ? (week as any).topics : []
      return `
        <tr>
          <td style="border:1px solid #c7d2e1;padding:8px;vertical-align:top;">${week.week}</td>
          <td style="border:1px solid #c7d2e1;padding:8px;vertical-align:top;">${escapeHtml(week.focus)}</td>
          <td style="border:1px solid #c7d2e1;padding:8px;vertical-align:top;">${escapeHtml(topics.join(', '))}</td>
          <td style="border:1px solid #c7d2e1;padding:8px;vertical-align:top;">${escapeHtml((week.tasks || []).join('; '))}</td>
          <td style="border:1px solid #c7d2e1;padding:8px;vertical-align:top;">${week.time_budget_hours}</td>
          <td style="border:1px solid #c7d2e1;padding:8px;vertical-align:top;">${escapeHtml(week.output)}</td>
        </tr>
      `
    })
    .join('')

  return `
    <div style="font-family:Arial,sans-serif;color:#102a43;line-height:1.45;padding:14px;">
      <h1 style="margin:0 0 6px 0;">Career Roadmap</h1>
      <p style="margin:0 0 10px 0;"><strong>Generated:</strong> ${escapeHtml(now)}</p>
      <p style="margin:0 0 10px 0;"><strong>Target role:</strong> ${escapeHtml(report.target_role || careerCoachStore.targetRole)}</p>
      <p style="margin:0 0 10px 0;"><strong>Timeline:</strong> ${report.timeline_weeks} weeks</p>
      <h2 style="margin:14px 0 6px 0;">Roadmap Summary</h2>
      <p style="margin:0;">${escapeHtml(report.roadmap_summary || '')}</p>

      <h2 style="margin:16px 0 6px 0;">Phases</h2>
      ${phasesHtml || '<p>-</p>'}

      <h2 style="margin:16px 0 6px 0;">Detailed Weekly Plan</h2>
      <table style="width:100%;border-collapse:collapse;font-size:12px;">
        <thead>
          <tr style="background:#f0f4f8;">
            <th style="border:1px solid #c7d2e1;padding:8px;">Week</th>
            <th style="border:1px solid #c7d2e1;padding:8px;">Focus</th>
            <th style="border:1px solid #c7d2e1;padding:8px;">Topics</th>
            <th style="border:1px solid #c7d2e1;padding:8px;">Tasks</th>
            <th style="border:1px solid #c7d2e1;padding:8px;">Hours</th>
            <th style="border:1px solid #c7d2e1;padding:8px;">Output</th>
          </tr>
        </thead>
        <tbody>
          ${weeklyHtml || '<tr><td colspan="6" style="padding:10px;border:1px solid #c7d2e1;">No weekly plan available.</td></tr>'}
        </tbody>
      </table>

      <h2 style="margin:16px 0 6px 0;">Application Strategy</h2>
      <p style="margin:0;"><strong>Start week:</strong> ${(report.application_strategy || {}).start_week ?? '-'}</p>
      <p style="margin:4px 0 0 0;"><strong>Applications/week:</strong> ${(report.application_strategy || {}).target_applications_per_week ?? '-'}</p>
      <p style="margin:4px 0 0 0;"><strong>Referrals/month:</strong> ${(report.application_strategy || {}).target_referrals_per_month ?? '-'}</p>
      <p style="margin:4px 0 0 0;"><strong>Company tiers:</strong> ${escapeHtml(((report.application_strategy || {}).company_tiers || []).join(', '))}</p>

      <h2 style="margin:16px 0 6px 0;">Guardrails</h2>
      ${renderPdfList(report.burnout_guardrails || [])}
    </div>
  `
}

async function downloadRoadmapPdf() {
  if (!careerCoachStore.roadmapReport || isGeneratingRoadmapPdf.value) return

  isGeneratingRoadmapPdf.value = true
  careerCoachStore.setError(null)
  let container: HTMLDivElement | null = null

  try {
    const html2pdfModule = await import('html2pdf.js')
    const html2pdf = (html2pdfModule.default || html2pdfModule) as any

    container = document.createElement('div')
    container.innerHTML = buildRoadmapPdfHtml()
    container.style.position = 'fixed'
    container.style.left = '-10000px'
    container.style.top = '0'
    container.style.width = '980px'
    container.style.background = '#ffffff'
    container.style.zIndex = '-1'
    document.body.appendChild(container)

    const safeRole = (careerCoachStore.targetRole || 'career_roadmap')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')

    await html2pdf()
      .set({
        margin: [10, 10, 10, 10],
        filename: `${safeRole || 'career_roadmap'}_roadmap.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
        pagebreak: { mode: ['css', 'legacy'] },
      })
      .from(container)
      .save()
  } catch {
    careerCoachStore.setError('Failed to generate roadmap PDF. Please try again.')
  } finally {
    if (container && container.parentNode) {
      container.parentNode.removeChild(container)
    }
    isGeneratingRoadmapPdf.value = false
  }
}

function toggleInterviewType(type: string) {
  const existing = new Set(parseListInput(careerCoachStore.interviewTypesInput).map((item) => item.toLowerCase()))
  const normalized = type.toLowerCase()
  if (existing.has(normalized)) {
    existing.delete(normalized)
  } else {
    existing.add(normalized)
  }
  careerCoachStore.interviewTypesInput = Array.from(existing).join(', ')
}

async function sendCareerAction(action: string, payload: Record<string, unknown>) {
  careerCoachStore.setError(null)
  careerCoachStore.setLoading(true)
  try {
    const messageContent = `CAREER_COACH_REQUEST\n${JSON.stringify({ action, payload }, null, 2)}`
    const result = await chatStore.sendMessage(
      agentId,
      messageContent,
      careerCoachStore.conversationId || chatStore.activeConversationId || undefined,
    )

    if (!result.success) {
      careerCoachStore.setError(result.error || 'Failed to run career coach action')
      return null
    }

    if (chatStore.activeConversationId && careerCoachStore.conversationId !== chatStore.activeConversationId) {
      careerCoachStore.setConversationId(chatStore.activeConversationId)
    }

    const conversationId = careerCoachStore.conversationId || chatStore.activeConversationId
    if (!conversationId) {
      careerCoachStore.setError('Conversation is not available.')
      return null
    }

    await chatStore.fetchConversation(conversationId, true)
    const latestAssistant = [...chatStore.messages].reverse().find((m) => m.role === 'assistant' && !!m.content)
    if (!latestAssistant) {
      careerCoachStore.setError('No assistant response received.')
      return null
    }

    const parsed = parseAssistantJson(latestAssistant.content)
    if (!parsed) {
      careerCoachStore.setError('Could not parse structured response from the Career Coach Agent.')
      return null
    }

    if (parsed.status === 'error' || parsed.error) {
      careerCoachStore.setError(parsed.message || parsed.error || 'Career coach action failed.')
    }

    return parsed
  } finally {
    careerCoachStore.setLoading(false)
  }
}

async function runIntakeAssessment() {
  if (!careerCoachStore.currentRole.trim() && !careerCoachStore.targetRole.trim()) {
    careerCoachStore.setError('Provide at least current role or target role to start.')
    return
  }
  const parsed = await sendCareerAction('intake_assessment', buildProfilePayload())
  if (parsed && parsed.action === 'intake_assessment') careerCoachStore.intakeReport = parsed as any
}

async function runOpportunityStrategy() {
  if (!careerCoachStore.targetRole.trim()) {
    careerCoachStore.setError('Target role is required for opportunity strategy.')
    return
  }
  const parsed = await sendCareerAction('opportunity_strategy', {
    ...buildProfilePayload(),
    intake_assessment: careerCoachStore.intakeReport,
  })
  if (parsed && parsed.action === 'opportunity_strategy') {
    careerCoachStore.opportunityStrategyReport = parsed as any
  }
}

async function runRoadmap() {
  if (!careerCoachStore.targetRole.trim()) {
    careerCoachStore.setError('Target role is required to build a roadmap.')
    return
  }
  const parsed = await sendCareerAction('build_roadmap', {
    ...buildProfilePayload(),
    opportunity_strategy_report: careerCoachStore.opportunityStrategyReport,
    timeline_weeks: careerCoachStore.timelineWeeks,
    weekly_hours: careerCoachStore.weeklyHours,
  })
  if (parsed && parsed.action === 'build_roadmap') careerCoachStore.roadmapReport = parsed as any
}

async function runWeeklyCheckin() {
  if (!careerCoachStore.roadmapReport || careerCoachStore.roadmapReport.status !== 'ok') {
    careerCoachStore.setError('Build a roadmap before running weekly check-in.')
    return
  }

  const completedTopics = parseListInput(careerCoachStore.completedTopicsInput)
  if (!completedTopics.length) {
    careerCoachStore.setError('Completed topics are required for weekly check-in.')
    return
  }

  const expectedTopics = getRoadmapTopicsForWeek(careerCoachStore.weekNumber)
  if (expectedTopics.length > 0 && !completedTopics.some((topic) => topicMatchesRoadmap(topic, expectedTopics))) {
    careerCoachStore.setError(
      `Completed topics must align with roadmap week ${careerCoachStore.weekNumber} topics: ${expectedTopics.join(', ')}`,
    )
    return
  }

  const parsed = await sendCareerAction('weekly_checkin', {
    week_number: careerCoachStore.weekNumber,
    time_spent_hours: careerCoachStore.timeSpentHours,
    completed_topics: completedTopics,
    expected_week_topics: expectedTopics,
    completed_tasks: parseListInput(careerCoachStore.completedTasksInput),
    blocked_tasks: parseListInput(careerCoachStore.blockedTasksInput),
    wins: parseListInput(careerCoachStore.winsInput),
    notes: careerCoachStore.checkinNotes,
    roadmap_report: careerCoachStore.roadmapReport,
    target_role: careerCoachStore.targetRole,
  })
  if (parsed && parsed.action === 'weekly_checkin') {
    careerCoachStore.weeklyCheckinReport = parsed as any
    if (parsed.status === 'ok') careerCoachStore.weekNumber += 1
  }
}

async function runInterviewReadiness() {
  if (!careerCoachStore.targetRole.trim()) {
    careerCoachStore.setError('Target role is required for interview readiness.')
    return
  }
  const parsed = await sendCareerAction('interview_readiness', {
    ...buildProfilePayload(),
    interview_types: parseListInput(careerCoachStore.interviewTypesInput),
    upcoming_interview_context: careerCoachStore.upcomingInterviewContext,
    opportunity_strategy_report: careerCoachStore.opportunityStrategyReport,
    roadmap_report: careerCoachStore.roadmapReport,
  })
  if (parsed && parsed.action === 'interview_readiness') careerCoachStore.interviewReadinessReport = parsed as any
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
      careerCoachStore.conversationId || chatStore.activeConversationId || undefined,
    )

    if (!result.success) {
      alert(result.error || 'Failed to send message')
      sidebarInput.value = message
      return
    }

    if (chatStore.activeConversationId && careerCoachStore.conversationId !== chatStore.activeConversationId) {
      careerCoachStore.setConversationId(chatStore.activeConversationId)
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
.career-coach-container {
  min-height: 100vh;
  background: linear-gradient(180deg, #051824 0%, #07293b 50%, #0b3b4f 100%);
  color: #e9f2f7;
  --panel: rgba(7, 31, 45, 0.88);
  --panel-strong: rgba(4, 24, 36, 0.96);
  --panel-border: rgba(127, 193, 221, 0.28);
  --input-bg: rgba(3, 21, 32, 0.86);
  --muted: #9fb8c6;
  --shadow: 0 16px 38px rgba(1, 16, 25, 0.4);
}

.career-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 28px;
  border-bottom: 1px solid var(--panel-border);
  background: rgba(5, 22, 33, 0.92);
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
  border: 1px solid rgba(127, 193, 221, 0.48);
  background: rgba(9, 36, 52, 0.6);
  color: #e9f2f7;
  font-size: 14px;
}

.btn-secondary {
  padding: 8px 16px;
  border: 1px solid rgba(127, 193, 221, 0.44);
  background: rgba(5, 27, 40, 0.95);
  color: #e9f2f7;
  font-size: 14px;
}

.btn-secondary-inline {
  border: 1px solid rgba(127, 193, 221, 0.44);
  background: rgba(5, 27, 40, 0.75);
  color: #cfe6f3;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 12px;
  cursor: pointer;
}

.career-content {
  display: flex;
  position: relative;
  min-height: calc(100vh - 72px);
}

.coach-sidebar {
  width: 320px;
  border-right: 1px solid var(--panel-border);
  background: var(--panel-strong);
  display: flex;
  flex-direction: column;
}

.coach-sidebar.minimized {
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
  border: 1px solid rgba(127, 193, 221, 0.4);
  background: rgba(8, 34, 50, 0.7);
  color: #e9f2f7;
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
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  color: #ffffff;
}

.sidebar-message.assistant .sidebar-message-content {
  margin-right: auto;
  background: rgba(3, 22, 33, 0.95);
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
  border: 1px solid rgba(127, 193, 221, 0.5);
  background: var(--input-bg);
  color: #e9f2f7;
  font-size: 13px;
}

.btn-send-small {
  margin-top: 8px;
  width: 100%;
  padding: 8px;
  border: none;
  background: #0284c7;
  color: #ffffff;
}

.chat-minimized-btn {
  position: absolute;
  left: 16px;
  bottom: 16px;
  border: 1px solid rgba(56, 189, 248, 0.65);
  padding: 10px 16px;
  background: #0284c7;
  color: #ffffff;
}

.coach-main {
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
  color: #c8ddea;
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
  color: #c7d8e2;
}

.field input,
.field textarea {
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(127, 193, 221, 0.45);
  background: var(--input-bg);
  color: #e9f2f7;
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
  color: #c7d8e2;
}

.btn-suggestion {
  border: 1px solid rgba(127, 193, 221, 0.44);
  background: rgba(8, 34, 50, 0.7);
  color: #e9f2f7;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 9999px;
  cursor: pointer;
}

.btn-suggestion.active {
  background: rgba(14, 165, 233, 0.25);
  border-color: rgba(14, 165, 233, 0.7);
}

.action-row {
  display: flex;
  margin-top: 6px;
}

.btn-primary {
  border: none;
  padding: 11px 18px;
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.stat-card {
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(127, 193, 221, 0.25);
  background: rgba(2, 21, 31, 0.82);
}

.stat-card span {
  display: block;
  font-size: 11px;
  color: var(--muted);
}

.stat-card strong {
  display: block;
  margin-top: 4px;
  font-size: 15px;
  color: #d9f1fb;
}

.score-card,
.summary-card,
.list-card {
  margin-bottom: 14px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(4, 27, 40, 0.72);
  border: 1px solid var(--panel-border);
}

.score-value {
  font-size: 28px;
  font-weight: 800;
  color: #67e8f9;
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
  border: 1px solid rgba(127, 193, 221, 0.25);
  background: rgba(2, 21, 31, 0.82);
}

.nested-header {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.topic-chip-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-chip {
  display: inline-block;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 9999px;
  background: rgba(8, 34, 50, 0.7);
  border: 1px solid rgba(127, 193, 221, 0.44);
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

  .stats-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 960px) {
  .career-content {
    flex-direction: column;
  }

  .coach-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--panel-border);
    max-height: 320px;
  }

  .coach-main {
    padding: 18px 16px 28px;
  }

  .grid-2 {
    grid-template-columns: 1fr;
  }

  .career-header {
    padding: 14px 16px;
  }
}
</style>
