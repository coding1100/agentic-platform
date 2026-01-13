import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ExamPrepStep = 
  | 'exam-setup'
  | 'study-schedule'
  | 'practice-exam'
  | 'progress-dashboard'
  | 'weak-areas'
  | 'topic-review'

export type ExamType = 'SAT' | 'ACT' | 'GRE' | 'GMAT' | 'TOEFL' | 'IELTS' | 'Certification' | 'Academic' | 'Other'

export type ProficiencyLevel = 'beginner' | 'intermediate' | 'advanced'

export interface ExamInfo {
  examType: ExamType | null
  subject: string | null
  examDate: string | null // YYYY-MM-DD format
  currentLevel: ProficiencyLevel | null
  targetScore: number | null
  hoursPerDay: number
}

export interface StudySchedule {
  examDate: string
  daysRemaining: number
  hoursPerDay: number
  totalHours: number
  weeklyBreakdown: WeekSchedule[]
  practiceExamDates: string[]
  milestones: Milestone[]
}

export interface WeekSchedule {
  weekNumber: number
  focus: string
  dailyGoals: DailyGoal[]
  milestone: string
}

export interface DailyGoal {
  day: number
  topic: string
  hours: number
}

export interface Milestone {
  id: string
  label: string
  completed: boolean
  targetDate: string
}

export interface PracticeExam {
  id: string
  examType: string
  subject: string
  numQuestions: number
  timeLimit: number // minutes
  questions: ExamQuestion[]
  startedAt: Date | null
  completedAt: Date | null
  score: number | null
  answers: Record<string, string>
}

export interface ExamQuestion {
  id: string
  number: number
  type: 'multiple-choice' | 'short-answer' | 'essay'
  question: string
  options?: string[]
  correctAnswer: string
  explanation: string
  points: number
}

export interface ProgressData {
  practiceScores: PracticeScore[]
  averageScore: number
  bestScore: number
  improvementRate: number
  readinessPercentage: number
  milestonesAchieved: string[]
  areasOfImprovement: ImprovementArea[]
}

export interface PracticeScore {
  date: string
  score: number
  examType: string
  subject: string
}

export interface ImprovementArea {
  area: string
  currentStatus: string
  target: string
}

export interface WeakArea {
  id: string
  topic: string
  priority: 'high' | 'medium' | 'low'
  currentPerformance: number
  targetImprovement: number
  specificTopics: string[]
  recommendedMaterials: string[]
  improvementStrategy: string[]
}

export interface TopicReview {
  topic: string
  difficulty: string
  keyConcepts: Concept[]
  formulas: Formula[]
  examples: Example[]
  practiceQuestions: PracticeQuestion[]
  commonMistakes: CommonMistake[]
}

export interface Concept {
  name: string
  definition: string
  keyPoints: string[]
}

export interface Formula {
  formula: string
  whenToUse: string
  example: string
}

export interface Example {
  type: string
  problem: string
  solution: string
  takeaway: string
}

export interface PracticeQuestion {
  question: string
  answer: string
  explanation: string
}

export interface CommonMistake {
  mistake: string
  howToAvoid: string
}

export const useExamPrepStore = defineStore('examPrep', () => {
  const currentStep = ref<ExamPrepStep>('exam-setup')
  const conversationId = ref<string | null>(null)
  
  const examInfo = ref<ExamInfo>({
    examType: null,
    subject: null,
    examDate: null,
    currentLevel: null,
    targetScore: null,
    hoursPerDay: 2
  })

  const studySchedule = ref<StudySchedule | null>(null)
  const currentPracticeExam = ref<PracticeExam | null>(null)
  const progressData = ref<ProgressData | null>(null)
  const weakAreas = ref<WeakArea[]>([])
  const currentTopicReview = ref<TopicReview | null>(null)
  const justSubmittedExam = ref<boolean>(false)

  function setStep(step: ExamPrepStep) {
    currentStep.value = step
  }

  function setConversationId(id: string | null) {
    conversationId.value = id
  }

  function setExamInfo(info: Partial<ExamInfo>) {
    examInfo.value = { ...examInfo.value, ...info }
  }

  function setStudySchedule(schedule: StudySchedule) {
    studySchedule.value = schedule
  }

  function setCurrentPracticeExam(exam: PracticeExam | null) {
    currentPracticeExam.value = exam
  }

  function setProgressData(data: ProgressData) {
    progressData.value = data
  }

  function setWeakAreas(areas: WeakArea[]) {
    weakAreas.value = areas
  }

  function setCurrentTopicReview(review: TopicReview | null) {
    currentTopicReview.value = review
  }

  function addPracticeScore(score: PracticeScore) {
    if (!progressData.value) {
      progressData.value = {
        practiceScores: [],
        averageScore: 0,
        bestScore: 0,
        improvementRate: 0,
        readinessPercentage: 0,
        milestonesAchieved: [],
        areasOfImprovement: []
      }
    }
    progressData.value.practiceScores.push(score)
    
    // Recalculate stats
    const scores = progressData.value.practiceScores.map(s => s.score)
    progressData.value.averageScore = scores.reduce((a, b) => a + b, 0) / scores.length
    progressData.value.bestScore = Math.max(...scores)
    
    // Calculate readiness percentage based on average score and improvement trend
    const avgScore = progressData.value.averageScore
    const improvementBonus = Math.max(0, progressData.value.improvementRate) * 0.5
    progressData.value.readinessPercentage = Math.min(100, Math.round(avgScore + improvementBonus))
    
    if (scores.length > 1) {
      const recent = scores.slice(-3)
      const older = scores.slice(0, -3)
      if (older.length > 0) {
        const recentAvg = recent.reduce((a, b) => a + b, 0) / recent.length
        const olderAvg = older.reduce((a, b) => a + b, 0) / older.length
        progressData.value.improvementRate = recentAvg - olderAvg
      }
    }
  }
  
  function setJustSubmittedExam(value: boolean) {
    justSubmittedExam.value = value
  }

  function reset() {
    currentStep.value = 'exam-setup'
    conversationId.value = null
    examInfo.value = {
      examType: null,
      subject: null,
      examDate: null,
      currentLevel: null,
      targetScore: null,
      hoursPerDay: 2
    }
    studySchedule.value = null
    currentPracticeExam.value = null
    progressData.value = null
    weakAreas.value = []
    currentTopicReview.value = null
  }

  return {
    // State
    currentStep,
    conversationId,
    examInfo,
    studySchedule,
    currentPracticeExam,
    progressData,
    weakAreas,
    currentTopicReview,
    justSubmittedExam,
    
    // Actions
    setStep,
    setConversationId,
    setExamInfo,
    setStudySchedule,
    setCurrentPracticeExam,
    setProgressData,
    setWeakAreas,
    setCurrentTopicReview,
    addPracticeScore,
    setJustSubmittedExam,
    reset
  }
})

