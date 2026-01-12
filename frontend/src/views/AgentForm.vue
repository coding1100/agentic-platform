<template>
  <div class="agent-form-container">
    <div class="agent-form-card">
      <h1>{{ isEdit ? 'Edit Agent' : 'Create New Agent' }}</h1>
      
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="name">Agent Name *</label>
          <input
            id="name"
            v-model="form.name"
            type="text"
            required
            placeholder="e.g., Customer Support Agent"
            maxlength="200"
          />
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <textarea
            id="description"
            v-model="form.description"
            placeholder="Brief description of what this agent does"
            rows="3"
            maxlength="1000"
          />
        </div>

        <div class="form-group">
          <label for="system_prompt">System Prompt *</label>
          <textarea
            id="system_prompt"
            v-model="form.system_prompt"
            required
            placeholder="Define the agent's personality, role, and behavior..."
            rows="8"
          />
          <small class="hint">This prompt defines how the agent behaves and responds.</small>
        </div>

        <div class="form-group">
          <label for="greeting_message">Greeting Message</label>
          <textarea
            id="greeting_message"
            v-model="form.greeting_message"
            placeholder="Optional welcome message shown when users start a conversation..."
            rows="4"
            maxlength="2000"
          />
          <small class="hint">This message will be automatically sent when a user starts a new conversation with this agent.</small>
        </div>

        <div class="form-group">
          <label for="temperature">Temperature</label>
          <input
            id="temperature"
            v-model.number="form.temperature"
            type="number"
            min="0"
            max="2"
            step="0.1"
          />
          <small class="hint">0.0 = focused, 2.0 = creative</small>
        </div>

        <div v-if="error" class="error-message">{{ error }}</div>

        <div class="form-actions">
          <button type="button" @click="goBack" class="btn-secondary">Cancel</button>
          <button type="submit" :disabled="loading" class="btn-primary">
            {{ loading ? 'Saving...' : (isEdit ? 'Update Agent' : 'Create Agent') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAgentsStore } from '@/stores/agents'

const route = useRoute()
const router = useRouter()
const agentsStore = useAgentsStore()

const isEdit = ref(false)
const loading = ref(false)
const error = ref('')

const form = ref({
  name: '',
  description: '',
  system_prompt: '',
  greeting_message: '',
  temperature: 0.7
})

onMounted(async () => {
  const agentId = route.params.agentId as string
  if (agentId) {
    isEdit.value = true
    const result = await agentsStore.fetchAgent(agentId)
    if (result.success && result.agent) {
      form.value = {
        name: result.agent.name,
        description: result.agent.description || '',
        system_prompt: result.agent.system_prompt,
        greeting_message: result.agent.greeting_message || '',
        temperature: result.agent.temperature
      }
    }
  }
})

async function handleSubmit() {
  error.value = ''
  loading.value = true

  const agentId = route.params.agentId as string
  const result = isEdit.value
    ? await agentsStore.updateAgent(agentId, form.value)
    : await agentsStore.createAgent(form.value)

  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.error || 'Failed to save agent'
  }

  loading.value = false
}

function goBack() {
  router.push('/dashboard')
}
</script>

<style scoped>
.agent-form-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  padding: 40px 20px;
  position: relative;
}

.agent-form-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.3) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.agent-form-card {
  max-width: 800px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border-radius: 24px;
  padding: 48px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  position: relative;
  z-index: 1;
}

h1 {
  color: white;
  margin-bottom: 36px;
  font-size: 32px;
  font-weight: 700;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.form-group {
  margin-bottom: 24px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 500;
}

input,
textarea {
  width: 100%;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  font-family: inherit;
  color: white;
  transition: all 0.3s ease;
}

input::placeholder,
textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

input:focus,
textarea:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

textarea {
  resize: vertical;
}

.hint {
  display: block;
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 36px;
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
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.btn-primary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.error-message {
  color: #ff6b6b;
  margin-bottom: 15px;
  padding: 12px;
  background: rgba(255, 107, 107, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 10px;
  font-size: 14px;
}
</style>

