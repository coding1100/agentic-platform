<template>
  <div class="learning-area">
    <!-- Level Selection -->
    <div v-if="!currentLevel && !currentQuiz" class="level-selection">
      <div class="level-card">
        <h2>Choose a Level 🎮</h2>
        <p class="level-description">Select a difficulty level to start learning {{ topic?.name }}</p>
        <div class="levels-grid">
          <button
            v-for="level in levels"
            :key="level.id"
            @click="selectLevel(level)"
            :class="['level-btn', level.difficulty]"
          >
            <span class="level-number">Level {{ level.number }}</span>
            <span class="level-name">{{ level.name }}</span>
            <span class="level-difficulty">{{ level.difficulty }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Loading Quiz -->
    <div v-else-if="!currentQuiz" class="loading-quiz">
      <div class="loading-card">
        <h2>Preparing Your Quiz 📝</h2>
        <p>Getting questions ready for {{ topic?.name }} - {{ currentLevel?.name }}...</p>
        <div class="spinner"></div>
        <div v-if="quizError" class="error-message">
          <p>{{ quizError }}</p>
          <button @click="retryQuizRequest" class="btn-retry-loading">Retry</button>
        </div>
      </div>
    </div>

    <!-- Quiz Intro -->
    <div v-else-if="!quizStarted" class="quiz-intro">
      <div class="intro-card">
        <h2>Ready to Learn {{ topic?.name }}? 🎯</h2>
        <p class="intro-text">
          Hi {{ childName }}! Let's practice {{ topic?.name.toLowerCase() }} at {{ currentLevel?.name }} level. 
          Answer the questions below and I'll help you learn!
        </p>
        <button @click="startQuiz" class="btn-primary">
          Start Quiz
        </button>
      </div>
    </div>

    <!-- Active Quiz -->
    <div v-else-if="!quizCompleted" class="quiz-container">
      <div class="quiz-header">
        <h2>{{ topic?.name }} - {{ currentLevel?.name }}</h2>
        <div class="quiz-progress">
          Question {{ currentQuestionIndex + 1 }} of {{ questions.length }}
        </div>
      </div>

      <div class="question-card">
        <!-- Instructions with TTS -->
        <div class="instructions-section">
          <div class="instructions-text">
            {{ questionTextOnly }}
          </div>
          <button @click="speakInstructions" class="tts-btn" :disabled="isSpeaking">
            <span v-if="!isSpeaking">🔊</span>
            <span v-else>⏸️</span>
            {{ isSpeaking ? 'Speaking...' : 'Listen' }}
          </button>
        </div>
        
        <!-- Response Type Toggle -->
        <div class="response-type-toggle">
          <button
            @click="responseType = 'mcq'"
            :class="['toggle-btn', { active: responseType === 'mcq' }]"
          >
            Multiple Choice
          </button>
          <button
            @click="responseType = 'typing'"
            :class="['toggle-btn', { active: responseType === 'typing' }]"
          >
            Type Answer
          </button>
        </div>

        <!-- MCQ Options -->
        <div v-if="responseType === 'mcq'" class="options-list">
          <button
            v-for="option in currentQuestion.options"
            :key="option.letter"
            @click="selectAnswer(option.letter)"
            :class="['option-btn', { 
              selected: selectedAnswer === option.letter,
              correct: showResult && isCorrect && selectedAnswer === option.letter,
              incorrect: showResult && !isCorrect && selectedAnswer === option.letter
            }]"
            :disabled="showResult || isValidatingAnswer"
          >
            <span class="option-letter">{{ option.letter }})</span>
            <span class="option-text">{{ option.text }}</span>
          </button>
        </div>

        <!-- Typing Input -->
        <div v-else class="typing-input-section">
          <input
            v-model="typedAnswer"
            @keyup.enter="submitTypedAnswer"
            type="text"
            placeholder="Type your answer here..."
            :disabled="showResult || isValidatingAnswer"
            class="typing-input"
          />
          <button
            @click="submitTypedAnswer"
            :disabled="!typedAnswer.trim() || showResult || isValidatingAnswer"
            class="btn-submit-answer"
          >
            Submit
          </button>
        </div>

        <!-- Loading State for AI Validation -->
        <div v-if="isValidatingAnswer" class="validating-answer">
          <div class="validating-content">
            <div class="spinner-small"></div>
            <p>AI is checking your answer...</p>
          </div>
        </div>

        <!-- Adaptive Feedback -->
        <div v-else-if="showResult" class="result-feedback">
          <div v-if="isCorrect" class="feedback correct">
            <span class="feedback-icon">✅</span>
            <div class="feedback-content">
              <span class="feedback-text">Great job! That's correct!</span>
              <div v-if="aiValidationResponse" class="ai-response">
                <strong>AI Feedback:</strong> {{ aiValidationResponse }}
              </div>
            </div>
          </div>
          <div v-else class="feedback incorrect">
            <span class="feedback-icon">❌</span>
            <div class="feedback-content">
              <div v-if="aiValidationResponse" class="ai-response">
                <strong>AI Feedback:</strong> {{ aiValidationResponse }}
              </div>
              <div v-else class="feedback-text">
                {{ adaptiveExplanation }}
              </div>
              <div v-if="wrongAttempts >= 2" class="hint-section">
                <strong>Hint:</strong> {{ currentQuestion.hint || 'Think carefully about the question.' }}
              </div>
            </div>
          </div>
          <div class="feedback-actions">
            <button
              v-if="!isCorrect && wrongAttempts < 3"
              @click="retryQuestion"
              class="btn-retry"
            >
              Try Again
            </button>
            <button
              v-else
              @click="nextQuestion"
              class="btn-next"
            >
              {{ isLastQuestion ? 'See Results' : 'Next Question' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Quiz Results -->
    <div v-else class="quiz-results">
      <div class="results-card">
        <h2>Quiz Complete! 🎉</h2>
        <div class="score-display">
          <div class="score-circle" :class="scoreClass">
            <span class="score-value">{{ results.percentage }}%</span>
            <span class="score-label">Score</span>
          </div>
          <div class="score-details">
            <p>You got <strong>{{ results.correct }}</strong> out of <strong>{{ results.total }}</strong> questions correct!</p>
          </div>
        </div>

        <div v-if="results.weakAreas.length > 0" class="weak-areas">
          <h3>Areas to Focus On:</h3>
          <ul>
            <li v-for="area in results.weakAreas" :key="area">{{ area }}</li>
          </ul>
        </div>

        <div v-else class="perfect-score">
          <p>🎊 Perfect score! You've mastered this level!</p>
        </div>

        <div class="results-actions">
          <button
            v-if="results.percentage < 100"
            @click="restartQuiz"
            class="btn-secondary"
          >
            Practice More
          </button>
          <button
            v-if="results.percentage === 100 && hasNextLevel"
            @click="nextLevel"
            class="btn-primary"
          >
            Next Level
          </button>
          <button
            v-else-if="results.percentage === 100"
            @click="progressiveAssessment"
            class="btn-primary"
          >
            More Challenging Questions
          </button>
          <button @click="goToTopics" class="btn-secondary">
            Choose Another Topic
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTutorStore } from '@/stores/tutor'
import { useChatStore } from '@/stores/chat'
import { parseQuiz, type QuizQuestion } from '@/utils/quizParser'
import { ttsApi } from '@/services/api'
import type { Topic, Level } from '@/stores/tutor'

const props = defineProps<{
  topic: Topic | null
  childName: string
}>()

const emit = defineEmits<{
  quizComplete: [results: { correct: number; total: number; percentage: number; weakAreas: string[] }]
}>()

const route = useRoute()
const tutorStore = useTutorStore()
const chatStore = useChatStore()

// Levels for the topic
const levels: Level[] = [
  { id: 'level-1', number: 1, name: 'Beginner', difficulty: 'easy' },
  { id: 'level-2', number: 2, name: 'Intermediate', difficulty: 'medium' },
  { id: 'level-3', number: 3, name: 'Advanced', difficulty: 'hard' },
]

const currentLevel = computed(() => tutorStore.currentLevel)
const currentQuiz = ref<string | null>(null)
const quizStarted = ref(false)
const quizCompleted = ref(false)
const isLoadingQuiz = ref(false)
const quizError = ref<string | null>(null)
const questions = ref<QuizQuestion[]>([])
const currentQuestionIndex = ref(0)
const selectedAnswer = ref<string | null>(null)
const typedAnswer = ref('')
const responseType = ref<'mcq' | 'typing'>('mcq')
const showResult = ref(false)
const isValidatingAnswer = ref(false)
const aiValidationResponse = ref<string | null>(null)
const answers = ref<Record<number, { 
  selected: string; // User's selected answer (letter for MCQ, text for typing)
  selectedLetter: string; // User's selected letter (for MCQ)
  correctLetter: string; // Correct answer letter
  correctText: string; // Correct answer text
  attempts: number; 
  isCorrect?: boolean 
}>>({})
const results = ref<{ correct: number; total: number; percentage: number; weakAreas: string[] } | null>(null)
const isSpeaking = ref(false)
const currentAudio = ref<HTMLAudioElement | null>(null)

const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])

