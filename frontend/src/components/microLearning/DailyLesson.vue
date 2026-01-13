<template>
  <div class="daily-lesson">
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Generating your lesson...</p>
    </div>

    <div v-else-if="lessonContent" class="lesson-container">
      <div class="lesson-header">
        <div class="lesson-meta">
          <span class="lesson-time">{{ timeMinutes }} min</span>
          <span class="lesson-topic">{{ currentTopic }}</span>
        </div>
        <button @click="handleComplete" class="btn-complete">Mark Complete ✓</button>
      </div>

      <div class="lesson-content" v-html="formattedContent"></div>

      <div class="lesson-actions">
        <button @click="handleRequestQuiz" class="btn-primary">
          Test Your Understanding 🧪
        </button>
        <button @click="handleComplete" class="btn-secondary">
          Complete Lesson ✓
        </button>
      </div>
    </div>

    <div v-else class="lesson-start">
      <div class="start-card">
        <h2>Ready to Learn?</h2>
        <p>Choose your lesson duration:</p>
        <div class="time-selector">
          <button
            v-for="time in timeOptions"
            :key="time"
            @click="requestLesson(time)"
            class="time-btn"
          >
            {{ time }} min
          </button>
        </div>
        <p class="or-text">or</p>
        <button @click="requestLesson(timePerDay)" class="btn-primary btn-large">
          Start {{ timePerDay }}-Minute Lesson
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMicroLearningStore } from '@/stores/microLearning'
import { useChatStore } from '@/stores/chat'
import { useRoute } from 'vue-router'

const emit = defineEmits<{
  complete: []
  'request-quiz': []
}>()

const microLearningStore = useMicroLearningStore()
const chatStore = useChatStore()
const route = useRoute()

const isLoading = ref(false)
const lessonContent = ref('')
const currentTopic = ref('')
const timeMinutes = ref(10)

const timePerDay = computed(() => microLearningStore.onboardingData.timePerDay)
const timeOptions = [5, 10, 15]
const agentId = route.params.agentId as string

onMounted(() => {
  // Auto-start lesson if not already loaded
  if (!lessonContent.value && microLearningStore.conversationId) {
    requestLesson(timePerDay.value)
  }
})

function requestLesson(minutes: number) {
  isLoading.value = true
  timeMinutes.value = minutes
  
  // Select a random topic from user's interests
  const topics = microLearningStore.onboardingData.topics
  const topic = topics.length > 0 
    ? topics[Math.floor(Math.random() * topics.length)]
    : 'general knowledge'
  
  currentTopic.value = topic

  const message = `Generate a ${minutes}-minute micro-lesson about ${topic}. Use the generate_micro_lesson tool with topic="${topic}", time_minutes=${minutes}.`

  chatStore.sendMessage(agentId, message, microLearningStore.conversationId || undefined)
    .then(async (result) => {
      if (result.success) {
        // Update conversation ID if it was created
        if (result.response?.conversation_id) {
          microLearningStore.setConversationId(result.response.conversation_id)
        }
        // Wait a moment for the response to be generated, then start polling
        await new Promise(resolve => setTimeout(resolve, 2000))
        await pollForLesson()
      } else {
        isLoading.value = false
        lessonContent.value = 'Error generating lesson. Please try again.'
      }
    })
    .catch((error) => {
      console.error('Error sending message:', error)
      isLoading.value = false
      lessonContent.value = 'Error generating lesson. Please try again.'
    })
}

