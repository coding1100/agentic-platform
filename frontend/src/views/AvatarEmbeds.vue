<template>
  <div class="embed-admin-page">
    <header class="page-header">
      <div class="header-left">
        <button class="btn-back" @click="goBack">Back</button>
        <h1>Avatar Embed Deployments</h1>
      </div>
    </header>

    <main class="page-content">
      <div class="panel">
        <h2>Select Agent</h2>
        <select v-model="selectedAgentId" @change="loadDeployment" class="input">
          <option value="" disabled>Select avatar realtime agent</option>
          <option v-for="agent in avatarAgents" :key="agent.id" :value="agent.id">
            {{ agent.name }}
          </option>
        </select>
        <p v-if="avatarAgents.length === 0" class="muted">
          No avatar realtime agents found. Create one with interaction mode set to Avatar Realtime.
        </p>
      </div>

      <div v-if="selectedAgentId" class="panel">
        <h2>Deployment Settings</h2>

        <label class="label">
          <input type="checkbox" v-model="form.is_active" />
          Active
        </label>

        <label class="label">Allowed Origins (one per line)</label>
        <textarea
          class="input area"
          v-model="allowedOriginsText"
          placeholder="https://customer.example.com"
        />

        <div class="grid">
          <div>
            <label class="label">Token TTL (seconds)</label>
            <input class="input" type="number" min="60" max="3600" v-model.number="form.token_ttl_seconds" />
          </div>
          <div>
            <label class="label">Max Concurrent Sessions</label>
            <input class="input" type="number" min="1" max="200" v-model.number="form.max_concurrent_sessions" />
          </div>
        </div>

        <label class="label">Room Prefix</label>
        <input class="input" type="text" maxlength="64" v-model="form.room_name_prefix" placeholder="avatar-interview" />

        <div class="actions">
          <button class="btn-primary" @click="saveDeployment" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save Deployment' }}
          </button>
          <button class="btn-secondary" @click="loadSessions">Refresh Sessions</button>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
      </div>

      <div v-if="deployment" class="panel">
        <h2>Embed Snippet (iframe)</h2>
        <pre class="code">{{ iframeSnippet }}</pre>
        <button class="btn-secondary" @click="copy(iframeSnippet)">Copy iframe snippet</button>

        <h3>Public Token Endpoint</h3>
        <pre class="code">{{ publicTokenEndpoint }}</pre>
        <button class="btn-secondary" @click="copy(publicTokenEndpoint)">Copy endpoint</button>
      </div>

      <div v-if="selectedAgentId" class="panel">
        <h2>Recent Sessions</h2>
        <div v-if="sessions.length === 0" class="muted">No sessions yet.</div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>Participant</th>
              <th>Status</th>
              <th>Room</th>
              <th>Created</th>
              <th>Ended</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="session in sessions" :key="session.id">
              <td>{{ session.participant_name || session.participant_identity }}</td>
              <td>{{ session.status }}</td>
              <td>{{ session.room_name }}</td>
              <td>{{ formatDate(session.created_at) }}</td>
              <td>{{ session.ended_at ? formatDate(session.ended_at) : '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { realtimeApi } from '@/services/api'
import { useAgentsStore } from '@/stores/agents'
import type { EmbedDeployment, RealtimeSession } from '@/types'

const router = useRouter()
const agentsStore = useAgentsStore()

const selectedAgentId = ref('')
const deployment = ref<EmbedDeployment | null>(null)
const sessions = ref<RealtimeSession[]>([])
const saving = ref(false)
const error = ref('')

const form = ref({
  is_active: true,
  token_ttl_seconds: 900,
  max_concurrent_sessions: 5,
  room_name_prefix: ''
})
const allowedOriginsText = ref('')

const avatarAgents = computed(() =>
  agentsStore.agents.filter((a) => a.interaction_mode === 'avatar_realtime')
)

const iframeUrl = computed(() =>
  deployment.value ? `${window.location.origin}/embed/${deployment.value.embed_id}` : ''
)
const iframeSnippet = computed(() => {
  if (!iframeUrl.value) return ''
  return `<iframe src=\"${iframeUrl.value}\" title=\"Avatar Interview\" style=\"width:100%;height:700px;border:0;\" allow=\"camera; microphone; autoplay; clipboard-read; clipboard-write\" />`
})
const publicTokenEndpoint = computed(() =>
  deployment.value ? `${import.meta.env.VITE_API_BASE_URL || window.location.origin}/api/v1/public/realtime/embed/${deployment.value.embed_id}/token` : ''
)

function parseAllowedOrigins(): string[] | null {
  const values = allowedOriginsText.value
    .split('\n')
    .map((v) => v.trim())
    .filter(Boolean)
  return values.length > 0 ? values : null
}

function setFormFromDeployment(value: EmbedDeployment) {
  form.value.is_active = value.is_active
  form.value.token_ttl_seconds = value.token_ttl_seconds
  form.value.max_concurrent_sessions = value.max_concurrent_sessions
  form.value.room_name_prefix = value.room_name_prefix || ''
  allowedOriginsText.value = (value.allowed_origins || []).join('\n')
}

async function loadDeployment() {
  error.value = ''
  deployment.value = null
  sessions.value = []
  if (!selectedAgentId.value) return

  try {
    const current = await realtimeApi.getEmbedDeployment(selectedAgentId.value)
    deployment.value = current
    setFormFromDeployment(current)
  } catch (err: any) {
    if (err?.response?.status === 404) {
      form.value = {
        is_active: true,
        token_ttl_seconds: 900,
        max_concurrent_sessions: 5,
        room_name_prefix: ''
      }
      allowedOriginsText.value = ''
    } else {
      error.value = err?.response?.data?.detail || 'Failed to load deployment'
    }
  }

  await loadSessions()
}

async function saveDeployment() {
  if (!selectedAgentId.value) return
  error.value = ''
  saving.value = true
  try {
    const saved = await realtimeApi.upsertEmbedDeployment(selectedAgentId.value, {
      is_active: form.value.is_active,
      allowed_origins: parseAllowedOrigins(),
      token_ttl_seconds: form.value.token_ttl_seconds,
      max_concurrent_sessions: form.value.max_concurrent_sessions,
      room_name_prefix: form.value.room_name_prefix || null
    })
    deployment.value = saved
    setFormFromDeployment(saved)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Failed to save deployment'
  } finally {
    saving.value = false
  }
}

async function loadSessions() {
  if (!selectedAgentId.value) return
  try {
    sessions.value = await realtimeApi.listSessions(selectedAgentId.value, 100)
  } catch {
    sessions.value = []
  }
}

async function copy(text: string) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // ignore clipboard errors
  }
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString()
}

