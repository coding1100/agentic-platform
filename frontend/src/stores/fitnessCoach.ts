import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface GamificationPayload {
  xp_awarded: number
  streak_delta: number
  level_estimate: number
  badges_unlocked: string[]
  quest_prompt: string
}

export interface WeeklyTrainingTarget {
  sessions: number
  minutes_per_session: number
  intensity_distribution: {
    easy: number
    moderate: number
    hard: number
  }
}

export interface FitnessBaselineReport {
  action: 'profile_baseline'
  status: 'ok' | 'error'
  profile_summary: string
  training_readiness_score: number
  risk_flags: string[]
  recommended_focus_areas: string[]
  weekly_training_target: WeeklyTrainingTarget
  mobility_priorities: string[]
  gamification?: GamificationPayload
  assumptions: string[]
  error?: string
  message?: string
}

export interface AdaptiveWeeklySession {
  day: string
  focus: string
  session_type: string
  duration_minutes: number
  intensity: string
  workout_blocks: string[]
  progression_note: string
}

export interface ExerciseSubstitution {
  movement_pattern: string
  preferred_option: string
  backup_option: string
  when_to_use: string
}

export interface AdaptiveWorkoutPlanReport {
  action: 'generate_adaptive_plan'
  status: 'ok' | 'error'
  primary_goal: string
  timeline_weeks: number
  plan_summary: string
  weekly_schedule: AdaptiveWeeklySession[]
  progression_strategy: string[]
  exercise_substitutions: ExerciseSubstitution[]
  music_vibe_recommendations?: string[]
  recovery_protocol: string[]
  safety_notes: string[]
  gamification?: GamificationPayload
  share_card_text?: string
  assumptions: string[]
  error?: string
  message?: string
}

export interface QuickWorkoutBlock {
  block_name: string
  duration_minutes: number
  instructions: string[]
}

export interface QuickWorkoutBurstReport {
  action: 'quick_workout_burst'
  status: 'ok' | 'error'
  time_available_minutes: number
  workout_location: string
  workout_title: string
  format: string
  warmup: string[]
  main_set: QuickWorkoutBlock[]
  cooldown: string[]
  intensity_target: string
  equipment_substitutions: string[]
  safety_notes: string[]
  gamification?: GamificationPayload
  share_card_text?: string
  assumptions: string[]
  error?: string
  message?: string
}

export interface WorkoutPlanAdjustment {
  change: string
  reason: string
  effective_from: string
}

export interface WorkoutFeedbackReport {
  action: 'log_workout_feedback'
  status: 'ok' | 'error'
  week_number: number
  adherence_score: number
  fatigue_status: 'recovered' | 'manageable' | 'overreached' | string
  what_went_well: string[]
  friction_points: string[]
  plan_adjustments: WorkoutPlanAdjustment[]
  next_week_schedule_tweaks: string[]
  deload_recommendation: string
  injury_risk_alerts: string[]
  coach_message: string
  gamification?: GamificationPayload
  social_accountability_prompt?: string
  share_card_text?: string
  assumptions: string[]
  error?: string
  message?: string
}

export interface ChallengeMission {
  day: number
  mission: string
  duration_minutes: number
  difficulty: string
}

export interface ChallengeReward {
  milestone_day: number
  reward: string
  unlock_criteria: string
}

export interface ChallengeModeReport {
  action: 'challenge_mode'
  status: 'ok' | 'error'
  challenge_name: string
  challenge_duration_days: number
  primary_goal: string
  daily_missions: ChallengeMission[]
  weekly_bonus_tasks: string[]
  streak_rules: string[]
  reward_track: ChallengeReward[]
  friend_challenge_prompt: string
  safety_notes: string[]
  gamification?: GamificationPayload
  share_card_text?: string
  assumptions: string[]
  error?: string
  message?: string
}

export interface ProgressMetricTrend {
  metric: string
  baseline: string
  current: string
  trend: 'up' | 'flat' | 'down' | string
}

export interface UpdatedFitnessTarget {
  metric: string
  target: string
  deadline: string
}

export interface FitnessProgressReassessmentReport {
  action: 'progress_reassessment'
  status: 'ok' | 'error'
  goal_progress_score: number
  goal_progress_summary: string
  metric_trends: ProgressMetricTrend[]
  plateau_diagnosis: string[]
  next_30_day_focus: string[]
  updated_targets: UpdatedFitnessTarget[]
  accountability_checkpoints: string[]
  gamification?: GamificationPayload
  share_card_text?: string
  assumptions: string[]
  error?: string
  message?: string
}

