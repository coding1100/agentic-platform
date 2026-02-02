<template>
  <div class="topic-review">
    <div class="view-card">
      <h2>Topic Review 📚</h2>
      <p class="view-description">{{ reviewTopic ? `Reviewing: ${reviewTopic}` : 'Deep dive into topics you need to master.' }}</p>
      
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-text">Generating topic review...</p>
        <p class="loading-subtext">Creating comprehensive study materials for {{ reviewTopic || 'your selected topic' }}</p>
      </div>

      <!-- No Topic Selected -->
      <div v-else-if="!reviewTopic && !reviewContent" class="empty-state">
        <div class="empty-icon">📖</div>
        <h3>No Topic Selected</h3>
        <p>Go to Weak Areas to select a topic for in-depth review.</p>
        <button @click="handleGoToWeakAreas" class="btn-primary">View Weak Areas</button>
      </div>

      <!-- Review Content -->
      <div v-else-if="reviewContent" class="review-content">
        <div class="formatted-review" v-html="formattedReview"></div>
        
        <!-- Key Concepts Summary -->
        <div v-if="keyConcepts.length > 0" class="key-concepts">
          <h3>🔑 Key Concepts</h3>
          <div class="concepts-grid">
            <div v-for="(concept, index) in keyConcepts" :key="index" class="concept-card">
              <span class="concept-number">{{ index + 1 }}</span>
              <span class="concept-text">{{ concept }}</span>
            </div>
          </div>
        </div>

        <!-- Actionable Study Items -->
        <div v-if="actionableItems.length > 0" class="actionables-section">
          <h3>📋 Actionable Study Items</h3>
          <div class="actionables-list">
            <div v-for="(item, index) in actionableItems" :key="index" class="actionable-item">
              <div class="actionable-header">
                <span class="actionable-icon">{{ getActionIcon(item.type) }}</span>
                <div class="actionable-content">
                  <div class="actionable-title">{{ item.title }}</div>
                  <div v-if="item.description" class="actionable-description">{{ item.description }}</div>
                  <div v-if="item.subtasks && item.subtasks.length > 0" class="actionable-subtasks">
                    <div v-for="(subtask, subIdx) in item.subtasks" :key="subIdx" class="subtask-item">
                      <span class="subtask-bullet">•</span>
                      <span>{{ subtask }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Re-attempt Quiz Button -->
        <div class="review-actions">
          <button @click="handleReattemptQuiz" class="btn-reattempt">
            <span class="btn-icon">🔄</span>
            <span>Re-attempt Practice Quiz</span>
          </button>
        </div>

        <div class="action-buttons">
          <button @click="refreshReview" class="btn-refresh" :disabled="isLoading">
            🔄 Regenerate Review
          </button>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <p>{{ error }}</p>
        <button @click="loadTopicReview" class="btn-primary">Try Again</button>
      </div>

      <div class="view-actions">
        <button @click="handleBack" class="btn-secondary">← Back to Weak Areas</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useExamPrepStore } from '@/stores/examPrep'
import { useChatStore } from '@/stores/chat'
import { sanitizeHtml } from '@/utils/sanitizeHtml'

const emit = defineEmits<{
  complete: []
}>()

const props = defineProps<{
  topic?: string
}>()

const route = useRoute()
const examPrepStore = useExamPrepStore()
const chatStore = useChatStore()

const agentId = route.params.agentId as string

const isLoading = ref(false)
const error = ref<string | null>(null)
const reviewContent = ref('')
const reviewTopic = ref(props.topic || '')
const isMounted = ref(true)
const pollingAborted = ref(false)

interface ActionableItem {
  type: 'review' | 'practice' | 'memorize' | 'focus' | 'checklist'
  title: string
  description?: string
  subtasks?: string[]
}

