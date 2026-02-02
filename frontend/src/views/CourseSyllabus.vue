<template>
  <div class="syllabus-container">
    <header class="syllabus-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>Course Syllabus</h1>
      </div>
      <div class="header-actions">
        <button @click="downloadPDF" class="btn-download" :disabled="!syllabusContent">
          📥 Download PDF
        </button>
        <button @click="handleLogout" class="btn-secondary">Logout</button>
      </div>
    </header>

    <div class="syllabus-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Generating syllabus...</p>
      </div>

      <div v-else-if="!syllabusContent" class="empty-state">
        <p>No syllabus content available.</p>
        <button @click="goBack" class="btn-primary">Return to Course Creation</button>
      </div>

      <div v-else class="syllabus-preview" id="syllabus-content">
        <div class="syllabus-header-section">
          <h2>{{ courseOverview.title }}</h2>
          <p class="course-meta">
            <span><strong>Subject:</strong> {{ courseOverview.subject }}</span>
            <span><strong>Duration:</strong> {{ courseOverview.duration }} weeks</span>
            <span><strong>Difficulty:</strong> {{ formatDifficulty(courseOverview.difficulty) }}</span>
            <span><strong>Target Audience:</strong> {{ courseOverview.targetAudience }}</span>
          </p>
        </div>

        <div class="syllabus-body" v-html="formatSyllabus(syllabusContent)" v-if="syllabusContent"></div>

        <div class="syllabus-footer">
          <div class="course-structure-section" v-if="courseModules.length > 0">
            <h3>Course Structure</h3>
            <div v-for="(module, index) in courseModules" :key="module.id" class="module-section">
              <h4>Module {{ index + 1 }}: {{ module.name }}</h4>
              <p>{{ module.description }}</p>
              <ul v-if="module.lessons.length > 0" class="lessons-list">
                <li v-for="lesson in module.lessons" :key="lesson.id">
                  <strong>{{ lesson.title }}</strong> ({{ lesson.duration }}h)
                  <span v-if="lesson.topics.length > 0"> - Topics: {{ lesson.topics.join(', ') }}</span>
                </li>
              </ul>
            </div>
          </div>

          <div class="assessment-section" v-if="assessmentDesign">
            <h3>Assessment Plan</h3>
            <div class="assessment-types">
              <span v-if="assessmentDesign.diagnostic" class="assessment-badge">Diagnostic</span>
              <span v-if="assessmentDesign.formative" class="assessment-badge">Formative</span>
              <span v-if="assessmentDesign.summative" class="assessment-badge">Summative</span>
              <span v-if="assessmentDesign.comprehensive" class="assessment-badge">Comprehensive</span>
            </div>
            <ul v-if="assessmentDesign.assessmentDetails.length > 0" class="assessment-details">
              <li v-for="(detail, index) in assessmentDesign.assessmentDetails" :key="index">
                <strong>{{ detail.type }}</strong>: {{ detail.questions }} questions ({{ detail.weight }}% weight)
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useCourseCreationStore } from '@/stores/courseCreation'
import { useChatStore } from '@/stores/chat'
import { usePersistedStore } from '@/composables/usePersistedStore'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
// @ts-ignore - html2pdf.js doesn't have TypeScript definitions
import html2pdf from 'html2pdf.js'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const courseCreationStore = useCourseCreationStore()
const chatStore = useChatStore()

const agentId = route.params.agentId as string

const { ready: courseCreationReady } = usePersistedStore(
  `courseCreation:${agentId}`,
  () => courseCreationStore.exportState(),
  (data) => courseCreationStore.importState(data),
  () => courseCreationStore.$state
)

const loading = ref(false)
const syllabusContent = computed(() => courseCreationStore.generatedSyllabus)
const courseOverview = computed(() => courseCreationStore.courseOverview)
const courseModules = computed(() => courseCreationStore.courseModules)
const assessmentDesign = computed(() => courseCreationStore.assessmentDesign)