async function pollForLesson(maxAttempts = 30) {
  const checkedMessageIds = new Set<string>()
  let lastMessageCount = 0
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (microLearningStore.conversationId) {
      try {
        await chatStore.fetchConversation(microLearningStore.conversationId)
        
        const messages = chatStore.messages
        const currentMessageCount = messages.length
        
        // If we have new messages, reset checked IDs to re-check everything
        if (currentMessageCount > lastMessageCount) {
          checkedMessageIds.clear()
          lastMessageCount = currentMessageCount
        }
        
        if (messages.length > 0) {
          // Get all assistant messages with content, sorted by most recent first
          const assistantMessages = messages
            .filter(m => m.role === 'assistant' && m.content && m.content.trim().length > 50)
            .reverse() // Most recent first
          
          for (const message of assistantMessages) {
            // Skip if we've already checked this message
            if (checkedMessageIds.has(message.id)) {
              continue
            }
            
            const content = message.content.trim()
            
            // More flexible lesson detection patterns
            const isLesson = 
              // Explicit lesson markers
              content.toLowerCase().includes('micro-lesson') ||
              content.toLowerCase().includes('micro lesson') ||
              /lesson\s*:/i.test(content) ||
              // Lesson structure indicators
              content.includes('**Concept:**') || 
              content.includes('**Explanation:**') ||
              content.includes('**Example:**') ||
              content.includes('Key Takeaways') ||
              content.includes('Takeaways') ||
              // Markdown headers (check if content starts with headers)
              /^#{2,3}\s+/.test(content) ||
              // Structured content with markdown formatting
              (content.includes('**') && (content.includes('##') || content.includes('###'))) ||
              // Long formatted content (likely a lesson) - check for structured content
              (content.length > 300 && (
                (content.includes('**') && content.match(/\*\*/g)!.length > 5) || 
                content.includes('##') ||
                content.includes('###') ||
                (content.includes('*') && content.match(/\*/g)!.length > 3) ||
                content.includes('-')
              ))
            
            // Mark this message as checked
            checkedMessageIds.add(message.id)
            
            if (isLesson) {
              console.log('✅ Lesson detected!', { 
                messageId: message.id, 
                contentLength: content.length,
                preview: content.substring(0, 150),
                attempt: attempt + 1
              })
              lessonContent.value = content
              isLoading.value = false
              return
            }
          }
          
          // If no lesson found but we have a long assistant message, use it as fallback
          if (assistantMessages.length > 0) {
            const longestMessage = assistantMessages.reduce((longest, msg) => 
              msg.content.length > longest.content.length ? msg : longest
            )
            
            if (longestMessage.content.length > 500 && attempt >= 5) {
              console.log('⚠️ Using longest assistant message as fallback after 5 attempts', {
                contentLength: longestMessage.content.length,
                preview: longestMessage.content.substring(0, 150)
              })
              lessonContent.value = longestMessage.content
              isLoading.value = false
              return
            }
          }
        }
      } catch (error) {
        console.error('Error fetching conversation:', error)
      }
    }
    
    // Exponential backoff: start with 1.5s, increase gradually (max 3s)
    const delay = Math.min(1500 * Math.pow(1.1, attempt), 3000)
    if (attempt < maxAttempts - 1) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  // Final attempt: use the longest assistant message if available
  if (microLearningStore.conversationId) {
    try {
      await chatStore.fetchConversation(microLearningStore.conversationId)
      const messages = chatStore.messages
      const assistantMessages = messages
        .filter(m => m.role === 'assistant' && m.content && m.content.trim().length > 200)
      
      if (assistantMessages.length > 0) {
        const longestMessage = assistantMessages.reduce((longest, msg) => 
          msg.content.length > longest.content.length ? msg : longest
        )
        
        console.log('⚠️ Final fallback: Using longest assistant message', {
          contentLength: longestMessage.content.length,
          preview: longestMessage.content.substring(0, 150)
        })
        lessonContent.value = longestMessage.content
        isLoading.value = false
        return
      }
    } catch (error) {
      console.error('Final check error:', error)
    }
  }
  
  isLoading.value = false
  lessonContent.value = 'Lesson generation is taking longer than expected. Please try again.'
}

