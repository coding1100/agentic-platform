<template>
  <div class="workflow-automation-form">
    <div class="form-card">
      <h2>Workflow Automation ⚙️</h2>
      <p class="form-description">Set up automated workflows for your course.</p>
      
      <form @submit.prevent="handleSubmit" class="form">
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="formData.enabled" />
            <span>Enable Workflow Automation</span>
          </label>
        </div>

        <div v-if="formData.enabled">
          <div class="form-group">
            <label for="workflow-name">Workflow Name</label>
            <input
              id="workflow-name"
              v-model="formData.workflowName"
              type="text"
              placeholder="e.g., Course Delivery Workflow"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="automation-type">Automation Type</label>
            <select id="automation-type" v-model="formData.automationType" class="form-input">
              <option value="learning">Learning Process</option>
              <option value="assessment">Assessment</option>
              <option value="content_creation">Content Creation</option>
              <option value="course_delivery">Course Delivery</option>
            </select>
          </div>

          <div class="form-group">
            <label for="workflow-steps">Workflow Steps</label>
            <p class="form-hint">Enter each step on a new line</p>
            <textarea
              id="workflow-steps"
              v-model="workflowStepsText"
              rows="5"
              placeholder="Step 1: Content Review&#10;Step 2: Assessment Creation&#10;Step 3: Student Notification"
              class="form-input"
            ></textarea>
          </div>
        </div>
        
        <div class="form-actions">
          <button @click="handleBack" class="btn-back">← Back</button>
          <button type="submit" class="btn-primary">
            Continue to Validation →
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { WorkflowAutomation } from '@/stores/courseCreation'

const emit = defineEmits<{
  complete: [workflow: WorkflowAutomation]
}>()

const formData = ref<WorkflowAutomation>({
  enabled: false,
  workflowName: '',
  steps: [],
  automationType: 'learning'
})

const workflowStepsText = ref('')

function handleSubmit() {
  if (formData.value.enabled) {
    formData.value.steps = workflowStepsText.value
      .split('\n')
      .map(step => step.trim())
      .filter(step => step.length > 0)
  }

  emit('complete', { ...formData.value })
}

import { useCourseCreationStore } from '@/stores/courseCreation'

const courseCreationStore = useCourseCreationStore()

function handleBack() {
  courseCreationStore.setStep('concept-mapping')
}
</script>

<style scoped>
.workflow-automation-form {
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 24px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.checkbox-label span {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

label {
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.form-hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  margin: -4px 0 4px 0;
}

.form-input {
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  color: white;
  transition: all 0.3s ease;
  font-family: inherit;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.form-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.25);
}

.form-input option {
  background: #667eea;
  color: white;
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
</style>

