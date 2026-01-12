export interface User {
  id: string
  email: string
  created_at: string
}

export interface ApiKey {
  id: string
  agent_id: string
  name: string
  is_active: boolean
  last_used_at: string | null
  expires_at: string | null
  created_at: string
  rate_limit_per_minute: number
  total_requests: number
  key?: string // Only present when creating a new key
  agent_slug?: string // Agent slug for URL generation
}

export interface ApiKeyCreate {
  agent_id: string
  name: string
  expires_at?: string | null
  rate_limit_per_minute?: number
}

export interface ApiKeyUsageStats {
  total_requests: number
  last_used_at: string | null
  requests_today: number
  requests_this_month: number
}

export interface Agent {
  id: string
  user_id: string
  name: string
  description?: string
  system_prompt: string
  greeting_message?: string
  model: string
  temperature: number
  created_at: string
  updated_at: string
  slug?: string
  is_prebuilt?: boolean
  category?: string
}

export interface Conversation {
  id: string
  agent_id: string
  user_id: string
  title?: string
  created_at: string
  updated_at: string
  messages?: Message[]
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
}

export interface ChatRequest {
  conversation_id?: string | null
  message: string
}

export interface ChatResponse {
  conversation_id: string
  message: string
  agent_id: string
}

