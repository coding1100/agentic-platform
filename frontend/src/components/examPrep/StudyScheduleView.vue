<template>
  <div class="study-schedule-view">
    <div class="view-card">
      <h2>Your Study Schedule 📅</h2>
      <p class="view-description">Your personalized study plan leading up to your exam.</p>
      
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Generating your study schedule...</p>
      </div>

      <div v-else-if="scheduleContent" class="schedule-content" v-html="formattedSchedule"></div>

      <div v-else class="no-schedule">
        <p>No study schedule available. Please set up your exam information first.</p>
        <button @click="generateSchedule" class="btn-primary">Generate Schedule</button>
      </div>

      <div class="view-actions">
        <button @click="handleBack" class="btn-secondary">← Back</button>
        <button @click="handleStartPractice" class="btn-primary">Start Practice Exam →</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useExamPrepStore } from '@/stores/examPrep'
import { useChatStore } from '@/stores/chat'
import { useRoute } from 'vue-router'
import { sanitizeHtml } from '@/utils/sanitizeHtml'

const emit = defineEmits<{
  complete: []
  'start-practice': []
}>()

const examPrepStore = useExamPrepStore()
const chatStore = useChatStore()
const route = useRoute()

const agentId = route.params.agentId as string
const isLoading = ref(false)
const scheduleContent = ref('')
const isMounted = ref(true)
const pollingAborted = ref(false)

onMounted(async () => {
  isMounted.value = true
  pollingAborted.value = false
  await loadSchedule()
})

onUnmounted(() => {
  isMounted.value = false
  pollingAborted.value = true
})

async function loadSchedule() {
  // Only fetch if we have a conversation ID and haven't loaded yet
  if (examPrepStore.conversationId && !scheduleContent.value) {
    try {
      await chatStore.fetchConversation(examPrepStore.conversationId)
      const messages = chatStore.messages
      
      // Find schedule message (check most recent first)
      const assistantMessages = messages
        .filter(m => m.role === 'assistant' && m.content)
        .reverse()
      
      const scheduleMessage = assistantMessages.find(m => {
        const content = m.content || ''
        return content.includes('Study Schedule') || 
               content.includes('Weekly Breakdown') ||
               content.includes('Schedule Overview') ||
               content.includes('Days Remaining') ||
               content.includes('Week 1') ||
               content.includes('Daily Goals') ||
               (content.includes('Exam Date') && content.includes('Days Remaining'))
      })
      
      if (scheduleMessage) {
        scheduleContent.value = scheduleMessage.content
      }
    } catch (error) {
      console.error('Error loading schedule:', error)
    }
  }
}

async function generateSchedule() {
  if (!examPrepStore.examInfo.examType) {
    alert('Please complete exam setup first.')
    return
  }

  isLoading.value = true
  const info = examPrepStore.examInfo
  
  // Direct tool call without preambles or questions
  const message = `Use the create_study_schedule tool with:
- exam_date: "${info.examDate}"
- subjects: "${info.subject}"
- hours_per_day: ${info.hoursPerDay}
- current_level: "${info.currentLevel}"`

  try {
    const result = await chatStore.sendMessage(agentId, message, examPrepStore.conversationId || undefined)
    if (result.success && result.response?.conversation_id) {
      examPrepStore.setConversationId(result.response.conversation_id)
    }
    
    // Wait for schedule generation (it can take time)
    await new Promise(resolve => setTimeout(resolve, 5000))
    
    // Poll for schedule with limited attempts
    await pollForSchedule()
  } catch (error) {
    console.error('Error generating schedule:', error)
    isLoading.value = false
  }
}

