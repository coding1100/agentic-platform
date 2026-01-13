<template>
  <div class="exam-setup-form">
    <div class="form-card">
      <h2>Exam Information 📝</h2>
      <p class="form-description">Tell us about the exam you're preparing for so we can create a personalized study plan.</p>
      
      <form @submit.prevent="handleSubmit" class="form">
        <div class="form-group">
          <label for="exam-type">Exam Type:</label>
          <select
            id="exam-type"
            v-model="formData.examType"
            required
            class="form-input"
          >
            <option value="">Select exam type...</option>
            <option value="SAT">SAT</option>
            <option value="ACT">ACT</option>
            <option value="GRE">GRE</option>
            <option value="GMAT">GMAT</option>
            <option value="TOEFL">TOEFL</option>
            <option value="IELTS">IELTS</option>
            <option value="Certification">Certification Exam</option>
            <option value="Academic">Academic Exam</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div class="form-group">
          <label for="subject">Subject/Topic:</label>
          <input
            id="subject"
            v-model="formData.subject"
            type="text"
            placeholder="e.g., Mathematics, Biology, Python Programming"
            required
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="exam-date">Exam Date:</label>
          <input
            id="exam-date"
            v-model="formData.examDate"
            type="date"
            required
            class="form-input"
            :min="minDate"
          />
        </div>

        <div class="form-group">
          <label for="current-level">Current Knowledge Level:</label>
          <select
            id="current-level"
            v-model="formData.currentLevel"
            required
            class="form-input"
          >
            <option value="">Select your level...</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>

        <div class="form-group">
          <label for="target-score">Target Score (Optional):</label>
          <input
            id="target-score"
            v-model.number="formData.targetScore"
            type="number"
            placeholder="e.g., 1500 for SAT"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="hours-per-day">Hours Available Per Day:</label>
          <input
            id="hours-per-day"
            v-model.number="formData.hoursPerDay"
            type="number"
            min="1"
            max="12"
            required
            class="form-input"
          />
          <small class="form-hint">How many hours can you dedicate to studying each day?</small>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="!isFormValid || isCreatingSchedule">
            <span v-if="isCreatingSchedule">Creating Schedule...</span>
            <span v-else>Create Study Schedule →</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useExamPrepStore, type ExamInfo } from '@/stores/examPrep'
import { useChatStore } from '@/stores/chat'
import { useRoute } from 'vue-router'

const emit = defineEmits<{
  complete: []
}>()

const examPrepStore = useExamPrepStore()
const chatStore = useChatStore()
const route = useRoute()

const agentId = route.params.agentId as string
const isCreatingSchedule = ref(false)

const formData = ref<ExamInfo>({
  examType: null,
  subject: null,
  examDate: null,
  currentLevel: null,
  targetScore: null,
  hoursPerDay: 2
})

const minDate = computed(() => {
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  return tomorrow.toISOString().split('T')[0]
})

const isFormValid = computed(() => {
  return formData.value.examType !== null && 
         formData.value.subject !== null &&
         formData.value.examDate !== null &&
         formData.value.currentLevel !== null &&
         formData.value.hoursPerDay > 0
})

onMounted(() => {
  // Load existing exam info if available
  if (examPrepStore.examInfo.examType) {
    formData.value = { ...examPrepStore.examInfo }
  }
})

async function handleSubmit() {
  if (!isFormValid.value || isCreatingSchedule.value) return

  isCreatingSchedule.value = true
  
  // Save exam info to store
  examPrepStore.setExamInfo({ ...formData.value })

  // Create study schedule using AI agent - direct tool call
  const message = `Use the create_study_schedule tool with:
- exam_date: "${formData.value.examDate}"
- subjects: "${formData.value.subject}"
- hours_per_day: ${formData.value.hoursPerDay}
- current_level: "${formData.value.currentLevel}"`

  try {
    const result = await chatStore.sendMessage(
      agentId,
      message,
      examPrepStore.conversationId || undefined
    )

    if (result.success && result.response?.conversation_id) {
      examPrepStore.setConversationId(result.response.conversation_id)
    }

    // Move to study schedule step
    examPrepStore.setStep('study-schedule')
    emit('complete')
  } catch (error) {
    console.error('Error creating study schedule:', error)
    alert('Failed to create study schedule. Please try again.')
  } finally {
    isCreatingSchedule.value = false
  }
}
</script>

<style scoped>
.exam-setup-form {
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
  max-width: 600px;
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

.form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.form-input {
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  transition: all 0.3s ease;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.form-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
}

.form-input option {
  background: #667eea;
  color: white;
}

.form-hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  margin-top: 4px;
}

.form-actions {
  margin-top: 8px;
}

.btn-primary {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.2));
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.3));
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

