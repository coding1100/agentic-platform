<template>
  <div class="grammar-practice-form">
    <div class="form-card">
      <h2>Grammar Practice 📝</h2>
      <p class="form-description">Master grammar rules through interactive exercises.</p>
      
      <!-- Topic Selection -->
      <div v-if="!currentExercise" class="topic-selection">
        <h3>Choose a Grammar Topic</h3>
        <div v-if="isGeneratingExercises" class="generating-exercises">
          <div class="spinner-large"></div>
          <p class="loading-title">Generating grammar exercises...</p>
          <p class="sub-text">Creating personalized practice for you</p>
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
        <div v-else class="topic-grid">
          <button
            v-for="topic in grammarTopics"
            :key="topic.id"
            @click="selectTopic(topic)"
            :class="['topic-btn', { active: selectedTopic === topic.id }]"
          >
            <span class="topic-icon">{{ topic.icon }}</span>
            <div class="topic-info">
              <strong>{{ topic.name }}</strong>
              <p>{{ topic.description }}</p>
            </div>
          </button>
        </div>
      </div>

      <!-- Exercise View -->
      <div v-else class="exercise-view">
        <div class="exercise-header">
          <button @click="backToTopics" class="btn-back-small">← Back to Topics</button>
          <div class="exercise-progress">
            Exercise {{ currentExerciseIndex + 1 }} of {{ exercises.length }}
          </div>
        </div>

        <div class="exercise-card">
          <h3>{{ currentExercise.topic }}</h3>
          <p class="exercise-question">{{ currentExercise.question }}</p>

          <!-- Fill in the Blank -->
          <div v-if="currentExercise.type === 'fill-blank'" class="exercise-fill-blank">
            <p class="sentence-with-blank">{{ currentExercise.sentenceWithBlank }}</p>
            <input
              v-model="userAnswer"
              type="text"
              class="form-input"
              placeholder="Enter your answer"
            />
          </div>

          <!-- Multiple Choice -->
          <div v-else-if="currentExercise.type === 'multiple-choice'" class="exercise-multiple-choice">
            <button
              v-for="(option, index) in currentExercise.options"
              :key="index"
              @click="selectAnswer(option)"
              :class="['option-btn', { 
                selected: userAnswer === option,
                correct: showResult && option === currentExercise.correctAnswer,
                incorrect: showResult && userAnswer === option && option !== currentExercise.correctAnswer
              }]"
            >
              {{ String.fromCharCode(65 + index) }}) {{ option }}
            </button>
          </div>

          <!-- Sentence Construction -->
          <div v-else-if="currentExercise.type === 'sentence-construction'" class="exercise-construction">
            <p class="instruction">Arrange the words to form a correct sentence:</p>
            <div class="word-bank">
              <button
                v-for="(word, index) in shuffledWords"
                :key="index"
                @click="addWord(word, index)"
                :disabled="usedWords.includes(index)"
                class="word-chip"
              >
                {{ word }}
              </button>
            </div>
            <div class="sentence-builder">
              <span
                v-for="(word, index) in constructedSentence"
                :key="index"
                class="sentence-word"
                @click="removeWord(index)"
              >
                {{ word }}
              </span>
            </div>
          </div>

          <div v-if="showResult" class="exercise-result">
            <div :class="['result-message', { correct: isCorrect, incorrect: !isCorrect }]">
              <span class="result-icon">{{ isCorrect ? '✅' : '❌' }}</span>
              <span>{{ isCorrect ? 'Correct!' : 'Incorrect' }}</span>
            </div>
            <div class="explanation">
              <strong>Explanation:</strong>
              <p>{{ currentExercise.explanation }}</p>
            </div>
          </div>

          <div class="exercise-actions">
            <button
              v-if="!showResult"
              @click="checkAnswer"
              :disabled="!userAnswer || (currentExercise.type === 'sentence-construction' && constructedSentence.length === 0) || isCheckingAnswer"
              class="btn-check"
            >
              <span v-if="isCheckingAnswer">Checking...</span>
              <span v-else>Check Answer</span>
            </button>
            <button
              v-else
              @click="nextExercise"
              class="btn-next"
            >
              {{ currentExerciseIndex < exercises.length - 1 ? 'Next Exercise →' : 'Finish Topic' }}
            </button>
          </div>
        </div>

        <!-- Topic Progress -->
        <div class="topic-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${(completedExercises / exercises.length) * 100}%` }"></div>
          </div>
          <p>Progress: {{ completedExercises }} / {{ exercises.length }} exercises completed</p>
        </div>
      </div>
        
      <div class="form-actions">
        <button @click="handleBack" class="btn-back">← Back</button>
        <button @click="handleContinue" class="btn-primary">
          Continue to Conversation →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useLanguagePracticeStore } from '@/stores/languagePractice'
