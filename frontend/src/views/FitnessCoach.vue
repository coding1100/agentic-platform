<template>
  <div class="fitness-shell">
    <header class="hero">
      <div class="hero-left">
        <button class="btn ghost" @click="goBack">&larr; Dashboard</button>
        <div>
          <h1>{{ agent?.name || 'Fitness Coach Agent' }}</h1>
          <p>Adaptive plans, quick bursts, challenge mode, and progress loops.</p>
        </div>
      </div>
      <div class="hero-right">
        <div class="stat-pill">Level {{ fitnessCoachStore.levelEstimate }}</div>
        <div class="stat-pill">{{ fitnessCoachStore.totalXp }} XP</div>
        <div class="stat-pill">Streak {{ fitnessCoachStore.currentStreakDays }}d</div>
        <button class="btn ghost" @click="handleLogout">Logout</button>
      </div>
    </header>

    <main class="layout">
      <section class="stack">
        <article class="card">
          <h2>Baseline Scan</h2>
          <div class="chip-row">
            <button v-for="goal in goalChips" :key="goal" class="chip" @click="fitnessCoachStore.primaryGoal = goal">{{ goal }}</button>
          </div>
          <div class="grid two">
            <label>Primary Goal<input v-model="fitnessCoachStore.primaryGoal" type="text" placeholder="Fat loss, muscle gain, stamina..." /></label>
            <label>Fitness Level
              <select v-model="fitnessCoachStore.fitnessLevel">
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </label>
          </div>
          <div class="grid four">
            <label>Age<input v-model.number="fitnessCoachStore.age" type="number" min="13" max="90" /></label>
            <label>Weight kg<input v-model.number="fitnessCoachStore.weightKg" type="number" min="30" max="300" /></label>
            <label>Sessions / Week<input v-model.number="fitnessCoachStore.workoutDaysPerWeek" type="number" min="1" max="7" /></label>
            <label>Minutes / Session<input v-model.number="fitnessCoachStore.sessionDurationMinutes" type="number" min="10" max="180" /></label>
          </div>
          <div class="grid two">
            <label>Equipment<textarea v-model="fitnessCoachStore.equipmentInput" placeholder="Dumbbells, mat, resistance bands..." /></label>
            <label>Constraints / Injury History<textarea v-model="fitnessCoachStore.constraintsInput" placeholder="Lower-back sensitivity, travel weeks, sleep stress..." /></label>
          </div>
          <button class="btn primary" :disabled="fitnessCoachStore.loading" @click="runProfileBaseline">
            {{ fitnessCoachStore.loading ? 'Running...' : 'Generate Baseline' }}
          </button>
        </article>

        <article class="card">
          <h2>Adaptive Plan Builder</h2>
          <div class="grid two">
            <label>Timeline Weeks<input v-model.number="fitnessCoachStore.timelineWeeks" type="number" min="2" max="52" /></label>
            <label>Available Days<textarea v-model="fitnessCoachStore.availableDaysInput" placeholder="Mon, Tue, Thu, Sat..." /></label>
          </div>
          <button class="btn primary" :disabled="fitnessCoachStore.loading || !fitnessCoachStore.primaryGoal.trim()" @click="runAdaptivePlan">
            {{ fitnessCoachStore.loading ? 'Building...' : 'Build Adaptive Plan' }}
          </button>
        </article>

        <article class="card">
          <h2>Quick Workout Burst</h2>
          <p class="hint">For low-time days and high consistency. Ideal for mobile-first routines.</p>
          <div class="grid three">
            <label>Time Available (min)<input v-model.number="fitnessCoachStore.timeAvailableMinutes" type="number" min="5" max="90" /></label>
            <label>Location
              <select v-model="fitnessCoachStore.workoutLocation">
                <option value="home">Home</option>
                <option value="gym">Gym</option>
                <option value="outdoors">Outdoors</option>
              </select>
            </label>
            <label>Preferred Vibe<textarea v-model="fitnessCoachStore.preferredWorkoutsInput" placeholder="HIIT, dance-cardio, strength circuits..." /></label>
          </div>
          <button class="btn primary" :disabled="fitnessCoachStore.loading" @click="runQuickWorkoutBurst">
            {{ fitnessCoachStore.loading ? 'Generating...' : 'Create Quick Burst' }}
          </button>
        </article>

        <article class="card">
          <h2>Weekly Feedback Loop</h2>
          <div class="grid four">
            <label>Week<input v-model.number="fitnessCoachStore.weekNumber" type="number" min="1" max="520" /></label>
            <label>Adherence %<input v-model.number="fitnessCoachStore.adherencePercent" type="number" min="0" max="100" /></label>
            <label>Energy (1-10)<input v-model.number="fitnessCoachStore.energyLevel" type="number" min="1" max="10" /></label>
            <label>Soreness (1-10)<input v-model.number="fitnessCoachStore.sorenessLevel" type="number" min="1" max="10" /></label>
          </div>
          <div class="grid two">
            <label>Completed Sessions<textarea v-model="fitnessCoachStore.completedSessionsInput" placeholder="Day + session focus + notes" /></label>
            <label>Pain Points / Wins<textarea v-model="feedbackCompositeInput" placeholder="Pain points, wins, friction points..." /></label>
          </div>
          <button class="btn primary" :disabled="fitnessCoachStore.loading" @click="runWorkoutFeedback">
            {{ fitnessCoachStore.loading ? 'Adapting...' : 'Adapt Next Week' }}
          </button>
        </article>

        <article class="card">
          <h2>Challenge Mode</h2>
          <p class="hint">Streak missions, weekly bonus tasks, and reward milestones.</p>
          <div class="grid three">
            <label>Challenge Name<input v-model="fitnessCoachStore.challengeName" type="text" /></label>
            <label>Duration (days)<input v-model.number="fitnessCoachStore.challengeDurationDays" type="number" min="3" max="60" /></label>
            <label>Challenge Preferences<textarea v-model="fitnessCoachStore.challengePreferencesInput" placeholder="No jumping, outdoors allowed, social prompts..." /></label>
          </div>
          <button class="btn primary" :disabled="fitnessCoachStore.loading || !fitnessCoachStore.primaryGoal.trim()" @click="runChallengeMode">
            {{ fitnessCoachStore.loading ? 'Designing...' : 'Launch Challenge Mode' }}
          </button>
        </article>

        <article class="card">
          <h2>Progress Reassessment</h2>
          <label>Tracked Metrics<textarea v-model="fitnessCoachStore.feedbackNotes" placeholder="Weight trend, reps, pace, resting HR, sleep..." /></label>
          <button class="btn primary" :disabled="fitnessCoachStore.loading || !fitnessCoachStore.primaryGoal.trim()" @click="runProgressReassessment">
            {{ fitnessCoachStore.loading ? 'Reassessing...' : 'Run Reassessment' }}
          </button>
        </article>

        <p v-if="fitnessCoachStore.error" class="error">{{ fitnessCoachStore.error }}</p>
      </section>

      <section class="stack">
        <article class="card spotlight" v-if="fitnessCoachStore.activeQuestPrompt">
          <h2>Quest Prompt</h2>
          <p>{{ fitnessCoachStore.activeQuestPrompt }}</p>
        </article>

        <article class="card" v-if="fitnessCoachStore.unlockedBadges.length">
          <h2>Unlocked Badges</h2>
          <div class="badge-grid">
            <span v-for="badge in fitnessCoachStore.unlockedBadges" :key="badge" class="badge">{{ badge }}</span>
          </div>
        </article>

        <article class="card" v-if="fitnessCoachStore.baselineReport?.status === 'ok'">
          <h2>Baseline Report</h2>
          <p class="big">{{ fitnessCoachStore.baselineReport.training_readiness_score }}/100 readiness</p>
          <p>{{ fitnessCoachStore.baselineReport.profile_summary }}</p>
          <ul>
            <li v-for="item in fitnessCoachStore.baselineReport.recommended_focus_areas" :key="item">{{ item }}</li>
          </ul>
        </article>

        <article class="card" v-if="fitnessCoachStore.adaptivePlanReport?.status === 'ok'">
          <h2>Adaptive Plan</h2>
          <p>{{ fitnessCoachStore.adaptivePlanReport.plan_summary }}</p>
          <div class="session-list">
            <div v-for="(session, idx) in fitnessCoachStore.adaptivePlanReport.weekly_schedule" :key="session.day + idx" class="session-item">
              <div class="session-head">
                <strong>{{ session.day }} - {{ session.focus }}</strong>
                <span>{{ session.duration_minutes }} min</span>
              </div>
              <p>{{ session.intensity }} intensity | {{ session.session_type }}</p>
            </div>
          </div>
          <p v-if="fitnessCoachStore.adaptivePlanReport.share_card_text" class="share">{{ fitnessCoachStore.adaptivePlanReport.share_card_text }}</p>
        </article>

        <article class="card" v-if="fitnessCoachStore.quickWorkoutReport?.status === 'ok'">
          <h2>Quick Burst</h2>
          <p class="big">{{ fitnessCoachStore.quickWorkoutReport.workout_title }}</p>
          <p>{{ fitnessCoachStore.quickWorkoutReport.format }} | {{ fitnessCoachStore.quickWorkoutReport.time_available_minutes }} min</p>
          <ul>
            <li v-for="block in fitnessCoachStore.quickWorkoutReport.main_set" :key="block.block_name">
              {{ block.block_name }} ({{ block.duration_minutes }} min)
            </li>
          </ul>
          <p v-if="fitnessCoachStore.quickWorkoutReport.share_card_text" class="share">{{ fitnessCoachStore.quickWorkoutReport.share_card_text }}</p>
        </article>

        <article class="card" v-if="fitnessCoachStore.workoutFeedbackReport?.status === 'ok'">
          <h2>Feedback Adaptation</h2>
          <p class="big">{{ fitnessCoachStore.workoutFeedbackReport.adherence_score }}/100 adherence</p>
          <p>{{ fitnessCoachStore.workoutFeedbackReport.coach_message }}</p>
          <ul>
            <li v-for="adj in fitnessCoachStore.workoutFeedbackReport.plan_adjustments" :key="adj.change + adj.reason">{{ adj.change }} - {{ adj.reason }}</li>
          </ul>
          <p v-if="fitnessCoachStore.workoutFeedbackReport.social_accountability_prompt" class="share">
            {{ fitnessCoachStore.workoutFeedbackReport.social_accountability_prompt }}
          </p>
        </article>

        <article class="card" v-if="fitnessCoachStore.challengeModeReport?.status === 'ok'">
          <h2>{{ fitnessCoachStore.challengeModeReport.challenge_name }}</h2>
          <p>{{ fitnessCoachStore.challengeModeReport.challenge_duration_days }}-day challenge</p>
          <ul>
            <li v-for="mission in previewMissions" :key="mission.day + mission.mission">
              Day {{ mission.day }}: {{ mission.mission }} ({{ mission.duration_minutes }} min)
            </li>
          </ul>
          <p class="share">{{ fitnessCoachStore.challengeModeReport.friend_challenge_prompt }}</p>
        </article>

        <article class="card" v-if="fitnessCoachStore.progressReassessmentReport?.status === 'ok'">
          <h2>Progress Reassessment</h2>
          <p class="big">{{ fitnessCoachStore.progressReassessmentReport.goal_progress_score }}/100 goal progress</p>
          <p>{{ fitnessCoachStore.progressReassessmentReport.goal_progress_summary }}</p>
          <ul>
            <li v-for="target in fitnessCoachStore.progressReassessmentReport.updated_targets" :key="target.metric + target.deadline">
              {{ target.metric }}: {{ target.target }} by {{ target.deadline }}
            </li>
          </ul>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'