async function pollForSchedule(maxAttempts = 12) {
  pollingAborted.value = false
  const checkedMessageIds = new Set<string>()
  let lastMessageCount = 0
  const INITIAL_DELAY = 5000 // 5 seconds initial delay
  const MIN_FETCH_INTERVAL = 6000 // 6 seconds minimum between fetches
  const MAX_DELAY = 10000 // 10 seconds maximum delay
  
  // Initial delay before first fetch
  await new Promise(resolve => setTimeout(resolve, INITIAL_DELAY))
  
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    // Check if component is still mounted and polling not aborted
    if (!isMounted.value || pollingAborted.value) {
      isLoading.value = false
      return
    }
    
    if (examPrepStore.conversationId) {
      try {
        // Only force fetch on first attempt
        await chatStore.fetchConversation(examPrepStore.conversationId, attempt === 0)
        const messages = chatStore.messages
        const currentMessageCount = messages.length
        
        // Only re-check if we have new messages
        if (currentMessageCount > lastMessageCount) {
          checkedMessageIds.clear()
          lastMessageCount = currentMessageCount
        }
        
        const assistantMessages = messages
          .filter(m => m.role === 'assistant' && m.content && !checkedMessageIds.has(m.id))
          .reverse()
        
        for (const message of assistantMessages) {
          checkedMessageIds.add(message.id)
          
          const content = message.content || ''
          // Check for schedule indicators
          if (content.includes('Study Schedule') || 
              content.includes('Weekly Breakdown') ||
              content.includes('Schedule Overview') ||
              content.includes('Days Remaining') ||
              content.includes('Week 1') ||
              content.includes('Daily Goals') ||
              (content.includes('Exam Date') && content.includes('Days Remaining'))) {
            scheduleContent.value = content
            isLoading.value = false
            return
          }
        }
      } catch (error) {
        console.error('Error fetching conversation:', error)
        // On error, wait longer before retrying
        if (attempt < maxAttempts - 1) {
          await new Promise(resolve => setTimeout(resolve, MAX_DELAY))
        }
      }
    }
    
    // Exponential backoff: start with 6s, increase gradually
    const delay = Math.min(MIN_FETCH_INTERVAL + (attempt * 500), MAX_DELAY)
    if (attempt < maxAttempts - 1) {
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  if (isMounted.value) {
    isLoading.value = false
  }
}

const formattedSchedule = computed(() => {
  if (!scheduleContent.value) return ''
  
  let formatted = scheduleContent.value
  
  // Extract and protect code blocks first
  const codeBlockPlaceholders: string[] = []
  formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    const language = lang || 'text'
    const placeholder = `__CODE_BLOCK_${codeBlockPlaceholders.length}__`
    codeBlockPlaceholders.push(`<pre class="code-block"><code class="language-${language}">${code.trim()}</code></pre>`)
    return placeholder
  })
  
  // Format markdown headers
  formatted = formatted
    .replace(/^#\s+(.+)$/gm, (match, content) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return `<h1 class="schedule-title">${content}</h1>`
    })
    .replace(/^##\s+(.+)$/gm, (match, content) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return `<h2 class="schedule-phase">${content}</h2>`
    })
    .replace(/^###\s+(.+)$/gm, (match, content) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return `<h3 class="schedule-section">${content}</h3>`
    })
    .replace(/^####\s+(.+)$/gm, (match, content) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return `<h4 class="schedule-subsection">${content}</h4>`
    })
  
  // Format special schedule headers
  formatted = formatted
    .replace(/\*\*Phase\s+\d+:\*\*/gi, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return match.replace(/\*\*/g, '').replace(/^/, '<h2 class="schedule-phase">').replace(/$/, '</h2>')
    })
    .replace(/\*\*Schedule Overview:\*\*/gi, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h2 class="schedule-section">Schedule Overview</h2>'
    })
    .replace(/\*\*Weekly Breakdown:\*\*/gi, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h2 class="schedule-section">Weekly Breakdown</h2>'
    })
    .replace(/\*\*Practice Exam Schedule:\*\*/gi, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h2 class="schedule-section">Practice Exam Schedule</h2>'
    })
    .replace(/\*\*Milestones:\*\*/gi, (match) => {
      if (match.includes('__CODE_BLOCK_')) return match
      return '<h2 class="schedule-section">Milestones</h2>'
    })
  
  // Format bold text (**text**)
  formatted = formatted.replace(/\*\*([^*\n]+)\*\*/g, (match, content) => {
    if (match.includes('__CODE_BLOCK_')) return match
    // Don't format if it's already a header
    if (match.includes('<h')) return match
    return `<strong>${content}</strong>`
  })
  
  // Format italic text (*text*)
  formatted = formatted.replace(/(?<!\*)\*([^*\n\*]+)\*(?!\*)/g, (match, content) => {
    if (match.includes('__CODE_BLOCK_')) return match
    return `<em>${content}</em>`
  })
  
  // Format horizontal rules
  formatted = formatted.replace(/^---+\s*$/gm, (match) => {
    if (match.includes('__CODE_BLOCK_')) return match
    return '<hr class="schedule-divider">'
  })
  
  // Detect and format markdown tables
  const tableRegex = /(\|.+\|\n\|[:\s\-|]+\|\n(?:\|.+\|\n?)+)/g
  const tables: string[] = []
  formatted = formatted.replace(tableRegex, (match) => {
    const placeholder = `__TABLE_${tables.length}__`
    tables.push(match)
    return placeholder
  })
  
  // Process tables
  tables.forEach((table, index) => {
    const lines = table.trim().split('\n').filter(line => line.trim())
    if (lines.length < 2) return
    
    // Parse header
    const headerLine = lines[0]
    const separatorLine = lines[1]
    const headerCells = headerLine.split('|').map(cell => cell.trim()).filter(cell => cell)
    
    // Parse rows
    const rows: string[][] = []
    for (let i = 2; i < lines.length; i++) {
      const cells = lines[i].split('|').map(cell => cell.trim()).filter(cell => cell)
      if (cells.length > 0) {
        rows.push(cells)
      }
    }
    
    // Build HTML table
    let tableHtml = '<table class="schedule-table">'
    
    // Header
    tableHtml += '<thead><tr>'
    headerCells.forEach(cell => {
      tableHtml += `<th class="schedule-table-header">${cell}</th>`
    })
    tableHtml += '</tr></thead>'
    
    // Body
    tableHtml += '<tbody>'
    rows.forEach(row => {
      tableHtml += '<tr>'
      row.forEach((cell, cellIndex) => {
        // Format cell content
        let cellContent = cell
          .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
          .replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)(-|–|—)(Mon|Tue|Wed|Thu|Fri|Sat|Sun)?\b/gi, '<span class="schedule-day">$&</span>')
          .replace(/\b(\d+)\s*(hour|hours|hr|hrs|minute|minutes|min|mins)\s*\/?\s*day\b/gi, '<span class="schedule-time">$&</span>')
        
        tableHtml += `<td class="schedule-table-cell">${cellContent}</td>`
      })
      tableHtml += '</tr>'
    })
    tableHtml += '</tbody></table>'
    
    formatted = formatted.replace(`__TABLE_${index}__`, tableHtml)
  })
  
  // Also detect table-like structures (lines with | separators but not markdown format)
  const tableLikeRegex = /^(\|.+\|)\s*$/gm
  const tableLikeMatches: Array<{ start: number, end: number, lines: string[] }> = []
  const allLines = formatted.split('\n')
  
  let currentTable: string[] = []
  let tableStart = -1
  
  for (let i = 0; i < allLines.length; i++) {
    const line = allLines[i]
    if (line.match(/^\|.+\|/)) {
      if (currentTable.length === 0) {
        tableStart = i
      }
      currentTable.push(line)
    } else {
      if (currentTable.length >= 2) {
        tableLikeMatches.push({
          start: tableStart,
          end: i - 1,
          lines: [...currentTable]
        })
      }
      currentTable = []
      tableStart = -1
    }
  }
  
  // Process table-like structures (reverse order to maintain indices)
  for (let matchIndex = tableLikeMatches.length - 1; matchIndex >= 0; matchIndex--) {
    const match = tableLikeMatches[matchIndex]
    const tableLines = match.lines
    
    // Parse header (first line)
    const headerCells = tableLines[0].split('|').map(cell => cell.trim()).filter(cell => cell)
    
    // Check if second line is a separator
    const isSeparator = tableLines[1] && tableLines[1].match(/^[\s|:\-]+$/)
    const dataStartIndex = isSeparator ? 2 : 1
    
    // Parse data rows
    const rows: string[][] = []
    for (let i = dataStartIndex; i < tableLines.length; i++) {
      const cells = tableLines[i].split('|').map(cell => cell.trim()).filter(cell => cell)
      if (cells.length > 0 && cells.some(cell => cell.length > 0)) {
        rows.push(cells)
      }
    }
    
    if (headerCells.length > 0 && rows.length > 0) {
      // Build HTML table
      let tableHtml = '<table class="schedule-table">'
      
      // Header
      tableHtml += '<thead><tr>'
      headerCells.forEach(cell => {
        tableHtml += `<th class="schedule-table-header">${cell}</th>`
      })
      tableHtml += '</tr></thead>'
      
      // Body
      tableHtml += '<tbody>'
      rows.forEach(row => {
        tableHtml += '<tr>'
        // Ensure row has same number of cells as header
        for (let i = 0; i < headerCells.length; i++) {
          const cell = row[i] || ''
          let cellContent = cell
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)(-|–|—)(Mon|Tue|Wed|Thu|Fri|Sat|Sun)?\b/gi, '<span class="schedule-day">$&</span>')
            .replace(/\b(\d+)\s*(hour|hours|hr|hrs|minute|minutes|min|mins)\s*\/?\s*day\b/gi, '<span class="schedule-time">$&</span>')
          
          tableHtml += `<td class="schedule-table-cell">${cellContent || '&nbsp;'}</td>`
        }
        tableHtml += '</tr>'
      })
      tableHtml += '</tbody></table>'
      
      // Replace the table lines in the formatted text
      const beforeTable = allLines.slice(0, match.start).join('\n')
      const afterTable = allLines.slice(match.end + 1).join('\n')
      formatted = beforeTable + '\n' + tableHtml + '\n' + afterTable
      allLines.splice(match.start, match.end - match.start + 1, tableHtml)
    }
  }
  
  // Format lists - numbered lists
  const lines = formatted.split('\n')
  let inNumberedList = false
  let listItems: string[] = []
  let result: string[] = []
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    
    // Skip if it's a table
    if (line.includes('<table') || line.includes('</table>')) {
      result.push(line)
      continue
    }
    
    const numberedMatch = line.match(/^(\d+)\.\s+(.+)$/)
    const bulletMatch = line.match(/^[-*]\s+(.+)$/)
    
    if (numberedMatch) {
      if (!inNumberedList) {
        if (listItems.length > 0) {
          result.push(`<ul class="schedule-list">${listItems.join('')}</ul>`)
          listItems = []
        }
        inNumberedList = true
      }
      listItems.push(`<li class="schedule-list-item">${numberedMatch[2]}</li>`)
    } else if (bulletMatch) {
      if (inNumberedList) {
        result.push(`<ol class="schedule-list">${listItems.join('')}</ol>`)
        listItems = []
        inNumberedList = false
      }
      if (listItems.length === 0) {
        listItems.push(`<li class="schedule-list-item">${bulletMatch[1]}</li>`)
      } else {
        listItems.push(`<li class="schedule-list-item">${bulletMatch[1]}</li>`)
      }
    } else {
      if (listItems.length > 0) {
        if (inNumberedList) {
          result.push(`<ol class="schedule-list">${listItems.join('')}</ol>`)
        } else {
          result.push(`<ul class="schedule-list">${listItems.join('')}</ul>`)
        }
        listItems = []
        inNumberedList = false
      }
      
      // Format special patterns for schedule
      if (line.trim() && !line.includes('__CODE_BLOCK_') && !line.includes('<table')) {
        // Format day patterns (Mon-Wed, Thu-Fri, Sat, Sun)
        let formattedLine = line
          .replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)(-|–|—)(Mon|Tue|Wed|Thu|Fri|Sat|Sun)?\b/gi, '<span class="schedule-day">$&</span>')
          .replace(/\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun):\b/gi, '<span class="schedule-day">$&</span>')
        
        // Format month patterns (Month 1, Months 1-2, etc.)
        formattedLine = formattedLine.replace(/\b(Month|Months)\s+(\d+)(-|–|—)?(\d+)?\b/gi, '<span class="schedule-month">$&</span>')
        
        // Format week patterns (Week 1, Week 1-2, etc.)
        formattedLine = formattedLine.replace(/\b(Week)\s+(\d+)(-|–|—)?(\d+)?\b/gi, '<span class="schedule-week">$&</span>')
        
        // Format time patterns (1 hour, 2 hours, etc.)
        formattedLine = formattedLine.replace(/\b(\d+)\s*(hour|hours|hr|hrs|minute|minutes|min|mins)\b/gi, '<span class="schedule-time">$&</span>')
        
        result.push(formattedLine)
      } else if (line.includes('__CODE_BLOCK_')) {
        result.push(line)
      } else if (line.trim() === '') {
        result.push('<br>')
      } else {
        result.push(line)
      }
    }
  }
  
  // Add any remaining list items
  if (listItems.length > 0) {
    if (inNumberedList) {
      result.push(`<ol class="schedule-list">${listItems.join('')}</ol>`)
    } else {
      result.push(`<ul class="schedule-list">${listItems.join('')}</ul>`)
    }
  }
  
  formatted = result.join('\n')
  
  // Restore code blocks
  codeBlockPlaceholders.forEach((codeBlock, index) => {
    formatted = formatted.replace(`__CODE_BLOCK_${index}__`, codeBlock)
  })
  
  // Format paragraphs (lines that aren't already formatted)
  formatted = formatted.split('\n').map(line => {
    if (line.trim() === '' || line.includes('<') || line.includes('__CODE_BLOCK_')) {
      return line
    }
    return `<p class="schedule-paragraph">${line}</p>`
  }).join('\n')
  
  // Clean up empty paragraphs
  formatted = formatted.replace(/<p class="schedule-paragraph"><\/p>/g, '')
  formatted = formatted.replace(/<p class="schedule-paragraph"><br><\/p>/g, '<br>')
  
  return sanitizeHtml(formatted)
})

