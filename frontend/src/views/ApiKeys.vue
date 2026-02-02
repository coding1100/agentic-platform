<template>
  <div class="api-keys-page">
    <header class="page-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>API Keys</h1>
      </div>
      <div class="header-actions">
        <button @click="goToDocumentation" class="btn-secondary-header">
          📚 Documentation
        </button>
        <button @click="showCreateModal = true" class="btn-primary">
          + Create API Key
        </button>
      </div>
    </header>

    <main class="page-content">
      <div v-if="apiKeysStore.isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading API keys...</p>
      </div>

      <div v-else-if="apiKeysStore.error" class="error-state">
        <p>{{ apiKeysStore.error }}</p>
        <button @click="apiKeysStore.fetchApiKeys()" class="btn-secondary">Retry</button>
      </div>

      <div v-else-if="apiKeysStore.apiKeys.length === 0" class="empty-state">
        <div class="empty-icon">🔑</div>
        <h2>No API Keys</h2>
        <p>Create your first API key to start using the REST API</p>
        <button @click="showCreateModal = true" class="btn-primary">Create API Key</button>
      </div>

      <div v-else class="api-keys-list">
        <div
          v-for="key in apiKeysStore.apiKeys"
          :key="key.id"
          class="api-key-card"
        >
          <div class="key-header">
            <div class="key-info">
              <h3>{{ key.name }}</h3>
              <div class="key-meta">
                <span class="agent-name" v-if="key.agent_id && getAgentName(key.agent_id)">
                  Agent: {{ getAgentName(key.agent_id) }}
                </span>
                <span class="agent-name" v-else>
                  All Agents (Universal)
                </span>
                <span :class="['status-badge', key.is_active ? 'active' : 'inactive']">
                  {{ key.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
            </div>
            <div class="key-actions">
              <button
                @click="toggleKey(key.id)"
                :disabled="apiKeysStore.isLoading"
                class="btn-icon"
                :title="key.is_active ? 'Disable' : 'Enable'"
              >
                {{ key.is_active ? '⏸️' : '▶️' }}
              </button>
              <button
                @click="viewUsage(key.id)"
                class="btn-icon"
                title="View Usage"
              >
                📊
              </button>
              <button
                @click="deleteKey(key.id)"
                :disabled="apiKeysStore.isLoading"
                class="btn-icon danger"
                title="Delete"
              >
                🗑️
              </button>
            </div>
          </div>

          <div class="key-details">
            <div class="detail-item">
              <span class="label">Created:</span>
              <span class="value">{{ formatDate(key.created_at) }}</span>
            </div>
            <div class="detail-item" v-if="key.last_used_at">
              <span class="label">Last Used:</span>
              <span class="value">{{ formatDate(key.last_used_at) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Total Requests:</span>
              <span class="value">{{ key.total_requests.toLocaleString() }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Rate Limit:</span>
              <span class="value">{{ key.rate_limit_per_minute }} requests/min</span>
            </div>
            <div class="detail-item" v-if="key.expires_at">
              <span class="label">Expires:</span>
              <span class="value">{{ formatDate(key.expires_at) }}</span>
            </div>
            <div class="detail-item" v-if="key.allowed_origins && key.allowed_origins.length > 0">
              <span class="label">Allowed Origins:</span>
              <div class="origins-list">
                <span v-for="(origin, idx) in key.allowed_origins" :key="idx" class="origin-badge">{{ origin }}</span>
              </div>
            </div>
            <div class="detail-item" v-else>
              <span class="label">Allowed Origins:</span>
              <span class="value">All domains</span>
            </div>
          </div>
          <div class="key-actions-bottom">
            <button
              @click="editKey(key)"
              class="btn-secondary-small"
              title="Edit"
            >
              ✏️ Edit
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- Create API Key Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="closeCreateModal">
      <div class="modal">
        <div class="modal-header">
          <h2>Create New API Key</h2>
          <button @click="closeCreateModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
        <form @submit.prevent="handleCreateKey">
          <div class="form-group">
            <label for="agent-select">Agent</label>
            <select
              id="agent-select"
              v-model="newKeyForm.agent_id"
              class="form-input"
            >
              <option value="">All Agents (Universal Key)</option>
              <option
                v-for="agent in availableAgents"
                :key="agent.id"
                :value="agent.id"
              >
                {{ agent.name }} {{ agent.is_prebuilt ? '(Pre-built)' : '' }}
              </option>
            </select>
            <p class="form-hint">Select an agent for agent-specific key, or leave as "All Agents" for universal key</p>
          </div>
          <div class="form-group">
            <label for="key-name">Name *</label>
            <input
              id="key-name"
              v-model="newKeyForm.name"
              type="text"
              placeholder="e.g., Production Key, Development Key"
              required
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="rate-limit">Rate Limit (requests per minute)</label>
            <input
              id="rate-limit"
              v-model.number="newKeyForm.rate_limit_per_minute"
              type="number"
              min="1"
              max="1000"
              placeholder="60"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label for="expires-at">Expiration Date (optional)</label>
            <input
              id="expires-at"
              v-model="newKeyForm.expires_at"
              type="datetime-local"
              class="form-input"
              :min="minDate"
            />
          </div>
          <div class="form-group">
            <label>Domain Whitelisting (Optional)</label>
            <div class="whitelist-container">
              <div class="whitelist-info">
                <p class="form-hint">By default, API key works from any domain. Add domains to restrict usage.</p>
                <p class="form-hint-small">Format: https://example.com (no ports, no paths)</p>
              </div>
              <div class="whitelist-input-group">
                <input
                  v-model="newOriginInput"
                  type="text"
                  placeholder="https://example.com"
                  class="form-input"
                  @keyup.enter="addOrigin"
                />
                <button type="button" @click="addOrigin" class="btn-secondary-small">Add</button>
              </div>
              <div v-if="newKeyForm.allowed_origins && newKeyForm.allowed_origins.length > 0" class="whitelist-list">
                <div v-for="(origin, index) in newKeyForm.allowed_origins" :key="index" class="whitelist-item">
                  <span class="origin-text">{{ origin }}</span>
                  <button type="button" @click="removeOrigin(index)" class="btn-remove-small">×</button>
                </div>
              </div>
              <div v-else class="whitelist-empty">
                <p class="form-hint-small">No restrictions - key works from any domain</p>
              </div>
            </div>
          </div>
          <div class="form-group" v-if="selectedAgentForUrl">
            <label>API Endpoint URL</label>
            <div class="url-preview">
              <code class="url-text">{{ getApiUrl(selectedAgentForUrl.slug || '') }}</code>
              <button 
                type="button"
                @click="copyToClipboard(getApiUrl(selectedAgentForUrl.slug || ''), true)" 
                class="btn-copy-small"
              >
                {{ copiedUrl ? '✓' : '📋' }}
              </button>
            </div>
            <p class="form-hint">This is the URL where external platforms will make requests. See the documentation above for details.</p>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeCreateModal" class="btn-secondary-modal">Cancel</button>
            <button type="submit" :disabled="apiKeysStore.isLoading || !newKeyForm.name" class="btn-primary-modal">
              <span v-if="apiKeysStore.isLoading">Creating...</span>
              <span v-else>Create Key</span>
            </button>
          </div>
        </form>
        </div>
      </div>
    </div>

    <!-- New Key Display Modal -->
    <div v-if="newlyCreatedKey" class="modal-overlay" @click.self="closeKeyDisplay">
      <div class="modal key-display-modal">
        <div class="modal-header">
          <h2>🔑 API Key Created!</h2>
          <button @click="closeKeyDisplay" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="warning-box">
            <p><strong>⚠️ Important:</strong> This is the only time you'll see this key. Copy it now!</p>
          </div>
          <div class="key-display">
            <code class="api-key-value">{{ newlyCreatedKey.key }}</code>
            <button @click="copyToClipboard(newlyCreatedKey.key!)" class="btn-copy">
              {{ copied ? '✓ Copied!' : '📋 Copy' }}
            </button>
          </div>
          <div class="api-url-info" v-if="newlyCreatedKey.agent_slug">
            <p class="key-instruction">
              <strong>API Endpoint URL:</strong>
            </p>
            <div class="url-display">
              <code class="api-url">{{ getApiUrl(newlyCreatedKey.agent_slug) }}</code>
              <button @click="copyToClipboard(getApiUrl(newlyCreatedKey.agent_slug), true)" class="btn-copy-small">
                {{ copiedUrl ? '✓' : '📋' }}
              </button>
            </div>
            <p class="key-instruction">
              Use this key in the <code>X-API-Key</code> header when making requests to the above URL.
            </p>
          </div>
          <p class="key-instruction" v-else>
            Use this key in the <code>X-API-Key</code> header when making requests to the public API.
          </p>
        </div>
        <div class="modal-actions">
          <button @click="closeKeyDisplay" class="btn-primary-modal">Done</button>
        </div>
      </div>
    </div>

    <!-- Edit API Key Modal -->
    <div v-if="showEditModal && editingKey" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal">
        <div class="modal-header">
          <h2>Edit API Key</h2>
          <button @click="closeEditModal" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="handleUpdateKey">
            <div class="form-group">
              <label for="edit-name">Name *</label>
              <input
                id="edit-name"
                v-model="editForm.name"
                type="text"
                required
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label for="edit-rate-limit">Rate Limit (requests per minute)</label>
              <input
                id="edit-rate-limit"
                v-model.number="editForm.rate_limit_per_minute"
                type="number"
                min="1"
                max="1000"
                class="form-input"
              />
            </div>
            <div class="form-group">
              <label>
                <input
                  type="checkbox"
                  v-model="editForm.is_active"
                  class="form-checkbox"
                />
                Active
              </label>
            </div>
            <div class="form-group">
              <label>Domain Whitelisting</label>
              <div class="whitelist-container">
                <div class="whitelist-info">
                  <p class="form-hint">Add domains to restrict usage. Leave empty to allow all domains.</p>
                  <p class="form-hint-small">Format: https://example.com (no ports, no paths)</p>
                </div>
                <div class="whitelist-input-group">
                  <input
                    v-model="editOriginInput"
                    type="text"
                    placeholder="https://example.com"
                    class="form-input"
                    @keyup.enter="addEditOrigin"
                  />
                  <button type="button" @click="addEditOrigin" class="btn-secondary-small">Add</button>
                </div>
                <div v-if="editForm.allowed_origins && editForm.allowed_origins.length > 0" class="whitelist-list">
                  <div v-for="(origin, index) in editForm.allowed_origins" :key="index" class="whitelist-item">
                    <span class="origin-text">{{ origin }}</span>
                    <button type="button" @click="removeEditOrigin(index)" class="btn-remove-small">×</button>
                  </div>
                </div>
                <div v-else class="whitelist-empty">
                  <p class="form-hint-small">No restrictions - key works from any domain</p>
                </div>
              </div>
            </div>
            <div class="modal-actions">
              <button type="button" @click="closeEditModal" class="btn-secondary-modal">Cancel</button>
              <button type="submit" :disabled="apiKeysStore.isLoading" class="btn-primary-modal">
                <span v-if="apiKeysStore.isLoading">Updating...</span>
                <span v-else>Update Key</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Usage Stats Modal -->
    <div v-if="showUsageModal && selectedKey" class="modal-overlay" @click.self="closeUsageModal">
      <div class="modal">
        <div class="modal-header">
          <h2>Usage Statistics</h2>
          <button @click="closeUsageModal" class="btn-close">×</button>
        </div>
        <div class="modal-body" v-if="usageStats">
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-value">{{ usageStats.total_requests.toLocaleString() }}</div>
              <div class="stat-label">Total Requests</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ usageStats.requests_today }}</div>
              <div class="stat-label">Requests Today</div>
            </div>
            <div class="stat-card">
              <div class="stat-value">{{ usageStats.requests_this_month }}</div>
              <div class="stat-label">Requests This Month</div>
            </div>
          </div>
          <div class="detail-item" v-if="usageStats.last_used_at">
            <span class="label">Last Used:</span>
            <span class="value">{{ formatDate(usageStats.last_used_at) }}</span>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="closeUsageModal" class="btn-primary-modal">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useApiKeysStore } from '@/stores/apiKeys'
import { useAgentsStore } from '@/stores/agents'
import { useAuthStore } from '@/stores/auth'
import type { ApiKey, ApiKeyUsageStats, Agent } from '@/types'

const router = useRouter()
const apiKeysStore = useApiKeysStore()
const agentsStore = useAgentsStore()
const authStore = useAuthStore()

const showCreateModal = ref(false)
const newlyCreatedKey = ref<ApiKey | null>(null)
const copied = ref(false)
const copiedUrl = ref(false)
const showUsageModal = ref(false)
const selectedKey = ref<ApiKey | null>(null)
const usageStats = ref<ApiKeyUsageStats | null>(null)

const newKeyForm = ref({
  agent_id: '',
  name: '',
  rate_limit_per_minute: 60,
  expires_at: '',
  allowed_origins: [] as string[]
})

const newOriginInput = ref('')
const showEditModal = ref(false)
const editingKey = ref<ApiKey | null>(null)
const editForm = ref({
  name: '',
  allowed_origins: [] as string[],
  is_active: true,
  rate_limit_per_minute: 60
})
const editOriginInput = ref('')

const availableAgents = computed(() => {
  const userId = authStore.currentUser?.id
  return agentsStore.agents.filter(agent => agent.is_prebuilt || agent.user_id === userId)
})

const selectedAgentForUrl = computed(() => {
  if (!newKeyForm.value.agent_id) return null
  return agentsStore.agents.find(a => a.id === newKeyForm.value.agent_id) || null
})

const minDate = computed(() => {
  const now = new Date()
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
  return now.toISOString().slice(0, 16)
})

onMounted(async () => {
  await Promise.all([
    apiKeysStore.fetchApiKeys(),
    agentsStore.fetchAgents()
  ])
})

function getAgentName(agentId: string | null): string {
  if (!agentId) return ''
  const agent = agentsStore.agents.find(a => a.id === agentId)
  return agent?.name || 'Unknown Agent'
}

function getApiUrl(agentSlug: string): string {
  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    (import.meta.env.DEV ? 'http://localhost:8009' : window.location.origin)
  return `${baseUrl}/api/v1/public/agents/${agentSlug}/chat`
}


function goBack() {
  router.push('/dashboard')
}

function goToDocumentation() {
  router.push('/api-keys/documentation')
}

function closeCreateModal() {
  showCreateModal.value = false
  newKeyForm.value = {
    agent_id: '',
    name: '',
    rate_limit_per_minute: 60,
    expires_at: '',
    allowed_origins: []
  }
  newOriginInput.value = ''
}

function addOrigin() {
  const origin = newOriginInput.value.trim()
  if (!origin) return
  
  // Basic validation
  const originPattern = /^https?:\/\/[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/
  if (!originPattern.test(origin)) {
    alert('Invalid origin format. Must be like https://example.com (no ports, no paths)')
    return
  }
  
  // Check for ports
  if (origin.split('://')[1].includes(':')) {
    alert('Origin must not include port. Use format: https://example.com')
    return
  }
  
  const normalized = origin.replace(/\/$/, '').toLowerCase()
  if (!newKeyForm.value.allowed_origins) {
    newKeyForm.value.allowed_origins = []
  }
  
  // Check for duplicates
  if (newKeyForm.value.allowed_origins.some(o => o.toLowerCase() === normalized)) {
    alert('This origin is already added')
    return
  }
  
  newKeyForm.value.allowed_origins.push(origin.replace(/\/$/, ''))
  newOriginInput.value = ''
}

function removeOrigin(index: number) {
  if (newKeyForm.value.allowed_origins) {
    newKeyForm.value.allowed_origins.splice(index, 1)
  }
}

function editKey(key: ApiKey) {
  editingKey.value = key
  editForm.value = {
    name: key.name,
    allowed_origins: key.allowed_origins ? [...key.allowed_origins] : [],
    is_active: key.is_active,
    rate_limit_per_minute: key.rate_limit_per_minute
  }
  editOriginInput.value = ''
  showEditModal.value = true
}

function closeEditModal() {
  showEditModal.value = false
  editingKey.value = null
  editForm.value = {
    name: '',
    allowed_origins: [],
    is_active: true,
    rate_limit_per_minute: 60
  }
  editOriginInput.value = ''
}

function addEditOrigin() {
  const origin = editOriginInput.value.trim()
  if (!origin) return
  
  // Basic validation
  const originPattern = /^https?:\/\/[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/
  if (!originPattern.test(origin)) {
    alert('Invalid origin format. Must be like https://example.com (no ports, no paths)')
    return
  }
  
  // Check for ports
  if (origin.split('://')[1].includes(':')) {
    alert('Origin must not include port. Use format: https://example.com')
    return
  }
  
  const normalized = origin.replace(/\/$/, '').toLowerCase()
  if (!editForm.value.allowed_origins) {
    editForm.value.allowed_origins = []
  }
  
  // Check for duplicates
  if (editForm.value.allowed_origins.some(o => o.toLowerCase() === normalized)) {
    alert('This origin is already added')
    return
  }
  
  editForm.value.allowed_origins.push(origin.replace(/\/$/, ''))
  editOriginInput.value = ''
}

function removeEditOrigin(index: number) {
  if (editForm.value.allowed_origins) {
    editForm.value.allowed_origins.splice(index, 1)
  }
}

async function handleUpdateKey() {
  if (!editingKey.value) return
  
  try {
    const updateData: any = {
      name: editForm.value.name,
      is_active: editForm.value.is_active,
      rate_limit_per_minute: editForm.value.rate_limit_per_minute,
      allowed_origins: editForm.value.allowed_origins.length > 0 ? editForm.value.allowed_origins : null
    }
    
    await apiKeysStore.updateApiKey(editingKey.value.id, updateData)
    closeEditModal()
  } catch (error: any) {
    console.error('Failed to update API key:', error)
    alert(error.response?.data?.detail || 'Failed to update API key. Please try again.')
  }
}

async function handleCreateKey() {
  if (!newKeyForm.value.name) {
    alert('Please enter a name for the API key')
    return
  }
  
  try {
    const data: any = {
      name: newKeyForm.value.name,
      rate_limit_per_minute: newKeyForm.value.rate_limit_per_minute || 60
    }
    
    // Only include agent_id if selected (not empty string)
    if (newKeyForm.value.agent_id) {
      data.agent_id = newKeyForm.value.agent_id
    } else {
      data.agent_id = null // Universal key
    }
    
    if (newKeyForm.value.expires_at) {
      data.expires_at = new Date(newKeyForm.value.expires_at).toISOString()
    }
    
    // Include allowed_origins only if there are any
    if (newKeyForm.value.allowed_origins && newKeyForm.value.allowed_origins.length > 0) {
      data.allowed_origins = newKeyForm.value.allowed_origins
    } else {
      data.allowed_origins = null // Allow all origins
    }
    
    const created = await apiKeysStore.createApiKey(data)
    newlyCreatedKey.value = created
    showCreateModal.value = false
  } catch (error: any) {
    console.error('Failed to create API key:', error)
    alert(error.response?.data?.detail || 'Failed to create API key. Please try again.')
  }
}

function closeKeyDisplay() {
  newlyCreatedKey.value = null
  copied.value = false
}

async function copyToClipboard(text: string, isUrl: boolean = false) {
  try {
    await navigator.clipboard.writeText(text)
    if (isUrl) {
      copiedUrl.value = true
      setTimeout(() => {
        copiedUrl.value = false
      }, 2000)
    } else {
      copied.value = true
      setTimeout(() => {
        copied.value = false
      }, 2000)
    }
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

async function deleteKey(keyId: string) {
  if (confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
    try {
      await apiKeysStore.deleteApiKey(keyId)
    } catch (error) {
      console.error('Failed to delete API key:', error)
    }
  }
}

async function toggleKey(keyId: string) {
  try {
    await apiKeysStore.toggleApiKey(keyId)
  } catch (error) {
    console.error('Failed to toggle API key:', error)
  }
}

async function viewUsage(keyId: string) {
  try {
    const key = apiKeysStore.apiKeys.find(k => k.id === keyId)
    selectedKey.value = key || null
    usageStats.value = await apiKeysStore.getUsageStats(keyId)
    showUsageModal.value = true
  } catch (error) {
    console.error('Failed to fetch usage stats:', error)
  }
}

function closeUsageModal() {
  showUsageModal.value = false
  selectedKey.value = null
  usageStats.value = null
}

function formatDate(dateString: string | null): string {
  if (!dateString) return 'Never'
  const date = new Date(dateString)
  return date.toLocaleString()
}
</script>

<style scoped>
.api-keys-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  position: relative;
}

.page-header {
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

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.btn-back {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 16px;
  cursor: pointer;
  padding: 10px 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateX(-4px);
}

h1 {
  color: white;
  font-size: 32px;
  font-weight: 700;
  margin: 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-secondary-header {
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

.btn-secondary-header:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
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

.btn-primary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-content {
  max-width: 1200px;
  margin: 40px auto;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 80px 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h2, .error-state h2 {
  color: white;
  margin-bottom: 10px;
}

.empty-state p, .error-state p {
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 30px;
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
}

.api-keys-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.api-key-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 28px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.api-key-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
  background: rgba(255, 255, 255, 0.2);
}

.key-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.key-info {
  flex: 1;
}

.key-info h3 {
  color: white;
  font-size: 22px;
  margin: 0 0 8px 0;
  font-weight: 600;
}

.status-badge {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin: 0 10px;
}

.status-badge.active {
  background: rgba(76, 175, 80, 0.9);
  color: white;
  border: 1px solid rgba(76, 175, 80, 1);
  box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
}

.status-badge.inactive {
  background: rgba(158, 158, 158, 0.7);
  color: white;
  border: 1px solid rgba(158, 158, 158, 0.9);
}

.key-actions {
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

.btn-icon:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.btn-icon.danger:hover:not(:disabled) {
  background: rgba(244, 67, 54, 0.3);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.key-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-item .label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  font-weight: 500;
}

.detail-item .value {
  color: white;
  font-size: 15px;
  font-weight: 600;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.modal-header h2 {
  margin: 0;
  color: #333;
  font-size: 24px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 32px;
  cursor: pointer;
  color: #666;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
}

.modal-body form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #333;
  font-weight: 600;
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  font-size: 16px;
  font-family: inherit;
  transition: all 0.3s ease;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin-top: 20px;
}

.btn-secondary-modal {
  padding: 12px 24px;
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary-modal:hover {
  background: #e0e0e0;
  border-color: #bbb;
}

.btn-primary-modal {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary-modal:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary-modal:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.url-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
}

.url-text {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #667eea;
  word-break: break-all;
  text-align: left;
  margin: 0;
}

.key-display-modal .modal-body {
  text-align: center;
}

.warning-box {
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.warning-box p {
  margin: 0;
  color: #f57c00;
}

.key-display {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 20px;
}

.api-key-value {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #333;
  word-break: break-all;
  text-align: left;
}

.btn-copy {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-copy:hover {
  background: #5568d3;
  transform: translateY(-2px);
}

.key-instruction {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.key-instruction code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.form-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #666;
  font-style: italic;
}

.api-url-info {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.url-display {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(102, 126, 234, 0.1);
  border-radius: 8px;
  padding: 12px;
  margin: 12px 0;
}

.api-url {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #667eea;
  word-break: break-all;
  text-align: left;
}

.btn-copy-small {
  padding: 6px 12px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  min-width: 40px;
}

.btn-copy-small:hover {
  background: #5568d3;
}


.docs-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.docs-section h5 {
  margin: 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.method-badge {
  display: inline-block;
  padding: 6px 14px;
  background: rgba(76, 175, 80, 0.8);
  color: white;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  border: 1px solid rgba(76, 175, 80, 0.5);
}

.code-block {
  position: relative;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  overflow-x: auto;
}

.code-block code,
.code-block pre {
  color: #e0e0e0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.code-block .btn-copy-inline {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 6px 10px;
  background: rgba(102, 126, 234, 0.8);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.code-block .btn-copy-inline:hover {
  background: rgba(102, 126, 234, 1);
  transform: scale(1.05);
}

.json-example,
.curl-example,
.js-example,
.python-example {
  margin: 0;
  padding: 0;
  background: transparent;
  color: #e0e0e0;
}

.docs-notes {
  margin: 0;
  padding-left: 24px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  line-height: 2;
}

.docs-notes li {
  margin-bottom: 10px;
}

.docs-notes code {
  background: rgba(255, 255, 255, 0.2);
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #fff;
  font-weight: 600;
}

.docs-notes strong {
  color: white;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(102, 126, 234, 0.1);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #667eea;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

/* Domain Whitelisting Styles */
.whitelist-container {
  margin-top: 12px;
  padding: 20px;
  background: rgba(102, 126, 234, 0.05);
  border: 1px solid rgba(102, 126, 234, 0.15);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.whitelist-container:hover {
  background: rgba(102, 126, 234, 0.08);
  border-color: rgba(102, 126, 234, 0.25);
}

.whitelist-info {
  margin-bottom: 16px;
}

.whitelist-info .form-hint {
  margin: 0 0 8px 0;
  color: #555;
  font-size: 13px;
  line-height: 1.5;
}

.whitelist-info .form-hint-small {
  margin: 0;
  color: #888;
  font-size: 12px;
  font-family: 'Courier New', monospace;
  background: rgba(0, 0, 0, 0.03);
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.whitelist-input-group {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  align-items: stretch;
}

.whitelist-input-group .form-input {
  flex: 1;
  padding: 12px 16px;
  font-size: 14px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 8px;
  background: white;
  color: #333;
  transition: all 0.2s ease;
}

.whitelist-input-group .form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.whitelist-input-group .form-input::placeholder {
  color: #999;
}

.btn-secondary-small {
  padding: 12px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.btn-secondary-small:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-secondary-small:active {
  transform: translateY(0);
}

.btn-secondary-small:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.whitelist-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.whitelist-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: white;
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.whitelist-item:hover {
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
  transform: translateX(2px);
}

.origin-text {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #333;
  font-weight: 500;
  word-break: break-all;
}

.btn-remove-small {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
  border: 1px solid rgba(244, 67, 54, 0.2);
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
  margin-left: 12px;
  line-height: 1;
  padding: 0;
}

.btn-remove-small:hover {
  background: rgba(244, 67, 54, 0.2);
  border-color: rgba(244, 67, 54, 0.4);
  transform: scale(1.1);
}

.btn-remove-small:active {
  transform: scale(0.95);
}

.whitelist-empty {
  padding: 16px;
  text-align: center;
  background: rgba(0, 0, 0, 0.02);
  border: 1px dashed rgba(102, 126, 234, 0.2);
  border-radius: 8px;
  margin-top: 12px;
}

.whitelist-empty .form-hint-small {
  margin: 0;
  color: #888;
  font-size: 13px;
  font-style: italic;
  background: transparent;
  padding: 0;
}

.origin-badge {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(102, 126, 234, 0.1);
  color: #667eea;
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  font-family: 'Courier New', monospace;
  margin-right: 6px;
  margin-bottom: 4px;
}
</style>

