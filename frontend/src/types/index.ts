export interface User {
  id: string
  email: string
  created_at: string
}

export interface ApiKey {
  id: string
  agent_id: string | null // null = universal key for all agents
  name: string
  is_active: boolean
  last_used_at: string | null
  expires_at: string | null
  created_at: string
  rate_limit_per_minute: number
  total_requests: number
  allowed_origins?: string[] | null // null or empty = allow all origins
  key?: string // Only present when creating a new key
  agent_slug?: string | null // Agent slug for URL generation
}

export interface ApiKeyCreate {
  agent_id?: string | null // null = universal key for all agents
  name: string
  expires_at?: string | null
  rate_limit_per_minute?: number
  allowed_origins?: string[] | null // null or empty = allow all origins
}

export interface ApiKeyUpdate {
  name?: string
  allowed_origins?: string[] | null // null or empty = allow all origins
  is_active?: boolean
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
  interaction_mode?: 'chat' | 'avatar_realtime'
  livekit_agent_name?: string | null
  avatar_provider?: string | null
  avatar_id?: string | null
  realtime_config?: Record<string, any> | null
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
  user_message?: Message | null
  assistant_message?: Message | null
}

export type TutorAcademicLevel = 'high_school' | 'college' | 'phd'
export type TutorAction = 'ask_question' | 'upload_notes' | 'practice'
export type TutorLearningMode =
  | 'personalized_learning'
  | 'assignment_assistant'
  | 'practice_quiz_generator'
  | 'concept_simplifier'
  | 'notes_summary'
  | 'exam_mode'
  | 'source_based_learning'
export type TutorSourceKind = 'notes' | 'pdf' | 'book'
export type TutorPracticeFormat = 'multiple_choice' | 'short_answer' | 'mixed'

export interface TutorRecentSource {
  name: string
  kind: TutorSourceKind
  char_count: number
  added_at: string
}

export interface TutorRecentResult {
  action: TutorAction
  learning_mode: TutorLearningMode
  title: string
  score?: number | null
  weak_topics: string[]
  created_at: string
}

export interface TutorProgressSummary {
  sessions_completed: number
  practice_sessions_attempted: number
  practice_sessions_completed: number
  source_sessions: number
  average_score?: number | null
  weak_topics: string[]
  mastery_by_topic: Record<string, number>
  recent_activity: string[]
  next_recommended_action?: string | null
}

export interface TutorWorkspaceState {
  subject: string
  academic_level?: TutorAcademicLevel | null
  learner_name?: string | null
  selected_action?: TutorAction | null
  selected_mode?: TutorLearningMode | null
  progress: TutorProgressSummary
  recent_sources: TutorRecentSource[]
  recent_results: TutorRecentResult[]
}

export interface TutorPracticeOption {
  id: string
  text: string
}

export interface TutorPracticeQuestion {
  id: string
  prompt: string
  type: 'multiple_choice' | 'short_answer'
  concept?: string | null
  options: TutorPracticeOption[]
  answer?: string | null
  explanation?: string | null
}

export interface TutorPracticeSet {
  title: string
  instructions: string
  questions: TutorPracticeQuestion[]
}

export interface TutorExecuteRequest {
  action: TutorAction
  learning_mode: TutorLearningMode
  subject: string
  academic_level: TutorAcademicLevel
  learner_name?: string | null
  prompt?: string | null
  source_text?: string | null
  source_name?: string | null
  source_kind?: TutorSourceKind | null
  question_count?: number | null
  practice_format?: TutorPracticeFormat | null
}

export interface TutorExecuteResponse {
  action: TutorAction
  learning_mode: TutorLearningMode
  subject: string
  academic_level: TutorAcademicLevel
  learner_name?: string | null
  summary?: string | null
  explanation: string
  steps: string[]
  practice_set: TutorPracticeSet
  key_concepts: string[]
  progress_snapshot: TutorProgressSummary
  suggested_next_actions: string[]
}

export interface RealtimeTokenRequest {
  room_name?: string | null
  participant_identity?: string | null
  participant_name?: string | null
  participant_metadata?: string | null
  participant_attributes?: Record<string, string> | null
  room_config?: Record<string, any> | null
  origin_hint?: string | null
}

export interface RealtimeTokenResponse {
  server_url: string
  participant_token: string
  room_name: string
  participant_identity: string
  participant_name: string
  expires_at: string
  agent_id: string
  session_id: string
  embed_id?: string | null
}

export interface EmbedDeployment {
  id: string
  user_id: string
  agent_id: string
  embed_id: string
  is_active: boolean
  allowed_origins?: string[] | null
  token_ttl_seconds: number
  max_concurrent_sessions: number
  room_name_prefix?: string | null
  created_at: string
  updated_at: string
}

export interface EmbedDeploymentUpsert {
  is_active: boolean
  allowed_origins?: string[] | null
  token_ttl_seconds?: number | null
  max_concurrent_sessions?: number | null
  room_name_prefix?: string | null
}

export interface RealtimeSession {
  id: string
  user_id: string
  agent_id: string
  embed_deployment_id?: string | null
  room_name: string
  participant_identity: string
  participant_name?: string | null
  status: string
  expires_at?: string | null
  ended_at?: string | null
  session_metadata?: Record<string, any> | null
  created_at: string
  updated_at: string
}

