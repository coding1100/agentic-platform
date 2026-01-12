<template>
  <div class="language-selection-form">
    <div class="form-card">
      <h2>Choose Your Language 🌍</h2>
      <p class="form-description">Select the language you want to learn and your native language.</p>
      
      <form @submit.prevent="handleSubmit" class="form">
        <div class="form-group">
          <label for="target-language">I want to learn:</label>
          <select
            id="target-language"
            v-model="formData.targetLanguage"
            required
            class="form-input"
          >
            <option value="">Select a language...</option>
            <option value="spanish">🇪🇸 Spanish</option>
            <option value="french">🇫🇷 French</option>
            <option value="german">🇩🇪 German</option>
            <option value="italian">🇮🇹 Italian</option>
            <option value="portuguese">🇵🇹 Portuguese</option>
            <option value="chinese">🇨🇳 Chinese (Mandarin)</option>
            <option value="japanese">🇯🇵 Japanese</option>
            <option value="korean">🇰🇷 Korean</option>
            <option value="arabic">🇸🇦 Arabic</option>
            <option value="hindi">🇮🇳 Hindi</option>
            <option value="russian">🇷🇺 Russian</option>
          </select>
        </div>

        <div class="form-group">
          <label for="native-language">My native language is:</label>
          <select
            id="native-language"
            v-model="formData.nativeLanguage"
            required
            class="form-input"
          >
            <option value="">Select your native language...</option>
            <option value="spanish">🇪🇸 Spanish</option>
            <option value="french">🇫🇷 French</option>
            <option value="german">🇩🇪 German</option>
            <option value="italian">🇮🇹 Italian</option>
            <option value="portuguese">🇵🇹 Portuguese</option>
            <option value="chinese">🇨🇳 Chinese</option>
            <option value="japanese">🇯🇵 Japanese</option>
            <option value="korean">🇰🇷 Korean</option>
            <option value="arabic">🇸🇦 Arabic</option>
            <option value="hindi">🇮🇳 Hindi</option>
            <option value="russian">🇷🇺 Russian</option>
            <option value="english">🇬🇧 English</option>
          </select>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="!isFormValid">
            Continue to Assessment →
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { LanguageProfile } from '@/stores/languagePractice'

const emit = defineEmits<{
  complete: [profile: LanguageProfile]
}>()

const formData = ref<LanguageProfile>({
  targetLanguage: null,
  nativeLanguage: null,
  proficiencyLevel: null,
  cefrLevel: null
})

const isFormValid = computed(() => {
  return formData.value.targetLanguage !== null && 
         formData.value.nativeLanguage !== null &&
         formData.value.targetLanguage !== formData.value.nativeLanguage
})

function handleSubmit() {
  if (isFormValid.value) {
    emit('complete', { ...formData.value })
  }
}
</script>

<style scoped>
.language-selection-form {
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
</style>