import { useFitnessCoachStore } from '@/stores/fitnessCoach'
import type { ChallengeMission } from '@/stores/fitnessCoach'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const fitnessCoachStore = useFitnessCoachStore()

const agentId = route.params.agentId as string
const goalChips = ['Fat loss', 'Lean muscle', 'Athletic stamina', 'Daily energy']
const feedbackCompositeInput = ref('')

const agent = computed(() => agentsStore.selectedAgent)
const previewMissions = computed<ChallengeMission[]>(() => {
  const missions = fitnessCoachStore.challengeModeReport?.daily_missions || []
  return missions.slice(0, 5)
})

onMounted(async () => {
  await agentsStore.fetchAgent(agentId)
  const urlConversationId = route.query.conversation_id as string
  const existing = urlConversationId || fitnessCoachStore.conversationId

  if (existing) {
    await chatStore.fetchConversation(existing, true)
    fitnessCoachStore.setConversationId(existing)
    if (!urlConversationId) {
      router.replace({ path: route.path, query: { ...route.query, conversation_id: existing } })
    }
  } else {
    const result = await chatStore.createConversation(agentId)
    if (result.success && result.conversation) {
      await chatStore.fetchConversation(result.conversation.id, true)
      fitnessCoachStore.setConversationId(result.conversation.id)
      router.replace({ path: route.path, query: { ...route.query, conversation_id: result.conversation.id } })
    }
  }
})

