<template>
  <div class="placement-test-form">
    <div class="form-card">
      <h2>Language Assessment 📊</h2>
      <p class="form-description">Let's assess your current level to create the perfect learning path for you.</p>
      
      <div v-if="!testStarted" class="test-intro">
        <div class="intro-content">
          <h3>What to Expect</h3>
          <ul>
            <li>10-15 questions covering vocabulary, grammar, and comprehension</li>
            <li>Takes about 5-10 minutes</li>
            <li>Answer honestly for the most accurate assessment</li>
            <li>Your level will be determined using CEFR standards (A1-C2)</li>
          </ul>
          <button @click="startTest" class="btn-primary" :disabled="isGeneratingQuestions">
            <span v-if="isGeneratingQuestions">
              <span class="button-spinner"></span>
              Generating Questions...
            </span>
            <span v-else>Start Assessment</span>
          </button>
        </div>
      </div>

      <div v-if="isGeneratingQuestions" class="loading-state">
        <div class="spinner-large"></div>
        <p class="loading-title">Generating personalized questions...</p>
        <p class="sub-text">Creating assessment for {{ getLanguageDisplayName(languagePracticeStore.languageProfile.targetLanguage) }}</p>
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>

      <div v-else-if="!testCompleted && questions.length > 0" class="test-questions">
        <div class="test-progress">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${(currentQuestion / questions.length) * 100}%` }"></div>
          </div>
          <p>Question {{ currentQuestion }} of {{ questions.length }}</p>
        </div>

        <div class="question-card">
          <h3>{{ questions[currentQuestion - 1]?.question || 'Loading question...' }}</h3>
          
          <div v-if="questions[currentQuestion - 1]?.type === 'multiple-choice'" class="options">
            <button
              v-for="(option, index) in questions[currentQuestion - 1]?.options || []"
              :key="index"
              @click="selectAnswer(option)"
              :class="['option-btn', { selected: selectedAnswer === option }]"
            >
              {{ String.fromCharCode(65 + index) }}) {{ option }}
            </button>
          </div>

          <div v-else-if="questions[currentQuestion - 1]?.type === 'fill-blank'" class="fill-blank">
            <p class="sentence">{{ questions[currentQuestion - 1]?.sentence }}</p>
            <input
              v-model="selectedAnswer"
              type="text"
              class="form-input"
              :placeholder="questions[currentQuestion - 1]?.placeholder || 'Enter your answer'"
            />
          </div>

          <button 
            @click="nextQuestion" 
            class="btn-primary"
            :disabled="!selectedAnswer"
          >
            {{ currentQuestion === questions.length ? 'Finish Assessment' : 'Next Question' }}
          </button>
        </div>
      </div>

      <div v-else class="test-results">
        <div v-if="isAssessingResults" class="assessing-results">
          <div class="spinner-large"></div>
          <p class="loading-title">Analyzing your responses...</p>
          <p class="sub-text">Determining your proficiency level</p>
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
        <div v-else class="results-content">
          <h3>Assessment Complete! 🎉</h3>
          <div class="result-card">
            <div class="result-level">
              <span class="cefr-level">{{ assessmentResult.cefrLevel }}</span>
              <span class="proficiency">{{ assessmentResult.proficiencyLevel }}</span>
            </div>
            <p class="result-description">{{ assessmentResult.description }}</p>
          </div>
          <button @click="handleComplete" class="btn-primary" :disabled="isCompleting">
            <span v-if="isCompleting">
              <span class="button-spinner"></span>
              Processing...
            </span>
            <span v-else>Continue to Learning Goals →</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useLanguagePracticeStore } from '@/stores/languagePractice'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/services/api'

const emit = defineEmits<{
  complete: [result: { proficiencyLevel: string; cefrLevel: string }]
}>()

const route = useRoute()
const languagePracticeStore = useLanguagePracticeStore()
const chatStore = useChatStore()

const testStarted = ref(false)
const testCompleted = ref(false)
const currentQuestion = ref(1)
const selectedAnswer = ref('')
const answers = ref<string[]>([])
const isGeneratingQuestions = ref(false)
const isAssessingResults = ref(false)
const isCompleting = ref(false)
const questions = ref<Array<{
  type: 'multiple-choice' | 'fill-blank'
  question: string
  options?: string[]
  sentence?: string
  placeholder?: string
  correct: string
}>>([])

const agentId = route.params.agentId as string

// Watch for language profile changes and auto-generate questions when component is visible
watch(() => languagePracticeStore.languageProfile.targetLanguage, async (newLang) => {
  if (newLang && questions.value.length === 0 && !testStarted.value && !isGeneratingQuestions.value) {
    // Auto-generate questions when language is set and we're on placement test step
    if (languagePracticeStore.currentStep === 'placement-test') {
      await generateQuestions()
    }
  }
}, { immediate: false })

// Initialize when component mounts
onMounted(async () => {
  // Check if we have a language selected and we're on the placement test step
  const targetLanguage = languagePracticeStore.languageProfile.targetLanguage
  if (targetLanguage && questions.value.length === 0 && languagePracticeStore.currentStep === 'placement-test') {
    // Pre-generate questions for better UX
    await generateQuestions()
  }
})

// Get language display name
function getLanguageDisplayName(language: string | null): string {
  if (!language) return 'the selected language'
  const names: Record<string, string> = {
    'spanish': 'Spanish',
    'french': 'French',
    'german': 'German',
    'italian': 'Italian',
    'portuguese': 'Portuguese',
    'chinese': 'Chinese',
    'japanese': 'Japanese',
    'korean': 'Korean',
    'arabic': 'Arabic',
    'hindi': 'Hindi',
    'russian': 'Russian'
  }
  return names[language] || language
}

// Generate questions from AI
async function generateQuestions() {
  const targetLanguage = languagePracticeStore.languageProfile.targetLanguage
  if (!targetLanguage) {
    console.warn('No target language selected for question generation')
    return
  }

  // Don't regenerate if we already have questions
  if (questions.value.length > 0) {
    return
  }

  // Prevent multiple simultaneous generations
  if (isGeneratingQuestions.value) {
    return
  }

  isGeneratingQuestions.value = true
  
  try {
    const languageName = getLanguageDisplayName(targetLanguage)
    const prompt = `Generate a placement test with 10-15 questions for ${languageName} language learners. 

