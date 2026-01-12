<template>
  <div class="topic-menu">
    <div class="menu-card">
      <h2>Choose a Topic to Learn 🎓</h2>
      <p class="menu-description">
        Select a {{ subjectName }} topic to start learning and practicing!
      </p>
      
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-topics">
        <div class="spinner"></div>
        <p>AI is preparing topics for you...</p>
      </div>
      
      <!-- Topics Grid -->
      <div v-else-if="topics.length > 0" class="topics-section">
        <div class="topics-grid">
          <button
            v-for="topic in topics"
            :key="topic.id"
            @click="selectTopic(topic)"
            class="topic-card"
          >
            <span class="topic-icon">{{ topic.icon }}</span>
            <span class="topic-name">{{ topic.name }}</span>
          </button>
        </div>
        
        <!-- Custom Topic Input -->
        <div class="custom-topic-section">
          <p class="custom-topic-label">Or enter your own topic:</p>
          <div class="custom-topic-input-container">
            <input
              v-model="customTopic"
              @keyup.enter="selectCustomTopic"
              type="text"
              placeholder="e.g., Algebra, Geometry, Calculus..."
              class="custom-topic-input"
            />
            <button
              @click="selectCustomTopic"
              :disabled="!customTopic.trim()"
              class="btn-custom-topic"
            >
              Start Learning
            </button>
          </div>
        </div>
      </div>
      
      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <p>{{ error }}</p>
        <button @click="fetchTopics" class="btn-retry">Retry</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTutorStore } from '@/stores/tutor'
import { useChatStore } from '@/stores/chat'
import { useRoute } from 'vue-router'

const emit = defineEmits<{
  selectTopic: [topic: { id: string; name: string; icon: string }]
}>()

const route = useRoute()
const tutorStore = useTutorStore()
const chatStore = useChatStore()

const topics = ref<Array<{ id: string; name: string; icon: string }>>([])
const isLoading = ref(false)
const error = ref<string | null>(null)
const customTopic = ref('')

const subjectName = computed(() => {
  // Capitalize first letter of subject
  const subject = tutorStore.selectedSubject || 'subject'
  return subject.charAt(0).toUpperCase() + subject.slice(1)
})

async function fetchTopics() {
  if (!tutorStore.selectedSubject) return
  
  isLoading.value = true
  error.value = null
  
  try {
    const agentId = route.params.agentId as string
    const subject = tutorStore.selectedSubject
    const proficiency = tutorStore.skillAssessment.proficiency || 'beginner'
    const childName = tutorStore.childDetails.name
    
    const message = `I need you to generate a list of ${subject} learning topics suitable for a ${proficiency} level student named ${childName}.

IMPORTANT: Please provide the topics in this EXACT format (one topic per line):
**Topic 1:** [Topic Name] [Emoji]
**Topic 2:** [Topic Name] [Emoji]
**Topic 3:** [Topic Name] [Emoji]
...continue for 8-12 topics...

CRITICAL FORMATTING RULES:
- Start IMMEDIATELY with **Topic 1:** - NO introductory text before it
- Each topic must be on its own line
- Each line must start with **Topic N:** where N is the number
- Include an appropriate emoji for each topic
- Generate 8-12 topics total
- NO other text, explanations, or conversational content - ONLY the topic list`

    const result = await chatStore.sendMessage(
      agentId,
      message,
      tutorStore.conversationId || undefined
    )

    if (result.success) {
      // Poll for the response
      await pollForTopics()
    } else {
      error.value = result.error || 'Failed to fetch topics'
      isLoading.value = false
    }
  } catch (err: any) {
    error.value = err.message || 'An error occurred while fetching topics'
    isLoading.value = false
  }
}

async function pollForTopics(maxAttempts = 15, delay = 1000) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (tutorStore.conversationId) {
      try {
        await chatStore.fetchConversation(tutorStore.conversationId)
        
        const newMessages = chatStore.messages
        if (newMessages.length > 0) {
          // Check the last few messages for topics
          const recentMessages = [...newMessages].reverse().slice(0, 5)
          
          for (const message of recentMessages) {
            if (message.role === 'assistant' && message.content) {
              const parsedTopics = parseTopicsFromResponse(message.content)
              if (parsedTopics.length > 0) {
                topics.value = parsedTopics
                tutorStore.setTopics(parsedTopics) // Store in global store
                isLoading.value = false
                return
              }
            }
          }
        }
      } catch (err) {
        console.error('Error fetching conversation:', err)
      }
    }
    
    const waitTime = Math.min(delay * Math.pow(1.2, attempt), 2500)
    await new Promise(resolve => setTimeout(resolve, waitTime))
  }
  
  isLoading.value = false
  error.value = 'Topics generation is taking longer than expected. Please try again.'
}

