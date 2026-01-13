<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>My Agents</h1>
      <div class="header-actions">
        <button @click="goToApiKeys" class="btn-secondary">🔑 API Keys</button>
        <button @click="handleLogout" class="btn-secondary">Logout</button>
        <button @click="goToNewAgent" class="btn-primary">+ New Agent</button>
      </div>
    </header>

    <main class="dashboard-content">
      <div v-if="agentsStore.loading" class="loading">Loading agents...</div>
      
      <div v-else-if="agentsStore.agents.length === 0" class="empty-state">
        <h2>No agents yet</h2>
        <p>Create your first AI agent to get started</p>
        <button @click="goToNewAgent" class="btn-primary">Create Agent</button>
      </div>

      <div v-else class="agents-grid">
        <div
          v-for="agent in agentsStore.agents"
          :key="agent.id"
          class="agent-card"
          @click="goToChat(agent.id)"
        >
          <div class="agent-header">
            <h3>{{ agent.name }}</h3>
            <div class="agent-actions" v-if="!agent.is_prebuilt">
              <button
                @click.stop="editAgent(agent.id)"
                class="btn-icon"
                title="Edit"
              >
                ✏️
              </button>
              <button
                @click.stop="deleteAgent(agent.id)"
                class="btn-icon"
                title="Delete"
              >
                🗑️
              </button>
            </div>
          </div>
          <p v-if="agent.description" class="agent-description">
            {{ agent.description }}
          </p>
          <div v-if="agent.is_prebuilt" class="prebuilt-badge">
            <span class="badge-icon">✨</span>
            <span>Pre-built</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAgentsStore } from '@/stores/agents'

const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()

onMounted(async () => {
  await agentsStore.fetchAgents()
})

function goToNewAgent() {
  router.push('/agents/new')
}

function goToChat(agentId: string) {
  router.push(`/agents/${agentId}/chat`)
}

function editAgent(agentId: string) {
  router.push(`/agents/${agentId}/edit`)
}

async function deleteAgent(agentId: string) {
  if (confirm('Are you sure you want to delete this agent?')) {
    await agentsStore.deleteAgent(agentId)
  }
}

function goToApiKeys() {
  router.push('/api-keys')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  position: relative;
}

.dashboard::before {
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

.dashboard-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 24px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

h1 {
  color: white;
  font-size: 32px;
  font-weight: 700;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn-primary {
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.2);
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

.btn-primary:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-secondary {
  padding: 12px 24px;
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

.dashboard-content {
  max-width: 1200px;
  margin: 40px auto;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}

.loading {
  text-align: center;
  padding: 60px;
  color: white;
  font-size: 18px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.empty-state h2 {
  color: white;
  margin-bottom: 10px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.empty-state p {
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 30px;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.agent-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 28px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.agent-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.1));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.agent-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
}

.agent-card:hover::before {
  opacity: 1;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.agent-header h3 {
  color: white;
  font-size: 22px;
  margin: 0;
  flex: 1;
  font-weight: 600;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.agent-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 18px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  color: white;
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.agent-description {
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 16px;
  line-height: 1.6;
  font-size: 15px;
}

.prebuilt-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  font-size: 13px;
  color: white;
  font-weight: 500;
  margin-top: 8px;
}

.badge-icon {
  font-size: 14px;
}
</style>