The test should include:
- Multiple choice questions covering basic vocabulary, common phrases, and grammar
- Fill-in-the-blank questions for grammar and sentence structure
- Questions should progress from beginner (A1) to intermediate (B1) level
- All questions and answers should be in ${languageName} or English as appropriate

Format your response as JSON with this exact structure:
{
  "questions": [
    {
      "type": "multiple-choice",
      "question": "How do you say 'Hello' in ${languageName}?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct": "Option A"
    },
    {
      "type": "fill-blank",
      "question": "Complete the sentence: [sentence with blank]",
      "sentence": "[sentence with ___ for blank]",
      "placeholder": "Enter the correct word",
      "correct": "correct answer"
    }
  ]
}

IMPORTANT: 
- Return ONLY valid JSON, no other text
- All questions must be relevant to ${languageName}
- Include 10-15 questions total
- Mix multiple-choice and fill-blank questions
- Make sure the correct answers are accurate`

    // Get or create conversation
    let conversationId = chatStore.activeConversationId
    if (!conversationId) {
      const result = await chatStore.createConversation(agentId)
      if (result.success && result.conversation) {
        conversationId = result.conversation.id
      }
    }

    const response = await chatApi.sendMessage(agentId, {
      conversation_id: conversationId || null,
      message: prompt
    })

    // Parse JSON from response
    let parsedQuestions
    try {
      // Try to extract JSON from response
      const jsonMatch = response.message.match(/\{[\s\S]*\}/)
      if (jsonMatch) {
        parsedQuestions = JSON.parse(jsonMatch[0])
      } else {
        // Try parsing the whole response
        parsedQuestions = JSON.parse(response.message)
      }

      if (parsedQuestions.questions && Array.isArray(parsedQuestions.questions)) {
        questions.value = parsedQuestions.questions
      } else {
        throw new Error('Invalid question format')
      }
    } catch (parseError) {
      console.error('Error parsing questions:', parseError)
      // Fallback: generate basic questions
      generateFallbackQuestions(targetLanguage)
    }

  } catch (error: any) {
    console.error('Error generating questions:', error)
    alert('Failed to generate questions. Using default questions.')
    generateFallbackQuestions(targetLanguage)
  } finally {
    isGeneratingQuestions.value = false
    testStarted.value = true
  }
}

// Fallback questions if AI generation fails
function generateFallbackQuestions(language: string) {
  const languageQuestions: Record<string, Array<any>> = {
    arabic: [
      {
        type: 'multiple-choice',
        question: 'How do you say "Hello" in Arabic?',
        options: ['مرحبا (Marhaba)', 'مع السلامة (Ma\'a salama)', 'شكرا (Shukran)', 'من فضلك (Min fadlik)'],
        correct: 'مرحبا (Marhaba)'
      },
      {
        type: 'fill-blank',
        question: 'Complete: "أنا ___ طالب" (I am a student)',
        sentence: 'أنا ___ طالب',
        placeholder: 'Enter the correct word',
        correct: 'طالب'
      },
      {
        type: 'multiple-choice',
        question: 'What does "كيف حالك؟" (Kayf halak?) mean?',
        options: ['What is your name?', 'How are you?', 'Where are you?', 'What time is it?'],
        correct: 'How are you?'
      }
    ],
    spanish: [
      {
        type: 'multiple-choice',
        question: 'How do you say "Hello" in Spanish?',
        options: ['Hola', 'Adiós', 'Gracias', 'Por favor'],
        correct: 'Hola'
      },
      {
        type: 'fill-blank',
        question: 'Complete: "Yo ___ estudiante."',
        sentence: 'Yo ___ estudiante.',
        placeholder: 'Enter the correct word',
        correct: 'soy'
      },
      {
        type: 'multiple-choice',
        question: 'What does "¿Cómo estás?" mean?',
        options: ['What is your name?', 'How are you?', 'Where are you?', 'What time is it?'],
        correct: 'How are you?'
      }
    ]
  }

  questions.value = languageQuestions[language] || languageQuestions.spanish
}

const assessmentResult = ref({
  cefrLevel: 'A1',
  proficiencyLevel: 'beginner',
  description: 'Perfect starting point! We\'ll begin with the fundamentals and build from there.'
})

// Compute assessment based on answers
function computeAssessment() {
  if (questions.value.length === 0 || answers.value.length === 0) {
    return
  }

  const correctCount = answers.value.filter((ans, idx) => {
    if (idx >= questions.value.length) return false
    const question = questions.value[idx]
    if (!question || !ans) return false
    return ans.toLowerCase().trim() === question.correct.toLowerCase().trim()
  }).length
  
  const percentage = (correctCount / questions.value.length) * 100
  
  if (percentage >= 80) {
    assessmentResult.value = {
      cefrLevel: 'B2',
      proficiencyLevel: 'upper-intermediate',
      description: 'Great! You have a solid foundation. We\'ll focus on advanced grammar and conversation.'
    }
  } else if (percentage >= 60) {
    assessmentResult.value = {
      cefrLevel: 'B1',
      proficiencyLevel: 'intermediate',
      description: 'Good progress! We\'ll build on your existing knowledge with structured practice.'
    }
  } else if (percentage >= 40) {
    assessmentResult.value = {
      cefrLevel: 'A2',
      proficiencyLevel: 'elementary',
      description: 'You\'re getting started! We\'ll focus on building vocabulary and basic grammar.'
    }
  } else {
    assessmentResult.value = {
      cefrLevel: 'A1',
      proficiencyLevel: 'beginner',
      description: 'Perfect starting point! We\'ll begin with the fundamentals and build from there.'
    }
  }
}

async function startTest() {
  // Always generate questions when starting test
  if (questions.value.length === 0) {
    await generateQuestions()
  }
  // If questions were already generated, just start
  if (questions.value.length > 0) {
    testStarted.value = true
  }
}

function selectAnswer(answer: string) {
  selectedAnswer.value = answer
}

function nextQuestion() {
  if (!selectedAnswer.value) return
  
  answers.value.push(selectedAnswer.value)
  
  if (currentQuestion.value < questions.value.length) {
    currentQuestion.value++
    selectedAnswer.value = ''
  } else {
    // Compute assessment when test is complete
    computeAssessment()
    testCompleted.value = true
    isAssessingResults.value = true
    // Small delay to show loading state before displaying results
    setTimeout(() => {
      isAssessingResults.value = false
    }, 1500)
  }
}


async function handleComplete() {
  isCompleting.value = true
  
  // Send results to AI for assessment
  const targetLanguage = languagePracticeStore.languageProfile.targetLanguage
  if (targetLanguage) {
    try {
      const languageName = getLanguageDisplayName(targetLanguage)
      const responsesSummary = answers.value.map((ans, idx) => 
        `Q${idx + 1}: ${ans}`
      ).join('\n')

      const assessmentPrompt = `Assess the placement test results for ${languageName}:

