<template>
  <div class="child-details-form">
    <div class="form-card">
      <h2>Welcome to Your Personal Tutor! 👋</h2>
      <p class="form-description">Let's start by getting to know your child better.</p>
      
      <form @submit.prevent="handleSubmit" class="form">
        <div class="form-group">
          <label for="child-name">Child's Name</label>
          <input
            id="child-name"
            v-model="childName"
            type="text"
            placeholder="Enter your child's name"
            required
            class="form-input"
          />
        </div>
        
        <button type="submit" class="btn-primary" :disabled="!childName.trim()">
          Continue
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  complete: [details: { name: string }]
}>()

const childName = ref('')

function handleSubmit() {
  if (childName.value.trim()) {
    emit('complete', { name: childName.value.trim() })
  }
}
</script>

<style scoped>
.child-details-form {
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
  max-width: 500px;
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
  margin-top: 8px;
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