onMounted(async () => {
  await courseCreationReady
  console.log('CourseSyllabus mounted, syllabusContent:', syllabusContent.value)
  console.log('Route query:', route.query)
  
  // If syllabus is not yet generated, try to get it from the last assistant message
  if (!syllabusContent.value) {
    loading.value = true
    try {
      const conversationId = route.query.conversation_id as string || courseCreationStore.conversationId
      console.log('Fetching conversation:', conversationId)
      
      if (conversationId) {
        await chatStore.fetchConversation(conversationId, true)
        // Get the last assistant message which should be the syllabus
        const messages = chatStore.messages
        console.log('Messages fetched:', messages.length)
        
        const assistantMessages = messages.filter(msg => msg.role === 'assistant')
        console.log('Assistant messages:', assistantMessages.length)
        
        if (assistantMessages.length > 0) {
          // Get the last assistant message (should be the syllabus)
          const lastAssistantMessage = assistantMessages[assistantMessages.length - 1]
          console.log('Last assistant message length:', lastAssistantMessage.content?.length)
          
          if (lastAssistantMessage && lastAssistantMessage.content && lastAssistantMessage.content.length > 100) {
            courseCreationStore.setGeneratedSyllabus(lastAssistantMessage.content)
            console.log('Syllabus set in store')
          }
        }
      } else {
        console.warn('No conversation ID found')
      }
    } catch (error) {
      console.error('Failed to fetch syllabus:', error)
    } finally {
      loading.value = false
    }
  } else {
    console.log('Syllabus already in store')
  }
})

function formatDifficulty(difficulty: string): string {
  return difficulty.charAt(0).toUpperCase() + difficulty.slice(1)
}

