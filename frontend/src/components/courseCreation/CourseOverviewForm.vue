<template>
  <div class="course-overview-form">
    <div class="form-card">
      <h2>Course Overview 📚</h2>
      <p class="form-description">Let's start by defining the basic information about your course. You can start from scratch or use a template.</p>
      
      <!-- Template Library -->
      <div class="template-section">
        <h3>Quick Start Templates</h3>
        <p class="template-hint">Choose a template to get started quickly, or start from scratch below.</p>
        <div class="template-grid">
          <div 
            v-for="template in templates" 
            :key="template.id"
            class="template-card"
            :class="{ selected: selectedTemplate === template.id }"
            @click="selectTemplate(template)"
          >
            <div class="template-icon">{{ template.icon }}</div>
            <h4>{{ template.name }}</h4>
            <p>{{ template.description }}</p>
            <div class="template-features">
              <span v-for="feature in template.features" :key="feature" class="template-tag">{{ feature }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <form @submit.prevent="handleSubmit" class="form">
        <div class="form-group">
          <label for="course-title">Course Title</label>
          <input
            id="course-title"
            v-model="formData.title"
            type="text"
            placeholder="e.g., Introduction to Web Development"
            required
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="subject">Subject Area</label>
          <input
            id="subject"
            v-model="formData.subject"
            type="text"
            placeholder="e.g., Computer Science, Mathematics, History"
            required
            class="form-input"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="duration">Duration (weeks)</label>
            <input
              id="duration"
              v-model.number="formData.duration"
              type="number"
              min="1"
              max="52"
              required
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label for="difficulty">Difficulty Level</label>
            <select
              id="difficulty"
              v-model="formData.difficulty"
              required
              class="form-input"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="target-audience">Target Audience</label>
          <input
            id="target-audience"
            v-model="formData.targetAudience"
            type="text"
            placeholder="e.g., High school students, College freshmen, Professionals"
            required
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="learning-objectives">Learning Objectives</label>
          <p class="form-hint">Enter each objective on a new line</p>
          <textarea
            id="learning-objectives"
            v-model="objectivesText"
            rows="5"
            placeholder="Students will be able to...&#10;Students will understand...&#10;Students will master..."
            required
            class="form-input"
          ></textarea>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="!isFormValid">
            Continue to Course Structure →
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { CourseOverview } from '@/stores/courseCreation'

const emit = defineEmits<{
  complete: [overview: CourseOverview]
}>()

const formData = ref<CourseOverview>({
  title: '',
  subject: '',
  duration: 8,
  learningObjectives: [],
  targetAudience: '',
  difficulty: 'beginner'
})

const objectivesText = ref('')
const selectedTemplate = ref<string | null>(null)

interface CourseTemplate {
  id: string
  name: string
  description: string
  icon: string
  features: string[]
  defaults: Partial<CourseOverview>
}

const templates: CourseTemplate[] = [
  {
    id: 'web-dev',
    name: 'Web Development',
    description: 'Complete web development course template',
    icon: '🌐',
    features: ['HTML/CSS', 'JavaScript', 'React'],
    defaults: {
      title: 'Complete Web Development Bootcamp',
      subject: 'Computer Science',
      duration: 12,
      targetAudience: 'Beginners to intermediate developers',
      difficulty: 'beginner',
      learningObjectives: [
        'Master HTML5 and CSS3 fundamentals',
        'Build responsive web applications',
        'Learn JavaScript and modern frameworks',
        'Deploy applications to production'
      ]
    }
  },
  {
    id: 'data-science',
    name: 'Data Science',
    description: 'Data science and analytics course',
    icon: '📊',
    features: ['Python', 'Statistics', 'ML'],
    defaults: {
      title: 'Data Science Fundamentals',
      subject: 'Data Science',
      duration: 10,
      targetAudience: 'Aspiring data scientists',
      difficulty: 'intermediate',
      learningObjectives: [
        'Understand data analysis fundamentals',
        'Master Python for data science',
        'Apply statistical methods',
        'Build machine learning models'
      ]
    }
  },
  {
    id: 'business',
    name: 'Business Strategy',
    description: 'Business and entrepreneurship course',
    icon: '💼',
    features: ['Strategy', 'Marketing', 'Finance'],
    defaults: {
      title: 'Business Strategy & Entrepreneurship',
      subject: 'Business',
      duration: 8,
      targetAudience: 'Entrepreneurs and business professionals',
      difficulty: 'intermediate',
      learningObjectives: [
        'Develop strategic thinking skills',
        'Understand market analysis',
        'Create effective business plans',
        'Master financial planning'
      ]
    }
  },
  {
    id: 'language',
    name: 'Language Learning',
    description: 'Interactive language learning course',
    icon: '🗣️',
    features: ['Grammar', 'Vocabulary', 'Conversation'],
    defaults: {
      title: 'Language Learning Mastery',
      subject: 'Languages',
      duration: 16,
      targetAudience: 'Language learners of all levels',
      difficulty: 'beginner',
      learningObjectives: [
        'Build foundational vocabulary',
        'Master grammar fundamentals',
        'Develop conversational skills',
        'Achieve fluency in speaking'
      ]
    }
  }
]

function selectTemplate(template: CourseTemplate) {
  selectedTemplate.value = template.id
  formData.value = {
    ...formData.value,
    ...template.defaults
  }
  if (template.defaults.learningObjectives) {
    objectivesText.value = template.defaults.learningObjectives.join('\n')
  }
}

const isFormValid = computed(() => {
  return formData.value.title.trim() !== '' &&
         formData.value.subject.trim() !== '' &&
         formData.value.targetAudience.trim() !== '' &&
         objectivesText.value.trim() !== ''
})

function handleSubmit() {
  if (!isFormValid.value) return

  formData.value.learningObjectives = objectivesText.value
    .split('\n')
    .map(obj => obj.trim())
    .filter(obj => obj.length > 0)

  emit('complete', { ...formData.value })
}
</script>

<style scoped>
.course-overview-form {
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

.form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
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
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.form-input option {
  background: #667eea;
  color: white;
}

textarea.form-input {
  resize: vertical;
  min-height: 100px;
}

.template-section {
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.template-section h3 {
  color: white;
  font-size: 20px;
  margin: 0 0 8px 0;
}

.template-hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  margin-bottom: 16px;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.template-card {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
}

.template-card:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-2px);
}

.template-card.selected {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.template-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.template-card h4 {
  color: white;
  font-size: 16px;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.template-card p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.template-features {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.template-tag {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 6px;
}

.form-actions {
  margin-top: 8px;
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

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>

