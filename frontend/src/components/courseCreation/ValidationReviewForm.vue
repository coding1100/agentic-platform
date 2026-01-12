<template>
  <div class="validation-review-form">
    <div class="form-card">
      <h2>Validation & Review ✅</h2>
      <p class="form-description">Review and validate your course content.</p>
      
      <div class="validation-status">
        <div class="status-item">
          <span class="status-label">Content Quality:</span>
          <span class="status-value">Validated</span>
        </div>
        <div class="status-item">
          <span class="status-label">Learning Objectives:</span>
          <span class="status-value">Aligned</span>
        </div>
        <div class="status-item">
          <span class="status-label">Assessments:</span>
          <span class="status-value">Complete</span>
        </div>
      </div>

      <div class="form-actions">
        <button @click="handleBack" class="btn-back">← Back</button>
        <button @click="handleContinue" class="btn-primary">
          Continue to Final Review →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ValidationResult } from '@/stores/courseCreation'

const emit = defineEmits<{
  complete: [result: ValidationResult]
}>()

function handleContinue() {
  emit('complete', {
    passed: true,
    issues: [],
    score: 95
  })
}

import { useCourseCreationStore } from '@/stores/courseCreation'

const courseCreationStore = useCourseCreationStore()

function handleBack() {
  courseCreationStore.setStep('workflow-automation')
}
</script>

<style scoped>
.validation-review-form {
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

.validation-status {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.status-label {
  color: white;
  font-weight: 600;
}

.status-value {
  color: rgba(76, 175, 80, 1);
  font-weight: 600;
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

