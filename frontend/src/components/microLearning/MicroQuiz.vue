<template>
  <div class="micro-quiz">
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Preparing your quiz...</p>
    </div>

    <div v-else-if="questions.length > 0" class="quiz-container">
      <div class="quiz-header">
        <h2>Quick Check 🧪</h2>
        <div class="quiz-progress">
          Question {{ currentQuestionIndex + 1 }} of {{ questions.length }}
        </div>
      </div>

      <div class="question-card">
        <div class="question-text">{{ currentQuestion.question }}</div>
        
        <div class="options-list">
          <button
            v-for="option in currentQuestion.options"
            :key="option.letter"
            @click="selectAnswer(option.letter)"
            :class="['option-btn', { selected: selectedAnswer === option.letter }]"
            :disabled="showResult"
          >
            <span class="option-letter">{{ option.letter }})</span>
            <span class="option-text">{{ option.text }}</span>
          </button>
        </div>

        <div v-if="showResult" class="result-feedback">
          <div :class="['feedback-card', { correct: isCorrect, incorrect: !isCorrect }]">
            <div class="feedback-icon">{{ isCorrect ? '✓' : '✗' }}</div>
            <div class="feedback-text">
              {{ isCorrect ? 'Correct! Great job!' : `Incorrect. The correct answer is ${correctAnswer}.` }}
            </div>
          </div>
        </div>

        <div class="quiz-actions">
          <button
            v-if="!showResult && selectedAnswer"
            @click="checkAnswer"
            class="btn-primary"
          >
            Submit Answer
          </button>
          <button
            v-if="showResult"
            @click="nextQuestion"
            class="btn-primary"
          >
            {{ isLastQuestion ? 'Finish Quiz' : 'Next Question' }}
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="quizComplete" class="quiz-complete">
      <div class="complete-card">
        <div class="complete-icon">🎉</div>
        <h2>Quiz Complete!</h2>
        <div class="score-display">
          <div class="score-value">{{ score }}</div>
          <div class="score-label">out of {{ questions.length }} correct</div>
        </div>
        <p class="complete-message">
          {{ score === questions.length ? 'Perfect score! You mastered this lesson!' : 'Good job! Keep practicing to improve.' }}
        </p>
        <button @click="handleComplete" class="btn-primary btn-large">
          Continue Learning →
        </button>
      </div>
    </div>

    <div v-else class="quiz-start">
      <div class="start-card">
        <h2>Test Your Understanding</h2>
        <p>Ready for a quick 2-3 question quiz?</p>
        <button @click="requestQuiz" class="btn-primary btn-large">
          Start Quiz 🧪
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMicroLearningStore } from '@/stores/microLearning'
import { useChatStore } from '@/stores/chat'
import { useRoute } from 'vue-router'
import { parseQuiz } from '@/utils/quizParser'

const emit = defineEmits<{
  complete: []
}>()

const microLearningStore = useMicroLearningStore()
const chatStore = useChatStore()
const route = useRoute()

const isLoading = ref(false)
const questions = ref<any[]>([])
const currentQuestionIndex = ref(0)
const selectedAnswer = ref<string | null>(null)
const showResult = ref(false)
const isCorrect = ref(false)
const correctAnswer = ref('')
const quizComplete = ref(false)
const score = ref(0)

const agentId = route.params.agentId as string
const currentTopic = computed(() => {
  return microLearningStore.currentLesson?.topic || 'the lesson'
})

const currentQuestion = computed(() => {
  return questions.value[currentQuestionIndex.value] || { question: '', options: [], answer: '' }
})

const isLastQuestion = computed(() => {
  return currentQuestionIndex.value === questions.value.length - 1
})

onMounted(() => {
  if (questions.value.length === 0) {
    requestQuiz()
  }
})

function requestQuiz() {
  isLoading.value = true
  const topic = microLearningStore.currentLesson?.topic || 'the lesson'
  
  const message = `Generate a quick 2-3 question micro-quiz about ${topic} to test understanding. Use the generate_quiz tool with topic="${topic}", num_questions=2, difficulty="medium".`

  chatStore.sendMessage(agentId, message, microLearningStore.conversationId || undefined)
    .then(async (result) => {
      if (result.success) {
        await pollForQuiz()
      } else {
        isLoading.value = false
      }
    })
    .catch(() => {
      isLoading.value = false
    })
}

