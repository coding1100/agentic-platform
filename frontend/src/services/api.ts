import axios, { AxiosInstance } from 'axios'
import type {
  User,
  Agent,
  Conversation,
  ChatRequest,
  ChatResponse,
  ApiKey,
  ApiKeyCreate,
  ApiKeyUsageStats
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8009'

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
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
    model?: string
    temperature?: number
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

export const ttsApi = {
  async speak(text: string, rate: number = 150, volume: number = 0.9): Promise<Blob> {
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE_URL}/api/v1/tts/speak`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : '',
      },
      body: JSON.stringify({ text, rate, volume }),
    })

    if (!response.ok) {
      throw new Error(`TTS failed: ${response.statusText}`)
    }

    return await response.blob()
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


