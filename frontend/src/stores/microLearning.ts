import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type MicroLearningStep = 
  | 'onboarding'
  | 'lesson'
  | 'quiz'
  | 'flashcards'
  | 'review'
  | 'dashboard'

export interface LearningGoal {
  id: string
  name: string
  selected: boolean
}

export interface OnboardingData {
  goals: string[]
  timePerDay: 5 | 10 | 15
  learningStyle: 'visual' | 'auditory' | 'reading' | 'kinesthetic' | null
  topics: string[]
  schedule?: {
    preferredTime?: string
    daysPerWeek?: number
  }
}

export interface MicroLesson {
  id: string
  topic: string
  content: string
  timeMinutes: number
  difficulty: 'easy' | 'medium' | 'hard'
  completed: boolean
  completedAt?: Date
  keyTakeaways?: string[]
}

export interface Flashcard {
  id: string
  question: string
  answer: string
  topic: string
  lastReviewed?: Date
  nextReview?: Date
  masteryLevel: number // 0-5
  timesReviewed: number
}

export interface Progress {
  currentStreak: number
  longestStreak: number
  totalLessons: number
  totalTimeMinutes: number
  topicsLearned: string[]
  lastLearnedDate?: Date
}

export const useMicroLearningStore = defineStore('microLearning', () => {
  // State
  const currentStep = ref<MicroLearningStep>('onboarding')
  const onboardingData = ref<OnboardingData>({
    goals: [],
    timePerDay: 10,
    learningStyle: null,
    topics: []
  })
  const currentLesson = ref<MicroLesson | null>(null)
  const lessons = ref<MicroLesson[]>([])
  const flashcards = ref<Flashcard[]>([])
  const progress = ref<Progress>({
    currentStreak: 0,
    longestStreak: 0,
    totalLessons: 0,
    totalTimeMinutes: 0,
    topicsLearned: []
  })
  const conversationId = ref<string | null>(null)
  const isLoading = ref(false)

  // Computed
  const isOnboardingComplete = computed(() => {
    return onboardingData.value.goals.length > 0 && 
           onboardingData.value.topics.length > 0 &&
           onboardingData.value.learningStyle !== null
  })

  const todayLearned = computed(() => {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return lessons.value.some(lesson => {
      if (!lesson.completedAt) return false
      const lessonDate = new Date(lesson.completedAt)
      lessonDate.setHours(0, 0, 0, 0)
      return lessonDate.getTime() === today.getTime()
    })
  })

  const cardsDueForReview = computed(() => {
    const now = new Date()
    return flashcards.value.filter(card => {
      if (!card.nextReview) return true
      return new Date(card.nextReview) <= now
    })
  })

  // Actions
  function setOnboardingData(data: Partial<OnboardingData>) {
    onboardingData.value = { ...onboardingData.value, ...data }
  }

  function addGoal(goal: string) {
    if (!onboardingData.value.goals.includes(goal)) {
      onboardingData.value.goals.push(goal)
    }
  }

  function removeGoal(goal: string) {
    onboardingData.value.goals = onboardingData.value.goals.filter(g => g !== goal)
  }

  function addTopic(topic: string) {
    if (!onboardingData.value.topics.includes(topic)) {
      onboardingData.value.topics.push(topic)
    }
  }

  function removeTopic(topic: string) {
    onboardingData.value.topics = onboardingData.value.topics.filter(t => t !== topic)
  }

  function setCurrentStep(step: MicroLearningStep) {
    currentStep.value = step
  }

  function setCurrentLesson(lesson: MicroLesson | null) {
    currentLesson.value = lesson
  }

  function addLesson(lesson: MicroLesson) {
    lessons.value.push(lesson)
  }

  function completeLesson(lessonId: string) {
    const lesson = lessons.value.find(l => l.id === lessonId)
    if (lesson) {
      lesson.completed = true
      lesson.completedAt = new Date()
      
      // Update progress
      progress.value.totalLessons++
      progress.value.totalTimeMinutes += lesson.timeMinutes
      
      if (!progress.value.topicsLearned.includes(lesson.topic)) {
        progress.value.topicsLearned.push(lesson.topic)
      }

      // Update streak
      updateStreak()
    }
  }

  function updateStreak() {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    
    const lastLearned = progress.value.lastLearnedDate
    if (lastLearned) {
      const lastDate = new Date(lastLearned)
      lastDate.setHours(0, 0, 0, 0)
      
      const daysDiff = Math.floor((today.getTime() - lastDate.getTime()) / (1000 * 60 * 60 * 24))
      
      if (daysDiff === 1) {
        // Consecutive day
        progress.value.currentStreak++
      } else if (daysDiff === 0) {
        // Same day, keep streak
      } else {
        // Streak broken
        if (progress.value.currentStreak > progress.value.longestStreak) {
          progress.value.longestStreak = progress.value.currentStreak
        }
        progress.value.currentStreak = 1
      }
    } else {
      progress.value.currentStreak = 1
    }
    
    progress.value.lastLearnedDate = today
    
    if (progress.value.currentStreak > progress.value.longestStreak) {
      progress.value.longestStreak = progress.value.currentStreak
    }
  }

  function addFlashcards(newCards: Flashcard[]) {
    flashcards.value.push(...newCards)
  }

  function updateFlashcardMastery(cardId: string, masteryLevel: number) {
    const card = flashcards.value.find(c => c.id === cardId)
    if (card) {
      card.masteryLevel = masteryLevel
      card.timesReviewed++
      card.lastReviewed = new Date()
      
      // Schedule next review based on mastery (spaced repetition)
      const now = new Date()
      let daysUntilNextReview = 1
      
      if (masteryLevel >= 4) {
        daysUntilNextReview = 7 // Mastered - review in a week
      } else if (masteryLevel >= 3) {
        daysUntilNextReview = 3 // Good - review in 3 days
      } else if (masteryLevel >= 2) {
        daysUntilNextReview = 1 // Fair - review tomorrow
      } else {
        daysUntilNextReview = 0 // Poor - review today again
      }
      
      card.nextReview = new Date(now.getTime() + daysUntilNextReview * 24 * 60 * 60 * 1000)
    }
  }

  function setConversationId(id: string | null) {
    conversationId.value = id
  }

  function reset() {
    currentStep.value = 'onboarding'
    onboardingData.value = {
      goals: [],
      timePerDay: 10,
      learningStyle: null,
      topics: []
    }
    currentLesson.value = null
    lessons.value = []
    flashcards.value = []
    progress.value = {
      currentStreak: 0,
      longestStreak: 0,
      totalLessons: 0,
      totalTimeMinutes: 0,
      topicsLearned: []
    }
    conversationId.value = null
  }

  return {
    // State
    currentStep,
    onboardingData,
    currentLesson,
    lessons,
    flashcards,
    progress,
    conversationId,
    isLoading,
    
    // Computed
    isOnboardingComplete,
    todayLearned,
    cardsDueForReview,
    
    // Actions
    setOnboardingData,
    addGoal,
    removeGoal,
    addTopic,
    removeTopic,
    setCurrentStep,
    setCurrentLesson,
    addLesson,
    completeLesson,
    updateStreak,
    addFlashcards,
    updateFlashcardMastery,
    setConversationId,
    reset
  }
})