import type { GrammarExercise } from '@/stores/languagePractice'

const emit = defineEmits<{
  complete: []
}>()

const languagePracticeStore = useLanguagePracticeStore()

const selectedTopic = ref<string | null>(null)
const currentExerciseIndex = ref(0)
const userAnswer = ref('')
const showResult = ref(false)
const constructedSentence = ref<string[]>([])
const usedWords = ref<number[]>([])
const isGeneratingExercises = ref(false)
const isCheckingAnswer = ref(false)

interface GrammarTopic {
  id: string
  name: string
  description: string
  icon: string
}

const grammarTopics: GrammarTopic[] = [
  { id: 'present-tense', name: 'Present Tense', description: 'Learn present tense conjugations', icon: '⏰' },
  { id: 'past-tense', name: 'Past Tense', description: 'Master past tense forms', icon: '📅' },
  { id: 'articles', name: 'Articles', description: 'Definite and indefinite articles', icon: '📄' },
  { id: 'prepositions', name: 'Prepositions', description: 'Common prepositions and usage', icon: '📍' },
  { id: 'pronouns', name: 'Pronouns', description: 'Subject, object, and possessive pronouns', icon: '👤' },
  { id: 'adjectives', name: 'Adjectives', description: 'Adjective agreement and placement', icon: '✨' }
]

const exercises = ref<GrammarExercise[]>([])
const currentExercise = computed(() => exercises.value[currentExerciseIndex.value])
const shuffledWords = ref<string[]>([])
const completedExercises = computed(() => exercises.value.filter(e => e.completed).length)
const isCorrect = computed(() => {
  if (!currentExercise.value) return false
  if (currentExercise.value.type === 'sentence-construction') {
    return constructedSentence.value.join(' ').toLowerCase() === currentExercise.value.correctAnswer.toString().toLowerCase()
  }
  return userAnswer.value.toLowerCase() === currentExercise.value.correctAnswer.toString().toLowerCase()
})

async function selectTopic(topic: GrammarTopic) {
  selectedTopic.value = topic.id
  await generateExercises(topic.id)
}

async function generateExercises(topicId: string) {
  isGeneratingExercises.value = true
  
  // Simulate AI generation delay
  await new Promise(resolve => setTimeout(resolve, 1200))
  
  // Sample exercises - in production, these would come from AI agent
  exercises.value = [
    {
      id: 'ex1',
      topic: 'Present Tense',
      type: 'fill-blank',
      question: 'Complete the sentence with the correct verb form:',
      sentenceWithBlank: 'Yo ___ (to be) estudiante.',
      correctAnswer: 'soy',
      explanation: '"Soy" is the first person singular form of "ser" (to be) in the present tense.',
      difficulty: 1,
      completed: false,
      attempts: 0,
      correctAttempts: 0
    },
    {
      id: 'ex2',
      topic: 'Present Tense',
      type: 'multiple-choice',
      question: 'Choose the correct form:',
      options: ['hablo', 'hablas', 'habla', 'hablamos'],
      correctAnswer: 'hablo',
      explanation: '"Hablo" is the first person singular form of "hablar" (to speak).',
      difficulty: 1,
      completed: false,
      attempts: 0,
      correctAttempts: 0
    }
  ]
  currentExerciseIndex.value = 0
  userAnswer.value = ''
  showResult.value = false
  isGeneratingExercises.value = false
}

function selectAnswer(answer: string) {
  userAnswer.value = answer
}

async function checkAnswer() {
  isCheckingAnswer.value = true
  
  // Simulate AI evaluation delay
  await new Promise(resolve => setTimeout(resolve, 600))
  
  showResult.value = true
  const exercise = currentExercise.value
  exercise.attempts++
  
  if (isCorrect.value) {
    exercise.correctAttempts++
    exercise.completed = true
    languagePracticeStore.addXP(15)
  }
  
  languagePracticeStore.updateGrammarExercise(exercise.id, exercise)
  isCheckingAnswer.value = false
}