watch(feedbackCompositeInput, (value) => {
  const lines = value.split('\n')
  const pain: string[] = []
  const wins: string[] = []
  for (const rawLine of lines) {
    const line = rawLine.trim()
    if (!line) continue
    const lower = line.toLowerCase()
    if (lower.startsWith('win:')) {
      wins.push(line.slice(4).trim())
    } else {
      pain.push(line)
    }
  }
  fitnessCoachStore.painPointsInput = pain.join('\n')
  fitnessCoachStore.winsInput = wins.join('\n')
})

function parseListInput(input: string): string[] {
  return input
    .split(/[\n,;]/g)
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
}

function parseAssistantJson(raw: string): Record<string, unknown> | null {
  const trimmed = (raw || '').trim()
  const first = trimmed.indexOf('{')
  const last = trimmed.lastIndexOf('}')
  if (first === -1 || last === -1 || last <= first) return null
  try {
    return JSON.parse(trimmed.slice(first, last + 1))
  } catch {
    return null
  }
}

async function sendFitnessAction(action: string, payload: Record<string, unknown>) {
  fitnessCoachStore.setError(null)
  fitnessCoachStore.setLoading(true)
  try {
    const message = `FITNESS_COACH_REQUEST\n${JSON.stringify({ action, payload }, null, 2)}`
    const result = await chatStore.sendMessage(
      agentId,
      message,
      fitnessCoachStore.conversationId || chatStore.activeConversationId || undefined,
    )
    if (!result.success) {
      fitnessCoachStore.setError(result.error || 'Failed to run fitness action')
      return null
    }

    if (chatStore.activeConversationId) {
      fitnessCoachStore.setConversationId(chatStore.activeConversationId)
    }

    const latestAssistant = [...chatStore.messages].reverse().find((m) => m.role === 'assistant' && !!m.content)
    if (!latestAssistant) {
      fitnessCoachStore.setError('No assistant response received.')
      return null
    }
    const parsed = parseAssistantJson(latestAssistant.content)
    if (!parsed) {
      fitnessCoachStore.setError('Could not parse structured response from Fitness Coach Agent.')
      return null
    }
    if (parsed['status'] === 'error' || parsed['error']) {
      fitnessCoachStore.setError(String(parsed['message'] || parsed['error'] || 'Fitness action failed.'))
      return null
    }
    if (typeof parsed['gamification'] === 'object' && parsed['gamification']) {
      fitnessCoachStore.applyGamification(parsed['gamification'] as any)
    }
    return parsed
  } finally {
    fitnessCoachStore.setLoading(false)
  }
}

