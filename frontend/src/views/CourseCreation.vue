<template>
  <div class="course-creation-container">
    <header class="course-creation-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>{{ agent?.name || 'Course Creation Agent' }}</h1>
      </div>
      <button @click="handleLogout" class="btn-secondary">Logout</button>
    </header>

    <div class="course-creation-content">
      <!-- Sidebar Chat -->
      <aside :class="['course-creation-sidebar', { minimized: isChatMinimized }]">
        <div class="sidebar-header">
          <h2>Chat with Agent</h2>
          <button @click="toggleChatMinimize" class="btn-minimize" :title="isChatMinimized ? 'Expand Chat' : 'Minimize Chat'">
            <span v-if="!isChatMinimized">−</span>
            <span v-else>+</span>
          </button>
        </div>
        <div v-if="!isChatMinimized" class="sidebar-messages" ref="sidebarMessagesRef">
          <!-- AI Suggestions Card -->
          <div class="ai-suggestions-card">
            <div class="suggestions-header">
              <span class="ai-icon">🤖</span>
              <h3>AI Suggestions</h3>
            </div>
            <div class="suggestions-content">
              <div v-for="(suggestion, index) in aiSuggestions" :key="index" class="suggestion-item">
                <div class="suggestion-icon">{{ suggestion.icon }}</div>
                <div class="suggestion-text">
                  <strong>{{ suggestion.title }}</strong>
                  <p>{{ suggestion.text }}</p>
                </div>
                <button 
                  v-if="suggestion.action" 
                  @click="applySuggestion(suggestion)"
                  class="btn-apply-suggestion"
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
          
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['sidebar-message', message.role]"
          >
            <div class="sidebar-message-content">
              <div class="sidebar-message-text" v-html="formatMessage(message.content)"></div>
              <div class="sidebar-message-time">
                {{ formatTime(message.created_at) }}
              </div>
            </div>
          </div>
          <div v-if="isLoading" class="sidebar-message assistant">
            <div class="sidebar-message-content">
              <div class="sidebar-message-text typing">Thinking...</div>
            </div>
          </div>
        </div>
        <div v-if="!isChatMinimized" class="sidebar-input">
          <form @submit.prevent="handleSidebarSend">
            <input
              v-model="sidebarInput"
              type="text"
              placeholder="Type your message..."
              :disabled="isLoading"
              class="sidebar-input-field"
            />
            <button
              type="submit"
              :disabled="!sidebarInput.trim() || isLoading"
              class="btn-send-small"
            >
              Send
            </button>
          </form>
        </div>
      </aside>

      <!-- Minimized Chat Button (when minimized) -->
      <button 
        v-if="isChatMinimized" 
        @click="toggleChatMinimize" 
        class="chat-minimized-btn"
        title="Expand Chat"
      >
        💬
      </button>
      
      <!-- Course Preview Button -->
      <button 
        v-if="courseCreationStore.courseOverview.title"
        @click="showPreview = !showPreview" 
        class="preview-btn"
        title="Preview Course"
      >
        👁️ Preview
      </button>
      
      <!-- Course Preview Modal -->
      <div v-if="showPreview" class="preview-modal-overlay" @click="showPreview = false">
        <div class="preview-modal" @click.stop>
          <div class="preview-header">
            <h2>Course Preview</h2>
            <button @click="showPreview = false" class="btn-close">×</button>
          </div>
          <div class="preview-content">
            <div class="preview-section">
              <h3>{{ courseCreationStore.courseOverview.title }}</h3>
              <p><strong>Subject:</strong> {{ courseCreationStore.courseOverview.subject }}</p>
              <p><strong>Duration:</strong> {{ courseCreationStore.courseOverview.duration }} weeks</p>
              <p><strong>Difficulty:</strong> {{ courseCreationStore.courseOverview.difficulty }}</p>
              <p><strong>Target Audience:</strong> {{ courseCreationStore.courseOverview.targetAudience }}</p>
            </div>
            <div class="preview-section" v-if="courseCreationStore.courseOverview.learningObjectives.length > 0">
              <h3>Learning Objectives</h3>
              <ul>
                <li v-for="(obj, index) in courseCreationStore.courseOverview.learningObjectives" :key="index">
                  {{ obj }}
                </li>
              </ul>
            </div>
            <div class="preview-section" v-if="courseCreationStore.courseModules.length > 0">
              <h3>Course Structure</h3>
              <div v-for="(module, index) in courseCreationStore.courseModules" :key="module.id" class="preview-module">
                <h4>Module {{ index + 1 }}: {{ module.name }}</h4>
                <p>{{ module.description }}</p>
                <div v-if="module.lessons.length > 0" class="preview-lessons">
                  <div v-for="lesson in module.lessons" :key="lesson.id" class="preview-lesson">
                    • {{ lesson.title }} ({{ lesson.duration }}h)
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Area -->
      <main :class="['course-creation-main', { expanded: isChatMinimized }]">
        <!-- Progress Indicator -->
        <div class="progress-indicator">
          <div 
            v-for="(step, index) in steps" 
            :key="step.id"
            :class="['progress-step', { 
              active: courseCreationStore.currentStep === step.id,
              completed: isStepCompleted(step.id)
            }]"
          >
            <div class="progress-step-number">{{ index + 1 }}</div>
            <div class="progress-step-label">{{ step.label }}</div>
          </div>
        </div>

        <!-- Step Components -->
        <div class="step-container">
          <!-- Course Overview Step -->
          <CourseOverviewForm 
            v-if="courseCreationStore.currentStep === 'course-overview'"
            @complete="handleCourseOverviewComplete" 
          />

          <!-- Course Structure Step -->
          <CourseStructureForm 
            v-else-if="courseCreationStore.currentStep === 'course-structure'"
            @complete="handleCourseStructureComplete" 
          />

          <!-- Assessment Design Step -->
          <AssessmentDesignForm 
            v-else-if="courseCreationStore.currentStep === 'assessment-design'"
            @complete="handleAssessmentDesignComplete" 
          />

          <!-- Concept Mapping Step -->
          <ConceptMappingForm 
            v-else-if="courseCreationStore.currentStep === 'concept-mapping'"
            @complete="handleConceptMappingComplete" 
          />

          <!-- Workflow Automation Step -->
          <WorkflowAutomationForm 
            v-else-if="courseCreationStore.currentStep === 'workflow-automation'"
            @complete="handleWorkflowAutomationComplete" 
          />

          <!-- Validation Review Step -->
          <ValidationReviewForm 
            v-else-if="courseCreationStore.currentStep === 'validation-review'"
            @complete="handleValidationReviewComplete" 
          />

          <!-- Final Review Step -->
          <FinalReviewForm 
            v-else-if="courseCreationStore.currentStep === 'final-review'"
            @complete="handleFinalReviewComplete" 
          />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAgentsStore } from '@/stores/agents'
