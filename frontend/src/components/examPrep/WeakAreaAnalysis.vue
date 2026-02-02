<template>
  <div class="weak-area-analysis">
    <div class="view-card">
      <h2>Weak Areas Analysis 🔍</h2>
      <p class="view-description">Areas that need more focus based on your practice results.</p>
      
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-text">Analyzing your practice results...</p>
        <p class="loading-subtext">Identifying areas that need improvement</p>
      </div>

      <!-- No Practice Data State -->
      <div v-else-if="!hasPracticeData" class="empty-state">
        <div class="empty-icon">📊</div>
        <h3>No Practice Data Yet</h3>
        <p>Complete at least one practice exam to get personalized weak area analysis.</p>
        <button @click="goToPractice" class="btn-primary">Start Practice Exam</button>
      </div>

      <!-- Analysis Content -->
      <div v-else-if="analysisContent" class="analysis-content">
        <div class="formatted-analysis" v-html="formattedAnalysis"></div>
        
        <!-- Parsed Weak Areas Cards -->
        <div v-if="parsedWeakAreas.length > 0" class="weak-areas-list">
          <h3 class="section-title">Priority Focus Areas</h3>
          <div v-for="area in parsedWeakAreas" :key="area.id" class="weak-area-card">
            <div class="area-header">
              <h4>{{ area.topic }}</h4>
              <span :class="['priority-badge', area.priority]">{{ area.priority.toUpperCase() }}</span>
            </div>
            <div class="area-stats">
              <div class="stat">
                <span class="stat-label">Current</span>
                <span class="stat-value">{{ area.currentPerformance }}%</span>
              </div>
              <div class="stat-arrow">→</div>
              <div class="stat">
                <span class="stat-label">Target</span>
                <span class="stat-value target">{{ area.targetImprovement }}%</span>
              </div>
            </div>
            <div v-if="area.specificTopics.length > 0" class="specific-topics">
              <span class="topics-label">Focus on:</span>
              <span v-for="(topic, idx) in area.specificTopics.slice(0, 3)" :key="idx" class="topic-tag">
                {{ topic }}
              </span>
            </div>
            <button @click="handleReviewTopic(area.topic)" class="btn-review">
              📚 Review This Topic
            </button>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button @click="refreshAnalysis" class="btn-refresh" :disabled="isLoading">
            🔄 Refresh Analysis
          </button>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">⚠️</div>
        <p>{{ error }}</p>
        <button @click="loadWeakAreas" class="btn-primary">Try Again</button>
      </div>

      <div class="view-actions">
        <button @click="handleBack" class="btn-secondary">← Back</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useExamPrepStore, type WeakArea } from '@/stores/examPrep'
import { useChatStore } from '@/stores/chat'
import { sanitizeHtml } from '@/utils/sanitizeHtml'

const emit = defineEmits<{
  complete: []
  'review-topic': [topic: string]
}>()

const route = useRoute()
const examPrepStore = useExamPrepStore()
const chatStore = useChatStore()

const agentId = route.params.agentId as string

const isLoading = ref(false)
const error = ref<string | null>(null)
const analysisContent = ref<string>('')
const parsedWeakAreas = ref<WeakArea[]>([])
const isMounted = ref(true)
const pollingAborted = ref(false)

const hasPracticeData = computed(() => {
  const progress = examPrepStore.progressData
  return progress && progress.practiceScores && progress.practiceScores.length > 0
})