function buildProfilePayload() {
  const payload: Record<string, unknown> = {
    primary_goal: fitnessCoachStore.primaryGoal,
    fitness_level: fitnessCoachStore.fitnessLevel,
    experience_level: fitnessCoachStore.experienceLevel,
    age: fitnessCoachStore.age,
    height_cm: fitnessCoachStore.heightCm,
    weight_kg: fitnessCoachStore.weightKg,
    workout_days_per_week: fitnessCoachStore.workoutDaysPerWeek,
    session_duration_minutes: fitnessCoachStore.sessionDurationMinutes,
    timeline_weeks: fitnessCoachStore.timelineWeeks,
    current_streak_days: fitnessCoachStore.currentStreakDays,
  }
  const equipment = parseListInput(fitnessCoachStore.equipmentInput)
  if (equipment.length > 0) payload.equipment_available = equipment
  const constraints = parseListInput(fitnessCoachStore.constraintsInput)
  if (constraints.length > 0) payload.constraints = constraints
  const injuries = parseListInput(fitnessCoachStore.injuryHistoryInput)
  if (injuries.length > 0) payload.injury_history = injuries
  const preferredWorkouts = parseListInput(fitnessCoachStore.preferredWorkoutsInput)
  if (preferredWorkouts.length > 0) payload.preferred_workouts = preferredWorkouts
  const availableDays = parseListInput(fitnessCoachStore.availableDaysInput)
  if (availableDays.length > 0) payload.available_days = availableDays
  const dislikes = parseListInput(fitnessCoachStore.dislikedExercisesInput)
  if (dislikes.length > 0) payload.disliked_exercises = dislikes
  return payload
}

