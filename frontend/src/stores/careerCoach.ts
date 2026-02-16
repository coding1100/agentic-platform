import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface CareerPathRecommendation {
  path: string
  fit_score: number
  rationale: string
  first_steps: string[]
}

export interface CareerMetricTarget {
  metric: string
  target: string
  cadence: string
}

export interface IntakeAssessmentReport {
  action: 'intake_assessment'
  status: 'ok' | 'error'
  profile_summary: string
  professional_brand: string
  strengths_to_leverage: string[]
  risks_to_address: string[]
  recommended_career_paths: CareerPathRecommendation[]
  immediate_priorities: string[]
  ninety_day_focus: string[]
  metrics_to_track: CareerMetricTarget[]
  assumptions: string[]
  confidence_score: number
  error?: string
  message?: string
}

export interface RoleTrackItem {
  role_title: string
  fit_score: number
  why_fit: string
  entry_points: string[]
}

export interface ChannelMixItem {
  channel: string
  target_share: string
  weekly_actions: string[]
}

export interface ThirtyDayExperiment {
  experiment: string
  success_metric: string
  time_budget_hours: number
}

export interface RiskCountermove {
  risk: string
  countermove: string
}

export interface OpportunityStrategyReport {
  action: 'opportunity_strategy'
  status: 'ok' | 'error'
  target_role: string
  market_fit_score: number
  strategy_summary: string
  positioning_statement: string
  top_role_tracks: RoleTrackItem[]
  application_channel_mix: ChannelMixItem[]
  market_signals_to_watch: string[]
  networking_plan: string[]
  portfolio_narrative: string[]
  thirty_day_experiments: ThirtyDayExperiment[]
  risks_and_countermoves: RiskCountermove[]
  assumptions: string[]
  error?: string
  message?: string
}

export interface RoadmapPhase {
  phase_name: string
  start_week: number
  end_week: number
  goal: string
  milestones: string[]
  deliverables: string[]
  success_criteria: string[]
}

export interface WeeklyRoadmapItem {
  week: number
  focus: string
  topics?: string[]
  tasks: string[]
  time_budget_hours: number
  output: string
}

export interface CareerRoadmapReport {
  action: 'build_roadmap'
  status: 'ok' | 'error'
  target_role: string
  timeline_weeks: number
  roadmap_summary: string
  phases: RoadmapPhase[]
  weekly_plan: WeeklyRoadmapItem[]
  application_strategy: {
    start_week: number
    target_applications_per_week: number
    target_referrals_per_month: number
    company_tiers: string[]
  }
  review_cadence: {
    weekly_checkin: string
    monthly_review: string
  }
  burnout_guardrails: string[]
  assumptions: string[]
  error?: string
  message?: string
}

export interface WeeklyBlocker {
  blocker: string
  impact: string
  next_step: string
  owner: string
}

export interface WeeklyAdjustment {
  change: string
  reason: string
}

export interface WeeklyCheckinReport {
  action: 'weekly_checkin'
  status: 'ok' | 'error'
  week_number: number
  progress_score: number
  progress_status: 'on_track' | 'at_risk' | 'off_track'
  completed_topics?: string[]
  matched_roadmap_topics?: string[]
  unmatched_topics?: string[]
  wins: string[]
  blockers: WeeklyBlocker[]
  plan_adjustments: WeeklyAdjustment[]
  next_week_plan: string[]
  motivation_note: string
  escalate_if: string[]
  assumptions: string[]
  error?: string
  message?: string
}

export interface ReadinessArea {
  area: string
  score: number
  gap: string
}

export interface InterviewTheme {
  theme: string
  sample_questions: string[]
  what_good_looks_like: string[]
}

export interface StoryBankItem {
  story_title: string
  competencies: string[]
  outline: string[]
}

export interface MockScheduleItem {
  week: number
  focus: string
  session_goal: string
}

