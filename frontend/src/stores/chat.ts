import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi, conversationsApi } from '@/services/api'
import type { Message, Conversation } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const activeConversationId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const conversations = ref<Conversation[]>([])
  const loading = ref(false)
  const sending = ref(false)
  const lastFetchTime = ref<Record<string, number>>({}) // Track last fetch time per conversation
  const lastMessageCount = ref<Record<string, number>>({}) // Track last message count per conversation

  async function fetchConversations(agentId: string) {
    loading.value = true
    try {
      conversations.value = await conversationsApi.listByAgent(agentId)
    } catch (error) {
      console.error('Failed to fetch conversations:', error)
    } finally {
      loading.value = false
    }
  }

  async function fetchConversation(conversationId: string, force: boolean = false) {
    const now = Date.now()
    const lastFetch = lastFetchTime.value[conversationId] || 0
    const currentMessageCount = messages.value.length
    const lastCount = lastMessageCount.value[conversationId] || 0
    
    // Skip if we just fetched this conversation recently (within 5 seconds) and message count hasn't changed
    // unless force is true
    const MIN_FETCH_INTERVAL = 5000 // 5 seconds minimum between fetches
    if (!force && now - lastFetch < MIN_FETCH_INTERVAL && currentMessageCount === lastCount && activeConversationId.value === conversationId) {
      return { success: true, conversation: { id: conversationId, messages: messages.value } }
    }
    
    loading.value = true
    try {
      const conversation = await conversationsApi.get(conversationId)
      const newMessageCount = conversation.messages?.length || 0
      
      messages.value = conversation.messages || []
      activeConversationId.value = conversationId
      lastFetchTime.value[conversationId] = now
      lastMessageCount.value[conversationId] = newMessageCount
      
      return { success: true, conversation }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch conversation' }
    } finally {
      loading.value = false
    }
  }

  async function createConversation(agentId: string, title?: string) {
    try {
      const conversation = await conversationsApi.create({ agent_id: agentId, title })
      conversations.value.push(conversation)
      activeConversationId.value = conversation.id
      // Don't clear messages here - fetchConversation will load them including greeting
      return { success: true, conversation }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Failed to create conversation' }
    }
  }

  async function sendMessage(agentId: string, message: string, conversationId?: string) {
    sending.value = true
    try {
      const response = await chatApi.sendMessage(agentId, {
        conversation_id: conversationId || null,
        message
      })

      // Refetch the conversation to get all messages including greeting if it's a new conversation
      await fetchConversation(response.conversation_id, true)

      activeConversationId.value = response.conversation_id

      return { success: true, response }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Failed to send message' }
    } finally {
      sending.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    activeConversationId.value = null
  }

  return {
    activeConversationId,
    messages,
    conversations,
    loading,
    sending,
    fetchConversations,
    fetchConversation,
    createConversation,
    sendMessage,
    clearMessages
  }
})