async function runProfileBaseline() {
  if (!fitnessCoachStore.primaryGoal.trim() && !fitnessCoachStore.equipmentInput.trim()) {
    fitnessCoachStore.setError('Provide at least a primary goal or equipment context.')
    return
  }
  const parsed = await sendFitnessAction('profile_baseline', buildProfilePayload())
  if (parsed && parsed['action'] === 'profile_baseline') {
    fitnessCoachStore.baselineReport = parsed as any
  }
}

async function runAdaptivePlan() {
  if (!fitnessCoachStore.primaryGoal.trim()) {
    fitnessCoachStore.setError('Primary goal is required.')
    return
  }
  const parsed = await sendFitnessAction('generate_adaptive_plan', {
    ...buildProfilePayload(),
    baseline_report: fitnessCoachStore.baselineReport,
  })
  if (parsed && parsed['action'] === 'generate_adaptive_plan') {
    fitnessCoachStore.adaptivePlanReport = parsed as any
  }
}

async function runQuickWorkoutBurst() {
  const parsed = await sendFitnessAction('quick_workout_burst', {
    ...buildProfilePayload(),
    time_available_minutes: fitnessCoachStore.timeAvailableMinutes,
    workout_location: fitnessCoachStore.workoutLocation,
  })
  if (parsed && parsed['action'] === 'quick_workout_burst') {
    fitnessCoachStore.quickWorkoutReport = parsed as any
  }
}

async function runWorkoutFeedback() {
  if (!fitnessCoachStore.adaptivePlanReport || fitnessCoachStore.adaptivePlanReport.status !== 'ok') {
    fitnessCoachStore.setError('Build an adaptive plan before running feedback adaptation.')
    return
  }
  const completed = parseListInput(fitnessCoachStore.completedSessionsInput)
  if (!completed.length) {
    fitnessCoachStore.setError('Completed sessions are required.')
    return
  }
  const parsed = await sendFitnessAction('log_workout_feedback', {
    week_number: fitnessCoachStore.weekNumber,
    adherence_percent: fitnessCoachStore.adherencePercent,
    energy_level: fitnessCoachStore.energyLevel,
    soreness_level: fitnessCoachStore.sorenessLevel,
    sleep_hours: fitnessCoachStore.sleepHours,
    completed_sessions: completed,
    pain_points: parseListInput(fitnessCoachStore.painPointsInput),
    wins: parseListInput(fitnessCoachStore.winsInput),
    plan_report: fitnessCoachStore.adaptivePlanReport,
    primary_goal: fitnessCoachStore.primaryGoal,
  })
  if (parsed && parsed['action'] === 'log_workout_feedback') {
    fitnessCoachStore.workoutFeedbackReport = parsed as any
    fitnessCoachStore.weekNumber += 1
  }
}

async function runChallengeMode() {
  if (!fitnessCoachStore.primaryGoal.trim()) {
    fitnessCoachStore.setError('Primary goal is required for challenge mode.')
    return
  }
  const parsed = await sendFitnessAction('challenge_mode', {
    ...buildProfilePayload(),
    challenge_name: fitnessCoachStore.challengeName,
    challenge_duration_days: fitnessCoachStore.challengeDurationDays,
    challenge_preferences: parseListInput(fitnessCoachStore.challengePreferencesInput),
  })
  if (parsed && parsed['action'] === 'challenge_mode') {
    fitnessCoachStore.challengeModeReport = parsed as any
  }
}

