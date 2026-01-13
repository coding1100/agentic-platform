<template>
  <div class="onboarding-flow">
    <!-- Step 1: Welcome -->
    <div v-if="currentStep === 1" class="onboarding-step">
      <div class="step-card">
        <div class="welcome-icon">📚</div>
        <h2>Welcome to Micro-Learning!</h2>
        <p class="step-description">
          I'll help you learn bite-sized lessons that fit into your busy schedule.
          Let's set up your personalized learning plan.
        </p>
        <button @click="nextStep" class="btn-primary">
          Get Started →
        </button>
      </div>
    </div>

    <!-- Step 2: Learning Goals -->
    <div v-if="currentStep === 2" class="onboarding-step">
      <div class="step-card">
        <h2>What are your learning goals? 🎯</h2>
        <p class="step-description">Select all that apply:</p>
        
        <div class="goal-grid">
          <button
            v-for="goal in availableGoals"
            :key="goal"
            type="button"
            @click="toggleGoal(goal)"
            :class="['goal-card', { selected: selectedGoals.includes(goal) }]"
          >
            <span class="goal-icon">{{ getGoalIcon(goal) }}</span>
            <span class="goal-text">{{ goal }}</span>
          </button>
        </div>

        <div class="custom-goal-input">
          <input
            v-model="customGoal"
            @keyup.enter="addCustomGoal"
            type="text"
            placeholder="Or add your own goal..."
            class="input-field"
          />
          <button @click="addCustomGoal" class="btn-add">+</button>
        </div>

        <div class="step-actions">
          <button @click="prevStep" class="btn-secondary">← Back</button>
          <button @click="nextStep" :disabled="selectedGoals.length === 0" class="btn-primary">
            Continue →
          </button>
        </div>
      </div>
    </div>

    <!-- Step 3: Time Preference -->
    <div v-if="currentStep === 3" class="onboarding-step">
      <div class="step-card">
        <h2>How much time do you have per day? ⏰</h2>
        <p class="step-description">Choose your preferred learning duration:</p>
        
        <div class="time-options">
          <button
            v-for="time in timeOptions"
            :key="time.value"
            type="button"
            @click="selectTime(time.value)"
            :class="['time-card', { selected: selectedTime === time.value }]"
          >
            <span class="time-value">{{ time.value }} min</span>
            <span class="time-label">{{ time.label }}</span>
          </button>
        </div>

        <div class="step-actions">
          <button @click="prevStep" class="btn-secondary">← Back</button>
          <button @click="nextStep" :disabled="!selectedTime" class="btn-primary">
            Continue →
          </button>
        </div>
      </div>
    </div>

    <!-- Step 4: Topics -->
    <div v-if="currentStep === 4" class="onboarding-step">
      <div class="step-card">
        <h2>What topics interest you? 📖</h2>
        <p class="step-description">Select topics you'd like to learn about:</p>
        
        <div class="topic-input-group">
          <input
            v-model="newTopic"
            @keyup.enter="addTopic"
            type="text"
            placeholder="Enter a topic (e.g., Python, Marketing, History...)"
            class="input-field"
          />
          <button @click="addTopic" class="btn-add" :disabled="!newTopic.trim()">+ Add</button>
        </div>

        <div v-if="selectedTopics.length > 0" class="topic-list">
          <div
            v-for="topic in selectedTopics"
            :key="topic"
            class="topic-tag"
          >
            <span>{{ topic }}</span>
            <button @click="removeTopic(topic)" class="btn-remove">×</button>
          </div>
        </div>

        <div class="popular-topics">
          <p class="popular-label">Popular topics:</p>
          <div class="popular-tags">
            <button
              v-for="topic in popularTopics"
              :key="topic"
              @click="addTopicFromPopular(topic)"
              class="popular-tag"
            >
              {{ topic }}
            </button>
          </div>
        </div>

        <div class="step-actions">
          <button @click="prevStep" class="btn-secondary">← Back</button>
          <button @click="nextStep" :disabled="selectedTopics.length === 0" class="btn-primary">
            Continue →
          </button>
        </div>
      </div>
    </div>

    <!-- Step 5: Summary & Complete -->
    <div v-if="currentStep === 5" class="onboarding-step">
      <div class="step-card">
        <div class="success-icon">✅</div>
        <h2>You're all set!</h2>
        <p class="step-description">Here's your personalized learning plan:</p>
        
        <div class="summary-section">
          <div class="summary-item">
            <span class="summary-label">Goals:</span>
            <div class="summary-value">
              <span v-for="goal in selectedGoals" :key="goal" class="summary-tag">{{ goal }}</span>
            </div>
          </div>
          <div class="summary-item">
            <span class="summary-label">Time per day:</span>
            <span class="summary-value">{{ selectedTime }} minutes</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Topics:</span>
            <div class="summary-value">
              <span v-for="topic in selectedTopics" :key="topic" class="summary-tag">{{ topic }}</span>
            </div>
          </div>
        </div>

        <button @click="completeOnboarding" class="btn-primary btn-large">
          Start Learning! 🚀
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMicroLearningStore } from '@/stores/microLearning'

const emit = defineEmits<{
  complete: []
}>()

const microLearningStore = useMicroLearningStore()

const currentStep = ref(1)
const selectedGoals = ref<string[]>([])
const customGoal = ref('')
const selectedTime = ref<5 | 10 | 15 | null>(null)
// Default to 'reading' for text-based learning only
const selectedStyle = ref<'reading'>('reading')
const selectedTopics = ref<string[]>([])
const newTopic = ref('')