function formatSyllabus(content: string): string {
  if (!content) return ''
  
  // Remove any quiz questions or random content that shouldn't be in a syllabus
  // Look for patterns like "Question 1:", "**Question 1:**", etc.
  const questionPattern = /(?:^|\n)(?:\*\*)?Question\s+\d+[:\-]?\s*\*\*/gi
  if (questionPattern.test(content)) {
    // If questions are found, try to extract only the syllabus part before questions
    const questionIndex = content.search(/(?:^|\n)(?:\*\*)?Question\s+\d+[:\-]?\s*\*\*/i)
    if (questionIndex > 0) {
      content = content.substring(0, questionIndex).trim()
    }
  }
  
  // Convert markdown-like formatting to HTML
  let formatted = content
    // Headers (must be at start of line)
    .replace(/^#\s+(.+)$/gm, '<h1>$1</h1>')
    .replace(/^##\s+(.+)$/gm, '<h2>$1</h2>')
    .replace(/^###\s+(.+)$/gm, '<h3>$1</h3>')
    .replace(/^####\s+(.+)$/gm, '<h4>$1</h4>')
    // Bold and italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Lists (must be at start of line)
    .replace(/^[-*]\s+(.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
  
  // Split by double newlines to create paragraphs
  const sections = formatted.split(/\n\n+/)
  formatted = sections
    .map(section => {
      const trimmed = section.trim()
      if (!trimmed) return ''
      
      // If it's already a heading, return as is
      if (trimmed.startsWith('<h')) {
        return trimmed
      }
      
      // Check if it contains list items
      if (trimmed.includes('<li>')) {
        return `<ul>${trimmed}</ul>`
      }
      
      // Replace single newlines with <br> within paragraphs
      const withBreaks = trimmed.replace(/\n/g, '<br>')
      return `<p>${withBreaks}</p>`
    })
    .filter(s => s.length > 0)
    .join('')
  
  const safe = formatted || '<p>' + content.replace(/\n/g, '<br>') + '</p>'
  return sanitizeHtml(safe)
}

async function downloadPDF() {
  const element = document.getElementById('syllabus-content')
  if (!element) return

  const opt = {
    margin: [0.5, 0.5, 0.5, 0.5],
    filename: `${courseOverview.value.title || 'Course'}_Syllabus.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
  }

  try {
    await html2pdf().set(opt).from(element).save()
  } catch (error) {
    console.error('Failed to generate PDF:', error)
    alert('Failed to generate PDF. Please try again.')
  }
}

function goBack() {
  router.push('/dashboard')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.syllabus-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
}

.syllabus-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  color: white;
  font-size: 24px;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-back {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 16px;
  cursor: pointer;
  padding: 10px 16px;
  border-radius: 12px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.btn-back:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateX(-4px);
}

.btn-download {
  padding: 10px 20px;
  background: rgba(76, 175, 80, 0.3);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(76, 175, 80, 0.5);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-download:hover:not(:disabled) {
  background: rgba(76, 175, 80, 0.4);
  transform: translateY(-2px);
}

.btn-download:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
}

.btn-primary {
  padding: 12px 24px;
  background: rgba(102, 126, 234, 0.3);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(102, 126, 234, 0.5);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: rgba(102, 126, 234, 0.4);
}

.syllabus-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: white;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  color: white;
  padding: 60px 20px;
}

.empty-state p {
  font-size: 18px;
  margin-bottom: 24px;
}

.syllabus-preview {
  background: white;
  border-radius: 16px;
  padding: 48px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  color: #333;
}

.syllabus-header-section {
  border-bottom: 2px solid #667eea;
  padding-bottom: 24px;
  margin-bottom: 32px;
}

.syllabus-header-section h2 {
  color: #667eea;
  font-size: 32px;
  margin: 0 0 16px 0;
  font-weight: 700;
}

.course-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  font-size: 14px;
  color: #666;
  margin: 0;
}

.course-meta span {
  display: flex;
  align-items: center;
  gap: 8px;
}

.course-meta strong {
  color: #333;
  font-weight: 600;
}

.syllabus-body {
  line-height: 1.8;
  font-size: 16px;
  color: #444;
  margin-bottom: 32px;
}

.syllabus-body :deep(p) {
  margin: 16px 0;
}

.syllabus-body :deep(h3) {
  color: #667eea;
  font-size: 24px;
  margin: 32px 0 16px 0;
  font-weight: 600;
}

.syllabus-body :deep(h4) {
  color: #764ba2;
  font-size: 20px;
  margin: 24px 0 12px 0;
  font-weight: 600;
}

.syllabus-body :deep(ul),
.syllabus-body :deep(ol) {
  margin: 16px 0;
  padding-left: 24px;
}

.syllabus-body :deep(li) {
  margin: 8px 0;
}

.syllabus-footer {
  border-top: 2px solid #f0f0f0;
  padding-top: 32px;
  margin-top: 32px;
}

.course-structure-section,
.assessment-section {
  margin-bottom: 32px;
}

.course-structure-section h3,
.assessment-section h3 {
  color: #667eea;
  font-size: 24px;
  margin: 0 0 16px 0;
  font-weight: 600;
}

.module-section {
  background: #f8f9fa;
  border-left: 4px solid #667eea;
  padding: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
}

.module-section h4 {
  color: #764ba2;
  font-size: 20px;
  margin: 0 0 12px 0;
  font-weight: 600;
}

.module-section p {
  color: #666;
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.lessons-list {
  list-style: none;
  padding-left: 0;
  margin: 12px 0 0 0;
}

.lessons-list li {
  padding: 8px 0;
  border-bottom: 1px solid #e0e0e0;
  color: #555;
}

.lessons-list li:last-child {
  border-bottom: none;
}

.assessment-types {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.assessment-badge {
  background: #667eea;
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.assessment-details {
  list-style: none;
  padding-left: 0;
}

.assessment-details li {
  padding: 12px;
  background: #f8f9fa;
  border-left: 3px solid #667eea;
  margin-bottom: 8px;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .syllabus-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .syllabus-preview {
    padding: 24px;
  }

  .syllabus-header-section h2 {
    font-size: 24px;
  }

  .course-meta {
    flex-direction: column;
    gap: 12px;
  }
}
</style>

