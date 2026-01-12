import { defineStore } from 'pinia'
import { ref } from 'vue'
import { agentsApi } from '@/services/api'
import type { Agent } from '@/types'

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref<Agent[]>([])
  const selectedAgent = ref<Agent | null>(null)
  const loading = ref(false)

  async function fetchAgents() {
    loading.value = true
    try {
      agents.value = await agentsApi.list()
    } catch (error) {
      console.error('Failed to fetch agents:', error)
    } finally {
      loading.value = false
    }
  }

  async function createAgent(agentData: Partial<Agent>) {
    try {
      const newAgent = await agentsApi.create(agentData as any)
      agents.value.push(newAgent)
      return { success: true, agent: newAgent }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Failed to create agent' }
    }
  }

  async function updateAgent(agentId: string, agentData: Partial<Agent>) {
    try {
      const updatedAgent = await agentsApi.update(agentId, agentData as any)
      const index = agents.value.findIndex(a => a.id === agentId)
      if (index !== -1) {
        agents.value[index] = updatedAgent
      }
      if (selectedAgent.value?.id === agentId) {
        selectedAgent.value = updatedAgent
      }
      return { success: true, agent: updatedAgent }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Failed to update agent' }
    }
  }

  async function deleteAgent(agentId: string) {
    try {
      await agentsApi.delete(agentId)
      agents.value = agents.value.filter(a => a.id !== agentId)
      if (selectedAgent.value?.id === agentId) {
        selectedAgent.value = null
      }
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Failed to delete agent' }
    }
  }

  async function fetchAgent(agentId: string) {
    try {
      const agent = await agentsApi.get(agentId)
      selectedAgent.value = agent
      return { success: true, agent }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch agent' }
    }
  }

  function setSelectedAgent(agent: Agent | null) {
    selectedAgent.value = agent
  }

  return {
    agents,
    selectedAgent,
    loading,
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    fetchAgent,
    setSelectedAgent
  }
})