const availableGoals = [
  'Career Development',
  'Skill Building',
  'Personal Growth',
  'Academic Learning',
  'Hobby & Interests',
  'Professional Certification'
]

const popularTopics = [
  'Python',
  'JavaScript',
  'Marketing',
  'Design',
  'Business',
  'History',
  'Science',
  'Languages',
  'Photography',
  'Cooking'
]

const timeOptions = [
  { value: 5, label: 'Quick Learn' },
  { value: 10, label: 'Standard' },
  { value: 15, label: 'Deep Dive' }
]

// Learning styles removed - only text-based learning is offered

function getGoalIcon(goal: string): string {
  const icons: Record<string, string> = {
    'Career Development': '💼',
    'Skill Building': '🛠️',
    'Personal Growth': '🌱',
    'Academic Learning': '🎓',
    'Hobby & Interests': '🎨',
    'Professional Certification': '🏆'
  }
  return icons[goal] || '📚'
}

function toggleGoal(goal: string) {
  // Prevent any default behavior
  const index = selectedGoals.value.indexOf(goal)
  if (index > -1) {
    selectedGoals.value.splice(index, 1)
  } else {
    selectedGoals.value.push(goal)
  }
  // Do NOT navigate - user must click Continue button
}

function addCustomGoal() {
  if (customGoal.value.trim() && !selectedGoals.value.includes(customGoal.value.trim())) {
    selectedGoals.value.push(customGoal.value.trim())
    customGoal.value = ''
  }
}

function selectTime(time: 5 | 10 | 15) {
  selectedTime.value = time
  // Do NOT navigate - user must click Continue button
}

// selectStyle function removed - learning style is always 'reading'

function addTopic() {
  if (newTopic.value.trim() && !selectedTopics.value.includes(newTopic.value.trim())) {
    selectedTopics.value.push(newTopic.value.trim())
    newTopic.value = ''
  }
}

function addTopicFromPopular(topic: string) {
  if (!selectedTopics.value.includes(topic)) {
    selectedTopics.value.push(topic)
  }
}

function removeTopic(topic: string) {
  const index = selectedTopics.value.indexOf(topic)
  if (index > -1) {
    selectedTopics.value.splice(index, 1)
  }
}

// getStyleLabel function removed - no longer needed

function nextStep() {
  if (currentStep.value < 5) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

function completeOnboarding() {
  // Save to store - always use 'reading' for text-based learning
  microLearningStore.setOnboardingData({
    goals: selectedGoals.value,
    timePerDay: selectedTime.value || 10,
    learningStyle: 'reading', // Always text-based
    topics: selectedTopics.value
  })

  emit('complete')
}
</script>

<style scoped>
.onboarding-flow {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
  padding: 2rem;
}

.onboarding-step {
  width: 100%;
  max-width: 800px;
}

.step-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 3rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.welcome-icon,
.success-icon {
  font-size: 4rem;
  text-align: center;
  margin-bottom: 1rem;
}

h2 {
  color: #333;
  font-size: 2rem;
  margin: 0 0 1rem 0;
  text-align: center;
}

.step-description {
  color: #666;
  text-align: center;
  margin-bottom: 2rem;
  font-size: 1.1rem;
}

.goal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.goal-card {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.goal-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.goal-card.selected {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: #667eea;
  color: white;
}

.goal-icon {
  font-size: 2rem;
}

.goal-text {
  font-weight: 500;
  text-align: center;
}

.custom-goal-input {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.input-field {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
}

.input-field:focus {
  outline: none;
  border-color: #667eea;
}

.btn-add {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1.2rem;
  font-weight: bold;
  transition: background 0.2s;
}

.btn-add:hover:not(:disabled) {
  background: #5568d3;
}

.btn-add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.time-options {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 2rem;
}

.time-card {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 2rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  min-width: 120px;
}

.time-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.time-card.selected {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: #667eea;
  color: white;
}

.time-value {
  font-size: 2rem;
  font-weight: bold;
}

.time-label {
  font-size: 0.9rem;
  opacity: 0.8;
}

.style-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.style-card {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  text-align: center;
}

.style-card:hover {
  border-color: #667eea;
  transform: translateY(-2px);
}

.style-card.selected {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-color: #667eea;
  color: white;
}

.style-icon {
  font-size: 2rem;
}

.style-label {
  font-weight: 600;
  font-size: 1.1rem;
}

.style-description {
  font-size: 0.85rem;
  opacity: 0.8;
}

.topic-input-group {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.topic-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.topic-tag {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.btn-remove {
  background: rgba(255, 255, 255, 0.3);
  border: none;
  color: white;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.2rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.popular-topics {
  margin-bottom: 2rem;
}

.popular-label {
  color: #666;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.popular-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.popular-tag {
  background: #f0f0f0;
  border: 1px solid #e0e0e0;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
}

.popular-tag:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary.btn-large {
  width: 100%;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  margin-top: 1rem;
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #f0f0f0;
}

.summary-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.summary-label {
  font-weight: 600;
  color: #666;
  font-size: 0.9rem;
}

.summary-value {
  color: #333;
  font-size: 1rem;
}

.summary-tag {
  display: inline-block;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  margin-right: 0.5rem;
  margin-top: 0.25rem;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .step-card {
    padding: 2rem 1.5rem;
  }

  .goal-grid,
  .style-grid {
    grid-template-columns: 1fr;
  }

  .time-options {
    flex-direction: column;
  }

  .step-actions {
    flex-direction: column-reverse;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
  }
}
</style>

