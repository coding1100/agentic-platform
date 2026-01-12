import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { chatApi, conversationsApi } from '@/services/api'

vi.mock('@/services/api', () => ({
  chatApi: {
    sendMessage: vi.fn(),
  },
  conversationsApi: {
    listByAgent: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
  }
}))

describe('Chat Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should fetch conversations', async () => {
    const store = useChatStore()
    const mockConversations = [
      { id: '1', agent_id: '1', user_id: '1', title: 'Conv 1', created_at: '2024-01-01', updated_at: '2024-01-01' },
      { id: '2', agent_id: '1', user_id: '1', title: 'Conv 2', created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]

    vi.mocked(conversationsApi.listByAgent).mockResolvedValue(mockConversations)

    await store.fetchConversations('1')

    expect(store.conversations).toEqual(mockConversations)
    expect(store.loading).toBe(false)
  })

  it('should fetch conversation with messages', async () => {
    const store = useChatStore()
    const mockConversation = {
      id: '1',
      agent_id: '1',
      user_id: '1',
      title: 'Conv',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
      messages: [
        { id: '1', conversation_id: '1', role: 'user', content: 'Hello', created_at: '2024-01-01' },
        { id: '2', conversation_id: '1', role: 'assistant', content: 'Hi', created_at: '2024-01-01' }
      ]
    }

    vi.mocked(conversationsApi.get).mockResolvedValue(mockConversation)

    const result = await store.fetchConversation('1')

    expect(result.success).toBe(true)
    expect(store.messages).toEqual(mockConversation.messages)
    expect(store.activeConversationId).toBe('1')
  })

  it('should create conversation', async () => {
    const store = useChatStore()
    const newConversation = {
      id: '1',
      agent_id: '1',
      user_id: '1',
      title: 'New Conv',
      created_at: '2024-01-01',
      updated_at: '2024-01-01'
    }

    vi.mocked(conversationsApi.create).mockResolvedValue(newConversation)

    const result = await store.createConversation('1', 'New Conv')

    expect(result.success).toBe(true)
    expect(store.activeConversationId).toBe('1')
    expect(store.messages).toEqual([])
  })

  it('should send message', async () => {
    const store = useChatStore()
    const mockResponse = {
      conversation_id: '1',
      message: 'Response message',
      agent_id: '1'
    }

    vi.mocked(chatApi.sendMessage).mockResolvedValue(mockResponse)

    const result = await store.sendMessage('1', 'Hello', undefined)

    expect(result.success).toBe(true)
    expect(store.messages.length).toBe(2) // User message + assistant response
    expect(store.messages[0].content).toBe('Hello')
    expect(store.messages[1].content).toBe('Response message')
    expect(store.activeConversationId).toBe('1')
  })

  it('should clear messages', () => {
    const store = useChatStore()
    store.messages = [
      { id: '1', conversation_id: '1', role: 'user', content: 'Hello', created_at: '2024-01-01' }
    ]
    store.activeConversationId = '1'

    store.clearMessages()

    expect(store.messages).toEqual([])
    expect(store.activeConversationId).toBe(null)
  })
})