// Extract question text without options
const questionTextOnly = computed(() => {
  if (!currentQuestion.value) return ''
  let text = currentQuestion.value.question
  
  // Remove options if they're embedded in the question text
  // Pattern: "A) option B) option C) option D) option" at the end
  text = text.replace(/\s*[A-D]\)\s*[^\n]*(?:\s+[A-D]\)\s*[^\n]*){0,3}\s*$/i, '').trim()
  
  // Also remove if options are on separate lines at the end
  const lines = text.split('\n')
  const filteredLines: string[] = []
  let foundOptions = false
  
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i].trim()
    if (line.match(/^[A-D]\)\s+/i)) {
      foundOptions = true
      continue
    }
    if (foundOptions && !line) {
      continue
    }
    if (foundOptions) {
      break
    }
    filteredLines.unshift(lines[i])
  }
  
  return foundOptions ? filteredLines.join('\n').trim() : text
})

const isLastQuestion = computed(() => currentQuestionIndex.value === questions.value.length - 1)
const wrongAttempts = computed(() => answers.value[currentQuestionIndex.value]?.attempts || 0)
const isCorrect = computed(() => {
  const question = currentQuestion.value
  const answer = answers.value[currentQuestionIndex.value]
  if (!answer) return false
  
  // Use the stored isCorrect flag from AI validation (most reliable)
  if (answer.isCorrect !== undefined) {
    return answer.isCorrect
  }
  
  // Fallback: Compare letters for MCQ, text for typing
  if (responseType.value === 'mcq' && answer.selectedLetter && answer.correctLetter) {
    return answer.selectedLetter === answer.correctLetter
  }
  
  // For typing answers, compare text
  return answer.selected.toLowerCase().trim() === answer.correctText.toLowerCase().trim()
})

const adaptiveExplanation = computed(() => {
  const question = currentQuestion.value
  if (!question) return 'Let me explain this again.'
  
  // Get the correct answer text
  let correctAnswerText = question.answer || ''
  if (question.options.length > 0 && correctAnswerText) {
    const correctOption = question.options.find(opt => opt.letter === correctAnswerText)
    if (correctOption) {
      correctAnswerText = correctOption.text
    }
  }
  
  if (wrongAttempts.value === 1) {
    return 'Let me explain this again. ' + (question.explanation || `The correct answer is ${correctAnswerText}.`)
  } else if (wrongAttempts.value >= 2) {
    return 'Let\'s try a different approach. ' + (question.detailedExplanation || question.explanation || 'Think about it step by step.')
  }
  return `The correct answer is ${correctAnswerText}.`
})