export interface InterviewReadinessReport {
  action: 'interview_readiness'
  status: 'ok' | 'error'
  target_role: string
  readiness_score: number
  readiness_breakdown: ReadinessArea[]
  top_question_themes: InterviewTheme[]
  story_bank: StoryBankItem[]
  technical_round_plan: string[]
  behavioral_round_plan: string[]
  mock_schedule: MockScheduleItem[]
  negotiation_prep: string[]
  final_30_day_checklist: string[]
  assumptions: string[]
  error?: string
  message?: string
}

export const useCareerCoachStore = defineStore('careerCoach', () => {
  const currentRole = ref('')
  const targetRole = ref('')
  const yearsExperience = ref<number>(5)
  const primaryIndustry = ref('')
  const locationPreference = ref('')
  const preferredWorkModel = ref('')
  const compensationGoal = ref('')
  const weeklyHours = ref<number>(6)
  const timelineWeeks = ref<number>(12)
  const currentSkillsInput = ref('')
  const achievementsInput = ref('')
  const constraintsInput = ref('')
  const careerInterestsInput = ref('')
  const targetJobDescription = ref('')

  const weekNumber = ref<number>(1)
  const completedTopicsInput = ref('')
  const completedTasksInput = ref('')
  const blockedTasksInput = ref('')
  const winsInput = ref('')
  const timeSpentHours = ref<number>(0)
  const checkinNotes = ref('')
  const interviewTypesInput = ref('')
  const upcomingInterviewContext = ref('')

  const loading = ref(false)
  const error = ref<string | null>(null)
  const conversationId = ref<string | null>(null)

  const intakeReport = ref<IntakeAssessmentReport | null>(null)
  const opportunityStrategyReport = ref<OpportunityStrategyReport | null>(null)
  const roadmapReport = ref<CareerRoadmapReport | null>(null)
  const weeklyCheckinReport = ref<WeeklyCheckinReport | null>(null)
  const interviewReadinessReport = ref<InterviewReadinessReport | null>(null)

  function setConversationId(id: string | null) {
    conversationId.value = id
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(message: string | null) {
    error.value = message
  }

  function resetReports() {
    intakeReport.value = null
    opportunityStrategyReport.value = null
    roadmapReport.value = null
    weeklyCheckinReport.value = null
    interviewReadinessReport.value = null
  }

  function resetAll() {
    currentRole.value = ''
    targetRole.value = ''
    yearsExperience.value = 5
    primaryIndustry.value = ''
    locationPreference.value = ''
    preferredWorkModel.value = ''
    compensationGoal.value = ''
    weeklyHours.value = 6
    timelineWeeks.value = 12
    currentSkillsInput.value = ''
    achievementsInput.value = ''
    constraintsInput.value = ''
    careerInterestsInput.value = ''
    targetJobDescription.value = ''
    weekNumber.value = 1
    completedTopicsInput.value = ''
    completedTasksInput.value = ''
    blockedTasksInput.value = ''
    winsInput.value = ''
    timeSpentHours.value = 0
    checkinNotes.value = ''
    interviewTypesInput.value = ''
    upcomingInterviewContext.value = ''
    loading.value = false
    error.value = null
    conversationId.value = null
    resetReports()
  }

  return {
    currentRole,
    targetRole,
    yearsExperience,
    primaryIndustry,
    locationPreference,
    preferredWorkModel,
    compensationGoal,
    weeklyHours,
    timelineWeeks,
    currentSkillsInput,
    achievementsInput,
    constraintsInput,
    careerInterestsInput,
    targetJobDescription,
    weekNumber,
    completedTopicsInput,
    completedTasksInput,
    blockedTasksInput,
    winsInput,
    timeSpentHours,
    checkinNotes,
    interviewTypesInput,
    upcomingInterviewContext,
    loading,
    error,
    conversationId,
    intakeReport,
    opportunityStrategyReport,
    roadmapReport,
    weeklyCheckinReport,
    interviewReadinessReport,
    setConversationId,
    setLoading,
    setError,
    resetReports,
    resetAll,
  }
})