function parseTopicsFromResponse(content: string): Array<{ id: string; name: string; icon: string }> {
  const topics: Array<{ id: string; name: string; icon: string }> = []
  
  // Pattern: **Topic N:** Topic Name Emoji
  const topicPattern = /\*\*Topic\s+(\d+):\*\*\s*(.+?)(?=\*\*Topic\s+\d+:|$)/gis
  const lines = content.split('\n')
  
  for (const line of lines) {
    const match = line.match(/\*\*Topic\s+\d+:\*\*\s*(.+)/i)
    if (match) {
      const topicText = match[1].trim()
      // Extract emoji (usually at the end) and topic name
      const emojiMatch = topicText.match(/([\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}])/u)
      const emoji = emojiMatch ? emojiMatch[0] : '📚'
      const name = topicText.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim()
      
      if (name) {
        const id = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
        topics.push({ id, name, icon: emoji })
      }
    }
  }
  
  // Fallback: if no structured format, try to extract from list
  if (topics.length === 0) {
    const listPattern = /(?:^|\n)(?:\d+\.|\*|\-)\s*(.+?)(?=\n|$)/gi
    let match
    while ((match = listPattern.exec(content)) !== null) {
      const topicText = match[1].trim()
      const emojiMatch = topicText.match(/([\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}])/u)
      const emoji = emojiMatch ? emojiMatch[0] : '📚'
      const name = topicText.replace(/[\u{1F300}-\u{1F9FF}]|[\u{2600}-\u{26FF}]|[\u{2700}-\u{27BF}]/gu, '').trim()
      
      if (name && name.length > 2) {
        const id = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
        topics.push({ id, name, icon: emoji })
      }
    }
  }
  
  return topics.slice(0, 12) // Limit to 12 topics
}

function selectTopic(topic: { id: string; name: string; icon: string }) {
  // Set topic and immediately navigate - no continue button needed
  tutorStore.setSelectedTopic(topic)
  tutorStore.setStep('learning')
  // Emit for parent component if needed
  emit('selectTopic', topic)
}

function selectCustomTopic() {
  if (!customTopic.value.trim()) return
  
  const topicName = customTopic.value.trim()
  // Create a topic object from custom input
  const customTopicObj = {
    id: topicName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
    name: topicName,
    icon: '📚' // Default icon for custom topics
  }
  
  // Set topic and navigate
  tutorStore.setSelectedTopic(customTopicObj)
  tutorStore.setStep('learning')
  emit('selectTopic', customTopicObj)
}

onMounted(() => {
  fetchTopics()
})
</script>

<style scoped>
.topic-menu {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
}

.menu-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 800px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h2 {
  color: white;
  font-size: 28px;
  margin: 0 0 12px 0;
  font-weight: 700;
  text-align: center;
}

.menu-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  text-align: center;
  margin-bottom: 32px;
  line-height: 1.6;
}

.topics-section {
  width: 100%;
}

.topics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.topic-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 32px 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.topic-card:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.topic-icon {
  font-size: 48px;
}

.topic-name {
  color: white;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
}

.custom-topic-section {
  margin-top: 32px;
  padding-top: 32px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.custom-topic-label {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  text-align: center;
  margin-bottom: 16px;
  font-weight: 500;
}

.custom-topic-input-container {
  display: flex;
  gap: 12px;
  align-items: center;
}

.custom-topic-input {
  flex: 1;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  transition: all 0.3s ease;
}

.custom-topic-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.custom-topic-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.15);
}

.btn-custom-topic {
  padding: 14px 24px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-custom-topic:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-custom-topic:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-topics {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  gap: 20px;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-topics p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
}

.error-state {
  text-align: center;
  padding: 40px 20px;
  color: white;
}

.error-state p {
  margin-bottom: 20px;
  color: rgba(255, 255, 255, 0.9);
}

.btn-retry {
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-retry:hover {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
}
</style>

