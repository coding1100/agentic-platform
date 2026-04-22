import { defineStore } from 'pinia'
import { ref } from 'vue'
import type {
  TutorAction,
  TutorAcademicLevel,
  TutorExecuteResponse,
  TutorLearningMode,
  TutorProgressSummary,
  TutorRecentResult,
  TutorRecentSource,
  TutorWorkspaceState,
} from '@/types'

export type TutorStep = 'setup' | 'action-selection' | 'workspace'

function createDefaultProgress(): TutorProgressSummary {
  return {
    sessions_completed: 0,
    practice_sessions_attempted: 0,
    practice_sessions_completed: 0,
    source_sessions: 0,
    average_score: null,
    weak_topics: [],
    mastery_by_topic: {},
    recent_activity: [],
    next_recommended_action: null,
  }
}

function createDefaultWorkspace(): TutorWorkspaceState {
  return {
    subject: '',
    academic_level: null,
    learner_name: null,
    selected_action: null,
    selected_mode: null,
    progress: createDefaultProgress(),
    recent_sources: [],
    recent_results: [],
  }
}

function normalizeProgress(value: Partial<TutorProgressSummary> | null | undefined): TutorProgressSummary {
  const defaults = createDefaultProgress()
  return {
    ...defaults,
    ...(value || {}),
    weak_topics: Array.isArray(value?.weak_topics) ? value!.weak_topics.filter(Boolean) : defaults.weak_topics,
    mastery_by_topic: typeof value?.mastery_by_topic === 'object' && value?.mastery_by_topic
      ? Object.fromEntries(
          Object.entries(value.mastery_by_topic).filter(([topic, score]) => {
            return typeof topic === 'string' && typeof score === 'number' && Number.isFinite(score)
          })
        )
      : defaults.mastery_by_topic,
    recent_activity: Array.isArray(value?.recent_activity)
      ? value!.recent_activity.filter(Boolean).slice(0, 8)
      : defaults.recent_activity,
  }
}

function normalizeWorkspaceState(value: Partial<TutorWorkspaceState> | null | undefined): TutorWorkspaceState {
  const defaults = createDefaultWorkspace()
  return {
    ...defaults,
    ...(value || {}),
    subject: typeof value?.subject === 'string' ? value.subject : defaults.subject,
    academic_level: value?.academic_level || defaults.academic_level,
    learner_name: typeof value?.learner_name === 'string' && value.learner_name.trim()
      ? value.learner_name.trim()
      : null,
    selected_action: value?.selected_action || null,
    selected_mode: value?.selected_mode || null,
    progress: normalizeProgress(value?.progress),
    recent_sources: Array.isArray(value?.recent_sources) ? value.recent_sources.slice(0, 8) as TutorRecentSource[] : [],
    recent_results: Array.isArray(value?.recent_results) ? value.recent_results.slice(0, 8) as TutorRecentResult[] : [],
  }
}

function defaultModeForAction(action: TutorAction): TutorLearningMode {
  switch (action) {
    case 'upload_notes':
      return 'notes_summary'
    case 'practice':
      return 'practice_quiz_generator'
    default:
      return 'personalized_learning'
  }
}

