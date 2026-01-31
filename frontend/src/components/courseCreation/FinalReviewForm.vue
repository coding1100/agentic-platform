<template>
  <div class="final-review-form">
    <div class="form-card">
      <h2>Final Review 🎉</h2>
      <p class="form-description">Review your complete course and export if ready.</p>
      
      <div class="review-summary">
        <h3>Course Summary</h3>
        <div class="summary-item">
          <span>Title:</span>
          <span>{{ courseOverview.title }}</span>
        </div>
        <div class="summary-item">
          <span>Subject:</span>
          <span>{{ courseOverview.subject }}</span>
        </div>
        <div class="summary-item">
          <span>Duration:</span>
          <span>{{ courseOverview.duration }} weeks</span>
        </div>
        <div class="summary-item">
          <span>Modules:</span>
          <span>{{ courseModules.length }}</span>
        </div>
      </div>

      <div class="form-actions">
        <button @click="handleBack" class="btn-back" :disabled="isGenerating">← Back</button>
        <button @click="handleComplete" class="btn-primary" :disabled="isGenerating">
          <span v-if="isGenerating">
            <span class="spinner-small"></span> Generating Syllabus...
          </span>
          <span v-else>Complete Course Creation ✓</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useCourseCreationStore } from '@/stores/courseCreation'

const emit = defineEmits<{
  complete: []
}>()

const props = defineProps<{
  isGenerating?: boolean
}>()

const courseCreationStore = useCourseCreationStore()
const isGenerating = computed(() => props.isGenerating || false)

const courseOverview = computed(() => courseCreationStore.courseOverview)
const courseModules = computed(() => courseCreationStore.courseModules)

function handleComplete() {
  emit('complete')
}

function handleBack() {
  courseCreationStore.setStep('validation-review')
}
</script>

<style scoped>
.final-review-form {
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

.review-summary {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 32px;
}

.review-summary h3 {
  color: white;
  font-size: 20px;
  margin: 0 0 16px 0;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-item span:first-child {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

.summary-item span:last-child {
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
  background: rgba(76, 175, 80, 0.3);
  color: white;
  border: 1px solid rgba(76, 175, 80, 0.5);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover:not(:disabled) {
  background: rgba(76, 175, 80, 0.4);
  transform: translateY(-2px);
}

.btn-primary:disabled,
.btn-back:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.spinner-small {
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>