const keyConcepts = computed(() => {
  if (!reviewContent.value) return []
  
  const concepts: string[] = []
  // Extract key concepts from the content
  const keyConceptsMatch = reviewContent.value.match(/Key (?:Concepts?|Points?|Ideas?)[:\s]*\n([\s\S]*?)(?=\n##|\n\*\*|$)/i)
  
  if (keyConceptsMatch) {
    const lines = keyConceptsMatch[1].match(/[-•*]\s*(.+)/g)
    if (lines) {
      lines.slice(0, 6).forEach(line => {
        const cleaned = line.replace(/^[-•*]\s*/, '').trim()
        if (cleaned && cleaned.length > 5) {
          concepts.push(cleaned)
        }
      })
    }
  }
  
  // If no concepts found, try to extract from numbered list
  if (concepts.length === 0) {
    const numberedMatch = reviewContent.value.match(/\d+\.\s+([^\n]+)/g)
    if (numberedMatch) {
      numberedMatch.slice(0, 6).forEach(line => {
        const cleaned = line.replace(/^\d+\.\s+/, '').trim()
        if (cleaned && cleaned.length > 5 && cleaned.length < 150) {
          concepts.push(cleaned)
        }
      })
    }
  }
  
  return concepts
})

const actionableItems = computed((): ActionableItem[] => {
  if (!reviewContent.value) return []
  
  const items: ActionableItem[] = []
  
  // Try to find actionable items section
  const actionablesSection = reviewContent.value.match(/Actionable (?:Study )?Items?[:\s]*\n([\s\S]*?)(?=\n##|$)/i)
  
  if (actionablesSection) {
    const content = actionablesSection[1]
    
    // Extract immediate actions
    const immediateMatch = content.match(/Immediate Actions?[:\s]*\n([\s\S]*?)(?=\n###|$)/i)
    if (immediateMatch) {
      const lines = immediateMatch[1].split('\n').filter(line => line.trim())
      lines.forEach(line => {
        const match = line.match(/^\d+\.\s*\*\*([^*]+):\*\*\s*(.+)$/i) || line.match(/^\d+\.\s*(.+)$/i)
        if (match) {
          const title = match[1] || match[2]
          const description = match[2] && match[1] ? match[2] : undefined
          const type = title.toLowerCase().includes('review') ? 'review' :
                      title.toLowerCase().includes('practice') ? 'practice' :
                      title.toLowerCase().includes('memorize') ? 'memorize' : 'focus'
          items.push({ type, title: title.trim(), description: description?.trim() })
        }
      })
    }
    
    // Extract study tasks
    const tasksMatch = content.match(/Study Tasks?[:\s]*\n([\s\S]*?)(?=\n###|$)/i)
    if (tasksMatch) {
      const taskBlocks = tasksMatch[1].split(/\d+\.\s*\*\*Focus Area:/i).filter(block => block.trim())
      taskBlocks.forEach(block => {
        const lines = block.split('\n').filter(line => line.trim())
        if (lines.length > 0) {
          const title = lines[0].replace(/\*\*/g, '').trim()
          const subtasks: string[] = []
          let description = ''
          
          for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim()
            if (line.match(/^[-•*]\s*/)) {
              subtasks.push(line.replace(/^[-•*]\s*/, '').trim())
            } else if (line.match(/^\*\*Action:\*\*/i)) {
              description = line.replace(/^\*\*Action:\*\*/i, '').trim()
            } else if (line && !line.match(/^\*\*(Resources?|Time):\*\*/i)) {
              if (!description) description = line
            }
          }
          
          items.push({
            type: 'focus',
            title: `Focus Area: ${title}`,
            description: description || undefined,
            subtasks: subtasks.length > 0 ? subtasks : undefined
          })
        }
      })
    }
    
    // Extract checklist items
    const checklistMatch = content.match(/Preparation Checklist[:\s]*\n([\s\S]*?)(?=\n##|$)/i)
    if (checklistMatch) {
      const lines = checklistMatch[1].split('\n').filter(line => line.trim() && line.includes('['))
      lines.forEach(line => {
        const match = line.match(/\[[ x]\]\s*(.+)$/i)
        if (match) {
          items.push({
            type: 'checklist',
            title: match[1].trim()
          })
        }
      })
    }
  }
  
  // Fallback: extract from "Next Steps" or similar sections
  if (items.length === 0) {
    const nextStepsMatch = reviewContent.value.match(/(?:Next Steps|Recommended Study Sequence|Action Plan)[:\s]*\n([\s\S]*?)(?=\n##|$)/i)
    if (nextStepsMatch) {
      const lines = nextStepsMatch[1].split('\n').filter(line => line.trim())
      lines.forEach((line, index) => {
        const match = line.match(/^\d+\.\s*(.+)$/i) || line.match(/^[-•*]\s*(.+)$/i)
        if (match) {
          items.push({
            type: 'focus',
            title: match[1].trim()
          })
        }
      })
    }
  }
  
  return items.slice(0, 8) // Limit to 8 items
})


const formattedReview = computed(() => {
  if (!reviewContent.value) return ''
  
  let html = reviewContent.value
  
  // Convert markdown headers - handle numbered sections (#### 1. Title)
  html = html.replace(/^#### (\d+)\. (.+)$/gm, '<h4 class="review-h4 numbered-section"><span class="section-number">$1.</span> $2</h4>')
  html = html.replace(/^#### (.+)$/gm, '<h4 class="review-h4">$1</h4>')
  html = html.replace(/^### (.+)$/gm, '<h4 class="review-h4">$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3 class="review-h3">$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2 class="review-h2">$1</h2>')
  
  // Handle concept definitions (Concept Name: Definition)
  html = html.replace(/^\*\*([^*:]+):\*\*\s*(.+)$/gm, '<div class="concept-definition"><strong class="concept-title">$1:</strong> <span class="concept-desc">$2</span></div>')
  
  // Bold text (but not if already in concept definition)
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // Italic text
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  
  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="code-block"><code>$2</code></pre>')
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
  
  // Enhanced list formatting - handle bullet points with better spacing
  html = html.replace(/^- (.+)$/gm, '<li class="list-item">$1</li>')
  html = html.replace(/^(\d+)\. (.+)$/gm, '<li class="numbered-item"><span class="num">$1.</span> $2</li>')
  
  // Wrap consecutive li elements in ul
  html = html.replace(/(<li[^>]*>[\s\S]*?<\/li>)\n(?!<li)/g, '$1</ul>\n')
  html = html.replace(/(?<!<\/ul>\n)(<li[^>]*>)/g, '<ul class="review-list">$1')
  
  // Handle key points sections
  html = html.replace(/\*\*Key Points?:\*\*/gi, '<div class="key-points-header"><strong>Key Points:</strong></div>')
  
  // Handle definitions and descriptions
  html = html.replace(/\*\*Definition:\*\*/gi, '<div class="definition-label"><strong>Definition:</strong></div>')
  html = html.replace(/\*\*When to Use:\*\*/gi, '<div class="definition-label"><strong>When to Use:</strong></div>')
  html = html.replace(/\*\*Example:\*\*/gi, '<div class="definition-label"><strong>Example:</strong></div>')
  
  // Paragraphs with better spacing
  html = html.replace(/\n\n+/g, '</p><p class="review-paragraph">')
  html = '<p class="review-paragraph">' + html + '</p>'
  
  // Clean up empty paragraphs and fix structure
  html = html.replace(/<p[^>]*>\s*<\/p>/g, '')
  html = html.replace(/<p[^>]*>\s*<(h[234]|ul|pre|div)/g, '<$1')
  html = html.replace(/<\/(h[234]|ul|pre|div)>\s*<\/p>/g, '</$1>')
  
  // Highlight important terms
  html = html.replace(/\b(Important|Note|Remember|Key|Tip|Warning):/gi, '<span class="highlight">$1:</span>')
  
  // Add spacing after headers
  html = html.replace(/(<\/h[234]>)</g, '$1\n')
  
  return sanitizeHtml(html)
})

async function loadTopicReview() {
  if (!agentId) {
    error.value = 'No agent ID found. Please start from the beginning.'
    return
  }

  if (!reviewTopic.value) {
    error.value = 'No topic selected for review.'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const examInfo = examPrepStore.examInfo
    
    // Direct tool call without preambles or questions
    const message = `Use the generate_topic_review tool with:
- topic: "${reviewTopic.value}"
- difficulty: "${examInfo.currentLevel || 'medium'}"
- review_type: "comprehensive"`

    const result = await chatStore.sendMessage(agentId, message, examPrepStore.conversationId || undefined)
    
    // Update conversation ID if a new one was created
    if (result.success && result.response?.conversation_id) {
      examPrepStore.setConversationId(result.response.conversation_id)
    }
    
    // Wait and poll for response
    await pollForReview()
    
  } catch (err) {
    console.error('Error loading topic review:', err)
    error.value = 'Failed to generate topic review. Please try again.'
  } finally {
    isLoading.value = false
  }
}

async function pollForReview(maxAttempts = 12) {
  pollingAborted.value = false
  const INITIAL_DELAY = 5000 // 5 seconds initial delay
  const MIN_FETCH_INTERVAL = 6000 // 6 seconds minimum between fetches
  const MAX_DELAY = 10000 // 10 seconds maximum delay
  
  // Initial delay before first fetch
  await new Promise(resolve => setTimeout(resolve, INITIAL_DELAY))
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    // Check if component is still mounted and polling not aborted
    if (!isMounted.value || pollingAborted.value) {
      return
    }
    
    // Exponential backoff: start with 6s, increase gradually
    const delay = Math.min(MIN_FETCH_INTERVAL + (attempt * 500), MAX_DELAY)
    if (attempt > 0) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }
    
    // Check again after delay
    if (!isMounted.value || pollingAborted.value) {
      return
    }
    
    if (examPrepStore.conversationId) {
      try {
        // Only force fetch on first attempt
        await chatStore.fetchConversation(examPrepStore.conversationId, attempt === 0)
        
        const messages = chatStore.messages
        const assistantMessages = messages
          .filter(m => m.role === 'assistant' && m.content && m.content.trim().length > 300)
          .reverse()
        
        for (const message of assistantMessages) {
          const content = message.content.trim()
          
          // Check if this looks like a topic review
          if (
            content.includes('Topic Review') ||
            (content.includes('Overview') && (content.includes('Key Concept') || content.includes('Concept'))) ||
            (content.includes(reviewTopic.value) && content.length > 500) ||
            (content.includes('Example') && content.includes('Practice')) ||
            (content.includes('Worked Examples') && content.includes('Practice Questions'))
          ) {
            reviewContent.value = content
            return
          }
        }
      } catch (err) {
        console.error('Error fetching conversation:', err)
        // On error, wait longer before retrying
        if (attempt < maxAttempts - 1) {
          await new Promise(resolve => setTimeout(resolve, MAX_DELAY))
        }
      }
    }
  }
  
  // If no review found, show error
  if (isMounted.value && !reviewContent.value) {
    error.value = 'Could not generate topic review. Please try again.'
  }
}

async function refreshReview() {
  reviewContent.value = ''
  await loadTopicReview()
}

function handleGoToWeakAreas() {
  examPrepStore.setStep('weak-areas')
}

function handleBack() {
  examPrepStore.setStep('weak-areas')
}

function handleReattemptQuiz() {
  // Navigate back to practice exam with context about the topic reviewed
  examPrepStore.setStep('practice-exam')
  // The practice exam will use the existing conversation context
}

function getActionIcon(type: string): string {
  switch (type) {
    case 'review':
      return '📖'
    case 'practice':
      return '✏️'
    case 'memorize':
      return '🧠'
    case 'focus':
      return '🎯'
    case 'checklist':
      return '✅'
    default:
      return '📋'
  }
}


// Watch for topic changes from props
watch(() => props.topic, (newTopic) => {
  if (newTopic && newTopic !== reviewTopic.value) {
    reviewTopic.value = newTopic
    reviewContent.value = ''
    loadTopicReview()
  }
})

onMounted(() => {
  isMounted.value = true
  pollingAborted.value = false
  
  // Check if we have a topic to review
  if (props.topic) {
    reviewTopic.value = props.topic
  }
  
  // If we have a topic but no content, load it
  if (reviewTopic.value && !reviewContent.value) {
    loadTopicReview()
  }
})

onUnmounted(() => {
  isMounted.value = false
  pollingAborted.value = true
})
</script>

<style scoped>
.topic-review {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  padding: 20px 0;
}

.view-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 900px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h2 {
  color: white;
  font-size: 28px;
  margin: 0 0 12px 0;
  font-weight: 700;
  text-align: center;
}

.view-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  text-align: center;
  margin-bottom: 32px;
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: #64ffda;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: white;
  font-size: 18px;
  margin-top: 20px;
  font-weight: 600;
}

.loading-subtext {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  margin-top: 8px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  color: white;
  font-size: 24px;
  margin: 0 0 12px 0;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  margin-bottom: 24px;
}

/* Error State */
.error-state {
  text-align: center;
  padding: 40px 20px;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.error-state p {
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 20px;
}

/* Review Content */
.review-content {
  margin-bottom: 24px;
}

.formatted-review {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 24px;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.9;
  max-height: 600px;
  overflow-y: auto;
  font-size: 15px;
}

.formatted-review::-webkit-scrollbar {
  width: 8px;
}

.formatted-review::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.formatted-review::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.formatted-review :deep(h2.review-h2) {
  color: #64ffda;
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 24px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(100, 255, 218, 0.3);
  line-height: 1.4;
}

.formatted-review :deep(h3.review-h3) {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 32px 0 16px 0;
  line-height: 1.4;
}

.formatted-review :deep(h4.review-h4) {
  color: rgba(255, 255, 255, 0.98);
  font-size: 18px;
  font-weight: 600;
  margin: 24px 0 12px 0;
  line-height: 1.5;
}

.formatted-review :deep(h4.review-h4.numbered-section) {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 28px 0 16px 0;
  padding: 16px;
  background: rgba(100, 255, 218, 0.1);
  border-left: 4px solid #64ffda;
  border-radius: 8px;
}

.formatted-review :deep(.section-number) {
  color: #64ffda;
  font-weight: 700;
  font-size: 20px;
  min-width: 32px;
}

.formatted-review :deep(ul.review-list) {
  margin: 16px 0;
  padding-left: 24px;
  list-style: none;
}

.formatted-review :deep(li.list-item) {
  margin: 10px 0;
  color: rgba(255, 255, 255, 0.92);
  padding-left: 8px;
  position: relative;
  line-height: 1.7;
}

.formatted-review :deep(li.list-item::before) {
  content: "•";
  color: #64ffda;
  font-weight: bold;
  position: absolute;
  left: -20px;
  font-size: 18px;
}

.formatted-review :deep(li.numbered-item) {
  margin: 12px 0;
  color: rgba(255, 255, 255, 0.92);
  padding-left: 8px;
  line-height: 1.7;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.formatted-review :deep(li.numbered-item .num) {
  color: #64ffda;
  font-weight: 600;
  min-width: 24px;
}

.formatted-review :deep(.code-block) {
  background: rgba(0, 0, 0, 0.4);
  border-radius: 8px;
  padding: 16px;
  overflow-x: auto;
  margin: 12px 0;
}

.formatted-review :deep(.code-block code) {
  color: #64ffda;
  font-family: 'Fira Code', monospace;
  font-size: 14px;
}

.formatted-review :deep(.inline-code) {
  background: rgba(100, 255, 218, 0.15);
  color: #64ffda;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
}

.formatted-review :deep(.highlight) {
  color: #ffce54;
  font-weight: 600;
  background: rgba(255, 206, 84, 0.15);
  padding: 2px 6px;
  border-radius: 4px;
}

.formatted-review :deep(.review-paragraph) {
  margin: 16px 0;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.9);
}

.formatted-review :deep(.concept-definition) {
  background: rgba(100, 255, 218, 0.08);
  border-left: 3px solid #64ffda;
  padding: 14px 18px;
  margin: 16px 0;
  border-radius: 8px;
  line-height: 1.7;
}

.formatted-review :deep(.concept-title) {
  color: #64ffda;
  font-size: 16px;
  font-weight: 600;
  display: block;
  margin-bottom: 6px;
}

.formatted-review :deep(.concept-desc) {
  color: rgba(255, 255, 255, 0.9);
  display: block;
}

.formatted-review :deep(.key-points-header) {
  color: #64ffda;
  font-weight: 600;
  font-size: 16px;
  margin: 20px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(100, 255, 218, 0.2);
}

.formatted-review :deep(.definition-label) {
  color: #64ffda;
  font-weight: 600;
  margin: 16px 0 8px 0;
  font-size: 15px;
}

.formatted-review :deep(strong) {
  color: rgba(255, 255, 255, 0.98);
  font-weight: 600;
}

.formatted-review :deep(em) {
  color: rgba(255, 255, 255, 0.85);
  font-style: italic;
}

/* Key Concepts */
.key-concepts {
  margin-bottom: 24px;
}

.key-concepts h3 {
  color: white;
  font-size: 18px;
  margin: 0 0 16px 0;
}

.concepts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.concept-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: rgba(100, 255, 218, 0.1);
  border: 1px solid rgba(100, 255, 218, 0.2);
  border-radius: 12px;
  padding: 16px;
}

.concept-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: rgba(100, 255, 218, 0.2);
  color: #64ffda;
  border-radius: 50%;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.concept-text {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  line-height: 1.5;
}

/* Practice Section */
.practice-section {
  margin-bottom: 32px;
}

.practice-section h3 {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 24px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(100, 255, 218, 0.3);
}

.practice-question-card {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.practice-question-card:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(100, 255, 218, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.question-header {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.question-number {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 40px;
  background: linear-gradient(135deg, rgba(100, 255, 218, 0.2), rgba(100, 255, 218, 0.1));
  border: 2px solid #64ffda;
  border-radius: 50%;
  color: #64ffda;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
}

.question-content {
  flex: 1;
}

.question-text {
  color: white;
  font-weight: 500;
  font-size: 16px;
  line-height: 1.7;
  margin-bottom: 16px;
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.option-item {
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 15px;
  transition: all 0.2s ease;
}

.option-item:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(100, 255, 218, 0.3);
}

.option-item.is-answer {
  background: rgba(76, 175, 80, 0.2);
  border-color: rgba(76, 175, 80, 0.5);
  color: #4caf50;
  font-weight: 600;
}

.answer-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 2px solid rgba(100, 255, 218, 0.2);
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 14px 18px;
  background: rgba(76, 175, 80, 0.15);
  border-left: 4px solid #4caf50;
  border-radius: 8px;
}

.answer-label {
  color: #4caf50;
  font-weight: 700;
  font-size: 16px;
}

.answer-value {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.solution-steps {
  margin-top: 16px;
  padding: 18px;
  background: rgba(100, 255, 218, 0.08);
  border-left: 4px solid #64ffda;
  border-radius: 8px;
}

.solution-label {
  color: #64ffda;
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 12px;
}

.solution-content {
  color: rgba(255, 255, 255, 0.92);
  font-size: 15px;
  line-height: 1.9;
  font-family: 'Courier New', 'Consolas', monospace;
}

.solution-step {
  margin: 10px 0;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  border-left: 3px solid rgba(100, 255, 218, 0.5);
}

.solution-step .step-paren {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 400;
}

.solution-step .step-content {
  color: rgba(255, 255, 255, 0.95);
}

.solution-content .math-expr {
  color: #64ffda;
  font-weight: 600;
  background: rgba(100, 255, 218, 0.15);
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'Courier New', 'Consolas', monospace;
  display: inline-block;
  margin: 2px 0;
}

.solution-content .step-arrow {
  color: #64ffda;
  font-weight: 700;
  margin: 0 10px;
  font-size: 20px;
  display: inline-block;
}

.solution-content .math-number {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.solution-content .variable-assign {
  color: #ffce54;
  font-weight: 600;
  background: rgba(255, 206, 84, 0.15);
  padding: 2px 6px;
  border-radius: 4px;
}

.solution-content .calculation {
  color: rgba(255, 255, 255, 0.95);
  font-weight: 500;
}

.solution-content .calculation strong {
  color: #64ffda;
  font-weight: 700;
  font-size: 16px;
}

.solution-content .final-answer {
  color: #4caf50;
  font-weight: 700;
  font-size: 17px;
  display: inline-block;
  margin-top: 8px;
  padding: 10px 16px;
  background: rgba(76, 175, 80, 0.2);
  border: 2px solid rgba(76, 175, 80, 0.4);
  border-radius: 8px;
}

.solution-content .currency {
  color: #4caf50;
  font-weight: 600;
}

.solution-content .percentage {
  color: #64ffda;
  font-weight: 600;
}

.btn-show-answer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 20px;
  background: linear-gradient(135deg, rgba(100, 255, 218, 0.2), rgba(100, 255, 218, 0.1));
  border: 1px solid rgba(100, 255, 218, 0.4);
  border-radius: 10px;
  color: #64ffda;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 12px;
}

.btn-show-answer:hover {
  background: linear-gradient(135deg, rgba(100, 255, 218, 0.3), rgba(100, 255, 218, 0.2));
  border-color: rgba(100, 255, 218, 0.6);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(100, 255, 218, 0.2);
}

.btn-icon {
  font-size: 18px;
  transition: transform 0.3s ease;
}

.btn-show-answer:hover .btn-icon {
  transform: translateY(2px);
}

/* Actionables Section */
.actionables-section {
  margin-bottom: 32px;
}

.actionables-section h3 {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 24px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(100, 255, 218, 0.3);
}

.actionables-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.actionable-item {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 20px;
  transition: all 0.3s ease;
}

.actionable-item:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(100, 255, 218, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.actionable-header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.actionable-icon {
  font-size: 28px;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(100, 255, 218, 0.15);
  border-radius: 12px;
}

.actionable-content {
  flex: 1;
}

.actionable-title {
  color: white;
  font-weight: 600;
  font-size: 17px;
  margin-bottom: 8px;
  line-height: 1.5;
}

.actionable-description {
  color: rgba(255, 255, 255, 0.85);
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.actionable-subtasks {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.subtask-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 8px;
}

.subtask-bullet {
  color: #64ffda;
  font-weight: bold;
  font-size: 16px;
  flex-shrink: 0;
  margin-top: 2px;
}

/* Review Actions */
.review-actions {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 2px solid rgba(100, 255, 218, 0.2);
}

.btn-reattempt {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 32px;
  background: linear-gradient(135deg, #64ffda, #00bcd4);
  border: none;
  border-radius: 12px;
  color: #1a1a2e;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(100, 255, 218, 0.3);
}

.btn-reattempt:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(100, 255, 218, 0.5);
}

.btn-reattempt .btn-icon {
  font-size: 20px;
}

/* Action Buttons */
.action-buttons {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.btn-refresh {
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-refresh:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  padding: 14px 28px;
  background: linear-gradient(135deg, #64ffda, #00bcd4);
  border: none;
  border-radius: 12px;
  color: #1a1a2e;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(100, 255, 218, 0.4);
}

.view-actions {
  display: flex;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary {
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
}

@media (max-width: 640px) {
  .view-card {
    padding: 24px;
  }
  
  .concepts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