async function pollForQuiz(maxAttempts = 20) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (microLearningStore.conversationId) {
      try {
        await chatStore.fetchConversation(microLearningStore.conversationId)
        
        const messages = chatStore.messages
        if (messages.length > 0) {
          const lastMessage = messages[messages.length - 1]
          if (lastMessage.role === 'assistant' && lastMessage.content) {
            const parsed = parseQuiz(lastMessage.content)
            if (parsed.hasQuiz && parsed.questions.length > 0) {
              questions.value = parsed.questions.slice(0, 3) // Max 3 questions
              isLoading.value = false
              return
            }
          }
        }
      } catch (error) {
        console.error('Error fetching conversation:', error)
      }
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  
  isLoading.value = false
}

function selectAnswer(letter: string) {
  if (!showResult.value) {
    selectedAnswer.value = letter
  }
}

function checkAnswer() {
  if (!selectedAnswer.value) return
  
  const question = currentQuestion.value
  const correct = question.answer?.toUpperCase() === selectedAnswer.value.toUpperCase()
  isCorrect.value = correct
  correctAnswer.value = question.answer || ''
  
  if (correct) {
    score.value++
  }
  
  showResult.value = true
}

function nextQuestion() {
  if (isLastQuestion.value) {
    quizComplete.value = true
  } else {
    currentQuestionIndex.value++
    selectedAnswer.value = null
    showResult.value = false
    isCorrect.value = false
    correctAnswer.value = ''
  }
}

function handleComplete() {
  emit('complete')
}
</script>

<style scoped>
.micro-quiz {
  max-width: 700px;
  margin: 0 auto;
}

.loading-state {
  text-align: center;
  padding: 4rem 2rem;
  color: white;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.quiz-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.quiz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.quiz-header h2 {
  margin: 0;
  color: #333;
}

.quiz-progress {
  color: #666;
  font-weight: 500;
}

.question-card {
  margin-bottom: 1rem;
}

.question-text {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.option-btn {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 1rem;
  text-align: left;
  width: 100%;
}

.option-btn:hover:not(:disabled) {
  border-color: #667eea;
  background: #f8f9ff;
}

.option-btn.selected {
  border-color: #667eea;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
}

.option-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.option-letter {
  font-weight: bold;
  color: #667eea;
  font-size: 1.1rem;
}

.option-text {
  flex: 1;
  color: #333;
}

.result-feedback {
  margin-bottom: 1.5rem;
}

.feedback-card {
  padding: 1rem 1.5rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.feedback-card.correct {
  background: #d1fae5;
  border: 2px solid #10b981;
}

.feedback-card.incorrect {
  background: #fee2e2;
  border: 2px solid #ef4444;
}

.feedback-icon {
  font-size: 2rem;
  font-weight: bold;
}

.feedback-card.correct .feedback-icon {
  color: #10b981;
}

.feedback-card.incorrect .feedback-icon {
  color: #ef4444;
}

.feedback-text {
  flex: 1;
  font-weight: 500;
  color: #333;
}

.quiz-actions {
  display: flex;
  justify-content: center;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s;
}

.btn-primary:hover {
  transform: translateY(-2px);
}

.quiz-start,
.quiz-complete {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.start-card,
.complete-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 500px;
}

.complete-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.score-display {
  margin: 2rem 0;
}

.score-value {
  font-size: 3rem;
  font-weight: bold;
  color: #667eea;
  line-height: 1;
}

.score-label {
  color: #666;
  margin-top: 0.5rem;
}

.complete-message {
  color: #666;
  margin: 1.5rem 0;
  font-size: 1.1rem;
}

.btn-large {
  width: 100%;
  padding: 1rem;
  font-size: 1.1rem;
  margin-top: 1rem;
}

@media (max-width: 768px) {
  .quiz-header {
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
  }
}
</style>




