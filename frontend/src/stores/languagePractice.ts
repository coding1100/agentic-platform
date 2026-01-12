import { defineStore } from 'pinia'
import { ref } from 'vue'

export type LanguagePracticeStep = 
  | 'language-selection'
  | 'placement-test'
  | 'learning-goals'
  | 'vocabulary-builder'
  | 'grammar-practice'
  | 'conversation-practice'
  | 'pronunciation-practice'
  | 'progress-dashboard'

export type Language = 'spanish' | 'french' | 'german' | 'italian' | 'portuguese' | 'chinese' | 'japanese' | 'korean' | 'arabic' | 'hindi' | 'russian'

export type ProficiencyLevel = 'beginner' | 'elementary' | 'intermediate' | 'upper-intermediate' | 'advanced' | 'native'

export interface LanguageProfile {
  targetLanguage: Language | null
  nativeLanguage: Language | null
  proficiencyLevel: ProficiencyLevel | null
  cefrLevel: string | null // A1, A2, B1, B2, C1, C2
}

export interface LearningGoals {
  goals: string[]
  dailyPracticeTime: number // minutes
  learningStyle: 'visual' | 'auditory' | 'kinesthetic' | 'mixed'
  focusAreas: ('vocabulary' | 'grammar' | 'speaking' | 'listening' | 'reading' | 'writing')[]
  targetDate: string | null
}

export interface VocabularyCard {
  id: string
  word: string
  translation: string
  phonetic: string
  exampleSentence: string
  exampleTranslation: string
  category: string
  difficulty: number
  lastReviewed: Date | null
  nextReview: Date
  reviewCount: number
  masteryLevel: number // 0-100
  imageUrl?: string
  audioUrl?: string
}

export interface GrammarExercise {
  id: string
  topic: string
  type: 'fill-blank' | 'multiple-choice' | 'sentence-construction' | 'transformation'
  question: string
  options?: string[]
  correctAnswer: string | string[]
  explanation: string
  difficulty: number
  completed: boolean
  attempts: number
  correctAttempts: number
}

export interface ConversationScenario {
  id: string
  title: string
  description: string
  context: string
  dialogues: ConversationDialogue[]
  difficulty: number
  completed: boolean
  score: number
}

export interface ConversationDialogue {
  id: string
  speaker: 'user' | 'native'
  text: string
  translation: string
  audioUrl?: string
}

export interface PronunciationExercise {
  id: string
  word: string
  phonetic: string
  audioUrl: string
  difficulty: number
  userAttempts: PronunciationAttempt[]
  bestScore: number
}

export interface PronunciationAttempt {
  timestamp: Date
  score: number
  feedback: string
  accuracy: {
    overall: number
    intonation: number
    stress: number
    clarity: number
  }
}

export interface ProgressStats {
  totalWordsLearned: number
  currentStreak: number
  longestStreak: number
  totalPracticeTime: number // minutes
  level: number
  xp: number
  xpToNextLevel: number
  badges: string[]
  weeklyGoal: number
  weeklyProgress: number
  strengths: string[]
  weaknesses: string[]
  vocabularyMastery: number
  grammarMastery: number
  speakingMastery: number
  listeningMastery: number
}

