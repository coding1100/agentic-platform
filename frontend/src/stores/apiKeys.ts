import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiKeysApi } from '@/services/api'
import type { ApiKey, ApiKeyCreate, ApiKeyUsageStats } from '@/types'

export const useApiKeysStore = defineStore('apiKeys', () => {
  const apiKeys = ref<ApiKey[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function fetchApiKeys() {
    isLoading.value = true
    error.value = null
    try {
      apiKeys.value = await apiKeysApi.list()
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch API keys'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createApiKey(data: ApiKeyCreate): Promise<ApiKey> {
    isLoading.value = true
    error.value = null
    try {
      const newKey = await apiKeysApi.create(data)
      await fetchApiKeys() // Refresh list
      return newKey
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create API key'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteApiKey(apiKeyId: string) {
    isLoading.value = true
    error.value = null
    try {
      await apiKeysApi.delete(apiKeyId)
      await fetchApiKeys() // Refresh list
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete API key'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function toggleApiKey(apiKeyId: string) {
    isLoading.value = true
    error.value = null
    try {
      await apiKeysApi.toggle(apiKeyId)
      await fetchApiKeys() // Refresh list
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to toggle API key'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getUsageStats(apiKeyId: string): Promise<ApiKeyUsageStats> {
    error.value = null
    try {
      return await apiKeysApi.getUsage(apiKeyId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch usage stats'
      throw err
    }
  }

  return {
    apiKeys,
    isLoading,
    error,
    fetchApiKeys,
    createApiKey,
    deleteApiKey,
    toggleApiKey,
    getUsageStats
  }
})