const formattedContent = computed(() => {
  if (!lessonContent.value) return ''
  
  let formatted = lessonContent.value
  
  // Remove any preamble/intro text before the actual lesson
  const lessonStartPatterns = [
    /(?:Here is|Here's|Here are).*?micro-lesson.*?\n/i,
    /^.*?---\s*\n/,
    /^.*?###\s*[🐍📚📖]/,
    /^.*?Excellent!.*?\n/i,
    /^.*?Let's dive.*?\n/i,
  ]
  
  for (const pattern of lessonStartPatterns) {
    const match = formatted.match(pattern)
    if (match) {
      formatted = formatted.substring(match[0].length).trim()
      break
    }
  }
  
  // Remove emoji from headers but keep them for styling
  formatted = formatted.replace(/^#{1,6}\s+[🐍📚📖💡✨🎯]\s*/gm, (match) => {
    return match.replace(/[🐍📚📖💡✨🎯]\s*/, '')
  })
  
  // Extract and protect code blocks first (before other formatting)
  const codeBlockPlaceholders: string[] = []
  formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    const language = lang || 'text'
    const placeholder = `__CODE_BLOCK_${codeBlockPlaceholders.length}__`
    codeBlockPlaceholders.push(`<pre class="code-block"><code class="language-${language}">${code.trim()}</code></pre>`)
    return placeholder
  })
  
  // Format inline code - detect special types for better styling
  // But skip if inside code block placeholders
  formatted = formatted.replace(/`([^`]+)`/g, (match, code) => {
    // Skip if this is part of a code block placeholder
    if (match.includes('__CODE_BLOCK_')) {
      return match
    }
    const trimmed = code.trim()
    // Detect operators (single character symbols)
    if (/^[+\-*/=<>!&|%^~]$/.test(trimmed)) {
      return `<code class="inline-code operator-code">${code}</code>`
    }
    // Detect data types
    if (/^(int|float|str|bool|list|dict|tuple|set|None)$/i.test(trimmed)) {
      return `<code class="inline-code type-code">${code}</code>`
    }
    // Detect keywords
    if (/^(def|class|import|from|return|if|else|elif|for|while|try|except|finally|with|as|in|is|and|or|not|True|False)$/i.test(trimmed)) {
      return `<code class="inline-code keyword-code">${code}</code>`
    }
    return `<code class="inline-code">${code}</code>`
  })
  
  // Format markdown headers (must be before bold/italic to avoid conflicts)
  // Skip lines that are code block placeholders
  formatted = formatted
    // H1 headers (#) - but not inside code blocks
    .replace(/^#\s+(.+)$/gm, (match, content) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return `<h1 class="lesson-title">${content}</h1>`
    })
    // H2 headers (##)
    .replace(/^##\s+(.+)$/gm, (match, content) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return `<h2 class="concept-header">${content}</h2>`
    })
    // H3 headers (###)
    .replace(/^###\s+(.+)$/gm, (match, content) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return `<h3 class="section-header">${content}</h3>`
    })
    // H4 headers (####)
    .replace(/^####\s+(.+)$/gm, (match, content) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return `<h4 class="subsection-header">${content}</h4>`
    })
  
  // Format special headers (like **Concept:**, **Explanation:**, etc.) - skip code blocks
  formatted = formatted
    .replace(/\*\*Concept:\*\*/g, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h2 class="concept-header">Concept</h2>'
    })
    .replace(/\*\*Explanation:\*\*/g, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h3 class="section-header">Explanation</h3>'
    })
    .replace(/\*\*Example:\*\*/g, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h3 class="section-header example-header">Example</h3>'
    })
    .replace(/\*\*Examples?:\*\*/g, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h3 class="section-header example-header">Examples</h3>'
    })
    .replace(/\*\*Key Takeaways?:\*\*/g, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h3 class="section-header takeaways-header">Key Takeaways</h3>'
    })
    .replace(/\*\*Takeaways?:\*\*/g, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h3 class="section-header takeaways-header">Takeaways</h3>'
    })
    .replace(/\*\*Summary:\*\*/g, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h3 class="section-header summary-header">Summary</h3>'
    })
    .replace(/\*\*Practice:\*\*/g, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h3 class="section-header practice-header">Practice</h3>'
    })
  
  // Format bold text (**text**) - must be after headers, but skip code blocks
  formatted = formatted.replace(/\*\*([^*\n]+)\*\*/g, (match, content) => {
    if (match.includes('__CODE_BLOCK_')) return match
    return `<strong>${content}</strong>`
  })
  
  // Format italic text (*text*) - careful not to match bold or list items, skip code blocks
  formatted = formatted.replace(/(?<!\*)\*([^*\n\*]+)\*(?!\*)/g, (match, content) => {
    if (match.includes('__CODE_BLOCK_')) return match
    return `<em>${content}</em>`
  })
  
  // Format horizontal rules - skip code blocks
  formatted = formatted.replace(/^---+\s*$/gm, (match) => {
    if (match.includes('__CODE_BLOCK_')) return match
    return '<hr class="lesson-divider">'
  })
  formatted = formatted.replace(/^___+\s*$/gm, (match) => {
    if (match.includes('__CODE_BLOCK_')) return match
    return '<hr class="lesson-divider">'
  })
  
  // Format blockquotes - skip code blocks
  formatted = formatted.replace(/^>\s+(.+)$/gm, (match, content) => {
    if (match.includes('__CODE_BLOCK_')) return match
    return `<blockquote class="lesson-quote">${content}</blockquote>`
  })
  
  // Format lists - handle both bullet and numbered lists
  // First, process numbered lists
  const lines = formatted.split('\n')
  const processedLines: string[] = []
  let inNumberedList = false
  let inBulletList = false
  let listItems: string[] = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    // Skip code block placeholders
    if (line.includes('__CODE_BLOCK_')) {
      processedLines.push(line)
      continue
    }
    const numberedMatch = line.match(/^(\d+)\.\s+(.+)$/)
    const bulletMatch = line.match(/^[•*\-]\s+(.+)$/)
    
    if (numberedMatch) {
      if (!inNumberedList) {
        if (inBulletList && listItems.length > 0) {
          processedLines.push(`<ul class="lesson-list bullet-list">${listItems.join('')}</ul>`)
          listItems = []
          inBulletList = false
        }
        inNumberedList = true
      }
      const content = numberedMatch[2].trim()
      // Process inline formatting in list items
      const processedContent = content
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
      listItems.push(`<li class="lesson-list-item">${processedContent}</li>`)
    } else if (bulletMatch) {
      if (!inBulletList) {
        if (inNumberedList && listItems.length > 0) {
          processedLines.push(`<ol class="lesson-list numbered-list">${listItems.join('')}</ol>`)
          listItems = []
          inNumberedList = false
        }
        inBulletList = true
      }
      const content = bulletMatch[1].trim()
      // Process inline formatting in list items
      const processedContent = content
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
      listItems.push(`<li class="lesson-list-item">${processedContent}</li>`)
    } else {
      // Close any open list
      if (inNumberedList && listItems.length > 0) {
        processedLines.push(`<ol class="lesson-list numbered-list">${listItems.join('')}</ol>`)
        listItems = []
        inNumberedList = false
      } else if (inBulletList && listItems.length > 0) {
        processedLines.push(`<ul class="lesson-list bullet-list">${listItems.join('')}</ul>`)
        listItems = []
        inBulletList = false
      }
      processedLines.push(line)
    }
  }
  
  // Close any remaining list
  if (inNumberedList && listItems.length > 0) {
    processedLines.push(`<ol class="lesson-list numbered-list">${listItems.join('')}</ol>`)
  } else if (inBulletList && listItems.length > 0) {
    processedLines.push(`<ul class="lesson-list bullet-list">${listItems.join('')}</ul>`)
  }
  
  formatted = processedLines.join('\n')
  
  // Restore code blocks before paragraph processing
  codeBlockPlaceholders.forEach((codeBlock, index) => {
    formatted = formatted.replace(`__CODE_BLOCK_${index}__`, codeBlock)
  })
  
  // Split into paragraphs (double newlines)
  const paragraphs = formatted.split(/\n\n+/)
  formatted = paragraphs
    .map(p => {
      p = p.trim()
      if (!p) return ''
      // Don't wrap headers, lists, code blocks, blockquotes, or HRs in <p>
      if (p.startsWith('<h') || 
          p.startsWith('<ul') || 
          p.startsWith('<ol') || 
          p.startsWith('<li') ||
          p.startsWith('<pre') ||
          (p.startsWith('<code') && p.includes('code-block')) ||
          p.startsWith('<blockquote') ||
          p.startsWith('<hr')) {
        return p
      }
      // Process remaining inline formatting in paragraphs (but skip already formatted code)
      p = p
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
        // Only replace backticks that aren't already inside <code> tags
        .replace(/(?<!<code[^>]*>)`([^`]+)`(?!<\/code>)/g, '<code class="inline-code">$1</code>')
      return '<p class="lesson-paragraph">' + p + '</p>'
    })
    .filter(p => p)
    .join('\n')
  
  // Clean up any remaining single newlines within paragraphs (convert to <br>)
  formatted = formatted.replace(/(<p[^>]*>)([\s\S]*?)(<\/p>)/g, (match, open, content, close) => {
    // Only convert newlines that aren't part of HTML tags
    const processed = content.replace(/\n(?!<[^>]+>)/g, '<br>')
    return open + processed + close
  })
  
  return formatted
})

