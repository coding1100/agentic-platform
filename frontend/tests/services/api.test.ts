import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { authApi, agentsApi, conversationsApi, chatApi, tutorApi } from '@/services/api'

vi.mock('axios')
const mockedAxios = axios as any

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('token', 'test-token')
  })

  describe('authApi', () => {
    it('should login with form data', async () => {
      const mockResponse = { data: { access_token: 'token', token_type: 'bearer' } }
      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await authApi.login({ email: 'test@example.com', password: 'password' })

      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/auth/login'),
        expect.any(FormData),
        expect.objectContaining({ headers: expect.any(Object) })
      )
      expect(result).toEqual(mockResponse.data)
    })

    it('should signup', async () => {
      const mockResponse = { data: { id: '1', email: 'test@example.com', created_at: '2024-01-01' } }
      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await authApi.signup({ email: 'test@example.com', password: 'password' })

      expect(result).toBeDefined()
    })

    it('should get current user', async () => {
      const mockResponse = { data: { id: '1', email: 'test@example.com', created_at: '2024-01-01' } }
      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await authApi.getCurrentUser()

      expect(result).toBeDefined()
    })
  })

  describe('agentsApi', () => {
    it('should list agents', async () => {
      const mockResponse = { data: [{ id: '1', name: 'Agent' }] }
      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await agentsApi.list()

      expect(result).toBeDefined()
    })

    it('should create agent', async () => {
      const mockResponse = { data: { id: '1', name: 'New Agent' } }
      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await agentsApi.create({ name: 'New Agent', system_prompt: 'Prompt' })

      expect(result).toBeDefined()
    })
  })

  describe('chatApi', () => {
    it('should send message', async () => {
      const mockResponse = {
        data: {
          conversation_id: '1',
          message: 'Response',
          agent_id: '1',
          user_message: {
            id: 'user-1',
            conversation_id: '1',
            role: 'user',
            content: 'Hello',
            created_at: '2024-01-01'
          },
          assistant_message: {
            id: 'assistant-1',
            conversation_id: '1',
            role: 'assistant',
            content: 'Response',
            created_at: '2024-01-01'
          }
        }
      }
      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await chatApi.sendMessage('1', { message: 'Hello' })

      expect(result).toBeDefined()
      expect(result.user_message?.content).toBe('Hello')
      expect(result.assistant_message?.content).toBe('Response')
    })
  })

  describe('tutorApi', () => {
    it('should load tutor workspace', async () => {
      const mockResponse = {
        data: {
          subject: 'Calculus',
          academic_level: 'college',
          learner_name: 'Hidden Learner',
          selected_action: 'practice',
          selected_mode: 'practice_quiz_generator',
          progress: {
            sessions_completed: 1,
            practice_sessions_attempted: 1,
            practice_sessions_completed: 1,
            source_sessions: 0,
            average_score: 90,
            weak_topics: [],
            mastery_by_topic: {},
            recent_activity: [],
            next_recommended_action: 'Ask a question'
          },
          recent_sources: [],
          recent_results: []
        }
      }
      mockedAxios.get.mockResolvedValue(mockResponse)

      const result = await tutorApi.getWorkspace('agent-1')

      expect(result.subject).toBe('Calculus')
      expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/tutor/agent-1/workspace')
    })

    it('should execute tutor action', async () => {
      const mockResponse = {
        data: {
          action: 'practice',
          learning_mode: 'practice_quiz_generator',
          subject: 'Calculus',
          academic_level: 'college',
          explanation: 'Work through derivatives one rule at a time.',
          steps: ['Review the power rule'],
          practice_set: {
            title: 'Derivative review',
            instructions: 'Solve each prompt.',
            questions: []
          },
          key_concepts: ['Derivatives'],
          progress_snapshot: {
            sessions_completed: 2,
            practice_sessions_attempted: 2,
            practice_sessions_completed: 1,
            source_sessions: 0,
            average_score: 88,
            weak_topics: [],
            mastery_by_topic: {},
            recent_activity: [],
            next_recommended_action: 'Upload notes'
          },
          suggested_next_actions: ['Upload notes']
        }
      }
      mockedAxios.post.mockResolvedValue(mockResponse)

      const result = await tutorApi.execute('agent-1', {
        action: 'practice',
        learning_mode: 'practice_quiz_generator',
        subject: 'Calculus',
        academic_level: 'college'
      })

      expect(result.practice_set.title).toBe('Derivative review')
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/tutor/agent-1/execute', {
        action: 'practice',
        learning_mode: 'practice_quiz_generator',
        subject: 'Calculus',
        academic_level: 'college'
      })
    })
  })
})