const hasNextLevel = computed(() => {
  if (!currentLevel.value) return false
  const currentLevelNum = currentLevel.value.number
  return currentLevelNum < levels.length
})

const scoreClass = computed(() => {
  if (!results.value) return ''
  if (results.value.percentage >= 90) return 'excellent'
  if (results.value.percentage >= 70) return 'good'
  if (results.value.percentage >= 50) return 'fair'
  return 'needs-improvement'
})

onMounted(async () => {
  // Auto-speak instructions when question loads
  watch(() => currentQuestion.value, () => {
    if (currentQuestion.value && quizStarted.value) {
      setTimeout(() => {
        speakInstructions()
      }, 500)
    }
  }, { immediate: false })
})

function selectLevel(level: Level) {
  tutorStore.setCurrentLevel(level)
  currentQuiz.value = null // Reset quiz state
  questions.value = [] // Clear previous questions
  requestQuiz()
}

async function requestQuiz() {
  const agentId = route.params.agentId as string
  if (!agentId || !tutorStore.currentLevel || !props.topic) return

  isLoadingQuiz.value = true
  quizError.value = null

  try {
    const difficulty = tutorStore.currentLevel.difficulty
    const topicName = props.topic.name
    const subject = tutorStore.selectedSubject || 'math'
    
    // Create a clear, specific quiz request with topic and subject context
    const message = `Generate a quiz about ${topicName} (${subject} subject) with exactly 5 multiple choice questions at ${difficulty} difficulty level. 

IMPORTANT: 
- The quiz must be specifically about "${topicName}" in ${subject}
- Use the generate_quiz tool
- Generate exactly 5 questions
- Difficulty level: ${difficulty}`
    
    const result = await chatStore.sendMessage(
      agentId,
      message,
      tutorStore.conversationId || undefined
    )

    if (result.success) {
      // Poll for the response with exponential backoff
      await pollForQuizResponse()
    } else {
      quizError.value = result.error || 'Failed to generate quiz'
      isLoadingQuiz.value = false
    }
  } catch (error: any) {
    quizError.value = error.message || 'An error occurred while generating the quiz'
    isLoadingQuiz.value = false
  }
}

function retryQuizRequest() {
  quizError.value = null
  requestQuiz()
}

async function pollForQuizResponse(maxAttempts = 20, delay = 1000) {
  console.log('Starting quiz polling...')
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (tutorStore.conversationId) {
      try {
        await chatStore.fetchConversation(tutorStore.conversationId)
        
        const newMessages = chatStore.messages
        console.log(`Poll attempt ${attempt + 1}: Found ${newMessages.length} messages`)
        
        if (newMessages.length > 0) {
          // Check the last few messages for quiz content (most recent first)
          const recentMessages = [...newMessages].reverse().slice(0, 5)
          
          for (const message of recentMessages) {
            if (message.role === 'assistant' && message.content) {
              console.log('Checking message:', message.content.substring(0, 150))
              const parsed = parseQuiz(message.content)
              console.log('Parse result:', { hasQuiz: parsed.hasQuiz, questionCount: parsed.questions.length })
              
              if (parsed.hasQuiz && parsed.questions.length > 0) {
                console.log('✅ Quiz found! Setting up questions...')
                console.log('Parsed questions with answers:', parsed.questions.map(q => ({
                  question: q.question.substring(0, 50),
                  answer: q.answer,
                  options: q.options.map(opt => opt.letter)
                })))
                
                // Check if any questions are missing answers
                const questionsWithoutAnswers = parsed.questions.filter(q => !q.answer)
                if (questionsWithoutAnswers.length > 0) {
                  console.error('⚠️ WARNING: Some questions are missing answers!', questionsWithoutAnswers.length)
                  console.error('Raw quiz content sample:', message.content.substring(0, 500))
                }
                
                currentQuiz.value = message.content
                questions.value = parsed.questions.map(q => {
                  // Get the correct answer text from options if available
                  let correctAnswerText = q.answer || ''
                  if (q.options.length > 0 && correctAnswerText) {
                    const correctOption = q.options.find(opt => opt.letter.toUpperCase() === correctAnswerText.toUpperCase())
                    if (correctOption) {
                      correctAnswerText = correctOption.text
                    }
                  }
                  
                  return {
                    ...q,
                    explanation: `The correct answer is ${correctAnswerText}.`,
                    detailedExplanation: `Let's break this down step by step. ${correctAnswerText} is correct because...`,
                    hint: `Consider the key concepts related to: ${q.question.substring(0, 50)}...`
                  }
                })
                isLoadingQuiz.value = false
                return // Successfully found quiz
              }
            }
          }
        }
      } catch (error) {
        console.error('Error fetching conversation:', error)
      }
    }
    
    // Wait before next attempt with exponential backoff (capped at 2.5 seconds)
    const waitTime = Math.min(delay * Math.pow(1.2, attempt), 2500)
    console.log(`Waiting ${waitTime}ms before next poll...`)
    await new Promise(resolve => setTimeout(resolve, waitTime))
  }
  
  // If we get here, quiz wasn't found - show error
  console.error('❌ Quiz not found after', maxAttempts, 'polling attempts')
  isLoadingQuiz.value = false
  quizError.value = 'Quiz generation is taking longer than expected. The AI might still be processing. Please try again or check the chat sidebar.'
}