export const useTutorStore = defineStore('tutor', () => {
  const currentStep = ref<TutorStep>('setup')
  const subject = ref('')
  const academicLevel = ref<TutorAcademicLevel | null>(null)
  const learnerName = ref<string | null>(null)
  const selectedAction = ref<TutorAction | null>(null)
  const selectedMode = ref<TutorLearningMode | null>(null)
  const progress = ref<TutorProgressSummary>(createDefaultProgress())
  const recentSources = ref<TutorRecentSource[]>([])
  const recentResults = ref<TutorRecentResult[]>([])
  const conversationId = ref<string | null>(null)
  const lastResult = ref<TutorExecuteResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  function syncStepFromWorkspace() {
    if (!subject.value.trim() || !academicLevel.value) {
      currentStep.value = 'setup'
      return
    }
    currentStep.value = selectedAction.value ? 'workspace' : 'action-selection'
  }

  function setWorkspaceState(state: Partial<TutorWorkspaceState>) {
    const normalized = normalizeWorkspaceState(state)
    subject.value = normalized.subject
    academicLevel.value = normalized.academic_level || null
    learnerName.value = normalized.learner_name || null
    selectedAction.value = normalized.selected_action || null
    selectedMode.value = normalized.selected_mode || null
    progress.value = normalizeProgress(normalized.progress)
    recentSources.value = normalized.recent_sources
    recentResults.value = normalized.recent_results
    syncStepFromWorkspace()
  }

  function exportWorkspaceState(): TutorWorkspaceState {
    return normalizeWorkspaceState({
      subject: subject.value,
      academic_level: academicLevel.value,
      learner_name: learnerName.value,
      selected_action: selectedAction.value,
      selected_mode: selectedMode.value,
      progress: progress.value,
      recent_sources: recentSources.value,
      recent_results: recentResults.value,
    })
  }

  function importWorkspaceState(state: Record<string, any>) {
    setWorkspaceState(state as Partial<TutorWorkspaceState>)
  }

  function setSetup(subjectValue: string, level: TutorAcademicLevel) {
    subject.value = subjectValue.trim()
    academicLevel.value = level
    if (!selectedMode.value) {
      selectedMode.value = 'personalized_learning'
    }
    currentStep.value = 'action-selection'
  }

  function setLearnerName(name: string | null | undefined) {
    const next = typeof name === 'string' ? name.trim() : ''
    learnerName.value = next || null
  }

  function chooseAction(action: TutorAction) {
    selectedAction.value = action
    if (!selectedMode.value || selectedMode.value === 'notes_summary' || selectedMode.value === 'practice_quiz_generator' || selectedMode.value === 'personalized_learning') {
      selectedMode.value = defaultModeForAction(action)
    }
    currentStep.value = 'workspace'
  }

  function setSelectedMode(mode: TutorLearningMode) {
    selectedMode.value = mode
  }

  function setConversationId(id: string | null) {
    conversationId.value = id
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setError(message: string | null) {
    error.value = message
  }

  function resetResult() {
    lastResult.value = null
  }

  function applyExecuteResult(result: TutorExecuteResponse) {
    lastResult.value = result
    subject.value = result.subject
    academicLevel.value = result.academic_level
    learnerName.value = result.learner_name || learnerName.value
    selectedAction.value = result.action
    selectedMode.value = result.learning_mode
    progress.value = normalizeProgress(result.progress_snapshot)

    recentResults.value = [
      {
        action: result.action,
        learning_mode: result.learning_mode,
        title: result.practice_set.title,
        score: recentResults.value[0]?.title === result.practice_set.title ? recentResults.value[0].score ?? null : null,
        weak_topics: recentResults.value[0]?.title === result.practice_set.title ? recentResults.value[0].weak_topics ?? [] : [],
        created_at: new Date().toISOString(),
      },
      ...recentResults.value.filter((item) => item.title !== result.practice_set.title),
    ].slice(0, 8)

    currentStep.value = 'workspace'
    error.value = null
  }

  function addRecentSource(source: TutorRecentSource) {
    recentSources.value = [source, ...recentSources.value.filter((item) => item.name !== source.name)].slice(0, 8)
  }

  function recordPracticeResult(payload: { title: string; score: number; weakTopics: string[]; masteredTopics?: string[] }) {
    const previousAttempts = progress.value.practice_sessions_attempted
    const previousAverage = progress.value.average_score ?? 0

    progress.value.practice_sessions_attempted += 1
    progress.value.practice_sessions_completed += 1
    progress.value.average_score = Number(
      (((previousAverage * previousAttempts) + payload.score) / progress.value.practice_sessions_attempted).toFixed(1)
    )

    const weakTopics = Array.from(new Set([...(progress.value.weak_topics || []), ...payload.weakTopics])).slice(0, 8)
    progress.value.weak_topics = weakTopics
    progress.value.recent_activity = [
      `${new Date().toISOString().slice(0, 16).replace('T', ' ')} - Practice scored ${payload.score}%`,
      ...progress.value.recent_activity,
    ].slice(0, 8)

    const mastery = { ...progress.value.mastery_by_topic }
    for (const topic of payload.weakTopics) {
      mastery[topic] = Math.max(0, (mastery[topic] ?? 60) - 10)
    }
    for (const topic of payload.masteredTopics || []) {
      mastery[topic] = Math.min(100, (mastery[topic] ?? 70) + 8)
    }
    progress.value.mastery_by_topic = mastery

    recentResults.value = recentResults.value.map((item, index) => {
      if (index === 0 && item.title === payload.title) {
        return {
          ...item,
          score: payload.score,
          weak_topics: payload.weakTopics,
        }
      }
      return item
    })
  }

  function goToActionSelection() {
    currentStep.value = 'action-selection'
  }

  function resetAll() {
    currentStep.value = 'setup'
    subject.value = ''
    academicLevel.value = null
    learnerName.value = null
    selectedAction.value = null
    selectedMode.value = null
    progress.value = createDefaultProgress()
    recentSources.value = []
    recentResults.value = []
    conversationId.value = null
    lastResult.value = null
    loading.value = false
    error.value = null
  }

  return {
    currentStep,
    subject,
    academicLevel,
    learnerName,
    selectedAction,
    selectedMode,
    progress,
    recentSources,
    recentResults,
    conversationId,
    lastResult,
    loading,
    error,
    exportWorkspaceState,
    importWorkspaceState,
    setWorkspaceState,
    setSetup,
    setLearnerName,
    chooseAction,
    setSelectedMode,
    setConversationId,
    setLoading,
    setError,
    resetResult,
    applyExecuteResult,
    addRecentSource,
    recordPracticeResult,
    goToActionSelection,
    resetAll,
  }
})
