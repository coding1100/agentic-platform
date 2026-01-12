import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAgentsStore } from '@/stores/agents'
import { agentsApi } from '@/services/api'

vi.mock('@/services/api', () => ({
  agentsApi: {
    list: vi.fn(),
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  }
}))

describe('Agents Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('should fetch agents', async () => {
    const store = useAgentsStore()
    const mockAgents = [
      { id: '1', name: 'Agent 1', system_prompt: 'Prompt 1', user_id: '1', model: 'gemini-2.5-pro', temperature: 0.7, created_at: '2024-01-01', updated_at: '2024-01-01' },
      { id: '2', name: 'Agent 2', system_prompt: 'Prompt 2', user_id: '1', model: 'gemini-2.5-pro', temperature: 0.7, created_at: '2024-01-01', updated_at: '2024-01-01' }
    ]

    vi.mocked(agentsApi.list).mockResolvedValue(mockAgents)

    await store.fetchAgents()

    expect(store.agents).toEqual(mockAgents)
    expect(store.loading).toBe(false)
  })

  it('should create agent', async () => {
    const store = useAgentsStore()
    const newAgent = {
      name: 'New Agent',
      system_prompt: 'New prompt',
      model: 'gemini-2.5-pro',
      temperature: 0.7
    }
    const createdAgent = { id: '1', ...newAgent, user_id: '1', created_at: '2024-01-01', updated_at: '2024-01-01' }

    vi.mocked(agentsApi.create).mockResolvedValue(createdAgent)

    const result = await store.createAgent(newAgent)

    expect(result.success).toBe(true)
    expect(store.agents).toContainEqual(createdAgent)
  })

  it('should update agent', async () => {
    const store = useAgentsStore()
    const existingAgent = { id: '1', name: 'Old Name', system_prompt: 'Prompt', user_id: '1', model: 'gemini-2.5-pro', temperature: 0.7, created_at: '2024-01-01', updated_at: '2024-01-01' }
    store.agents = [existingAgent]

    const updatedAgent = { ...existingAgent, name: 'New Name' }
    vi.mocked(agentsApi.update).mockResolvedValue(updatedAgent)

    const result = await store.updateAgent('1', { name: 'New Name' })

    expect(result.success).toBe(true)
    expect(store.agents[0].name).toBe('New Name')
  })

  it('should delete agent', async () => {
    const store = useAgentsStore()
    const agent = { id: '1', name: 'Agent', system_prompt: 'Prompt', user_id: '1', model: 'gemini-2.5-pro', temperature: 0.7, created_at: '2024-01-01', updated_at: '2024-01-01' }
    store.agents = [agent]

    vi.mocked(agentsApi.delete).mockResolvedValue(undefined)

    const result = await store.deleteAgent('1')

    expect(result.success).toBe(true)
    expect(store.agents).not.toContainEqual(agent)
  })

  it('should fetch single agent', async () => {
    const store = useAgentsStore()
    const agent = { id: '1', name: 'Agent', system_prompt: 'Prompt', user_id: '1', model: 'gemini-2.5-pro', temperature: 0.7, created_at: '2024-01-01', updated_at: '2024-01-01' }

    vi.mocked(agentsApi.get).mockResolvedValue(agent)

    const result = await store.fetchAgent('1')

    expect(result.success).toBe(true)
    expect(store.selectedAgent).toEqual(agent)
  })
})

