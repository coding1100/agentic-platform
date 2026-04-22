import axios, { AxiosInstance } from 'axios'
import type {
  User,
  Agent,
  Conversation,
  ChatRequest,
  ChatResponse,
  TutorExecuteRequest,
  TutorExecuteResponse,
  TutorWorkspaceState,
  ApiKey,
  ApiKeyCreate,
  ApiKeyUpdate,
  ApiKeyUsageStats,
  EmbedDeployment,
  EmbedDeploymentUpsert,
  RealtimeSession,
  RealtimeTokenRequest,
  RealtimeTokenResponse,
} from '@/types'

const defaultBaseUrl =
  import.meta.env.DEV
    ? 'http://localhost:8009'
    : (typeof window !== 'undefined' ? window.location.origin : '')
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || defaultBaseUrl

const createdClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})
const apiClient: AxiosInstance = (createdClient || (axios as unknown as AxiosInstance))

// Request interceptor to add auth token
if ((apiClient as any).interceptors?.request?.use) {
  apiClient.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers = config.headers || {}
        ;(config.headers as any).Authorization = `Bearer ${token}`
      }
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )
}

// Response interceptor to handle errors
if ((apiClient as any).interceptors?.response?.use) {
  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )
}

export const authApi = {
  async login(data: { email: string; password: string }) {
    const formData = new FormData()
    formData.append('username', data.email)
    formData.append('password', data.password)
    
    const response = await axios.post(`${API_BASE_URL}/api/v1/auth/login`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  async signup(data: { email: string; password: string }) {
    const response = await apiClient.post('/api/v1/auth/signup', data)
    return response.data
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/api/v1/auth/me')
    return response.data
  }
}

export const agentsApi = {
  async list(): Promise<Agent[]> {
    const response = await apiClient.get('/api/v1/agents')
    return response.data
  },

  async get(agentId: string): Promise<Agent> {
    const response = await apiClient.get(`/api/v1/agents/${agentId}`)
    return response.data
  },

  async create(data: {
    name: string
    description?: string
    system_prompt: string
    greeting_message?: string
    model?: string
    temperature?: number
    interaction_mode?: 'chat' | 'avatar_realtime'
    livekit_agent_name?: string | null
    avatar_provider?: string | null
    avatar_id?: string | null
    realtime_config?: Record<string, any> | null
  }): Promise<Agent> {
    const response = await apiClient.post('/api/v1/agents', data)
    return response.data
  },

  async update(agentId: string, data: Partial<Agent>): Promise<Agent> {
    const response = await apiClient.put(`/api/v1/agents/${agentId}`, data)
    return response.data
  },

  async delete(agentId: string): Promise<void> {
    await apiClient.delete(`/api/v1/agents/${agentId}`)
  }
}

export const conversationsApi = {
  async listByAgent(agentId: string): Promise<Conversation[]> {
    const response = await apiClient.get(`/api/v1/conversations/agent/${agentId}`)
    return response.data
  },

  async get(conversationId: string): Promise<Conversation> {
    const response = await apiClient.get(`/api/v1/conversations/${conversationId}`)
    return response.data
  },

  async create(data: { agent_id: string; title?: string }): Promise<Conversation> {
    const response = await apiClient.post('/api/v1/conversations', data)
    return response.data
  }
}

export const chatApi = {
  async sendMessage(agentId: string, data: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post(`/api/v1/chat/${agentId}`, data)
    return response.data
  },

  async streamMessage(agentId: string, data: ChatRequest): Promise<ReadableStream> {
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/${agentId}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      throw new Error(`Streaming failed: ${response.statusText}`)
    }

    return response.body as ReadableStream
  }
}

export const tutorApi = {
  async getWorkspace(agentId: string): Promise<TutorWorkspaceState> {
    const response = await apiClient.get(`/api/v1/tutor/${agentId}/workspace`)
    return response.data
  },

  async saveWorkspace(agentId: string, data: TutorWorkspaceState): Promise<TutorWorkspaceState> {
    const response = await apiClient.put(`/api/v1/tutor/${agentId}/workspace`, data)
    return response.data
  },

  async execute(agentId: string, data: TutorExecuteRequest): Promise<TutorExecuteResponse> {
    const response = await apiClient.post(`/api/v1/tutor/${agentId}/execute`, data)
    return response.data
  }
}

export interface PronunciationAssessmentRequest {
  word_or_phrase: string
  user_transcript: string
  language: string
  target_language_code?: string
}

export interface PronunciationAssessmentResponse {
  overall_score: number
  accuracy_score: number
  fluency_score: number
  intonation_score: number
  stress_score: number
  clarity_score: number
  feedback: string
  suggestions: string[]
  correct_pronunciation: string
  user_pronunciation: string
  phonetic_comparison?: string
}

export const pronunciationApi = {
  async assess(data: PronunciationAssessmentRequest): Promise<PronunciationAssessmentResponse> {
    const response = await apiClient.post('/api/v1/chat/pronunciation-assessment', data)
    return response.data
  }
}

export const apiKeysApi = {
  async list(): Promise<ApiKey[]> {
    const response = await apiClient.get('/api/v1/api-keys')
    return response.data
  },

  async create(data: ApiKeyCreate): Promise<ApiKey> {
    const response = await apiClient.post('/api/v1/api-keys', data)
    return response.data
  },

  async get(apiKeyId: string): Promise<ApiKey> {
    const response = await apiClient.get(`/api/v1/api-keys/${apiKeyId}`)
    return response.data
  },

  async delete(apiKeyId: string): Promise<void> {
    await apiClient.delete(`/api/v1/api-keys/${apiKeyId}`)
  },

  async toggle(apiKeyId: string): Promise<ApiKey> {
    const response = await apiClient.patch(`/api/v1/api-keys/${apiKeyId}/toggle`)
    return response.data
  },

  async getUsage(apiKeyId: string): Promise<ApiKeyUsageStats> {
    const response = await apiClient.get(`/api/v1/api-keys/${apiKeyId}/usage`)
    return response.data
  },

  async update(apiKeyId: string, data: ApiKeyUpdate): Promise<ApiKey> {
    const response = await apiClient.patch(`/api/v1/api-keys/${apiKeyId}`, data)
    return response.data
  }
}

export interface UserStateResponse {
  namespace: string
  data: Record<string, any>
  updated_at?: string | null
}

export const stateApi = {
  async get(namespace: string): Promise<UserStateResponse> {
    const response = await apiClient.get(`/api/v1/state/${encodeURIComponent(namespace)}`)
    return response.data
  },

  async save(namespace: string, data: Record<string, any>): Promise<UserStateResponse> {
    const response = await apiClient.put(`/api/v1/state/${encodeURIComponent(namespace)}`, { data })
    return response.data
  }
}

export const realtimeApi = {
  async upsertEmbedDeployment(agentId: string, data: EmbedDeploymentUpsert): Promise<EmbedDeployment> {
    const response = await apiClient.put(`/api/v1/realtime/agents/${agentId}/embed`, data)
    return response.data
  },

  async getEmbedDeployment(agentId: string): Promise<EmbedDeployment> {
    const response = await apiClient.get(`/api/v1/realtime/agents/${agentId}/embed`)
    return response.data
  },

  async createAgentToken(agentId: string, data: RealtimeTokenRequest): Promise<RealtimeTokenResponse> {
    const response = await apiClient.post(`/api/v1/realtime/agents/${agentId}/token`, data)
    return response.data
  },

  async listSessions(agentId: string, limit: number = 50): Promise<RealtimeSession[]> {
    const response = await apiClient.get(`/api/v1/realtime/agents/${agentId}/sessions`, {
      params: { limit }
    })
    return response.data
  },

  async endSession(sessionId: string): Promise<RealtimeSession> {
    const response = await apiClient.post(`/api/v1/realtime/sessions/${sessionId}/end`)
    return response.data
  }
}
