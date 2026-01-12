<template>
  <div class="assessment-design-form">
    <div class="form-card">
      <h2>Assessment Design 📝</h2>
      <p class="form-description">Choose the types of assessments for your course.</p>
      
      <form @submit.prevent="handleSubmit" class="form">
        <div class="assessment-types">
          <label class="checkbox-label">
            <input type="checkbox" v-model="formData.diagnostic" />
            <span>Diagnostic Assessment</span>
            <p class="checkbox-hint">Evaluate prior knowledge at the start</p>
          </label>

          <label class="checkbox-label">
            <input type="checkbox" v-model="formData.formative" />
            <span>Formative Assessment</span>
            <p class="checkbox-hint">Ongoing assessments during learning</p>
          </label>

          <label class="checkbox-label">
            <input type="checkbox" v-model="formData.summative" />
            <span>Summative Assessment</span>
            <p class="checkbox-hint">Final evaluations at module/course end</p>
          </label>

          <label class="checkbox-label">
            <input type="checkbox" v-model="formData.comprehensive" />
            <span>Comprehensive Assessment</span>
            <p class="checkbox-hint">Full course evaluation</p>
          </label>
        </div>
        
        <!-- Question Types Selection -->
        <div v-if="hasAnyAssessment" class="question-types-section">
          <h3>Question Types</h3>
          <p class="section-hint">Select the types of questions you want to include in your assessments.</p>
          <div class="question-types-grid">
            <label 
              v-for="qType in questionTypes" 
              :key="qType.id"
              class="question-type-card"
              :class="{ selected: selectedQuestionTypes.includes(qType.id) }"
            >
              <input 
                type="checkbox" 
                :value="qType.id"
                v-model="selectedQuestionTypes"
              />
              <div class="question-type-icon">{{ qType.icon }}</div>
              <div class="question-type-info">
                <strong>{{ qType.name }}</strong>
                <p>{{ qType.description }}</p>
              </div>
            </label>
          </div>
        </div>
        
        <!-- Assessment Configuration -->
        <div v-if="hasAnyAssessment" class="assessment-config">
          <h3>Assessment Configuration</h3>
          <div class="config-grid">
            <div class="form-group">
              <label>Default Questions per Assessment</label>
              <input 
                v-model.number="defaultQuestions" 
                type="number" 
                min="5" 
                max="50" 
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>Time Limit (minutes)</label>
              <input 
                v-model.number="timeLimit" 
                type="number" 
                min="10" 
                max="180" 
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>Passing Score (%)</label>
              <input 
                v-model.number="passingScore" 
                type="number" 
                min="50" 
                max="100" 
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>Allow Retakes</label>
              <select v-model="allowRetakes" class="form-input">
                <option value="unlimited">Unlimited</option>
                <option value="3">3 attempts</option>
                <option value="1">1 attempt</option>
                <option value="0">No retakes</option>
              </select>
            </div>
          </div>
        </div>
        
        <div class="form-actions">
          <button @click="handleBack" class="btn-back">← Back</button>
          <button type="submit" class="btn-primary">
            Continue to Concept Mapping →
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { AssessmentDesign } from '@/stores/courseCreation'

const emit = defineEmits<{
  complete: [design: AssessmentDesign]
}>()

const formData = ref<AssessmentDesign>({
  diagnostic: false,
  formative: false,
  summative: false,
  comprehensive: false,
  assessmentDetails: []
})

const selectedQuestionTypes = ref<string[]>(['multiple-choice', 'short-answer'])
const defaultQuestions = ref(10)
const timeLimit = ref(60)
const passingScore = ref(70)
const allowRetakes = ref('unlimited')

interface QuestionType {
  id: string
  name: string
  description: string
  icon: string
}

const questionTypes: QuestionType[] = [
  {
    id: 'multiple-choice',
    name: 'Multiple Choice',
    description: 'Single or multiple correct answers',
    icon: '☑️'
  },
  {
    id: 'true-false',
    name: 'True/False',
    description: 'Simple binary questions',
    icon: '✓✗'
  },
  {
    id: 'short-answer',
    name: 'Short Answer',
    description: 'Brief text responses',
    icon: '✍️'
  },
  {
    id: 'essay',
    name: 'Essay',
    description: 'Long-form written responses',
    icon: '📝'
  },
  {
    id: 'matching',
    name: 'Matching',
    description: 'Match items from two columns',
    icon: '🔗'
  },
  {
    id: 'fill-blank',
    name: 'Fill in the Blank',
    description: 'Complete missing words or phrases',
    icon: '⬜'
  },
  {
    id: 'coding',
    name: 'Coding Challenge',
    description: 'Programming exercises',
    icon: '💻'
  },
  {
    id: 'case-study',
    name: 'Case Study',
    description: 'Real-world scenario analysis',
    icon: '📊'
  }
]

const hasAnyAssessment = computed(() => {
  return formData.value.diagnostic || 
         formData.value.formative || 
         formData.value.summative || 
         formData.value.comprehensive
})

function handleSubmit() {
  // Add assessment details with configuration
  formData.value.assessmentDetails = []
  
  if (formData.value.diagnostic) {
    formData.value.assessmentDetails.push({
      type: 'diagnostic',
      questions: defaultQuestions.value,
      weight: 10
    })
  }
  if (formData.value.formative) {
    formData.value.assessmentDetails.push({
      type: 'formative',
      questions: defaultQuestions.value,
      weight: 20
    })
  }
  if (formData.value.summative) {
    formData.value.assessmentDetails.push({
      type: 'summative',
      questions: defaultQuestions.value * 2,
      weight: 40
    })
  }
  if (formData.value.comprehensive) {
    formData.value.assessmentDetails.push({
      type: 'comprehensive',
      questions: defaultQuestions.value * 3,
      weight: 30
    })
  }
  
  emit('complete', { 
    ...formData.value,
    questionTypes: selectedQuestionTypes.value,
    config: {
      defaultQuestions: defaultQuestions.value,
      timeLimit: timeLimit.value,
      passingScore: passingScore.value,
      allowRetakes: allowRetakes.value
    }
  })
}

import { useCourseCreationStore } from '@/stores/courseCreation'

const courseCreationStore = useCourseCreationStore()

function handleBack() {
  courseCreationStore.setStep('course-structure')
}
</script>

<style scoped>
.assessment-design-form {
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

.assessment-types {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 32px;
}

.checkbox-label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.checkbox-label:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.checkbox-label span {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.checkbox-hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  margin: 0;
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

.question-types-section {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.question-types-section h3 {
  color: white;
  font-size: 20px;
  margin: 0 0 8px 0;
}

.section-hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  margin-bottom: 20px;
}

.question-types-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.question-type-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.question-type-card:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.question-type-card.selected {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.question-type-card input[type="checkbox"] {
  display: none;
}

.question-type-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.question-type-info {
  flex: 1;
}

.question-type-info strong {
  color: white;
  font-size: 14px;
  display: block;
  margin-bottom: 4px;
}

.question-type-info p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
  margin: 0;
  line-height: 1.4;
}

.assessment-config {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.assessment-config h3 {
  color: white;
  font-size: 20px;
  margin: 0 0 20px 0;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

@media (max-width: 768px) {
  .question-types-grid {
    grid-template-columns: 1fr;
  }
  
  .config-grid {
    grid-template-columns: 1fr;
  }
}
</style>