function handleBack() {
  examPrepStore.setStep('exam-setup')
}

function handleStartPractice() {
  emit('start-practice')
}
</script>

<style scoped>
.study-schedule-view {
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

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 40px;
  color: white;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.schedule-content {
  color: white;
  line-height: 1.9;
  margin-bottom: 32px;
  font-size: 15px;
}

.schedule-content :deep(.schedule-title) {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 32px 0;
  color: #64ffda;
  text-align: center;
  padding-bottom: 16px;
  border-bottom: 2px solid rgba(100, 255, 218, 0.3);
}

.schedule-content :deep(.schedule-phase) {
  font-size: 22px;
  font-weight: 700;
  margin: 36px 0 20px 0;
  color: white;
  padding: 16px;
  background: rgba(100, 255, 218, 0.1);
  border-left: 4px solid #64ffda;
  border-radius: 8px;
}

.schedule-content :deep(.schedule-section) {
  font-size: 20px;
  font-weight: 600;
  margin: 28px 0 16px 0;
  color: white;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.schedule-content :deep(.schedule-subsection) {
  font-size: 18px;
  font-weight: 600;
  margin: 20px 0 12px 0;
  color: rgba(255, 255, 255, 0.98);
  padding-left: 12px;
  border-left: 3px solid rgba(100, 255, 218, 0.5);
}

.schedule-content :deep(.schedule-paragraph) {
  margin: 16px 0;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.9);
}

.schedule-content :deep(.schedule-list) {
  margin: 18px 0;
  padding-left: 24px;
  list-style: none;
}

.schedule-content :deep(.schedule-list-item) {
  margin: 10px 0;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.92);
  padding-left: 8px;
  position: relative;
}