// Watch for new messages with better detection
watch(() => chatStore.messages, (newMessages, oldMessages) => {
  if (!currentQuiz.value && newMessages.length > 0) {
    // Check the last few messages (most recent first)
    const messagesToCheck = [...newMessages].reverse().slice(0, 5)
    
    for (const message of messagesToCheck) {
      if (message.role === 'assistant' && message.content) {
        // Check if this is a new message
        const isNew = !oldMessages || !oldMessages.find(m => m.id === message.id && m.content === message.content)
        
        if (isNew) {
          console.log('Checking message for quiz:', message.content.substring(0, 100))
          const parsed = parseQuiz(message.content)
          console.log('Parsed quiz:', parsed.hasQuiz, 'Questions:', parsed.questions.length)
          
          if (parsed.hasQuiz && parsed.questions.length > 0) {
            console.log('Quiz detected! Setting questions...')
            currentQuiz.value = message.content
            questions.value = parsed.questions.map(q => {
              // Get the correct answer text from options if available
              let correctAnswerText = q.answer || ''
              if (q.options.length > 0 && correctAnswerText) {
                const correctOption = q.options.find(opt => opt.letter === correctAnswerText)
                if (correctOption) {
                  correctAnswerText = correctOption.text
                }
              }
              
              return {
                ...q,
                explanation: `The correct answer is ${correctAnswerText}.`,
                detailedExplanation: `Let's break this down step by step. ${correctAnswerText} is correct because...`,
                hint: `Consider the key concepts related to: ${q.question.substring(0, 50)}...`
              }
            })
            isLoadingQuiz.value = false
            break
          }
        }
      }
    }
  }
}, { deep: true, immediate: true })

async function speakInstructions() {
  if (!currentQuestion.value || isSpeaking.value) return
  
  try {
    isSpeaking.value = true
    
    // Stop any currently playing audio
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
    }
    
    // Speak only the question text, not the options
    const textToSpeak = questionTextOnly.value
    const audioBlob = await ttsApi.speak(textToSpeak, 150, 0.9)
    const audioUrl = URL.createObjectURL(audioBlob)
    
    const audio = new Audio(audioUrl)
    currentAudio.value = audio
    
    audio.onended = () => {
      isSpeaking.value = false
      URL.revokeObjectURL(audioUrl)
    }
    
    audio.onerror = () => {
      isSpeaking.value = false
      URL.revokeObjectURL(audioUrl)
    }
    
    await audio.play()
  } catch (error) {
    console.error('TTS Error:', error)
    isSpeaking.value = false
  }
}

function startQuiz() {
  quizStarted.value = true
  speakInstructions()
}

function selectAnswer(letter: string) {
  // Prevent multiple calls - check if already validating or result shown
  if (showResult.value || isValidatingAnswer.value) return
  selectedAnswer.value = letter
  checkAnswer(letter)
}

function submitTypedAnswer() {
  // Prevent multiple calls - check if already validating or result shown
  if (!typedAnswer.value.trim() || showResult.value || isValidatingAnswer.value) return
  checkAnswer(typedAnswer.value.trim())
}

