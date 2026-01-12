import { streamText } from 'ai'
import { createOpenAI } from '@ai-sdk/openai'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8009'

// Custom provider that uses our backend streaming endpoint
export async function streamChatResponse(
  agentId: string,
  message: string,
  conversationId?: string | null
) {
  const token = localStorage.getItem('token')
  
  const response = await fetch(`${API_BASE_URL}/api/v1/chat/${agentId}/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId || null,
    }),
  })

  if (!response.ok) {
    throw new Error(`Streaming failed: ${response.statusText}`)
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('No reader available')
  }

  return {
    async *[Symbol.asyncIterator]() {
      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            
            if (data === '[DONE]') {
              return
            }
            
            try {
              const parsed = JSON.parse(data)
              
              // Handle error
              if (parsed.error) {
                throw new Error(parsed.error.message || 'Streaming error')
              }
              
              // Extract content from Vercel AI SDK format
              const content = parsed.choices?.[0]?.delta?.content
              if (content) {
                yield content
              }
            } catch (e) {
              // Skip invalid JSON
              continue
            }
          }
        }
      }
    }
  }
}