import { useChatStore } from '@/stores/chat'
import { useCourseCreationStore } from '@/stores/courseCreation'
import CourseOverviewForm from '@/components/courseCreation/CourseOverviewForm.vue'
import CourseStructureForm from '@/components/courseCreation/CourseStructureForm.vue'
import AssessmentDesignForm from '@/components/courseCreation/AssessmentDesignForm.vue'
import ConceptMappingForm from '@/components/courseCreation/ConceptMappingForm.vue'
import WorkflowAutomationForm from '@/components/courseCreation/WorkflowAutomationForm.vue'
import ValidationReviewForm from '@/components/courseCreation/ValidationReviewForm.vue'
import FinalReviewForm from '@/components/courseCreation/FinalReviewForm.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const agentsStore = useAgentsStore()
const chatStore = useChatStore()
const courseCreationStore = useCourseCreationStore()

const agentId = route.params.agentId as string
const sidebarInput = ref('')
const sidebarMessagesRef = ref<HTMLElement | null>(null)
const isChatMinimized = ref(false)
const showPreview = ref(false)

const agent = computed(() => agentsStore.selectedAgent)
const messages = computed(() => chatStore.messages)
const isLoading = computed(() => chatStore.sending || chatStore.loading)

// AI Suggestions based on current step
const aiSuggestions = computed(() => {
  const step = courseCreationStore.currentStep
  const suggestions: Array<{ icon: string; title: string; text: string; action?: () => void }> = []
  
  switch (step) {
    case 'course-overview':
      if (!courseCreationStore.courseOverview.title) {
        suggestions.push({
          icon: '💡',
          title: 'Start with a Template',
          text: 'Use a template to get started quickly with pre-filled course structure.',
          action: () => {
            // Focus on template selection
            document.querySelector('.template-section')?.scrollIntoView({ behavior: 'smooth' })
          }
        })
      }
      if (courseCreationStore.courseOverview.learningObjectives.length === 0) {
        suggestions.push({
          icon: '🎯',
          title: 'Define Clear Objectives',
          text: 'Add 3-5 specific learning objectives. Use action verbs like "Master", "Build", "Understand".'
        })
      }
      break
    case 'course-structure':
      if (courseCreationStore.courseModules.length === 0) {
        suggestions.push({
          icon: '📚',
          title: 'Create Your First Module',
          text: 'Start by adding a module. Aim for 4-6 modules for a balanced course structure.'
        })
      } else if (courseCreationStore.courseModules.length < 3) {
        suggestions.push({
          icon: '✨',
          title: 'Add More Modules',
          text: `You have ${courseCreationStore.courseModules.length} module(s). Consider adding 2-4 more for comprehensive coverage.`
        })
      }
      break
    case 'assessment-design':
      suggestions.push({
        icon: '📝',
        title: 'Mix Assessment Types',
        text: 'Combine diagnostic, formative, and summative assessments for best learning outcomes.'
      })
      break
    case 'concept-mapping':
      suggestions.push({
        icon: '🔗',
        title: 'Map Key Relationships',
        text: 'Visualize how concepts connect. This helps students understand the bigger picture.'
      })
      break
    case 'validation-review':
      suggestions.push({
        icon: '✅',
        title: 'Review Content Quality',
        text: 'Ensure all learning objectives are covered and assessments align with course goals.'
      })
      break
  }
  
  return suggestions
})

