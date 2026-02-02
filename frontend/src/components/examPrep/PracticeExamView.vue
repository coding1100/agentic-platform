<template>
  <div class="practice-exam-view">
    <div class="view-card">
      <h2>Practice Exam 📝</h2>
      
      <div v-if="!currentExam || !currentExam.questions || currentExam.questions.length === 0" class="exam-setup">
        <p class="view-description">Take a practice exam to assess your readiness.</p>
        <div v-if="isGenerating" class="loading-state">
          <div class="spinner"></div>
          <p>Generating your practice exam...</p>
          <p class="sub-text">This might take a moment as I craft personalized questions.</p>
        </div>
        <button v-else @click="generateExam" class="btn-primary" :disabled="isGenerating">
          Generate Practice Exam
        </button>
        <p v-if="!isGenerating && !currentExam" class="error-message" style="margin-top: 20px; color: #ff6b6b;">
          {{ examGenerationError || '' }}
        </p>
      </div>

      <div v-else class="exam-interface">
        <div class="exam-header">
          <div class="exam-info">
            <h3>{{ currentExam.examType }} - {{ currentExam.subject }}</h3>
            <p>{{ currentExam.numQuestions }} questions • {{ currentExam.timeLimit }} minutes</p>
          </div>
          <div class="timer" v-if="timeRemaining !== null">
            ⏱️ {{ formatTime(timeRemaining) }}
          </div>
        </div>

        <div class="exam-questions" v-if="currentExam.questions && currentExam.questions.length > 0">
          <div v-for="question in currentExam.questions" :key="question.id" class="question-card">
            <h4>Question {{ question.number }}</h4>
            <p class="question-text">{{ question.question }}</p>
            
            <div v-if="question.type === 'multiple-choice' && question.options && question.options.length > 0" class="options">
              <label v-for="(option, idx) in question.options" :key="idx" class="option-label">
                <input 
                  type="radio" 
                  :name="`q${question.number}`"
                  :value="String.fromCharCode(65 + idx)"
                  v-model="answers[question.id]"
                />
                <span>{{ String.fromCharCode(65 + idx) }}) {{ option }}</span>
              </label>
            </div>

            <textarea 
              v-else
              v-model="answers[question.id]"
              placeholder="Type your answer..."
              class="answer-textarea"
              rows="4"
            ></textarea>
          </div>
        </div>
        
        <div v-else class="no-questions">
          <p>No questions found. Please try generating the exam again.</p>
        </div>

        <div class="exam-actions">
          <button 
            @click="submitExam" 
            class="btn-primary" 
            type="button"
            :disabled="isSubmitting"
          >
            <span v-if="isSubmitting">Submitting...</span>
            <span v-else>Submit Exam</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useExamPrepStore } from '@/stores/examPrep'
import { useChatStore } from '@/stores/chat'
import { useRoute } from 'vue-router'
import { parseQuiz } from '@/utils/quizParser'

const emit = defineEmits<{
  complete: []
}>()

const examPrepStore = useExamPrepStore()
const chatStore = useChatStore()
const route = useRoute()

const agentId = route.params.agentId as string
const isGenerating = ref(false)
const currentExam = ref<any>(null)
const answers = ref<Record<string, string>>({})
const timeRemaining = ref<number | null>(null)
const timerInterval = ref<number | null>(null)
const examGenerationError = ref<string | null>(null)
const isSubmitting = ref(false)
const isMounted = ref(true)
const pollingAborted = ref(false)

interface ExamQuestion {
  id: string
  number: number
  type: 'multiple-choice' | 'short-answer' | 'essay'
  question: string
  options?: string[]
  correctAnswer: string
  explanation: string
  points: number
}

onMounted(() => {
  const storedExam = examPrepStore.currentPracticeExam
  if (storedExam && storedExam.questions && storedExam.questions.length > 0 && !storedExam.completedAt) {
    currentExam.value = storedExam
    answers.value = { ...(storedExam.answers || {}) }

    if (storedExam.startedAt) {
      const startedAt = new Date(storedExam.startedAt).getTime()
      const limitSeconds = (storedExam.timeLimit || 60) * 60
      const elapsed = Math.floor((Date.now() - startedAt) / 1000)
      const remaining = Math.max(0, limitSeconds - elapsed)
      timeRemaining.value = remaining
      if (remaining > 0) {
        startTimer()
      } else {
        submitExam()
      }
    }
  }
})

