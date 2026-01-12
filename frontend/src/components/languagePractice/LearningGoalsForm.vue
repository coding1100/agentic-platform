<template>
  <div class="learning-goals-form">
    <div class="form-card">
      <h2>Set Your Learning Goals 🎯</h2>
      <p class="form-description">Tell us about your goals and preferences to personalize your learning experience.</p>
      
      <form @submit.prevent="handleSubmit" class="form">
        <div class="form-group">
          <label>What are your learning goals? (Select all that apply)</label>
          <div class="checkbox-grid">
            <label class="checkbox-item">
              <input type="checkbox" value="travel" v-model="formData.goals" />
              <span>🗺️ Travel & Tourism</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="business" v-model="formData.goals" />
              <span>💼 Business & Work</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="academic" v-model="formData.goals" />
              <span>📚 Academic Studies</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="conversation" v-model="formData.goals" />
              <span>💬 Daily Conversation</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="culture" v-model="formData.goals" />
              <span>🎭 Culture & Heritage</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="fluency" v-model="formData.goals" />
              <span>🌟 Native-like Fluency</span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label for="daily-time">Daily Practice Time (minutes)</label>
          <input
            id="daily-time"
            v-model.number="formData.dailyPracticeTime"
            type="number"
            min="5"
            max="120"
            step="5"
            class="form-input"
          />
          <p class="form-hint">Recommended: 15-30 minutes daily for best results</p>
        </div>

        <div class="form-group">
          <label for="learning-style">Learning Style</label>
          <select id="learning-style" v-model="formData.learningStyle" class="form-input">
            <option value="visual">👁️ Visual (Images, Videos, Charts)</option>
            <option value="auditory">👂 Auditory (Audio, Music, Listening)</option>
            <option value="kinesthetic">✋ Kinesthetic (Hands-on, Writing, Practice)</option>
            <option value="mixed">🔄 Mixed (Combination of all)</option>
          </select>
        </div>

        <div class="form-group">
          <label>Focus Areas (Select all that apply)</label>
          <div class="checkbox-grid">
            <label class="checkbox-item">
              <input type="checkbox" value="vocabulary" v-model="formData.focusAreas" />
              <span>📖 Vocabulary</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="grammar" v-model="formData.focusAreas" />
              <span>📝 Grammar</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="speaking" v-model="formData.focusAreas" />
              <span>🗣️ Speaking</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="listening" v-model="formData.focusAreas" />
              <span>👂 Listening</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="reading" v-model="formData.focusAreas" />
              <span>📚 Reading</span>
            </label>
            <label class="checkbox-item">
              <input type="checkbox" value="writing" v-model="formData.focusAreas" />
              <span>✍️ Writing</span>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label for="target-date">Target Date (Optional)</label>
          <input
            id="target-date"
            v-model="formData.targetDate"
            type="date"
            class="form-input"
          />
          <p class="form-hint">Set a goal date to stay motivated (e.g., trip date, exam date)</p>
        </div>
        
        <div class="form-actions">
          <button @click="handleBack" class="btn-back">← Back</button>
          <button type="submit" class="btn-primary" :disabled="formData.goals.length === 0 || formData.focusAreas.length === 0">
            Start Learning →
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useLanguagePracticeStore } from '@/stores/languagePractice'
import type { LearningGoals } from '@/stores/languagePractice'

const emit = defineEmits<{
  complete: [goals: LearningGoals]
}>()

const languagePracticeStore = useLanguagePracticeStore()

const formData = ref<LearningGoals>({
  goals: [],
  dailyPracticeTime: 15,
  learningStyle: 'mixed',
  focusAreas: [],
  targetDate: null
})

function handleSubmit() {
  emit('complete', { ...formData.value })
}

function handleBack() {
  languagePracticeStore.setStep('placement-test')
}
</script>

<style scoped>
.learning-goals-form {
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

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.checkbox-item:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.checkbox-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-item input[type="checkbox"]:checked + span {
  color: white;
  font-weight: 600;
}

.checkbox-item:has(input:checked) {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.checkbox-item span {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
}

.form-hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  margin-top: 4px;
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

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
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
  transition: all 0.3s ease;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.25);
}

.btn-primary {
  flex: 2;
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
  .checkbox-grid {
    grid-template-columns: 1fr;
  }
}
</style>