async function checkAnswer(answer: string) {
  // Guard: Prevent multiple concurrent API calls
  if (isValidatingAnswer.value || showResult.value) {
    console.log('Validation already in progress or result already shown, skipping...')
    return
  }
  
  // Show loading state immediately
  isValidatingAnswer.value = true
  aiValidationResponse.value = null
  
  const questionIndex = currentQuestionIndex.value
  const question = currentQuestion.value
  
  if (!question) {
    console.error('No question available')
    isValidatingAnswer.value = false
    return
  }
  
  // Get the correct answer letter from the question
  let correctAnswerLetter = question.answer || ''
  
  // If answer is missing, try to extract it from raw quiz content as fallback
  if (!correctAnswerLetter && currentQuiz.value) {
    console.warn('⚠️ Answer not found in parsed question, attempting to extract from raw content...')
    
    // Try to re-parse the quiz content to extract answers
    const rawParsed = parseQuiz(currentQuiz.value)
    if (rawParsed.questions && rawParsed.questions.length > questionIndex) {
      const rawQuestion = rawParsed.questions[questionIndex]
      if (rawQuestion.answer) {
        console.log(`✅ Found answer "${rawQuestion.answer}" from raw content`)
        correctAnswerLetter = rawQuestion.answer
        // Update the question object with the found answer
        questions.value[questionIndex].answer = rawQuestion.answer
      }
    }
    
    // If still no answer, try to extract directly from raw content using regex
    if (!correctAnswerLetter && currentQuiz.value) {
      const questionNum = questionIndex + 1
      // Look for answer after this specific question
      const questionMarker = `**Question ${questionNum}:**`
      const nextQuestionMarker = `**Question ${questionNum + 1}:**`
      
      const questionStart = currentQuiz.value.indexOf(questionMarker)
      const questionEnd = currentQuiz.value.indexOf(nextQuestionMarker, questionStart)
      const questionSection = questionEnd > 0 
        ? currentQuiz.value.substring(questionStart, questionEnd)
        : currentQuiz.value.substring(questionStart)
      
      // Try to find answer in this section
      const answerMatch = questionSection.match(/\*\*Answer:\*\*\s*([A-D])/i) || 
                          questionSection.match(/Answer:\s*([A-D])/i)
      if (answerMatch && answerMatch[1]) {
        correctAnswerLetter = answerMatch[1].toUpperCase()
        console.log(`✅ Extracted answer "${correctAnswerLetter}" using regex fallback`)
        // Update the question object
        questions.value[questionIndex].answer = correctAnswerLetter
      }
    }
  }
  
    // If still no answer after all attempts, show error (with small delay to show loading)
    if (!correctAnswerLetter) {
      console.error('❌ CRITICAL ERROR: Could not find answer after all attempts!', {
        questionIndex,
        questionText: question.question?.substring(0, 100),
        hasRawContent: !!currentQuiz.value,
        rawContentSample: currentQuiz.value?.substring(0, 1000),
        allQuestionsAnswers: questions.value.map((q, idx) => ({
          index: idx,
          answer: q.answer
        }))
      })
      
      // Small delay to show loading state before error
      await new Promise(resolve => setTimeout(resolve, 500))
      
      isValidatingAnswer.value = false
      aiValidationResponse.value = 'Error: Quiz answer not found. The quiz may be corrupted. Please restart the quiz.'
      showResult.value = true
      return
    }
  
  // Get the full correct answer text for display
  let correctAnswerText = correctAnswerLetter
  if (question.options.length > 0 && correctAnswerLetter) {
    const correctOption = question.options.find(opt => opt.letter.toUpperCase() === correctAnswerLetter.toUpperCase())
    if (correctOption) {
      correctAnswerText = correctOption.text
    } else {
      console.warn(`⚠️ Could not find option for letter "${correctAnswerLetter}"`, {
        availableOptions: question.options.map(opt => opt.letter),
        correctAnswerLetter
      })
    }
  }
  
  // For MCQ: user selects a letter, we need to get the text for that option
  let userAnswerText = answer
  if (responseType.value === 'mcq' && question.options.length > 0) {
    const selectedOption = question.options.find(opt => opt.letter.toUpperCase() === answer.toUpperCase())
    if (selectedOption) {
      userAnswerText = selectedOption.text
    }
  }
  
  // Validate answer using AI (which will use direct comparison first)
  const validationResult = await validateAnswerWithAI(
    question.question, 
    userAnswerText, 
    correctAnswerText, 
    question.options,
    correctAnswerLetter,
    answer
  )
  
  console.log('✅ Validation Result:', {
    isCorrect: validationResult.isCorrect,
    response: validationResult.response,
    userAnswer: userAnswerText,
    userLetter: answer,
    correctAnswer: correctAnswerText,
    correctLetter: correctAnswerLetter
  })
  
  // Store the answer with both letter and text for proper validation
  if (!answers.value[questionIndex]) {
    answers.value[questionIndex] = {
      selected: responseType.value === 'mcq' ? answer : userAnswerText,
      selectedLetter: responseType.value === 'mcq' ? answer.toUpperCase() : '',
      correctLetter: correctAnswerLetter.toUpperCase(),
      correctText: correctAnswerText,
      attempts: 0,
      isCorrect: validationResult.isCorrect
    }
  } else {
    answers.value[questionIndex].selected = responseType.value === 'mcq' ? answer : userAnswerText
    answers.value[questionIndex].selectedLetter = responseType.value === 'mcq' ? answer.toUpperCase() : ''
  }
  
  answers.value[questionIndex].attempts++
  answers.value[questionIndex].isCorrect = validationResult.isCorrect
  
  // Store AI response
  aiValidationResponse.value = validationResult.response || null
  
  console.log('Stored answer:', answers.value[questionIndex])
  console.log('Is correct:', validationResult.isCorrect)
  
  // Track wrong answers for adaptive learning
  if (!validationResult.isCorrect) {
    tutorStore.incrementWrongAnswer(questionIndex)
  }
  
  // Now show the result
  isValidatingAnswer.value = false
  showResult.value = true
  
  // Speak feedback
  if (validationResult.isCorrect) {
    speakText('Great job! That is correct!')
  } else {
    // Speak only the AI feedback, not "Not quite right"
    const feedbackToSpeak = validationResult.response || adaptiveExplanation.value
    speakText(feedbackToSpeak)
  }
}