function handleRequestQuiz() {
  emit('request-quiz')
}

function handleComplete() {
  // Mark lesson as complete
  const lesson: any = {
    id: Date.now().toString(),
    topic: currentTopic.value,
    content: lessonContent.value,
    timeMinutes: timeMinutes.value,
    difficulty: 'medium' as const,
    completed: true,
    completedAt: new Date()
  }
  
  microLearningStore.addLesson(lesson)
  microLearningStore.completeLesson(lesson.id)
  
  emit('complete')
}
</script>

<style scoped>
.daily-lesson {
  max-width: 900px;
  margin: 0 auto;
}

.loading-state {
  text-align: center;
  padding: 4rem 2rem;
  color: white;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.lesson-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.lesson-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.lesson-meta {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.lesson-time {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
}

.lesson-topic {
  color: #333;
  font-weight: 600;
  font-size: 1.1rem;
}

.btn-complete {
  background: #10b981;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-complete:hover {
  background: #059669;
}

.lesson-content {
  color: #333;
  line-height: 1.8;
  margin-bottom: 2rem;
  font-size: 1.05rem;
}

/* Headers */
.lesson-content :deep(.lesson-title) {
  color: #667eea;
  font-size: 2rem;
  font-weight: 700;
  margin: 2rem 0 1.5rem 0;
  line-height: 1.3;
  border-bottom: 3px solid #667eea;
  padding-bottom: 0.5rem;
}

.lesson-content :deep(.concept-header) {
  color: #667eea;
  font-size: 1.75rem;
  font-weight: 700;
  margin: 2rem 0 1rem 0;
  line-height: 1.4;
  padding-left: 0.5rem;
  border-left: 4px solid #667eea;
}

.lesson-content :deep(.section-header) {
  color: #764ba2;
  font-size: 1.4rem;
  font-weight: 600;
  margin: 1.75rem 0 0.75rem 0;
  line-height: 1.4;
}

.lesson-content :deep(.section-header.example-header) {
  color: #10b981;
  border-left: 4px solid #10b981;
  padding-left: 0.5rem;
}

.lesson-content :deep(.section-header.takeaways-header) {
  color: #f59e0b;
  border-left: 4px solid #f59e0b;
  padding-left: 0.5rem;
}

.lesson-content :deep(.section-header.summary-header) {
  color: #3b82f6;
  border-left: 4px solid #3b82f6;
  padding-left: 0.5rem;
}

.lesson-content :deep(.section-header.practice-header) {
  color: #8b5cf6;
  border-left: 4px solid #8b5cf6;
  padding-left: 0.5rem;
}

.lesson-content :deep(.subsection-header) {
  color: #555;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 1.5rem 0 0.75rem 0;
  line-height: 1.4;
}

/* Paragraphs */
.lesson-content :deep(.lesson-paragraph) {
  margin: 1rem 0;
  line-height: 1.8;
  color: #444;
  text-align: justify;
}

.lesson-content :deep(.lesson-paragraph:first-of-type) {
  margin-top: 0;
}

/* Text formatting */
.lesson-content :deep(strong) {
  color: #667eea;
  font-weight: 600;
}

.lesson-content :deep(em) {
  color: #764ba2;
  font-style: italic;
}

/* Lists */
.lesson-content :deep(.lesson-list) {
  margin: 1.25rem 0;
  padding-left: 0;
  list-style: none;
}

.lesson-content :deep(.bullet-list) {
  padding-left: 1.5rem;
}

.lesson-content :deep(.numbered-list) {
  padding-left: 1.5rem;
  counter-reset: list-counter;
}

.lesson-content :deep(.lesson-list-item) {
  margin: 0.75rem 0;
  padding: 0.5rem 0 0.5rem 2rem;
  position: relative;
  line-height: 1.7;
  color: #444;
}

.lesson-content :deep(.bullet-list .lesson-list-item::before) {
  content: '▸';
  position: absolute;
  left: 0.5rem;
  color: #667eea;
  font-weight: bold;
  font-size: 1.2rem;
}

.lesson-content :deep(.numbered-list .lesson-list-item) {
  counter-increment: list-counter;
  padding-left: 2.5rem;
}

.lesson-content :deep(.numbered-list .lesson-list-item::before) {
  content: counter(list-counter) '.';
  position: absolute;
  left: 0.5rem;
  color: #667eea;
  font-weight: 600;
  font-size: 1.1rem;
}

/* Code blocks - Enhanced with gradient and top border */
.lesson-content :deep(.code-block) {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #ffffff;
  padding: 1.5rem;
  border-radius: 12px;
  margin: 1.75rem 0;
  overflow-x: auto;
  font-family: 'Fira Code', 'Courier New', 'Monaco', 'Consolas', monospace;
  font-size: 0.95rem;
  line-height: 1.7;
  border: 2px solid #334155;
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  position: relative;
}

.lesson-content :deep(.code-block::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2, #10b981);
  border-radius: 12px 12px 0 0;
}

.lesson-content :deep(.code-block code) {
  background: transparent;
  color: #ffffff !important;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
  display: block;
  white-space: pre;
}

/* Ensure all text elements in code blocks are white */
.lesson-content :deep(.code-block *),
.lesson-content :deep(.code-block code *),
.lesson-content :deep(.code-block .keyword),
.lesson-content :deep(.code-block .string),
.lesson-content :deep(.code-block .number),
.lesson-content :deep(.code-block .function),
.lesson-content :deep(.code-block .comment),
.lesson-content :deep(.code-block .variable),
.lesson-content :deep(.code-block .operator) {
  color: #ffffff !important;
}

/* Inline code - Enhanced with better visual appeal */
.lesson-content :deep(.inline-code) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  color: #dc2626;
  padding: 0.4rem 0.7rem;
  border-radius: 6px;
  font-family: 'Fira Code', 'Courier New', 'Monaco', 'Consolas', monospace;
  font-size: 0.93em;
  font-weight: 600;
  border: 1.5px solid #e2e8f0;
  box-shadow: 
    0 2px 4px rgba(0, 0, 0, 0.06),
    inset 0 1px 2px rgba(255, 255, 255, 0.9),
    0 1px 0 rgba(255, 255, 255, 0.5);
  display: inline-block;
  line-height: 1.5;
  transition: all 0.2s ease;
  position: relative;
  letter-spacing: 0.3px;
  margin: 0 0.15rem;
  vertical-align: baseline;
}

.lesson-content :deep(.inline-code:hover) {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border-color: #cbd5e1;
  box-shadow: 
    0 3px 8px rgba(0, 0, 0, 0.12),
    inset 0 1px 2px rgba(255, 255, 255, 1),
    0 1px 0 rgba(255, 255, 255, 0.6);
  transform: translateY(-1px);
}

/* Special styling for single-character operators */
.lesson-content :deep(.inline-code:only-child) {
  min-width: 1.8rem;
  text-align: center;
  padding: 0.4rem 0.6rem;
}

/* Code within paragraphs and lists - better spacing */
.lesson-content :deep(p .inline-code),
.lesson-content :deep(li .inline-code),
.lesson-content :deep(strong .inline-code),
.lesson-content :deep(em .inline-code) {
  margin: 0 0.25rem;
  vertical-align: baseline;
}

/* Enhanced code block styling with scrollbar */
.lesson-content :deep(.code-block::-webkit-scrollbar) {
  height: 8px;
}

.lesson-content :deep(.code-block::-webkit-scrollbar-track) {
  background: #0f172a;
  border-radius: 4px;
}

.lesson-content :deep(.code-block::-webkit-scrollbar-thumb) {
  background: #475569;
  border-radius: 4px;
}

.lesson-content :deep(.code-block::-webkit-scrollbar-thumb:hover) {
  background: #64748b;
}

/* Code block syntax highlighting support */
.lesson-content :deep(.code-block .keyword) {
  color: #c792ea;
  font-weight: 600;
}

.lesson-content :deep(.code-block .string) {
  color: #c3e88d;
}

.lesson-content :deep(.code-block .number) {
  color: #f78c6c;
}

.lesson-content :deep(.code-block .function) {
  color: #82aaff;
}

.lesson-content :deep(.code-block .comment) {
  color: #546e7a;
  font-style: italic;
}

/* Special emphasis for code in headers */
.lesson-content :deep(h1 .inline-code),
.lesson-content :deep(h2 .inline-code),
.lesson-content :deep(h3 .inline-code),
.lesson-content :deep(h4 .inline-code) {
  font-size: 0.85em;
  padding: 0.3rem 0.6rem;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  border-color: #fcd34d;
}

/* Special styling for operator code */
.lesson-content :deep(.operator-code) {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  color: #92400e;
  border-color: #fcd34d;
  font-weight: 700;
  min-width: 1.8rem;
  text-align: center;
  padding: 0.4rem 0.6rem;
}

/* Special styling for type code */
.lesson-content :deep(.type-code) {
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  color: #991b1b;
  border-color: #fca5a5;
  font-weight: 600;
}

/* Special styling for keyword code */
.lesson-content :deep(.keyword-code) {
  background: linear-gradient(135deg, #ddd6fe 0%, #c4b5fd 100%);
  color: #5b21b6;
  border-color: #a78bfa;
  font-weight: 600;
}

/* Blockquotes */
.lesson-content :deep(.lesson-quote) {
  border-left: 4px solid #667eea;
  background: #f8f9fa;
  padding: 1rem 1.5rem;
  margin: 1.5rem 0;
  border-radius: 0 8px 8px 0;
  font-style: italic;
  color: #555;
  line-height: 1.7;
}

/* Horizontal rules */
.lesson-content :deep(.lesson-divider) {
  border: none;
  border-top: 2px solid #e2e8f0;
  margin: 2rem 0;
  background: none;
}

/* Spacing improvements */
.lesson-content :deep(h1 + p),
.lesson-content :deep(h2 + p),
.lesson-content :deep(h3 + p),
.lesson-content :deep(h4 + p) {
  margin-top: 0.5rem;
}

.lesson-content :deep(p + h2),
.lesson-content :deep(p + h3),
.lesson-content :deep(p + h4) {
  margin-top: 2rem;
}

.lesson-content :deep(ul + p),
.lesson-content :deep(ol + p),
.lesson-content :deep(p + ul),
.lesson-content :deep(p + ol) {
  margin-top: 1rem;
}

.lesson-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s;
}

.btn-primary:hover {
  transform: translateY(-2px);
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #f0f0f0;
}

.lesson-start {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.start-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 500px;
}

.start-card h2 {
  color: #333;
  margin-bottom: 1rem;
}

.time-selector {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin: 1.5rem 0;
}

.time-btn {
  background: white;
  border: 2px solid #e0e0e0;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.time-btn:hover {
  border-color: #667eea;
  background: #f0f0f0;
}

.or-text {
  color: #666;
  margin: 1rem 0;
}

.btn-large {
  width: 100%;
  padding: 1rem;
  font-size: 1.1rem;
}

@media (max-width: 768px) {
  .lesson-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .lesson-actions {
    flex-direction: column;
  }

  .time-selector {
    flex-direction: column;
  }
}
</style>

