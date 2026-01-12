<template>
  <div class="focus-areas-form">
    <div class="form-card">
      <h2>Focus Areas 🎯</h2>
      <p class="form-description">
        Are there any specific {{ subjectName }} topics you want your child to focus on?
        (You can select multiple or skip to see all topics)
      </p>
      
      <div class="focus-areas-grid">
        <button
          v-for="area in focusAreas"
          :key="area.id"
          @click="toggleArea(area.id)"
          :class="['focus-area-btn', { active: area.selected }]"
        >
          <span class="area-icon">{{ getAreaIcon(area.id) }}</span>
          <span class="area-label">{{ area.name }}</span>
        </button>
      </div>
      
      <button @click="handleSubmit" class="btn-primary">
        Continue to Topics
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useTutorStore } from '@/stores/tutor'

const emit = defineEmits<{
  complete: []
}>()

const tutorStore = useTutorStore()
const focusAreas = computed(() => tutorStore.focusAreas)

const subjectName = computed(() => {
  // Capitalize first letter of subject
  const subject = tutorStore.selectedSubject || 'subject'
  return subject.charAt(0).toUpperCase() + subject.slice(1)
})

function getAreaIcon(areaId: string): string {
  const icons: Record<string, string> = {
    // Math
    'addition': '➕',
    'subtraction': '➖',
    'multiplication': '✖️',
    'division': '➗',
    'fractions': '🍕',
    'place-values': '🔢',
    // Science
    'biology': '🌱',
    'chemistry': '⚗️',
    'physics': '⚡',
    'experiments': '🔬',
    // English
    'grammar': '📝',
    'vocabulary': '📚',
    'reading': '📖',
    'writing': '✍️',
    // History
    'ancient': '🏛️',
    'modern': '📜',
    'world': '🌎',
    // Geography
    'continents': '🌍',
    'countries': '🗺️',
    'landforms': '⛰️'
  }
  return icons[areaId] || '📚'
}

function toggleArea(areaId: string) {
  tutorStore.toggleFocusArea(areaId)
}

function handleSubmit() {
  emit('complete')
}
</script>

<style scoped>
.focus-areas-form {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
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

.focus-areas-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.focus-area-btn {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.focus-area-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.focus-area-btn.active {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.area-icon {
  font-size: 36px;
}

.area-label {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.btn-primary {
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
  width: 100%;
}

.btn-primary:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}
</style>