watch(
  answers,
  (nextAnswers) => {
    if (examPrepStore.currentPracticeExam) {
      examPrepStore.setCurrentPracticeExam({
        ...examPrepStore.currentPracticeExam,
        answers: { ...nextAnswers }
      })
    }
  },
  { deep: true }
)

async function generateExam() {
  isGenerating.value = true
  examGenerationError.value = null
  currentExam.value = null
  
  const info = examPrepStore.examInfo
  
  if (!info.examType || !info.subject) {
    examGenerationError.value = 'Please complete exam setup first.'
    isGenerating.value = false
    return
  }
  
  const message = `Generate a practice exam for ${info.examType} in ${info.subject}. 
Use the create_practice_exam tool with:
- exam_type: "${info.examType}"
- subject: "${info.subject}"
- num_questions: 20
- time_limit: 60
- difficulty: "${info.currentLevel}"`

  try {
    console.log('📤 Sending exam generation request...', { message })
    const result = await chatStore.sendMessage(agentId, message, examPrepStore.conversationId || undefined)
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to send message')
    }
    
    if (result.response?.conversation_id) {
      examPrepStore.setConversationId(result.response.conversation_id)
    }
    
    console.log('✅ Message sent, waiting for response...')
    // Wait a moment for the response to be generated (longer initial delay for exam generation)
    await new Promise(resolve => setTimeout(resolve, 4000))
    
    // Poll for exam questions
    await pollForExam()
  } catch (error) {
    console.error('❌ Error generating exam:', error)
    examGenerationError.value = 'Failed to generate exam. Please try again.'
    isGenerating.value = false
  }
}