export const useLanguagePracticeStore = defineStore('languagePractice', () => {
  const currentStep = ref<LanguagePracticeStep>('language-selection')
  const languageProfile = ref<LanguageProfile>({
    targetLanguage: null,
    nativeLanguage: null,
    proficiencyLevel: null,
    cefrLevel: null
  })
  const learningGoals = ref<LearningGoals>({
    goals: [],
    dailyPracticeTime: 15,
    learningStyle: 'mixed',
    focusAreas: [],
    targetDate: null
  })
  const vocabularyCards = ref<VocabularyCard[]>([])
  const grammarExercises = ref<GrammarExercise[]>([])
  const conversationScenarios = ref<ConversationScenario[]>([])
  const pronunciationExercises = ref<PronunciationExercise[]>([])
  const progressStats = ref<ProgressStats>({
    totalWordsLearned: 0,
    currentStreak: 0,
    longestStreak: 0,
    totalPracticeTime: 0,
    level: 1,
    xp: 0,
    xpToNextLevel: 100,
    badges: [],
    weeklyGoal: 105, // 15 min * 7 days
    weeklyProgress: 0,
    strengths: [],
    weaknesses: [],
    vocabularyMastery: 0,
    grammarMastery: 0,
    speakingMastery: 0,
    listeningMastery: 0
  })
  const conversationId = ref<string | null>(null)
  const currentVocabularySet = ref<VocabularyCard[]>([])
  const currentGrammarTopic = ref<string | null>(null)
  const activeConversation = ref<ConversationScenario | null>(null)

  function setStep(step: LanguagePracticeStep) {
    currentStep.value = step
  }

  function setLanguageProfile(profile: LanguageProfile) {
    languageProfile.value = profile
  }

  function setLearningGoals(goals: LearningGoals) {
    learningGoals.value = goals
  }

  function addVocabularyCard(card: VocabularyCard) {
    vocabularyCards.value.push(card)
  }

  function updateVocabularyCard(cardId: string, updates: Partial<VocabularyCard>) {
    const index = vocabularyCards.value.findIndex(c => c.id === cardId)
    if (index !== -1) {
      vocabularyCards.value[index] = { ...vocabularyCards.value[index], ...updates }
    }
  }

  function addGrammarExercise(exercise: GrammarExercise) {
    grammarExercises.value.push(exercise)
  }

  function updateGrammarExercise(exerciseId: string, updates: Partial<GrammarExercise>) {
    const index = grammarExercises.value.findIndex(e => e.id === exerciseId)
    if (index !== -1) {
      grammarExercises.value[index] = { ...grammarExercises.value[index], ...updates }
    }
  }

  function addConversationScenario(scenario: ConversationScenario) {
    conversationScenarios.value.push(scenario)
  }

  function addPronunciationExercise(exercise: PronunciationExercise) {
    pronunciationExercises.value.push(exercise)
  }

  function updateProgressStats(updates: Partial<ProgressStats>) {
    progressStats.value = { ...progressStats.value, ...updates }
  }

  function addXP(amount: number) {
    progressStats.value.xp += amount
    if (progressStats.value.xp >= progressStats.value.xpToNextLevel) {
      progressStats.value.level += 1
      progressStats.value.xp -= progressStats.value.xpToNextLevel
      progressStats.value.xpToNextLevel = progressStats.value.level * 100
    }
  }

  function setConversationId(id: string | null) {
    conversationId.value = id
  }

  function setCurrentVocabularySet(cards: VocabularyCard[]) {
    currentVocabularySet.value = cards
  }

  function setCurrentGrammarTopic(topic: string | null) {
    currentGrammarTopic.value = topic
  }

  function setActiveConversation(scenario: ConversationScenario | null) {
    activeConversation.value = scenario
  }

  function reset() {
    currentStep.value = 'language-selection'
    languageProfile.value = {
      targetLanguage: null,
      nativeLanguage: null,
      proficiencyLevel: null,
      cefrLevel: null
    }
    learningGoals.value = {
      goals: [],
      dailyPracticeTime: 15,
      learningStyle: 'mixed',
      focusAreas: [],
      targetDate: null
    }
    vocabularyCards.value = []
    grammarExercises.value = []
    conversationScenarios.value = []
    pronunciationExercises.value = []
    progressStats.value = {
      totalWordsLearned: 0,
      currentStreak: 0,
      longestStreak: 0,
      totalPracticeTime: 0,
      level: 1,
      xp: 0,
      xpToNextLevel: 100,
      badges: [],
      weeklyGoal: 105,
      weeklyProgress: 0,
      strengths: [],
      weaknesses: [],
      vocabularyMastery: 0,
      grammarMastery: 0,
      speakingMastery: 0,
      listeningMastery: 0
    }
    conversationId.value = null
    currentVocabularySet.value = []
    currentGrammarTopic.value = null
    activeConversation.value = null
  }

  return {
    // State
    currentStep,
    languageProfile,
    learningGoals,
    vocabularyCards,
    grammarExercises,
    conversationScenarios,
    pronunciationExercises,
    progressStats,
    conversationId,
    currentVocabularySet,
    currentGrammarTopic,
    activeConversation,
    // Actions
    setStep,
    setLanguageProfile,
    setLearningGoals,
    addVocabularyCard,
    updateVocabularyCard,
    addGrammarExercise,
    updateGrammarExercise,
    addConversationScenario,
    addPronunciationExercise,
    updateProgressStats,
    addXP,
    setConversationId,
    setCurrentVocabularySet,
    setCurrentGrammarTopic,
    setActiveConversation,
    reset
  }
})



 

