import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { authApi, agentsApi, conversationsApi, chatApi } from '@/services/api'

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
      mockedAxios.create.mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse),
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })

      const result = await authApi.signup({ email: 'test@example.com', password: 'password' })

      expect(result).toBeDefined()
    })

    it('should get current user', async () => {
      const mockResponse = { data: { id: '1', email: 'test@example.com', created_at: '2024-01-01' } }
      mockedAxios.create.mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse),
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })

      const result = await authApi.getCurrentUser()

      expect(result).toBeDefined()
    })
  })

  describe('agentsApi', () => {
    it('should list agents', async () => {
      const mockResponse = { data: [{ id: '1', name: 'Agent' }] }
      mockedAxios.create.mockReturnValue({
        get: vi.fn().mockResolvedValue(mockResponse),
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })

      const result = await agentsApi.list()

      expect(result).toBeDefined()
    })

    it('should create agent', async () => {
      const mockResponse = { data: { id: '1', name: 'New Agent' } }
      mockedAxios.create.mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse),
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })

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
          agent_id: '1'
        }
      }
      mockedAxios.create.mockReturnValue({
        post: vi.fn().mockResolvedValue(mockResponse),
        interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } }
      })

      const result = await chatApi.sendMessage('1', { message: 'Hello' })

      expect(result).toBeDefined()
    })
  })
})