async function validateAnswerWithAI(
  question: string, 
  userAnswer: string, 
  correctAnswer: string,
  options: Array<{ letter: string; text: string }> = [],
  correctAnswerLetter: string = '',
  userAnswerLetter: string = ''
): Promise<{ isCorrect: boolean; response: string }> {
  try {
    const agentId = route.params.agentId as string
    
    // For MCQ, check if letters match first (fastest and most reliable)
    if (options.length > 0 && correctAnswerLetter && userAnswerLetter) {
      const isCorrect = correctAnswerLetter.toUpperCase() === userAnswerLetter.toUpperCase()
      console.log(`Direct comparison: User="${userAnswerLetter}", Correct="${correctAnswerLetter}", Match=${isCorrect}`)
      if (isCorrect) {
        return { isCorrect: true, response: 'Your answer is correct! Great job!' }
      } else {
        // If wrong, we can still use AI for explanation, but return immediately if we want fast feedback
        // For now, let's return immediately with the correct answer
        const correctOption = options.find(opt => opt.letter.toUpperCase() === correctAnswerLetter.toUpperCase())
        const correctText = correctOption ? correctOption.text : correctAnswerLetter
        return { 
          isCorrect: false, 
          response: `The correct answer is ${correctAnswerLetter}) ${correctText}. Please review and try again.` 
        }
      }
    }
    
    // If we don't have answer letters, try to use AI validation
    console.warn('Missing answer letters, attempting AI validation. CorrectLetter:', correctAnswerLetter, 'UserLetter:', userAnswerLetter)
    
    // Build validation prompt
    let validationPrompt = `Please validate if the student's answer is correct for this question:

Question: ${question}
Correct Answer: ${correctAnswer}
Student's Answer: ${userAnswer}

Please respond in this EXACT format:
**VALIDATION:** CORRECT or INCORRECT
**EXPLANATION:** [Brief explanation of why the answer is correct or incorrect]

Start with **VALIDATION:** followed by either CORRECT or INCORRECT, then **EXPLANATION:** with your reasoning.`

    // For MCQ, also include options for context
    if (options.length > 0) {
      const optionsText = options.map(opt => `${opt.letter}) ${opt.text}`).join('\n')
      validationPrompt = `Please validate if the student's answer is correct for this multiple choice question:

Question: ${question}
Options:
${optionsText}
Correct Answer: ${correctAnswer} (Option ${correctAnswerLetter})
Student's Answer: ${userAnswer}${userAnswerLetter ? ` (Option ${userAnswerLetter})` : ''}

Please respond in this EXACT format:
**VALIDATION:** CORRECT or INCORRECT
**EXPLANATION:** [Brief explanation of why the answer is correct or incorrect]

Start with **VALIDATION:** followed by either CORRECT or INCORRECT, then **EXPLANATION:** with your reasoning.`
    }
    
    const result = await chatStore.sendMessage(
      agentId,
      validationPrompt,
      tutorStore.conversationId || undefined
    )
    
    if (result.success) {
      // Poll for the validation response
      const validationResult = await pollForValidation()
      
      // If polling returned a valid result (not a fallback message), use it
      if (validationResult.response && !validationResult.response.includes('not received') && !validationResult.response.includes('Could not validate')) {
        return validationResult
      }
      
      // If polling failed, fall through to direct comparison
      console.log('Polling did not return valid result, using direct comparison')
    }
    
    // Fallback to simple comparison if AI validation fails
    console.log('AI validation failed, using fallback comparison')
    let isCorrect = false
    if (correctAnswerLetter && userAnswerLetter) {
      isCorrect = correctAnswerLetter.toUpperCase() === userAnswerLetter.toUpperCase()
      console.log(`Fallback: Comparing letters - User: ${userAnswerLetter}, Correct: ${correctAnswerLetter}, Match: ${isCorrect}`)
    } else {
      isCorrect = userAnswer.toLowerCase().trim() === correctAnswer.toLowerCase().trim()
      console.log(`Fallback: Comparing text - User: "${userAnswer}", Correct: "${correctAnswer}", Match: ${isCorrect}`)
    }
    
    return { 
      isCorrect, 
      response: isCorrect 
        ? 'Your answer is correct!' 
        : `The correct answer is ${correctAnswerLetter || correctAnswer}. ${isCorrect ? '' : 'Please try again.'}` 
    }
  } catch (error) {
    console.error('AI validation error:', error)
    // Fallback to simple comparison
    let isCorrect = false
    if (correctAnswerLetter && userAnswerLetter) {
      isCorrect = correctAnswerLetter.toUpperCase() === userAnswerLetter.toUpperCase()
      console.log(`Error fallback: Comparing letters - User: ${userAnswerLetter}, Correct: ${correctAnswerLetter}, Match: ${isCorrect}`)
    } else {
      isCorrect = userAnswer.toLowerCase().trim() === correctAnswer.toLowerCase().trim()
      console.log(`Error fallback: Comparing text - User: "${userAnswer}", Correct: "${correctAnswer}", Match: ${isCorrect}`)
    }
    
    return { 
      isCorrect, 
      response: isCorrect 
        ? 'Your answer is correct!' 
        : `The correct answer is ${correctAnswerLetter || correctAnswer}. Please review and try again.` 
    }
  }
}

async function pollForValidation(maxAttempts = 15, delay = 500): Promise<{ isCorrect: boolean; response: string }> {
  // Track if we've already found a validation result to prevent multiple returns
  let validationFound = false
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    // If validation is no longer in progress, stop polling
    if (!isValidatingAnswer.value || showResult.value) {
      break
    }
    
    if (tutorStore.conversationId) {
      try {
        await chatStore.fetchConversation(tutorStore.conversationId)
        
        const newMessages = chatStore.messages
        if (newMessages.length > 0) {
          const recentMessages = [...newMessages].reverse().slice(0, 5)
          
          for (const message of recentMessages) {
            if (message.role === 'assistant' && message.content) {
              const content = message.content
              
              // Try to parse structured format
              const validationMatch = content.match(/\*\*VALIDATION:\*\*\s*(CORRECT|INCORRECT)/i)
              const explanationMatch = content.match(/\*\*EXPLANATION:\*\*\s*(.+?)(?=\*\*|$)/is)
              
              if (validationMatch && !validationFound) {
                validationFound = true
                const isCorrect = validationMatch[1].toUpperCase() === 'CORRECT'
                const explanation = explanationMatch ? explanationMatch[1].trim() : (isCorrect ? 'Your answer is correct!' : 'Your answer needs correction.')
                return { isCorrect, response: explanation }
              }
              
              // Fallback: check for standalone CORRECT/INCORRECT (not in the prompt)
              // Look for lines that start with CORRECT or INCORRECT
              const lines = content.split('\n').map(line => line.trim()).filter(line => line.length > 0)
              const correctLine = lines.find(line => {
                const upper = line.toUpperCase()
                return (upper.startsWith('CORRECT') || upper === 'CORRECT') && 
                       !upper.includes('VALIDATION') &&
                       !upper.includes('PLEASE') &&
                       !upper.includes('RESPOND')
              })
              const incorrectLine = lines.find(line => {
                const upper = line.toUpperCase()
                return (upper.startsWith('INCORRECT') || upper === 'INCORRECT') && 
                       !upper.includes('VALIDATION') &&
                       !upper.includes('PLEASE') &&
                       !upper.includes('RESPOND')
              })
              
              if (correctLine && !incorrectLine && !validationFound) {
                validationFound = true
                // Find explanation text
                const explanation = lines.find(line => 
                  !line.toUpperCase().includes('VALIDATION') && 
                  !line.toUpperCase().includes('CORRECT') &&
                  !line.toUpperCase().includes('INCORRECT') &&
                  !line.toUpperCase().includes('PLEASE') &&
                  !line.toUpperCase().includes('RESPOND') &&
                  line.trim().length > 10
                ) || 'Your answer is correct!'
                return { isCorrect: true, response: explanation.trim() }
              } else if (incorrectLine && !validationFound) {
                validationFound = true
                const explanation = lines.find(line => 
                  !line.toUpperCase().includes('VALIDATION') && 
                  !line.toUpperCase().includes('CORRECT') &&
                  !line.toUpperCase().includes('INCORRECT') &&
                  !line.toUpperCase().includes('PLEASE') &&
                  !line.toUpperCase().includes('RESPOND') &&
                  line.trim().length > 10
                ) || 'Your answer needs correction.'
                return { isCorrect: false, response: explanation.trim() }
              }
            }
          }
        }
      } catch (err) {
        console.error('Error fetching conversation:', err)
      }
    }
    
    await new Promise(resolve => setTimeout(resolve, delay))
  }
  
  // If we get here, validation wasn't found - use fallback comparison
  // This should not happen often, but if polling fails, we'll compare directly
  console.warn('Validation polling completed but no result found, using fallback comparison')
  
  // Return a fallback that will trigger the comparison in validateAnswerWithAI
  // The caller should handle this by using the letter comparison
  return { isCorrect: false, response: 'Validation response not received. Using direct comparison...' }
}