function applySuggestion(suggestion: { action?: () => void }) {
  if (suggestion.action) {
    suggestion.action()
  }
}

const steps = [
  { id: 'course-overview', label: 'Overview' },
  { id: 'course-structure', label: 'Structure' },
  { id: 'assessment-design', label: 'Assessments' },
  { id: 'concept-mapping', label: 'Concepts' },
  { id: 'workflow-automation', label: 'Automation' },
  { id: 'validation-review', label: 'Validation' },
  { id: 'final-review', label: 'Review' }
]

function isStepCompleted(stepId: string): boolean {
  const stepIndex = steps.findIndex(s => s.id === stepId)
  const currentIndex = steps.findIndex(s => s.id === courseCreationStore.currentStep)
  return stepIndex < currentIndex
}

onMounted(async () => {
  await agentsStore.fetchAgent(agentId)
  
  // Initialize conversation
  const conversationId = route.query.conversation_id as string
  if (conversationId) {
    await chatStore.fetchConversation(conversationId)
    courseCreationStore.setConversationId(conversationId)
  } else {
    const result = await chatStore.createConversation(agentId)
    if (result.success && result.conversation) {
      await chatStore.fetchConversation(result.conversation.id)
      courseCreationStore.setConversationId(result.conversation.id)
      router.replace({ 
        path: route.path, 
        query: { ...route.query, conversation_id: result.conversation.id } 
      })
    }
  }
})

watch(messages, () => {
  nextTick(() => {
    scrollSidebarToBottom()
  })
})

function scrollSidebarToBottom() {
  if (sidebarMessagesRef.value) {
    sidebarMessagesRef.value.scrollTop = sidebarMessagesRef.value.scrollHeight
  }
}

async function handleSidebarSend() {
  if (!sidebarInput.value.trim() || isLoading.value) return

  const message = sidebarInput.value.trim()
  sidebarInput.value = ''

  const result = await chatStore.sendMessage(
    agentId,
    message,
    courseCreationStore.conversationId || undefined
  )

  if (!result.success) {
    alert(result.error || 'Failed to send message')
    sidebarInput.value = message
  }
}