function nextExercise() {
  if (currentExerciseIndex.value < exercises.value.length - 1) {
    currentExerciseIndex.value++
    userAnswer.value = ''
    showResult.value = false
    constructedSentence.value = []
    usedWords.value = []
  } else {
    // Topic completed
    selectedTopic.value = null
  }
}

function addWord(word: string, index: number) {
  constructedSentence.value.push(word)
  usedWords.value.push(index)
}

function removeWord(index: number) {
  const wordIndex = usedWords.value[index]
  constructedSentence.value.splice(index, 1)
  usedWords.value.splice(index, 1)
}

function backToTopics() {
  selectedTopic.value = null
  exercises.value = []
}

function handleBack() {
  languagePracticeStore.setStep('vocabulary-builder')
}

function handleContinue() {
  emit('complete')
}
</script>

<style scoped>
.grammar-practice-form {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  padding: 20px 0;
}

.form-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 700px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h2 {
  color: white;
  font-size: 28px;
  margin: 0 0 12px 0;
  font-weight: 700;
  text-align: center;
}

.form-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  text-align: center;
  margin-bottom: 32px;
  line-height: 1.6;
}

.topic-selection h3 {
  color: white;
  font-size: 20px;
  margin-bottom: 20px;
}

.topic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.topic-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}

.topic-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.topic-btn.active {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.topic-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.topic-info {
  flex: 1;
}

.topic-info strong {
  display: block;
  font-size: 16px;
  margin-bottom: 4px;
}

.topic-info p {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
}

.exercise-view {
  margin-bottom: 32px;
}

.exercise-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.btn-back-small {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.exercise-progress {
  color: white;
  font-size: 14px;
}

.exercise-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
}

.exercise-card h3 {
  color: white;
  font-size: 20px;
  margin: 0 0 16px 0;
}

.exercise-question {
  color: white;
  font-size: 16px;
  margin-bottom: 24px;
}

.sentence-with-blank {
  font-size: 20px;
  color: white;
  font-family: monospace;
  margin-bottom: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.exercise-multiple-choice {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-btn {
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.15);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  text-align: left;
  cursor: pointer;
  transition: all 0.3s ease;
}

.option-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

.option-btn.selected {
  background: rgba(102, 126, 234, 0.4);
  border-color: rgba(255, 255, 255, 0.5);
}

.option-btn.correct {
  background: rgba(76, 175, 80, 0.4);
  border-color: rgba(76, 175, 80, 0.6);
}

.option-btn.incorrect {
  background: rgba(255, 87, 34, 0.4);
  border-color: rgba(255, 87, 34, 0.6);
}

.exercise-construction {
  margin-bottom: 24px;
}

.instruction {
  color: white;
  margin-bottom: 16px;
}

.word-bank {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.word-chip {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.word-chip:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
}

.word-chip:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.sentence-builder {
  min-height: 60px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.sentence-word {
  padding: 8px 16px;
  background: rgba(102, 126, 234, 0.4);
  border-radius: 20px;
  color: white;
  font-size: 14px;
  cursor: pointer;
}

.exercise-result {
  margin-top: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.result-message {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
}

.result-message.correct {
  color: #4caf50;
}

.result-message.incorrect {
  color: #ff5722;
}

.explanation {
  color: white;
  font-size: 14px;
  line-height: 1.6;
}

.explanation strong {
  display: block;
  margin-bottom: 8px;
}

.exercise-actions {
  margin-top: 24px;
}

.btn-check, .btn-next {
  width: 100%;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.25);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-check:hover:not(:disabled), .btn-next:hover {
  background: rgba(255, 255, 255, 0.35);
}

.btn-check:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.topic-progress {
  text-align: center;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-fill {
  height: 100%;
  background: rgba(76, 175, 80, 0.8);
  transition: width 0.3s ease;
}

.topic-progress p {
  color: white;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-back {
  flex: 1;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  cursor: pointer;
}

.btn-primary {
  flex: 2;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.25);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.generating-exercises {
  text-align: center;
  padding: 80px 20px;
  min-height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.spinner-large {
  width: 60px;
  height: 60px;
  border: 5px solid rgba(255, 255, 255, 0.2);
  border-top-color: rgba(102, 126, 234, 1);
  border-right-color: rgba(102, 126, 234, 0.8);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 32px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-title {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.sub-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  margin: 0 0 24px 0;
}

.loading-dots {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-top: 16px;
}

.loading-dots span {
  width: 10px;
  height: 10px;
  background: rgba(102, 126, 234, 0.8);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}
</style>