Questions and correct answers:
${questions.value.map((q, idx) => `Q${idx + 1}: ${q.question}\nCorrect: ${q.correct}\nUser answered: ${answers.value[idx] || 'No answer'}`).join('\n\n')}

Provide assessment in this JSON format:
{
  "cefrLevel": "A1",
  "proficiencyLevel": "beginner",
  "description": "Brief description of the level"
}`

      let conversationId = chatStore.activeConversationId
      if (!conversationId) {
        const result = await chatStore.createConversation(agentId)
        if (result.success && result.conversation) {
          conversationId = result.conversation.id
        }
      }

      const response = await chatApi.sendMessage(agentId, {
        conversation_id: conversationId || null,
        message: assessmentPrompt
      })

      // Try to parse assessment from response
      try {
        const jsonMatch = response.message.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          const assessment = JSON.parse(jsonMatch[0])
          if (assessment.cefrLevel && assessment.proficiencyLevel) {
            // Update the assessment result with AI assessment
            assessmentResult.value = {
              cefrLevel: assessment.cefrLevel,
              proficiencyLevel: assessment.proficiencyLevel,
              description: assessment.description || assessmentResult.value.description
            }
          }
        }
      } catch (e) {
        console.error('Error parsing assessment:', e)
        // Use computed assessment result
      }
    } catch (error) {
      console.error('Error getting AI assessment:', error)
      // Use computed assessment result
    }
  }

  // Update store with results
  languagePracticeStore.setProficiencyLevel(
    assessmentResult.value.proficiencyLevel as any,
    assessmentResult.value.cefrLevel
  )

  isAssessingResults.value = false
  isCompleting.value = false

  emit('complete', {
    proficiencyLevel: assessmentResult.value.proficiencyLevel,
    cefrLevel: assessmentResult.value.cefrLevel
  })
}
</script>

<style scoped>
.placement-test-form {
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

.test-intro {
  text-align: center;
}

.intro-content h3 {
  color: white;
  font-size: 22px;
  margin-bottom: 20px;
}

.intro-content ul {
  text-align: left;
  color: rgba(255, 255, 255, 0.9);
  margin: 24px auto;
  max-width: 500px;
  line-height: 1.8;
}

.intro-content li {
  margin: 12px 0;
}

.test-progress {
  margin-bottom: 24px;
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

.test-progress p {
  color: white;
  text-align: center;
  font-size: 14px;
}

.question-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 32px;
}

.question-card h3 {
  color: white;
  font-size: 20px;
  margin: 0 0 24px 0;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 24px;
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
  border-color: rgba(255, 255, 255, 0.4);
}

.option-btn.selected {
  background: rgba(102, 126, 234, 0.4);
  border-color: rgba(255, 255, 255, 0.5);
}

.fill-blank {
  margin-bottom: 24px;
}

.sentence {
  color: white;
  font-size: 18px;
  margin-bottom: 16px;
  font-family: monospace;
}

.test-results {
  text-align: center;
}

.test-results h3 {
  color: white;
  font-size: 24px;
  margin-bottom: 24px;
}

.result-card {
  background: rgba(76, 175, 80, 0.2);
  border: 2px solid rgba(76, 175, 80, 0.4);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
}

.result-level {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.cefr-level {
  font-size: 48px;
  font-weight: 700;
  color: white;
}

.proficiency {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.9);
  text-transform: capitalize;
}

.result-description {
  color: white;
  font-size: 16px;
  line-height: 1.6;
}

.btn-primary {
  width: 100%;
  padding: 14px 28px;
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

.btn-primary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-state {
  text-align: center;
  padding: 80px 20px;
  min-height: 400px;
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

.assessing-results {
  text-align: center;
  padding: 80px 20px;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.results-content {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.button-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}
</style>