async function runProgressReassessment() {
  if (!fitnessCoachStore.primaryGoal.trim()) {
    fitnessCoachStore.setError('Primary goal is required.')
    return
  }
  const parsed = await sendFitnessAction('progress_reassessment', {
    ...buildProfilePayload(),
    baseline_report: fitnessCoachStore.baselineReport,
    plan_report: fitnessCoachStore.adaptivePlanReport,
    feedback_report: fitnessCoachStore.workoutFeedbackReport,
    challenge_report: fitnessCoachStore.challengeModeReport,
    tracked_metrics: parseListInput(fitnessCoachStore.feedbackNotes),
  })
  if (parsed && parsed['action'] === 'progress_reassessment') {
    fitnessCoachStore.progressReassessmentReport = parsed as any
  }
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
.fitness-shell {
  min-height: 100vh;
  background:
    radial-gradient(90rem 50rem at 12% -10%, rgba(0, 255, 170, 0.16), transparent 60%),
    radial-gradient(70rem 40rem at 95% 10%, rgba(255, 149, 0, 0.15), transparent 55%),
    linear-gradient(145deg, #0e1f2f 0%, #153447 45%, #1a483b 100%);
  color: #f4fff8;
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(190, 255, 230, 0.24);
  background: rgba(6, 21, 30, 0.62);
  backdrop-filter: blur(14px);
}

.hero-left {
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.hero h1 {
  margin: 0;
  font-size: 30px;
  line-height: 1.08;
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
}

.hero p {
  margin: 4px 0 0;
  color: #bfdbd1;
  font-size: 13px;
}

.hero-right {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.stat-pill {
  border: 1px solid rgba(183, 255, 226, 0.35);
  background: rgba(10, 33, 24, 0.72);
  border-radius: 999px;
  padding: 7px 12px;
  font-size: 12px;
  font-weight: 700;
}

.layout {
  max-width: 1400px;
  margin: 0 auto;
  padding: 22px;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 16px;
}

.stack {
  display: grid;
  gap: 14px;
  align-content: start;
}

.card {
  border: 1px solid rgba(183, 255, 226, 0.22);
  border-radius: 18px;
  padding: 16px;
  background: linear-gradient(155deg, rgba(8, 29, 40, 0.86), rgba(13, 35, 27, 0.82));
  box-shadow: 0 14px 40px rgba(2, 14, 20, 0.35);
}

.spotlight {
  background: linear-gradient(135deg, rgba(0, 109, 87, 0.42), rgba(10, 53, 61, 0.75));
}

.card h2 {
  margin: 0 0 10px;
  font-size: 18px;
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
}

.hint {
  margin: -2px 0 10px;
  color: #b9d8c7;
  font-size: 12px;
}

.chip-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.chip {
  border: 1px solid rgba(183, 255, 226, 0.35);
  background: rgba(13, 40, 27, 0.7);
  color: #e6fff3;
  border-radius: 999px;
  padding: 7px 11px;
  font-size: 12px;
  cursor: pointer;
}

.grid {
  display: grid;
  gap: 10px;
  margin-bottom: 10px;
}

.two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.four {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #d6f6e7;
}

input,
textarea,
select {
  width: 100%;
  border: 1px solid rgba(183, 255, 226, 0.34);
  border-radius: 11px;
  padding: 9px 11px;
  background: rgba(5, 21, 30, 0.82);
  color: #f4fff8;
  font-size: 13px;
}

textarea {
  min-height: 74px;
  resize: vertical;
}

.btn {
  border-radius: 999px;
  padding: 8px 14px;
  border: 1px solid rgba(183, 255, 226, 0.38);
  color: #ebfff6;
  font-weight: 700;
  cursor: pointer;
}

.ghost {
  background: rgba(17, 43, 57, 0.72);
}

.primary {
  border: none;
  background: linear-gradient(130deg, #00c27f, #00a8c9);
}

.primary:disabled {
  opacity: 0.66;
  cursor: not-allowed;
}

.badge-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.badge {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 7px 11px;
  font-size: 12px;
  border: 1px solid rgba(230, 255, 247, 0.35);
  background: rgba(8, 64, 44, 0.74);
}

.big {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.2px;
}

.session-list {
  display: grid;
  gap: 8px;
}

.session-item {
  border: 1px solid rgba(183, 255, 226, 0.2);
  border-radius: 12px;
  padding: 9px 10px;
  background: rgba(9, 34, 24, 0.5);
}

.session-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.share {
  margin: 8px 0 0;
  font-size: 12px;
  color: #afe8d0;
}

ul {
  margin: 8px 0 0;
  padding-left: 18px;
}

li {
  margin-bottom: 6px;
}

.error {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid rgba(248, 113, 113, 0.6);
  background: rgba(127, 29, 29, 0.3);
  border-radius: 10px;
  color: #fecaca;
}

@media (max-width: 1200px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .hero {
    flex-direction: column;
    align-items: flex-start;
  }

  .hero-right {
    justify-content: flex-start;
  }

  .two,
  .three,
  .four {
    grid-template-columns: 1fr;
  }
}
</style>