async function pollForExam(maxAttempts = 12) {
  pollingAborted.value = false
  const checkedMessageIds = new Set<string>()
  let lastMessageCount = 0
  let lastFetchTime = 0
  const INITIAL_DELAY = 5000 // 5 seconds initial delay
  const MIN_FETCH_INTERVAL = 6000 // Minimum 6 seconds between fetches
  const MAX_DELAY = 10000 // 10 seconds maximum delay
  
  // Initial delay before first fetch
  await new Promise(resolve => setTimeout(resolve, INITIAL_DELAY))
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    // Check if component is still mounted and polling not aborted
    if (!isMounted.value || pollingAborted.value) {
      isGenerating.value = false
      return
    }
    
    if (examPrepStore.conversationId) {
      try {
        // Fetch conversation and check for exam questions
        // Only fetch if enough time has passed since last fetch
        const now = Date.now()
        const timeSinceLastFetch = now - lastFetchTime
        
        if (timeSinceLastFetch < MIN_FETCH_INTERVAL && attempt > 0) {
          // Skip fetch, just wait for the remaining time
          const waitTime = MIN_FETCH_INTERVAL - timeSinceLastFetch
          await new Promise(resolve => setTimeout(resolve, waitTime))
          
          // Check again after delay
          if (!isMounted.value || pollingAborted.value) {
            isGenerating.value = false
            return
          }
          
          // After waiting, check if we already have messages without fetching
          const currentMessages = chatStore.messages
          if (currentMessages.length > 0 && currentMessages.length === lastMessageCount) {
            // No new messages, continue with exponential backoff
            const delay = Math.min(MIN_FETCH_INTERVAL + (attempt * 500), MAX_DELAY)
            await new Promise(resolve => setTimeout(resolve, delay))
            continue
          }
        }
        
        lastFetchTime = Date.now()
        // Only force fetch on first attempt, otherwise let cache handle it
        const forceFetch = attempt === 0
        await chatStore.fetchConversation(examPrepStore.conversationId, forceFetch)
        
        const messages = chatStore.messages
        const currentMessageCount = messages.length
        
        // If no new messages since last check, skip processing and wait longer
        if (currentMessageCount === lastMessageCount && attempt > 0) {
          // No new messages, wait longer before next attempt
          const delay = Math.min(MIN_FETCH_INTERVAL + (attempt * 500), MAX_DELAY)
          await new Promise(resolve => setTimeout(resolve, delay))
          
          // Check again after delay
          if (!isMounted.value || pollingAborted.value) {
            isGenerating.value = false
            return
          }
          continue
        }
        
        // If we have new messages, reset checked IDs to re-check everything
        if (currentMessageCount > lastMessageCount) {
          checkedMessageIds.clear()
          lastMessageCount = currentMessageCount
        }
        
        // Process messages to find exam
        if (messages.length > 0) {
          // Get all assistant messages with content, sorted by most recent first
          const assistantMessages = messages
            .filter(m => m.role === 'assistant' && m.content && m.content.trim().length > 100)
            .reverse() // Most recent first
          
          for (const message of assistantMessages) {
            // Skip if we've already checked this message
            if (checkedMessageIds.has(message.id)) {
              continue
            }
            
            const content = message.content.trim()
            
            // Always try to parse - the exam might be in various formats
            const parsed = parseQuiz(content)
            
            // Check if this looks like an exam (contains questions)
            const isExam = 
              parsed.questions.length > 0 ||
              content.includes('Practice Exam') ||
              content.includes('practice exam') ||
              (content.includes('Question') && content.length > 500) ||
              (content.includes('Total Questions') && content.includes('Time Limit'))
            
            // Mark this message as checked
            checkedMessageIds.add(message.id)
            
            if (isExam && parsed.questions.length > 0) {
              console.log('✅ Exam detected!', { 
                messageId: message.id, 
                questionCount: parsed.questions.length,
                attempt: attempt + 1,
                contentPreview: content.substring(0, 200)
              })
              
              // Parse questions from quiz format
              const questions: ExamQuestion[] = parsed.questions.map((q, index) => {
                const hasOptions = q.options && q.options.length > 0
                return {
                  id: `q${q.number}`,
                  number: q.number || index + 1,
                  type: hasOptions ? 'multiple-choice' : 'short-answer',
                  question: q.question,
                  options: hasOptions ? q.options.map(opt => opt.text) : undefined,
                  correctAnswer: q.answer || '',
                  explanation: '',
                  points: 1
                }
              })
              
              const info = examPrepStore.examInfo
              currentExam.value = {
                examType: info.examType,
                subject: info.subject,
                numQuestions: questions.length,
                timeLimit: 60,
                questions: questions
              }
              
              // Initialize answers
              questions.forEach(q => {
                answers.value[q.id] = ''
              })

              examPrepStore.setCurrentPracticeExam({
                id: `exam-${Date.now()}`,
                examType: info.examType || 'General',
                subject: info.subject || 'General',
                numQuestions: questions.length,
                timeLimit: 60,
                questions: questions,
                startedAt: new Date(),
                completedAt: null,
                score: null,
                answers: { ...answers.value }
              })
              
              // Start timer
              timeRemaining.value = 60 * 60 // seconds
              startTimer()
              
              isGenerating.value = false
              return // Successfully found exam
            }
          }
          
          // If no exam found but we have a long assistant message, use it as fallback after several attempts
          if (assistantMessages.length > 0 && attempt >= 3) {
            // Try parsing all messages, not just the longest
            for (const msg of assistantMessages) {
              if (checkedMessageIds.has(msg.id)) continue
              
              const parsed = parseQuiz(msg.content)
              if (parsed.questions.length > 0) {
                console.log('⚠️ Found exam in fallback message', {
                  messageId: msg.id,
                  questionCount: parsed.questions.length
                })
                
                const questions: ExamQuestion[] = parsed.questions.map((q, index) => {
                  const hasOptions = q.options && q.options.length > 0
                  return {
                    id: `q${q.number}`,
                    number: q.number || index + 1,
                    type: hasOptions ? 'multiple-choice' : 'short-answer',
                    question: q.question,
                    options: hasOptions ? q.options.map(opt => opt.text) : undefined,
                    correctAnswer: q.answer || '',
                    explanation: '',
                    points: 1
                  }
                })
                
                const info = examPrepStore.examInfo
                currentExam.value = {
                  examType: info.examType,
                  subject: info.subject,
                  numQuestions: questions.length,
                  timeLimit: 60,
                  questions: questions
                }
                
                questions.forEach(q => {
                  answers.value[q.id] = ''
                })

                examPrepStore.setCurrentPracticeExam({
                  id: `exam-${Date.now()}`,
                  examType: info.examType || 'General',
                  subject: info.subject || 'General',
                  numQuestions: questions.length,
                  timeLimit: 60,
                  questions: questions,
                  startedAt: new Date(),
                  completedAt: null,
                  score: null,
                  answers: { ...answers.value }
                })
                
                timeRemaining.value = 60 * 60
                startTimer()
                isGenerating.value = false
                return
              }
            }
            
            // If still no questions, try the longest message
            const longestMessage = assistantMessages.reduce((longest, msg) => 
              msg.content.length > longest.content.length ? msg : longest
            )
            
            if (longestMessage.content.length > 500) {
              const parsed = parseQuiz(longestMessage.content)
              if (parsed.questions.length > 0) {
                console.log('⚠️ Using longest assistant message as fallback', {
                  contentLength: longestMessage.content.length,
                  questionCount: parsed.questions.length
                })
                
                const questions: ExamQuestion[] = parsed.questions.map((q, index) => {
                  const hasOptions = q.options && q.options.length > 0
                  return {
                    id: `q${q.number}`,
                    number: q.number || index + 1,
                    type: hasOptions ? 'multiple-choice' : 'short-answer',
                    question: q.question,
                    options: hasOptions ? q.options.map(opt => opt.text) : undefined,
                    correctAnswer: q.answer || '',
                    explanation: '',
                    points: 1
                  }
                })
                
                const info = examPrepStore.examInfo
                currentExam.value = {
                  examType: info.examType,
                  subject: info.subject,
                  numQuestions: questions.length,
                  timeLimit: 60,
                  questions: questions
                }
                
                questions.forEach(q => {
                  answers.value[q.id] = ''
                })

                examPrepStore.setCurrentPracticeExam({
                  id: `exam-${Date.now()}`,
                  examType: info.examType || 'General',
                  subject: info.subject || 'General',
                  numQuestions: questions.length,
                  timeLimit: 60,
                  questions: questions,
                  startedAt: new Date(),
                  completedAt: null,
                  score: null,
                  answers: { ...answers.value }
                })
                
                timeRemaining.value = 60 * 60
                startTimer()
                isGenerating.value = false
                return
              }
            }
          }
        }
      } catch (error) {
        console.error('Error fetching conversation:', error)
        // Continue to next attempt even if there's an error
      }
    } else {
      // No conversation ID, wait and retry
      const delay = Math.min(3000 * Math.pow(1.2, attempt), 6000)
      if (attempt < maxAttempts - 1) {
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    
    // Exponential backoff: start with 3s, increase gradually (max 6s)
    // Only wait if we haven't found the exam yet
    if (!currentExam.value) {
      const delay = Math.min(3000 * Math.pow(1.2, attempt), 6000)
      if (attempt < maxAttempts - 1) {
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
  }
  
  // Final attempt: use the longest assistant message if available (only one more fetch)
  if (examPrepStore.conversationId && !currentExam.value) {
    try {
      await chatStore.fetchConversation(examPrepStore.conversationId)
      const messages = chatStore.messages
      const assistantMessages = messages
        .filter(m => m.role === 'assistant' && m.content && m.content.trim().length > 200)
      
      if (assistantMessages.length > 0) {
        const longestMessage = assistantMessages.reduce((longest, msg) => 
          msg.content.length > longest.content.length ? msg : longest
        )
        
        const parsed = parseQuiz(longestMessage.content)
        if (parsed.questions.length > 0) {
          console.log('⚠️ Final fallback: Using longest assistant message', {
            contentLength: longestMessage.content.length,
            questionCount: parsed.questions.length
          })
          
          const questions: ExamQuestion[] = parsed.questions.map((q, index) => {
            const hasOptions = q.options && q.options.length > 0
            return {
              id: `q${q.number}`,
              number: q.number || index + 1,
              type: hasOptions ? 'multiple-choice' : 'short-answer',
              question: q.question,
              options: hasOptions ? q.options.map(opt => opt.text) : undefined,
              correctAnswer: q.answer || '',
              explanation: '',
              points: 1
            }
          })
          
          const info = examPrepStore.examInfo
          currentExam.value = {
            examType: info.examType,
            subject: info.subject,
            numQuestions: questions.length,
            timeLimit: 60,
            questions: questions
          }
          
          questions.forEach(q => {
            answers.value[q.id] = ''
          })

          examPrepStore.setCurrentPracticeExam({
            id: `exam-${Date.now()}`,
            examType: info.examType || 'General',
            subject: info.subject || 'General',
            numQuestions: questions.length,
            timeLimit: 60,
            questions: questions,
            startedAt: new Date(),
            completedAt: null,
            score: null,
            answers: { ...answers.value }
          })
          
          timeRemaining.value = 60 * 60
          startTimer()
        }
      }
    } catch (error) {
      console.error('Final check error:', error)
    }
  }
  
  isGenerating.value = false
  if (!currentExam.value) {
    console.error('❌ Failed to generate exam after all attempts')
    console.log('Last messages:', chatStore.messages.slice(-3).map(m => ({
      role: m.role,
      contentLength: m.content?.length || 0,
      preview: m.content?.substring(0, 200) || ''
    })))
  }
}

function startTimer() {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
  }
  
  timerInterval.value = window.setInterval(() => {
    if (timeRemaining.value !== null && timeRemaining.value > 0) {
      timeRemaining.value--
    } else {
      if (timerInterval.value) {
        clearInterval(timerInterval.value)
        timerInterval.value = null
      }
      submitExam()
    }
  }, 1000)
}

onUnmounted(() => {
  isMounted.value = false
  pollingAborted.value = true
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
})

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function submitExam(event?: Event) {
  if (event) {
    event.preventDefault()
    event.stopPropagation()
  }
  
  if (isSubmitting.value) {
    console.log('⚠️ Already submitting, ignoring click')
    return
  }
  
  isSubmitting.value = true
  console.log('🔘 Submit button clicked')
  
  try {
    // Calculate score
    if (currentExam.value && currentExam.value.questions) {
      let correctAnswers = 0
      const questions = currentExam.value.questions
      
      questions.forEach(q => {
        const userAnswer = answers.value[q.id]?.trim().toUpperCase()
        const correctAnswer = q.correctAnswer?.trim().toUpperCase()
        
        if (userAnswer && correctAnswer) {
          // Check if answer matches (handle both letter and full answer)
          if (userAnswer === correctAnswer || 
              userAnswer === correctAnswer.charAt(0) ||
              correctAnswer.includes(userAnswer)) {
            correctAnswers++
          }
        }
      })
      
      const score = questions.length > 0 
        ? Math.round((correctAnswers / questions.length) * 100)
        : 0
      
      // Save to progress data
      examPrepStore.addPracticeScore({
        date: new Date().toISOString(),
        score: score,
        examType: currentExam.value.examType || 'General',
        subject: currentExam.value.subject || 'General'
      })

      if (examPrepStore.currentPracticeExam) {
        examPrepStore.setCurrentPracticeExam({
          ...examPrepStore.currentPracticeExam,
          completedAt: new Date(),
          score,
          answers: { ...answers.value }
        })
      }
      
      // Mark that we just submitted an exam (for auto-triggering weak area analysis)
      examPrepStore.setJustSubmittedExam(true)
      
      console.log('📊 Exam submitted:', {
        correctAnswers,
        totalQuestions: questions.length,
        score,
        answers: answers.value
      })
    } else {
      console.warn('⚠️ No exam data available to submit')
    }
    
    // Stop timer
    if (timerInterval.value) {
      clearInterval(timerInterval.value)
      timerInterval.value = null
    }
    
    // Redirect to progress dashboard
    console.log('🔄 Redirecting to progress dashboard...')
    examPrepStore.setStep('progress-dashboard')
    console.log('✅ Step changed to:', examPrepStore.currentStep)
    
  } catch (error) {
    console.error('❌ Error submitting exam:', error)
    alert('Failed to submit exam. Please try again.')
    isSubmitting.value = false
  } finally {
    // Reset submitting state after a short delay to allow navigation
    setTimeout(() => {
      isSubmitting.value = false
    }, 1000)
  }
}
</script>

<style scoped>
.practice-exam-view {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  padding: 20px 0;
}

.view-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 900px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h2 {
  color: white;
  font-size: 28px;
  margin: 0 0 12px 0;
  font-weight: 700;
  text-align: center;
}

.exam-setup {
  text-align: center;
  padding: 40px;
}

.view-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  margin-bottom: 24px;
}

.btn-primary {
  padding: 14px 28px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.2));
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  z-index: 10;
  pointer-events: auto;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.3));
  transform: translateY(-2px);
}

    .btn-primary:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .loading-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      padding: 40px;
      color: white;
    }

    .spinner {
      width: 40px;
      height: 40px;
      border: 4px solid rgba(255, 255, 255, 0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 1s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .sub-text {
      font-size: 14px;
      opacity: 0.8;
    }

    .error-message {
      color: #ff6b6b;
      font-weight: 600;
      text-align: center;
    }

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.exam-info h3 {
  color: white;
  margin: 0 0 4px 0;
}

.exam-info p {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.timer {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.question-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.question-card h4 {
  color: white;
  margin: 0 0 12px 0;
}

.question-text {
  color: white;
  margin-bottom: 16px;
  line-height: 1.6;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.option-label {
  display: flex;
  align-items: center;
  gap: 12px;
  color: white;
  cursor: pointer;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: background 0.2s;
}

.option-label:hover {
  background: rgba(255, 255, 255, 0.1);
}

.option-label input[type="radio"] {
  cursor: pointer;
}

.answer-textarea {
  width: 100%;
  min-height: 100px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: white;
  font-size: 14px;
  resize: vertical;
}

.answer-textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.exam-actions {
  margin-top: 32px;
  text-align: center;
}
</style>