async function speakText(text: string) {
  try {
    const audioBlob = await ttsApi.speak(text, 150, 0.9)
    const audioUrl = URL.createObjectURL(audioBlob)
    const audio = new Audio(audioUrl)
    await audio.play()
    audio.onended = () => URL.revokeObjectURL(audioUrl)
  } catch (error) {
    console.error('TTS Error:', error)
  }
}

function retryQuestion() {
  showResult.value = false
  isValidatingAnswer.value = false
  aiValidationResponse.value = null
  selectedAnswer.value = null
  typedAnswer.value = ''
  // Speak the question again
  setTimeout(() => {
    speakInstructions()
  }, 300)
}

function nextQuestion() {
  if (isLastQuestion.value) {
    calculateResults()
    quizCompleted.value = true
  } else {
    currentQuestionIndex.value++
    selectedAnswer.value = null
    typedAnswer.value = ''
    showResult.value = false
    // Auto-speak next question
    setTimeout(() => {
      speakInstructions()
    }, 500)
  }
}

function calculateResults() {
  let correct = 0
  const weakAreas: string[] = []

  questions.value.forEach((question, index) => {
    const answer = answers.value[index]
    if (answer) {
      // Use isCorrect flag if available (from AI validation)
      let isAnswerCorrect = false
      if (answer.isCorrect !== undefined) {
        isAnswerCorrect = answer.isCorrect
      } else {
        // Fallback: Compare based on answer type
        if (answer.selectedLetter && answer.correctLetter) {
          // MCQ: Compare letters
          isAnswerCorrect = answer.selectedLetter === answer.correctLetter
        } else {
          // Typing: Compare text
          isAnswerCorrect = answer.selected.toLowerCase().trim() === answer.correctText.toLowerCase().trim()
        }
      }
      
      if (isAnswerCorrect) {
        correct++
      } else {
        weakAreas.push(`Question ${index + 1}`)
      }
    } else {
      // No answer provided
      weakAreas.push(`Question ${index + 1}`)
    }
  })

  const percentage = Math.round((correct / questions.value.length) * 100)

  results.value = {
    correct,
    total: questions.value.length,
    percentage,
    weakAreas
  }

  emit('quizComplete', results.value)
}

async function progressiveAssessment() {
  // Generate more challenging questions
  quizCompleted.value = false
  quizStarted.value = false
  currentQuestionIndex.value = 0
  selectedAnswer.value = null
  typedAnswer.value = ''
  showResult.value = false
  answers.value = {}
  tutorStore.resetWrongAnswers()
  
  const agentId = route.params.agentId as string
  const message = `Generate a more challenging quiz about ${props.topic?.name.toLowerCase()} with 5 advanced multiple choice questions. These should be harder than the previous quiz.`
  
  await chatStore.sendMessage(
    agentId,
    message,
    tutorStore.conversationId || undefined
  )
  
  if (tutorStore.conversationId) {
    await chatStore.fetchConversation(tutorStore.conversationId)
  }
}

function nextLevel() {
  if (!currentLevel.value) return
  
  const nextLevelNum = currentLevel.value.number + 1
  const nextLevel = levels.find(l => l.number === nextLevelNum)
  
  if (nextLevel) {
    tutorStore.setCurrentLevel(nextLevel)
    tutorStore.setLevelProgress(props.topic?.id || '', nextLevelNum)
    quizCompleted.value = false
    quizStarted.value = false
    currentQuestionIndex.value = 0
    currentQuiz.value = null
    questions.value = []
    answers.value = {}
    results.value = null
    tutorStore.resetWrongAnswers()
    requestQuiz()
  }
}

function restartQuiz() {
  quizStarted.value = false
  quizCompleted.value = false
  currentQuestionIndex.value = 0
  selectedAnswer.value = null
  typedAnswer.value = ''
  showResult.value = false
  answers.value = {}
  results.value = null
  tutorStore.resetWrongAnswers()
  requestQuiz()
}

function goToTopics() {
  tutorStore.setStep('topic-menu')
}
</script>

<style scoped>
.learning-area {
  width: 100%;
  min-height: 100%;
}

.level-selection,
.loading-quiz,
.quiz-intro {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
}

.level-card,
.loading-card,
.intro-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  text-align: center;
  max-width: 700px;
}

h2 {
  color: white;
  font-size: 28px;
  margin: 0 0 16px 0;
  font-weight: 700;
}

.level-description,
.intro-text {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 32px;
}

.levels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.level-btn {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.level-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-4px);
}

.level-btn.easy {
  border-color: rgba(76, 175, 80, 0.5);
}

.level-btn.medium {
  border-color: rgba(255, 193, 7, 0.5);
}

.level-btn.hard {
  border-color: rgba(244, 67, 54, 0.5);
}

.level-number {
  color: white;
  font-size: 18px;
  font-weight: 700;
}