function goBack() {
  router.push('/dashboard')
}

onMounted(async () => {
  await agentsStore.fetchAgents()
  if (avatarAgents.value.length > 0) {
    selectedAgentId.value = avatarAgents.value[0].id
    await loadDeployment()
  }
})
</script>

<style scoped>
.embed-admin-page {
  min-height: 100vh;
  background: linear-gradient(120deg, #0f172a, #1e293b);
  color: #e2e8f0;
}

.page-header {
  padding: 16px 22px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.25);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.page-content {
  max-width: 980px;
  margin: 0 auto;
  padding: 18px;
  display: grid;
  gap: 14px;
}

.panel {
  background: rgba(15, 23, 42, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 12px;
  padding: 14px;
}

.panel h2 {
  margin: 0 0 10px;
}

.panel h3 {
  margin: 14px 0 8px;
}

.label {
  display: block;
  font-size: 14px;
  margin-top: 8px;
  margin-bottom: 6px;
}

.input {
  width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: #0b1220;
  color: #e2e8f0;
  padding: 10px 12px;
}

.area {
  min-height: 90px;
  resize: vertical;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.btn-primary,
.btn-secondary,
.btn-back {
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  color: #e2e8f0;
  background: rgba(30, 41, 59, 0.95);
  padding: 9px 12px;
  cursor: pointer;
}

.btn-primary {
  background: rgba(14, 116, 144, 0.95);
}

.code {
  background: #020617;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 8px;
  padding: 10px;
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.table th,
.table td {
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  text-align: left;
  padding: 7px 6px;
}

.error {
  color: #fecaca;
  margin-top: 10px;
}

.muted {
  color: #94a3b8;
}

@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