.schedule-content :deep(ul.schedule-list .schedule-list-item::before) {
  content: "•";
  color: #64ffda;
  font-weight: bold;
  position: absolute;
  left: -20px;
  font-size: 18px;
}

.schedule-content :deep(ol.schedule-list .schedule-list-item) {
  padding-left: 0;
}

.schedule-content :deep(ol.schedule-list .schedule-list-item::before) {
  content: none;
}

.schedule-content :deep(.schedule-day) {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.schedule-content :deep(.schedule-month) {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(102, 126, 234, 0.3);
  padding: 2px 8px;
  border-radius: 4px;
}

.schedule-content :deep(.schedule-week) {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(118, 75, 162, 0.3);
  padding: 2px 8px;
  border-radius: 4px;
}

.schedule-content :deep(.schedule-time) {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(240, 147, 251, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

.schedule-content :deep(.schedule-divider) {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  margin: 24px 0;
}

.schedule-content :deep(strong) {
  font-weight: 600;
  color: white;
}

.schedule-content :deep(em) {
  font-style: italic;
  color: rgba(255, 255, 255, 0.9);
}

.schedule-content :deep(.code-block) {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
  overflow-x: auto;
}

.schedule-content :deep(.code-block code) {
  color: #ffffff !important;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
}

.schedule-content :deep(.schedule-table) {
  width: 100%;
  border-collapse: collapse;
  margin: 24px 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.schedule-content :deep(.schedule-table-header) {
  background: rgba(102, 126, 234, 0.3);
  color: white;
  font-weight: 600;
  font-size: 16px;
  padding: 16px;
  text-align: left;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
}

.schedule-content :deep(.schedule-table-cell) {
  padding: 14px 16px;
  color: white;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  vertical-align: top;
  line-height: 1.6;
}

.schedule-content :deep(.schedule-table tbody tr:last-child .schedule-table-cell) {
  border-bottom: none;
}

.schedule-content :deep(.schedule-table tbody tr:hover) {
  background: rgba(255, 255, 255, 0.05);
}

.schedule-content :deep(.schedule-table tbody tr:nth-child(even)) {
  background: rgba(255, 255, 255, 0.02);
}

.schedule-content :deep(.schedule-table tbody tr:nth-child(even):hover) {
  background: rgba(255, 255, 255, 0.08);
}

.no-schedule {
  text-align: center;
  color: white;
  padding: 40px;
}

.view-actions {
  display: flex;
  gap: 16px;
  justify-content: space-between;
  margin-top: 32px;
}

.btn-primary, .btn-secondary {
  flex: 1;
  padding: 14px 24px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.2));
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.btn-primary:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.3));
  transform: translateY(-2px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
}
</style>