.level-name {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.level-difficulty {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  text-transform: capitalize;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 20px auto;
}

.error-message {
  margin-top: 24px;
  padding: 16px;
  background: rgba(244, 67, 54, 0.2);
  border: 1px solid rgba(244, 67, 54, 0.4);
  border-radius: 12px;
}

.error-message p {
  color: white;
  margin: 0 0 12px 0;
  font-size: 14px;
}

.btn-retry-loading {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-retry-loading:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.quiz-container {
  width: 100%;
}

.quiz-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.quiz-header h2 {
  color: white;
  font-size: 24px;
  margin: 0;
}

.quiz-progress {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 600;
}

.question-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.instructions-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.instructions-text {
  color: white;
  font-size: 20px;
  font-weight: 600;
  line-height: 1.6;
  flex: 1;
}

.tts-btn {
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.tts-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
}

.tts-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.response-type-toggle {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px;
  border-radius: 12px;
}

.toggle-btn {
  flex: 1;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.toggle-btn.active {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
}

.option-btn {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.option-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateX(4px);
}

.option-btn.selected {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

.option-btn.correct {
  background: rgba(76, 175, 80, 0.4);
  border-color: rgba(76, 175, 80, 0.8);
  border-width: 2px;
  box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
}

.option-btn.incorrect {
  background: rgba(244, 67, 54, 0.3);
  border-color: rgba(244, 67, 54, 0.6);
}

.option-letter {
  color: white;
  font-weight: 700;
  font-size: 18px;
  min-width: 24px;
}

.option-text {
  color: white;
  font-size: 16px;
  flex: 1;
}

.typing-input-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.typing-input {
  flex: 1;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  color: white;
}

.typing-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.typing-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.25);
}

.btn-submit-answer {
  padding: 14px 24px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-submit-answer:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
}

.btn-submit-answer:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result-feedback {
  margin-top: 28px;
  padding-top: 28px;
  border-top: 2px solid rgba(255, 255, 255, 0.2);
}

.feedback {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  margin-bottom: 20px;
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.feedback.correct {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(56, 142, 60, 0.25));
  border: 2px solid rgba(76, 175, 80, 0.5);
  box-shadow: 0 4px 20px rgba(76, 175, 80, 0.2);
}

.feedback.incorrect {
  background: linear-gradient(135deg, rgba(244, 67, 54, 0.25), rgba(211, 47, 47, 0.25));
  border: 2px solid rgba(244, 67, 54, 0.5);
  box-shadow: 0 4px 20px rgba(244, 67, 54, 0.2);
}

.feedback-icon {
  font-size: 28px;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
  flex-shrink: 0;
}

.feedback-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feedback-text {
  color: white;
  font-size: 17px;
  font-weight: 600;
  line-height: 1.6;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.hint-section {
  color: rgba(255, 255, 255, 0.95);
  font-size: 15px;
  line-height: 1.6;
  padding: 14px;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 152, 0, 0.2));
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 193, 7, 0.4);
  border-radius: 12px;
  margin-top: 12px;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.15);
}

.hint-section strong {
  color: white;
  font-weight: 700;
  display: block;
  margin-bottom: 6px;
  font-size: 16px;
}

.validating-answer {
  margin-top: 24px;
  padding: 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.validating-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.validating-content p {
  color: white;
  font-size: 15px;
  font-weight: 500;
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.spinner-small {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.ai-response {
  color: rgba(255, 255, 255, 0.95);
  font-size: 15px;
  line-height: 1.7;
  padding: 16px;
  background: rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  margin-top: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.1);
}

.ai-response strong {
  color: white;
  font-weight: 700;
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
}

.feedback-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 4px;
}

.btn-retry,
.btn-next {
  padding: 14px 28px;
  backdrop-filter: blur(15px);
  color: white;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.btn-retry {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.25), rgba(255, 152, 0, 0.25));
  border: 2px solid rgba(255, 193, 7, 0.5);
}

.btn-retry:hover {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.35), rgba(255, 152, 0, 0.35));
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 193, 7, 0.3);
}

.btn-next {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(56, 142, 60, 0.25));
  border: 2px solid rgba(76, 175, 80, 0.5);
}

.btn-next:hover {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.35), rgba(56, 142, 60, 0.35));
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(76, 175, 80, 0.3);
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
}

.quiz-results {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
}

.results-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  max-width: 600px;
  width: 100%;
  text-align: center;
}

.score-display {
  margin: 32px 0;
}

.score-circle {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  border: 6px solid;
}

.score-circle.excellent {
  background: rgba(76, 175, 80, 0.2);
  border-color: rgba(76, 175, 80, 0.6);
}

.score-circle.good {
  background: rgba(33, 150, 243, 0.2);
  border-color: rgba(33, 150, 243, 0.6);
}

.score-circle.fair {
  background: rgba(255, 193, 7, 0.2);
  border-color: rgba(255, 193, 7, 0.6);
}

.score-circle.needs-improvement {
  background: rgba(244, 67, 54, 0.2);
  border-color: rgba(244, 67, 54, 0.6);
}

.score-value {
  color: white;
  font-size: 48px;
  font-weight: 700;
}

.score-label {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 600;
}

.score-details {
  color: white;
  font-size: 18px;
  margin-bottom: 24px;
}

.weak-areas,
.perfect-score {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  margin: 24px 0;
}

.weak-areas h3 {
  color: white;
  font-size: 18px;
  margin: 0 0 12px 0;
}

.weak-areas ul {
  list-style: none;
  padding: 0;
  margin: 0;
  text-align: left;
}

.weak-areas li {
  color: rgba(255, 255, 255, 0.9);
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.perfect-score p {
  color: white;
  font-size: 18px;
  margin: 0;
}

.results-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 32px;
}

.btn-primary,
.btn-secondary {
  padding: 14px 28px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.btn-primary:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}
</style>