function formatTime(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatMessage(content: string): string {
  return content
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

function handleCourseOverviewComplete(overview: any) {
  courseCreationStore.setCourseOverview(overview)
  courseCreationStore.setStep('course-structure')
}

function handleCourseStructureComplete(modules: any) {
  courseCreationStore.setCourseModules(modules)
  courseCreationStore.setStep('assessment-design')
}

function handleAssessmentDesignComplete(design: any) {
  courseCreationStore.setAssessmentDesign(design)
  courseCreationStore.setStep('concept-mapping')
}

function handleConceptMappingComplete(map: any) {
  courseCreationStore.setConceptMap(map)
  courseCreationStore.setStep('workflow-automation')
}

function handleWorkflowAutomationComplete(workflow: any) {
  courseCreationStore.setWorkflowAutomation(workflow)
  courseCreationStore.setStep('validation-review')
}

function handleValidationReviewComplete(result: any) {
  courseCreationStore.setValidationResult(result)
  courseCreationStore.setStep('final-review')
}

async function handleFinalReviewComplete() {
  // On final completion, ask the Course Creation Agent to generate a full course summary/syllabus
  // based on the structured data we've collected, then route to syllabus page.
  const overview = courseCreationStore.courseOverview
  const modules = courseCreationStore.courseModules
  const assessments = courseCreationStore.assessmentDesign
  const conceptMap = courseCreationStore.conceptMap
  const workflow = courseCreationStore.workflowAutomation
  const validation = courseCreationStore.validationResult

  const summaryPrompt = `
Using the following structured course design data, generate a final, exportable course syllabus.

COURSE OVERVIEW:
- Title: ${overview.title}
- Subject: ${overview.subject}
- Duration (weeks): ${overview.duration}
- Difficulty: ${overview.difficulty}
- Target Audience: ${overview.targetAudience}
- Learning Objectives:
${overview.learningObjectives.map((o, i) => `  ${i + 1}. ${o}`).join('\n')}

COURSE MODULES:
${modules
  .map(
    (m, i) => `Module ${i + 1}: ${m.name}
Description: ${m.description}
Lessons:
${m.lessons
  .map(
    (l, j) =>
      `  ${j + 1}. ${l.title} (${l.duration}h) - Topics: ${l.topics.join(', ')}`
  )
  .join('\n')}`
  )
  .join('\n\n')}

ASSESSMENT DESIGN:
${JSON.stringify(assessments, null, 2)}

CONCEPT MAP:
${conceptMap ? JSON.stringify(conceptMap, null, 2) : 'Not provided'}

WORKFLOW AUTOMATION:
${JSON.stringify(workflow, null, 2)}

VALIDATION RESULT:
${validation ? JSON.stringify(validation, null, 2) : 'Not provided'}

Generate a clean, human-readable syllabus with:
- A short course description
- List of modules and lessons
- Assessment plan
- Any relevant notes for instructors.
`

  // Send message to agent and wait for response
  if (courseCreationStore.conversationId) {
    const result = await chatStore.sendMessage(
      agentId,
      summaryPrompt,
      courseCreationStore.conversationId
    )

    if (result.success) {
      // Wait a bit for the message to be processed and then fetch the conversation
      await new Promise(resolve => setTimeout(resolve, 2000))
      await chatStore.fetchConversation(courseCreationStore.conversationId!)

      // Get the last assistant message (the syllabus)
      const messages = chatStore.messages
      const lastAssistantMessage = [...messages]
        .reverse()
        .find(msg => msg.role === 'assistant')

      if (lastAssistantMessage) {
        courseCreationStore.setGeneratedSyllabus(lastAssistantMessage.content)
      }

      // Route to syllabus page
      router.push({
        name: 'CourseSyllabus',
        params: { agentId },
        query: { conversation_id: courseCreationStore.conversationId }
      })
    } else {
      alert('Failed to generate syllabus. Please try again.')
    }
  } else {
    alert('No conversation found. Please try again.')
  }
}

function goBack() {
  router.push('/dashboard')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function toggleChatMinimize() {
  isChatMinimized.value = !isChatMinimized.value
}
</script>

<style scoped>
.course-creation-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  position: relative;
}

.course-creation-container::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(255, 119, 198, 0.3) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.course-creation-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 20px 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
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

h1 {
  color: white;
  font-size: 24px;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
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

.course-creation-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.course-creation-sidebar {
  width: 350px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease, width 0.3s ease;
  overflow: hidden;
}

.course-creation-sidebar.minimized {
  width: 0;
  transform: translateX(-100%);
  border: none;
}

.chat-minimized-btn {
  position: fixed;
  left: 20px;
  bottom: 20px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.chat-minimized-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h2 {
  color: white;
  font-size: 18px;
  margin: 0;
  font-weight: 600;
  flex: 1;
}

.btn-minimize {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: none;
  outline: none;
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-minimize:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: scale(1.05);
}

.sidebar-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sidebar-message {
  display: flex;
}

.sidebar-message.user {
  justify-content: flex-end;
}

.sidebar-message.assistant {
  justify-content: flex-start;
}

.sidebar-message-content {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.sidebar-message.user .sidebar-message-content {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.sidebar-message.assistant .sidebar-message-content {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-message-text {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 4px;
}

.sidebar-message-time {
  font-size: 11px;
  opacity: 0.7;
  margin-top: 4px;
}

.typing {
  font-style: italic;
  opacity: 0.7;
}

.sidebar-input {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.sidebar-input form {
  display: flex;
  gap: 8px;
}

.sidebar-input-field {
  flex: 1;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  font-size: 14px;
  color: white;
}

.sidebar-input-field::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.sidebar-input-field:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.25);
}

.btn-send-small {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-send-small:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
}

.btn-send-small:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.course-creation-main {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: width 0.3s ease;
}

.course-creation-main.expanded {
  width: 100%;
}

.progress-indicator {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.progress-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.5;
  transition: opacity 0.3s ease;
}

.progress-step.active {
  opacity: 1;
}

.progress-step.completed {
  opacity: 0.8;
}

.progress-step-number {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  transition: all 0.3s ease;
}

.progress-step.active .progress-step-number {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
  transform: scale(1.1);
}

.progress-step.completed .progress-step-number {
  background: rgba(76, 175, 80, 0.3);
  border-color: rgba(76, 175, 80, 0.5);
}

.progress-step-label {
  color: white;
  font-size: 12px;
  font-weight: 500;
  text-align: center;
}

.step-container {
  width: 100%;
  max-width: 900px;
}

.ai-suggestions-card {
  background: rgba(102, 126, 234, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.suggestions-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.ai-icon {
  font-size: 20px;
}

.suggestions-header h3 {
  color: white;
  font-size: 14px;
  margin: 0;
  font-weight: 600;
}

.suggestions-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.suggestion-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.suggestion-text {
  flex: 1;
}

.suggestion-text strong {
  color: white;
  font-size: 12px;
  display: block;
  margin-bottom: 4px;
}

.suggestion-text p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 11px;
  margin: 0;
  line-height: 1.4;
}

.btn-apply-suggestion {
  padding: 6px 12px;
  background: rgba(76, 175, 80, 0.3);
  color: white;
  border: 1px solid rgba(76, 175, 80, 0.5);
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
  flex-shrink: 0;
}

.btn-apply-suggestion:hover {
  background: rgba(76, 175, 80, 0.4);
}

.preview-btn {
  position: fixed;
  right: 20px;
  bottom: 20px;
  padding: 12px 20px;
  background: rgba(102, 126, 234, 0.3);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.preview-btn:hover {
  background: rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
}

.preview-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.preview-modal {
  background: rgba(102, 126, 234, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 24px;
  padding: 32px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.preview-header h2 {
  color: white;
  font-size: 24px;
  margin: 0;
}

.btn-close {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.preview-content {
  color: white;
}

.preview-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.preview-section:last-child {
  border-bottom: none;
}

.preview-section h3 {
  font-size: 20px;
  margin: 0 0 12px 0;
}

.preview-section p {
  margin: 8px 0;
  line-height: 1.6;
}

.preview-section ul {
  margin: 12px 0;
  padding-left: 24px;
}

.preview-section li {
  margin: 8px 0;
  line-height: 1.6;
}

.preview-module {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

.preview-module h4 {
  font-size: 16px;
  margin: 0 0 8px 0;
}

.preview-lessons {
  margin-top: 12px;
  padding-left: 16px;
}

.preview-lesson {
  margin: 6px 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

@media (max-width: 768px) {
  .course-creation-sidebar {
    width: 100%;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 10;
    display: none;
  }

  .course-creation-main {
    padding: 20px;
  }

  .progress-indicator {
    gap: 8px;
  }

  .progress-step-label {
    font-size: 10px;
  }
  
  .preview-btn {
    right: 10px;
    bottom: 10px;
    padding: 10px 16px;
    font-size: 12px;
  }
}
</style>

