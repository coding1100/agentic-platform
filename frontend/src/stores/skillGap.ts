import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface CapabilitySnapshotItem {
  skill: string
  current_level: string
  evidence: string
}

export interface SkillGapBaselineReport {
  action: 'profile_baseline'
  status: 'ok' | 'error'
  profile_summary: string
  current_capability_snapshot: CapabilitySnapshotItem[]
  strengths: string[]
  risks: string[]
  focus_areas: string[]
  manager_alignment_questions: string[]
  confidence_score: number
  assumptions: string[]
  error?: string
  message?: string
}

export interface CriticalSkillGapItem {
  skill: string
  priority: string
  current_level: string
  target_level: string
  business_impact: string
  development_recommendation: string
}

export interface SkillGapAnalysisReport {
  action: 'identify_skill_gaps'
  status: 'ok' | 'error'
  target_role: string
  overall_gap_score: number
  critical_skill_gaps: CriticalSkillGapItem[]
  adjacent_skills_to_build: string[]
  role_expectation_keywords: string[]
  quick_wins: string[]
  manager_support_requests: string[]
  assumptions: string[]
  error?: string
  message?: string
}

export interface DevelopmentPhase {
  phase_name: string
  start_week: number
  end_week: number
  goal: string
  deliverables: string[]
  activities: string[]
  success_criteria: string[]
}

export interface WeeklyLearningPlanItem {
  week: number
  focus: string
  activities: string[]
  time_budget_hours: number
  evidence_output: string
}

export interface EnablementResource {
  resource_type: string
  name: string
  purpose: string
  estimated_hours: number
}

export interface ManagerCheckpoint {
  week: number
  agenda: string
  expected_outcomes: string[]
}

export interface SkillDevelopmentPlanReport {
  action: 'build_development_plan'
  status: 'ok' | 'error'
  target_role: string
  timeline_weeks: number
  plan_summary: string
  phases: DevelopmentPhase[]
  weekly_learning_plan: WeeklyLearningPlanItem[]
  enablement_resources: EnablementResource[]
  manager_checkpoints: ManagerCheckpoint[]
  risk_mitigation: string[]
  assumptions: string[]
  error?: string
  message?: string
}

export interface ProgressBlocker {
  blocker: string
  impact: string
  next_step: string
  owner: string
}

export interface ProgressAdjustment {
  change: string
  reason: string
  effective_week: number
}

export interface SkillGapWeeklyCheckinReport {
  action: 'weekly_progress_checkin'
  status: 'ok' | 'error'
  week_number: number
  progress_score: number
  trajectory: 'on_track' | 'at_risk' | 'off_track'
  wins: string[]
  blockers: ProgressBlocker[]
  plan_adjustments: ProgressAdjustment[]
  next_week_priorities: string[]
  support_needed: string[]
  assumptions: string[]
  error?: string
  message?: string
}

export interface ReadinessCompetency {
  competency: string
  score: number
  gap: string
  evidence_needed: string
}

export interface SkillReadinessReport {
  action: 'readiness_assessment'
  status: 'ok' | 'error'
  target_role: string
  readiness_score: number
  competency_breakdown: ReadinessCompetency[]
  strongest_signals: string[]
  remaining_gaps: string[]
  thirty_day_focus: string[]
  stakeholder_alignment_plan: string[]
  decision_risks: string[]
  assumptions: string[]
  error?: string
  message?: string
}

export const useSkillGapStore = defineStore('skillGap', () => {
  const currentRole = ref('')
  const targetRole = ref('')
  const department = ref('')
  const yearsExperience = ref<number>(4)
  const weeklyLearningHours = ref<number>(5)
  const timelineWeeks = ref<number>(12)

  const currentSkillsInput = ref('')
  const targetSkillsInput = ref('')
  const constraintsInput = ref('')
  const focusAreasInput = ref('')
  const projectsInput = ref('')
  const performanceNotes = ref('')
  const roleExpectationsInput = ref('')
  const learningPreferencesInput = ref('')
  const managerFeedbackInput = ref('')
  const peerFeedbackInput = ref('')

  const weekNumber = ref<number>(1)
  const completedActivitiesInput = ref('')
  const blockedActivitiesInput = ref('')
  const winsInput = ref('')
  const supportNeededInput = ref('')
  const evidenceLinksInput = ref('')
  const learningHoursSpent = ref<number>(0)
  const checkinNotes = ref('')

  const loading = ref(false)
  const error = ref<string | null>(null)
  const conversationId = ref<string | null>(null)

  const baselineReport = ref<SkillGapBaselineReport | null>(null)
  const gapReport = ref<SkillGapAnalysisReport | null>(null)
  const planReport = ref<SkillDevelopmentPlanReport | null>(null)
  const weeklyCheckinReport = ref<SkillGapWeeklyCheckinReport | null>(null)
  const readinessReport = ref<SkillReadinessReport | null>(null)

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
    baselineReport.value = null
    gapReport.value = null
    planReport.value = null
    weeklyCheckinReport.value = null
    readinessReport.value = null
  }

  function resetAll() {
    currentRole.value = ''
    targetRole.value = ''
    department.value = ''
    yearsExperience.value = 4
    weeklyLearningHours.value = 5
    timelineWeeks.value = 12
    currentSkillsInput.value = ''
    targetSkillsInput.value = ''
    constraintsInput.value = ''
    focusAreasInput.value = ''
    projectsInput.value = ''
    performanceNotes.value = ''
    roleExpectationsInput.value = ''
    learningPreferencesInput.value = ''
    managerFeedbackInput.value = ''
    peerFeedbackInput.value = ''
    weekNumber.value = 1
    completedActivitiesInput.value = ''
    blockedActivitiesInput.value = ''
    winsInput.value = ''
    supportNeededInput.value = ''
    evidenceLinksInput.value = ''
    learningHoursSpent.value = 0
    checkinNotes.value = ''
    loading.value = false
    error.value = null
    conversationId.value = null
    resetReports()
  }

  return {
    currentRole,
    targetRole,
    department,
    yearsExperience,
    weeklyLearningHours,
    timelineWeeks,
    currentSkillsInput,
    targetSkillsInput,
    constraintsInput,
    focusAreasInput,
    projectsInput,
    performanceNotes,
    roleExpectationsInput,
    learningPreferencesInput,
    managerFeedbackInput,
    peerFeedbackInput,
    weekNumber,
    completedActivitiesInput,
    blockedActivitiesInput,
    winsInput,
    supportNeededInput,
    evidenceLinksInput,
    learningHoursSpent,
    checkinNotes,
    loading,
    error,
    conversationId,
    baselineReport,
    gapReport,
    planReport,
    weeklyCheckinReport,
    readinessReport,
    setConversationId,
    setLoading,
    setError,
    resetReports,
    resetAll,
  }
})