const formattedAnalysis = computed(() => {
  if (!analysisContent.value) return ''
  
  let html = analysisContent.value
  
  // Convert markdown headers - handle numbered sections
  html = html.replace(/^#### (\d+)\. (.+)$/gm, '<h4 class="analysis-h4 numbered-section"><span class="section-number">$1.</span> $2</h4>')
  html = html.replace(/^#### (.+)$/gm, '<h4 class="analysis-h4">$1</h4>')
  html = html.replace(/^### (\d+)\. (.+)$/gm, '<h4 class="analysis-h4 numbered-section"><span class="section-number">$1.</span> $2</h4>')
  html = html.replace(/^### (.+)$/gm, '<h4 class="analysis-h4">$1</h4>')
  html = html.replace(/^## (.+)$/gm, '<h3 class="analysis-h3">$1</h3>')
  html = html.replace(/^# (.+)$/gm, '<h2 class="analysis-h2">$1</h2>')
  
  // Handle weak area sections with priority
  html = html.replace(/### (\d+)\. ([^-]+) - (HIGH|MEDIUM|LOW) PRIORITY/gi, '<h4 class="analysis-h4 priority-section"><span class="section-number">$1.</span> $2 <span class="priority-badge-inline $3.toLowerCase()">$3 PRIORITY</span></h4>')
  
  // Bold text
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  
  // Enhanced list formatting
  html = html.replace(/^- (.+)$/gm, '<li class="list-item">$1</li>')
  html = html.replace(/^(\d+)\. (.+)$/gm, '<li class="numbered-item"><span class="num">$1.</span> $2</li>')
  
  // Wrap consecutive li elements
  html = html.replace(/(<li[^>]*>[\s\S]*?<\/li>)\n(?!<li)/g, '$1</ul>\n')
  html = html.replace(/(?<!<\/ul>\n)(<li[^>]*>)/g, '<ul class="analysis-list">$1')
  
  // Handle key sections
  html = html.replace(/\*\*Current Performance:\*\*/gi, '<div class="section-label"><strong>Current Performance:</strong></div>')
  html = html.replace(/\*\*Target Improvement:\*\*/gi, '<div class="section-label"><strong>Target Improvement:</strong></div>')
  html = html.replace(/\*\*Specific Topics to Focus On:\*\*/gi, '<div class="section-label"><strong>Specific Topics to Focus On:</strong></div>')
  html = html.replace(/\*\*Improvement Strategy:\*\*/gi, '<div class="section-label"><strong>Improvement Strategy:</strong></div>')
  
  // Paragraphs with better spacing
  html = html.replace(/\n\n+/g, '</p><p class="analysis-paragraph">')
  html = '<p class="analysis-paragraph">' + html + '</p>'
  
  // Clean up empty paragraphs
  html = html.replace(/<p[^>]*>\s*<\/p>/g, '')
  html = html.replace(/<p[^>]*>\s*<(h[234]|ul|div)/g, '<$1')
  html = html.replace(/<\/(h[234]|ul|div)>\s*<\/p>/g, '</$1>')
  
  // Priority highlights
  html = html.replace(/HIGH PRIORITY/gi, '<span class="priority-high">HIGH PRIORITY</span>')
  html = html.replace(/MEDIUM PRIORITY/gi, '<span class="priority-medium">MEDIUM PRIORITY</span>')
  html = html.replace(/LOW PRIORITY/gi, '<span class="priority-low">LOW PRIORITY</span>')
  
  return sanitizeHtml(html)
})

async function loadWeakAreas() {
  if (!agentId) {
    error.value = 'No agent ID found. Please start from the beginning.'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    // Build practice results summary
    const progress = examPrepStore.progressData
    let practiceResultsSummary = 'No practice results available yet.'
    
    if (progress && progress.practiceScores.length > 0) {
      const scores = progress.practiceScores
      const avgScore = progress.averageScore.toFixed(1)
      const bestScore = progress.bestScore
      
      practiceResultsSummary = `Practice Exam Results: Total Practice Exams: ${scores.length}, Average Score: ${avgScore}%, Best Score: ${bestScore}%, Recent Scores: ${scores.slice(-3).map(s => `${s.score}%`).join(', ')}, Improvement Rate: ${progress.improvementRate > 0 ? '+' : ''}${progress.improvementRate.toFixed(1)}%, Areas of Improvement: ${progress.areasOfImprovement.map(a => a.area).join(', ') || 'To be identified'}`
    }

    // Direct tool call without preambles or questions - single line format for practice_results
    const message = `Use the identify_weak_areas tool with:
- subject: "${examPrepStore.examInfo.subject || 'General'}"
- practice_results: "${practiceResultsSummary.replace(/"/g, "'")}"
- exam_type: "${examPrepStore.examInfo.examType || 'General'}"`

    const result = await chatStore.sendMessage(agentId, message, examPrepStore.conversationId || undefined)
    
    // Update conversation ID if a new one was created
    if (result.success && result.response?.conversation_id) {
      examPrepStore.setConversationId(result.response.conversation_id)
    }
    
    // Wait and poll for response
    await pollForAnalysis()
    
  } catch (err) {
    console.error('Error loading weak areas:', err)
    error.value = 'Failed to analyze weak areas. Please try again.'
  } finally {
    isLoading.value = false
  }
}

async function pollForAnalysis(maxAttempts = 10) {
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
    
    const conversationId = examPrepStore.conversationId
    if (conversationId) {
      try {
        // Only force fetch on first attempt
        await chatStore.fetchConversation(conversationId, attempt === 0)
        
        const messages = chatStore.messages
        const assistantMessages = messages
          .filter(m => m.role === 'assistant' && m.content && m.content.trim().length > 200)
          .reverse()
        
        for (const message of assistantMessages) {
          const content = message.content.trim()
          
          // Check if this looks like a weak area analysis
          if (
            content.includes('Weak Area') ||
            content.includes('weak area') ||
            content.includes('Priority') ||
            content.includes('Performance Summary') ||
            (content.includes('HIGH') && content.includes('PRIORITY'))
          ) {
            analysisContent.value = content
            parseWeakAreasFromContent(content)
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
  
  // If no analysis found, show error
  if (isMounted.value && !analysisContent.value) {
    error.value = 'Could not generate weak area analysis. Please try again.'
  }
}

function parseWeakAreasFromContent(content: string) {
  const areas: WeakArea[] = []
  
  // Try to extract weak areas from the content
  const highPriorityMatch = content.match(/### \d+\. ([^-\n]+) - HIGH PRIORITY[\s\S]*?(?=### \d+\.|## |$)/gi)
  const mediumPriorityMatch = content.match(/### \d+\. ([^-\n]+) - MEDIUM PRIORITY[\s\S]*?(?=### \d+\.|## |$)/gi)
  const lowPriorityMatch = content.match(/### \d+\. ([^-\n]+) - LOW PRIORITY[\s\S]*?(?=### \d+\.|## |$)/gi)
  
  const extractAreaInfo = (match: string, priority: 'high' | 'medium' | 'low'): WeakArea | null => {
    const topicMatch = match.match(/### \d+\. ([^-\n]+) -/)
    if (!topicMatch) return null
    
    const topic = topicMatch[1].trim()
    
    // Extract performance percentage
    const perfMatch = match.match(/Current Performance[:\*]*\s*(\d+)/i)
    const currentPerformance = perfMatch ? parseInt(perfMatch[1]) : priority === 'high' ? 45 : priority === 'medium' ? 60 : 75
    
    // Extract target
    const targetMatch = match.match(/Target[:\*]*\s*(\d+)/i)
    const targetImprovement = targetMatch ? parseInt(targetMatch[1]) : Math.min(currentPerformance + 25, 95)
    
    // Extract specific topics
    const specificTopics: string[] = []
    const topicsSection = match.match(/Specific Topics[^:]*:[\s\S]*?(?=\*\*|###|$)/i)
    if (topicsSection) {
      const topicLines = topicsSection[0].match(/- ([^\n]+)/g)
      if (topicLines) {
        topicLines.forEach(line => {
          const cleaned = line.replace(/^- /, '').trim()
          if (cleaned && cleaned.length < 100) {
            specificTopics.push(cleaned)
          }
        })
      }
    }
    
    return {
      id: `weak-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      topic,
      priority,
      currentPerformance,
      targetImprovement,
      specificTopics: specificTopics.slice(0, 5),
      recommendedMaterials: [],
      improvementStrategy: []
    }
  }
  
  // Process matches
  if (highPriorityMatch) {
    highPriorityMatch.forEach(match => {
      const area = extractAreaInfo(match, 'high')
      if (area) areas.push(area)
    })
  }
  
  if (mediumPriorityMatch) {
    mediumPriorityMatch.forEach(match => {
      const area = extractAreaInfo(match, 'medium')
      if (area) areas.push(area)
    })
  }
  
  if (lowPriorityMatch) {
    lowPriorityMatch.forEach(match => {
      const area = extractAreaInfo(match, 'low')
      if (area) areas.push(area)
    })
  }
  
  // If no areas parsed, create default ones based on content keywords
  if (areas.length === 0) {
    const defaultAreas = extractDefaultAreas(content)
    areas.push(...defaultAreas)
  }
  
  parsedWeakAreas.value = areas
  examPrepStore.setWeakAreas(areas)
}

function extractDefaultAreas(content: string): WeakArea[] {
  const areas: WeakArea[] = []
  const subject = examPrepStore.examInfo.subject || 'General'
  
  // Look for any numbered items that might be weak areas
  const numberedItems = content.match(/(?:^|\n)\d+\.\s*\*?\*?([^*\n:]+)/gm)
  
  if (numberedItems && numberedItems.length > 0) {
    const priorities: ('high' | 'medium' | 'low')[] = ['high', 'medium', 'low']
    numberedItems.slice(0, 3).forEach((item, index) => {
      const topic = item.replace(/^\n?\d+\.\s*\*?\*?/, '').trim()
      if (topic && topic.length > 3 && topic.length < 100) {
        areas.push({
          id: `weak-default-${index}`,
          topic,
          priority: priorities[index] || 'low',
          currentPerformance: 50 - (index * 10),
          targetImprovement: 80,
          specificTopics: [],
          recommendedMaterials: [],
          improvementStrategy: []
        })
      }
    })
  }
  
  // If still no areas, create generic ones
  if (areas.length === 0) {
    areas.push({
      id: 'weak-generic-1',
      topic: `${subject} Fundamentals`,
      priority: 'high',
      currentPerformance: 55,
      targetImprovement: 80,
      specificTopics: ['Core concepts', 'Basic applications'],
      recommendedMaterials: [],
      improvementStrategy: []
    })
  }
  
  return areas
}

async function refreshAnalysis() {
  analysisContent.value = ''
  parsedWeakAreas.value = []
  await loadWeakAreas()
}

function handleReviewTopic(topic: string) {
  emit('review-topic', topic)
}

function goToPractice() {
  examPrepStore.setStep('practice-exam')
}

function handleBack() {
  examPrepStore.setStep('progress-dashboard')
}

onMounted(() => {
  isMounted.value = true
  pollingAborted.value = false
  
  // Check if we already have weak areas in store
  if (examPrepStore.weakAreas.length > 0) {
    parsedWeakAreas.value = examPrepStore.weakAreas
  } else if (hasPracticeData.value) {
    // Load weak areas if we have practice data
    loadWeakAreas()
  }
})

onUnmounted(() => {
  isMounted.value = false
  pollingAborted.value = true
})
</script>

<style scoped>
.weak-area-analysis {
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

/* Analysis Content */
.analysis-content {
  margin-bottom: 24px;
}

.formatted-analysis {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 32px;
  margin-bottom: 32px;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.9;
  max-height: 500px;
  overflow-y: auto;
  font-size: 15px;
}

.formatted-analysis::-webkit-scrollbar {
  width: 8px;
}

.formatted-analysis::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.formatted-analysis::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
}

.formatted-analysis :deep(h2.analysis-h2) {
  color: #64ffda;
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 24px 0;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(100, 255, 218, 0.3);
  line-height: 1.4;
}

.formatted-analysis :deep(h3.analysis-h3) {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 32px 0 16px 0;
  line-height: 1.4;
}

.formatted-analysis :deep(h4.analysis-h4) {
  color: rgba(255, 255, 255, 0.98);
  font-size: 18px;
  font-weight: 600;
  margin: 24px 0 12px 0;
  line-height: 1.5;
}

.formatted-analysis :deep(h4.analysis-h4.numbered-section) {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 28px 0 16px 0;
  padding: 16px;
  background: rgba(100, 255, 218, 0.1);
  border-left: 4px solid #64ffda;
  border-radius: 8px;
}

.formatted-analysis :deep(h4.analysis-h4.priority-section) {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin: 28px 0 16px 0;
  padding: 16px;
  background: rgba(100, 255, 218, 0.1);
  border-left: 4px solid #64ffda;
  border-radius: 8px;
}

.formatted-analysis :deep(.section-number) {
  color: #64ffda;
  font-weight: 700;
  font-size: 20px;
  min-width: 32px;
}

.formatted-analysis :deep(ul.analysis-list) {
  margin: 16px 0;
  padding-left: 24px;
  list-style: none;
}

.formatted-analysis :deep(li.list-item) {
  margin: 10px 0;
  color: rgba(255, 255, 255, 0.92);
  padding-left: 8px;
  position: relative;
  line-height: 1.7;
}

.formatted-analysis :deep(li.list-item::before) {
  content: "•";
  color: #64ffda;
  font-weight: bold;
  position: absolute;
  left: -20px;
  font-size: 18px;
}

.formatted-analysis :deep(li.numbered-item) {
  margin: 12px 0;
  color: rgba(255, 255, 255, 0.92);
  padding-left: 8px;
  line-height: 1.7;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.formatted-analysis :deep(li.numbered-item .num) {
  color: #64ffda;
  font-weight: 600;
  min-width: 24px;
}

.formatted-analysis :deep(.analysis-paragraph) {
  margin: 16px 0;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.9);
}

.formatted-analysis :deep(.section-label) {
  color: #64ffda;
  font-weight: 600;
  margin: 16px 0 8px 0;
  font-size: 15px;
}

.formatted-analysis :deep(.priority-badge-inline) {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin-left: auto;
}

.formatted-analysis :deep(.priority-badge-inline.high) {
  background: rgba(255, 107, 107, 0.3);
  color: #ff6b6b;
  border: 1px solid rgba(255, 107, 107, 0.5);
}

.formatted-analysis :deep(.priority-badge-inline.medium) {
  background: rgba(255, 206, 84, 0.3);
  color: #ffce54;
  border: 1px solid rgba(255, 206, 84, 0.5);
}

.formatted-analysis :deep(.priority-badge-inline.low) {
  background: rgba(76, 175, 80, 0.3);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.5);
}

.formatted-analysis :deep(strong) {
  color: rgba(255, 255, 255, 0.98);
  font-weight: 600;
}

.formatted-analysis :deep(.priority-high) {
  background: rgba(255, 107, 107, 0.3);
  color: #ff6b6b;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.formatted-analysis :deep(.priority-medium) {
  background: rgba(255, 206, 84, 0.3);
  color: #ffce54;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.formatted-analysis :deep(.priority-low) {
  background: rgba(76, 175, 80, 0.3);
  color: #4caf50;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

/* Section Title */
.section-title {
  color: white;
  font-size: 20px;
  margin: 0 0 20px 0;
  font-weight: 600;
}

/* Weak Areas List */
.weak-areas-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.weak-area-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
}

.weak-area-card:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.area-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.area-header h4 {
  color: white;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.priority-badge {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.priority-badge.high {
  background: rgba(255, 107, 107, 0.3);
  color: #ff6b6b;
  border: 1px solid rgba(255, 107, 107, 0.5);
}

.priority-badge.medium {
  background: rgba(255, 206, 84, 0.3);
  color: #ffce54;
  border: 1px solid rgba(255, 206, 84, 0.5);
}

.priority-badge.low {
  background: rgba(76, 175, 80, 0.3);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.5);
}

.area-stats {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  margin-bottom: 4px;
}

.stat-value {
  color: white;
  font-size: 24px;
  font-weight: 700;
}

.stat-value.target {
  color: #64ffda;
}

.stat-arrow {
  color: rgba(255, 255, 255, 0.5);
  font-size: 24px;
}

.specific-topics {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.topics-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.topic-tag {
  background: rgba(100, 255, 218, 0.15);
  color: #64ffda;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 13px;
}

.btn-review {
  padding: 12px 20px;
  background: linear-gradient(135deg, rgba(100, 255, 218, 0.2), rgba(100, 255, 218, 0.1));
  border: 1px solid rgba(100, 255, 218, 0.4);
  border-radius: 12px;
  color: #64ffda;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
}

.btn-review:hover {
  background: linear-gradient(135deg, rgba(100, 255, 218, 0.3), rgba(100, 255, 218, 0.2));
  transform: translateY(-1px);
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
  
  .area-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .stat-arrow {
    transform: rotate(90deg);
  }
}
</style>
