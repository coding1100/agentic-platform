<template>
  <div class="skill-assessment-form">
    <div class="form-card">
      <h2>{{ subjectName }} Skill Assessment 📊</h2>
      <p class="form-description">
        How would you rate your child's current {{ subjectName.toLowerCase() }} proficiency?
      </p>
      
      <div class="proficiency-options">
        <button
          v-for="level in proficiencyLevels"
          :key="level.value"
          @click="selectProficiency(level.value)"
          :class="['proficiency-btn', { active: selectedProficiency === level.value }]"
        >
          <span class="proficiency-icon">{{ level.icon }}</span>
          <span class="proficiency-label">{{ level.label }}</span>
          <span class="proficiency-description">{{ level.description }}</span>
        </button>
      </div>
      
      <button
        @click="handleSubmit"
        class="btn-primary"
        :disabled="!selectedProficiency"
      >
        Continue
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Subject } from '@/stores/tutor'

const props = defineProps<{
  subject: Subject
}>()

const emit = defineEmits<{
  complete: [assessment: { proficiency: 'beginner' | 'intermediate' | 'advanced'; subject: Subject }]
}>()

const selectedProficiency = ref<'beginner' | 'intermediate' | 'advanced' | null>(null)

const subjectName = computed(() => {
  // Capitalize first letter of subject
  const subject = props.subject || 'subject'
  return subject.charAt(0).toUpperCase() + subject.slice(1)
})

const proficiencyLevels = [
  {
    value: 'beginner' as const,
    label: 'Beginner',
    icon: '🌱',
    description: 'Just starting with basic concepts'
  },
  {
    value: 'intermediate' as const,
    label: 'Intermediate',
    icon: '📚',
    description: 'Comfortable with basics, ready for more'
  },
  {
    value: 'advanced' as const,
    label: 'Advanced',
    icon: '⭐',
    description: 'Strong foundation, ready for challenging topics'
  }
]

function selectProficiency(level: 'beginner' | 'intermediate' | 'advanced') {
  selectedProficiency.value = level
}

function handleSubmit() {
  if (selectedProficiency.value) {
    emit('complete', { proficiency: selectedProficiency.value, subject: props.subject })
  }
}
</script>

<style scoped>
.skill-assessment-form {
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

.proficiency-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.proficiency-btn {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.proficiency-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.proficiency-btn.active {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.proficiency-icon {
  font-size: 48px;
}

.proficiency-label {
  color: white;
  font-size: 20px;
  font-weight: 700;
}

.proficiency-description {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
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

.btn-primary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