export const useFitnessCoachStore = defineStore('fitnessCoach', () => {
  const primaryGoal = ref('')
  const fitnessLevel = ref('beginner')
  const experienceLevel = ref('beginner')
  const age = ref<number>(24)
  const heightCm = ref<number>(170)
  const weightKg = ref<number>(70)
  const workoutDaysPerWeek = ref<number>(4)
  const sessionDurationMinutes = ref<number>(45)
  const timelineWeeks = ref<number>(8)
  const equipmentInput = ref('')
  const constraintsInput = ref('')
  const injuryHistoryInput = ref('')
  const preferredWorkoutsInput = ref('')
  const availableDaysInput = ref('')
  const dislikedExercisesInput = ref('')

  const weekNumber = ref<number>(1)
  const adherencePercent = ref<number>(0)
  const energyLevel = ref<number>(6)
  const sorenessLevel = ref<number>(4)
  const sleepHours = ref<number>(7)
  const completedSessionsInput = ref('')
  const painPointsInput = ref('')
  const winsInput = ref('')
  const feedbackNotes = ref('')

  const timeAvailableMinutes = ref<number>(20)
  const workoutLocation = ref('home')
  const challengeName = ref('Momentum Challenge')
  const challengeDurationDays = ref<number>(7)
  const currentStreakDays = ref<number>(0)
  const challengePreferencesInput = ref('')

  const totalXp = ref<number>(0)
  const levelEstimate = ref<number>(1)
  const activeQuestPrompt = ref('')
  const unlockedBadges = ref<string[]>([])

  const loading = ref(false)
  const error = ref<string | null>(null)
  const conversationId = ref<string | null>(null)

  const baselineReport = ref<FitnessBaselineReport | null>(null)
  const adaptivePlanReport = ref<AdaptiveWorkoutPlanReport | null>(null)
  const quickWorkoutReport = ref<QuickWorkoutBurstReport | null>(null)
  const workoutFeedbackReport = ref<WorkoutFeedbackReport | null>(null)
  const challengeModeReport = ref<ChallengeModeReport | null>(null)
  const progressReassessmentReport = ref<FitnessProgressReassessmentReport | null>(null)

  function setConversationId(id: string | null) {
    conversationId.value = id
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(message: string | null) {
    error.value = message
  }

  function applyGamification(gamification?: GamificationPayload | null) {
    if (!gamification) return
    totalXp.value += Number(gamification.xp_awarded || 0)
    currentStreakDays.value = Math.max(0, currentStreakDays.value + Number(gamification.streak_delta || 0))
    levelEstimate.value = Math.max(levelEstimate.value, Number(gamification.level_estimate || 1))
    activeQuestPrompt.value = gamification.quest_prompt || activeQuestPrompt.value
    if (Array.isArray(gamification.badges_unlocked) && gamification.badges_unlocked.length > 0) {
      const current = new Set(unlockedBadges.value)
      for (const badge of gamification.badges_unlocked) {
        const label = String(badge || '').trim()
        if (label) current.add(label)
      }
      unlockedBadges.value = Array.from(current)
    }
  }

  function resetReports() {
    baselineReport.value = null
    adaptivePlanReport.value = null
    quickWorkoutReport.value = null
    workoutFeedbackReport.value = null
    challengeModeReport.value = null
    progressReassessmentReport.value = null
  }

  function resetAll() {
    primaryGoal.value = ''
    fitnessLevel.value = 'beginner'
    experienceLevel.value = 'beginner'
    age.value = 24
    heightCm.value = 170
    weightKg.value = 70
    workoutDaysPerWeek.value = 4
    sessionDurationMinutes.value = 45
    timelineWeeks.value = 8
    equipmentInput.value = ''
    constraintsInput.value = ''
    injuryHistoryInput.value = ''
    preferredWorkoutsInput.value = ''
    availableDaysInput.value = ''
    dislikedExercisesInput.value = ''
    weekNumber.value = 1
    adherencePercent.value = 0
    energyLevel.value = 6
    sorenessLevel.value = 4
    sleepHours.value = 7
    completedSessionsInput.value = ''
    painPointsInput.value = ''
    winsInput.value = ''
    feedbackNotes.value = ''
    timeAvailableMinutes.value = 20
    workoutLocation.value = 'home'
    challengeName.value = 'Momentum Challenge'
    challengeDurationDays.value = 7
    currentStreakDays.value = 0
    challengePreferencesInput.value = ''
    totalXp.value = 0
    levelEstimate.value = 1
    activeQuestPrompt.value = ''
    unlockedBadges.value = []
    loading.value = false
    error.value = null
    conversationId.value = null
    resetReports()
  }

  return {
    primaryGoal,
    fitnessLevel,
    experienceLevel,
    age,
    heightCm,
    weightKg,
    workoutDaysPerWeek,
    sessionDurationMinutes,
    timelineWeeks,
    equipmentInput,
    constraintsInput,
    injuryHistoryInput,
    preferredWorkoutsInput,
    availableDaysInput,
    dislikedExercisesInput,
    weekNumber,
    adherencePercent,
    energyLevel,
    sorenessLevel,
    sleepHours,
    completedSessionsInput,
    painPointsInput,
    winsInput,
    feedbackNotes,
    timeAvailableMinutes,
    workoutLocation,
    challengeName,
    challengeDurationDays,
    currentStreakDays,
    challengePreferencesInput,
    totalXp,
    levelEstimate,
    activeQuestPrompt,
    unlockedBadges,
    loading,
    error,
    conversationId,
    baselineReport,
    adaptivePlanReport,
    quickWorkoutReport,
    workoutFeedbackReport,
    challengeModeReport,
    progressReassessmentReport,
    setConversationId,
    setLoading,
    setError,
    applyGamification,
    resetReports,
    resetAll,
  }
})
