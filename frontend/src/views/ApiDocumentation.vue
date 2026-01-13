<template>
  <div class="api-documentation-page">
    <header class="page-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>📚 API Documentation</h1>
      </div>
    </header>

    <div class="docs-layout">
      <!-- Sidebar Navigation -->
      <aside class="docs-sidebar">
        <nav class="sidebar-nav">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="scrollToSection(tab.id)"
            :class="['nav-tab', { active: activeTab === tab.id }]"
          >
            <span class="tab-icon">{{ tab.icon }}</span>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </nav>
      </aside>

      <!-- Main Content Area -->
      <main class="docs-content">
        <div class="documentation-container">
          <!-- Overview Section -->
          <section id="overview" class="docs-section-main">
            <h2>Overview</h2>
            <p class="section-description">
              This API allows external platforms to interact with AI agents through REST endpoints. 
              Our pre-built agents are <strong>not simple chatbots</strong> - they follow structured workflows 
              and guide users through multi-step processes. Each agent maintains conversation context 
              and provides personalized, tutor-like interactions. API keys can be <strong>universal</strong> 
              (work with all agents) or <strong>agent-specific</strong> for enhanced security.
            </p>
            
            <h3>Base URL</h3>
            <div class="code-block">
              <code class="url-code">{{ baseUrl }}/api/v1/public/agents/{agent_slug}/chat</code>
              <button 
                @click="copyToClipboard(`${baseUrl}/api/v1/public/agents/{agent_slug}/chat`, false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>
              <p class="docs-note">
                Replace <code>{agent_slug}</code> with your agent's slug. 
                Available agents: <code>education.personal_tutor</code>, <code>education.course_creation_agent</code>, <code>education.language_practice_agent</code>, <code>education.micro_learning_agent</code>
              </p>

            <h3>Authentication</h3>
            <p class="section-description">
              All requests require an API key in the <code>X-API-Key</code> header. 
              API keys can be created from the API Keys page in your dashboard.
            </p>
            <div class="code-block">
              <code>X-API-Key: your_api_key_here</code>
              <button 
                @click="copyToClipboard('X-API-Key: your_api_key_here', false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>
            <h4>API Key Types</h4>
            <ul class="docs-notes">
              <li><strong>Universal Keys:</strong> Work with all agents. Create by leaving the agent selection as "All Agents" when creating a key.</li>
              <li><strong>Agent-Specific Keys:</strong> Work only with a specific agent. More secure but less flexible.</li>
              <li><strong>Domain Whitelisting:</strong> Optional security feature. Restrict API key usage to specific domains (e.g., <code>https://yourdomain.com</code>). Leave empty to allow all domains.</li>
            </ul>

            <h3>Getting Agent Information</h3>
            <p class="section-description">
              To get a list of available agents and their slugs, you can use the following endpoint:
            </p>
            <div class="endpoint-info">
              <code class="method-badge">GET</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents</code>
            </div>
            <div class="code-block">
              <pre class="json-example">{{ getListAgentsExample() }}</pre>
              <button 
                @click="copyToClipboard(getListAgentsExample(), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>
            <p class="docs-note">
              This endpoint returns a list of all available pre-built agents with their slugs, names, and descriptions. 
              Use the <code>slug</code> field in your chat requests.
            </p>
          </section>

          <!-- Personal Tutor Agent Section -->
          <section id="personal-tutor" class="docs-section-main">
            <h2>Personal Tutor Agent Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>education.personal_tutor</code><br>
              A one-on-one tutor that explains concepts step-by-step, creates practice quizzes, 
              and builds study plans. This agent follows a structured learning flow.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Initial Greeting:</strong> Agent introduces itself and asks what the user wants to learn</li>
              <li><strong>Topic Selection:</strong> User specifies a topic (e.g., "I want to learn about photosynthesis")</li>
              <li><strong>Concept Explanation:</strong> Agent explains concepts step-by-step with check-point questions</li>
              <li><strong>Practice Quiz:</strong> Agent generates quizzes with multiple questions in a single response</li>
              <li><strong>Study Plan:</strong> Agent can create personalized study plans</li>
            </ol>

            <h3>Endpoint</h3>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/education.personal_tutor/chat</code>
            </div>

            <h3>Request Format</h3>
            <h4>Headers</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  'X-API-Key': 'your_api_key_here',
  'Content-Type': 'application/json'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h4>Request Body</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "optional-uuid-or-null",
  "message": "Your message here"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  conversation_id: null,
  message: 'Your message here'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>
            <p class="docs-note">
              <code>conversation_id</code> is optional. If not provided or set to <code>null</code>, a new conversation will be created. 
              Include the same <code>conversation_id</code> in subsequent requests to maintain conversation context.
            </p>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "Agent's response text",
  "agent_id": "uuid-string"
}, null, 2) }}</pre>
            </div>

            <h3>Example: Requesting a Quiz</h3>
            <div class="code-block">
              <pre class="json-example">{{ getQuizExample() }}</pre>
              <button @click="copyToClipboard(getQuizExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Note:</strong> The agent generates ALL quiz questions in a single API call. 
              The response will contain all questions formatted as:<br>
              <code>**Question 1:** [question] ... **Answer:** [letter]</code>
            </p>

            <h3>Quiz Response Parsing</h3>
            <p class="section-description">
              Quiz responses contain all questions in a structured format. Here's how to parse them:
            </p>
            <div class="code-block">
              <pre class="js-example">{{ getQuizParserExample() }}</pre>
              <button 
                @click="copyToClipboard(getQuizParserExample(), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h3>Complete Workflow Example</h3>
            <div class="code-block">
              <pre class="js-example">{{ getCompleteWorkflowExample() }}</pre>
              <button 
                @click="copyToClipboard(getCompleteWorkflowExample(), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>
          </section>

          <!-- Course Creation Agent Section -->
          <section id="course-creation" class="docs-section-main">
            <h2>Course Creation Agent Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>education.course_creation_agent</code><br>
              A personal tutor that guides users through creating comprehensive courses with 
              learning assessments, concept maps, workflow automation, and validation.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Discovery Phase:</strong> Agent asks about learning objectives, target audience, duration, format</li>
              <li><strong>Structure Design:</strong> Agent creates course outline with modules and lessons</li>
              <li><strong>Concept Mapping:</strong> Agent visualizes relationships between topics</li>
              <li><strong>Assessment Design:</strong> Agent creates diagnostic, formative, and summative assessments</li>
              <li><strong>Workflow Creation:</strong> Agent designs automated workflows for course delivery</li>
              <li><strong>Validation:</strong> Agent validates content against educational standards</li>
            </ol>

            <h3>Endpoint</h3>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/education.course_creation_agent/chat</code>
            </div>

            <h3>Request Format</h3>
            <h4>Headers</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  'X-API-Key': 'your_api_key_here',
  'Content-Type': 'application/json'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h4>Request Body</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "optional-uuid-or-null",
  "message": "I want to create a course on Python programming for beginners"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  conversation_id: null,
  message: 'I want to create a course on Python programming for beginners'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h3>Example: Starting Course Creation</h3>
            <div class="code-block">
              <pre class="json-example">{{ getCourseCreationExample() }}</pre>
              <button @click="copyToClipboard(getCourseCreationExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Important:</strong> Maintain the same <code>conversation_id</code> throughout the entire 
              course creation process to preserve context and workflow state.
            </p>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "Agent's response with follow-up questions or course structure",
  "agent_id": "uuid-string"
}, null, 2) }}</pre>
            </div>
          </section>

          <!-- Language Practice Agent Section -->
          <section id="language-practice" class="docs-section-main">
            <h2>Language Practice Agent Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>education.language_practice_agent</code><br>
              A personal tutor that guides users through language learning with vocabulary, 
              grammar, conversation, and pronunciation practice.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Language Selection:</strong> User chooses target language</li>
              <li><strong>Placement Assessment:</strong> Agent assesses proficiency level (CEFR A1-C2)</li>
              <li><strong>Goal Setting:</strong> Agent understands learning goals and time commitment</li>
              <li><strong>Vocabulary Building:</strong> Agent creates vocabulary sets with spaced repetition</li>
              <li><strong>Grammar Practice:</strong> Agent provides interactive grammar exercises</li>
              <li><strong>Conversation Practice:</strong> Agent creates realistic dialogue scenarios</li>
              <li><strong>Pronunciation Training:</strong> Agent provides pronunciation exercises</li>
              <li><strong>Progress Tracking:</strong> Agent tracks progress with gamification (XP, levels, streaks)</li>
            </ol>

            <h3>Endpoint</h3>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/education.language_practice_agent/chat</code>
            </div>

            <h3>Request Format</h3>
            <h4>Headers</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  'X-API-Key': 'your_api_key_here',
  'Content-Type': 'application/json'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h4>Request Body</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "optional-uuid-or-null",
  "message": "I want to learn Spanish"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  conversation_id: null,
  message: 'I want to learn Spanish'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h3>Example: Starting Language Learning</h3>
            <div class="code-block">
              <pre class="json-example">{{ getLanguagePracticeExample() }}</pre>
              <button @click="copyToClipboard(getLanguagePracticeExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Tip:</strong> The agent maintains conversation context, so you can build on previous 
              interactions. For example, after selecting a language, you can ask for vocabulary without 
              repeating the language selection.
            </p>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "Agent's response with language learning guidance",
  "agent_id": "uuid-string"
}, null, 2) }}</pre>
            </div>
          </section>

          <!-- Micro-Learning Agent Section -->
          <section id="micro-learning" class="docs-section-main">
            <h2>Micro-Learning Agent Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>education.micro_learning_agent</code><br>
              A personal tutor that delivers daily bite-sized lessons for busy learners with interactive exercises, 
              spaced repetition, and progress tracking.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Onboarding:</strong> Agent understands learning goals, available time, and preferred topics</li>
              <li><strong>Daily Lesson:</strong> Agent generates focused lesson based on time availability (5/10/15 minutes)</li>
              <li><strong>Interactive Delivery:</strong> Agent presents lesson with examples, visual aids, and interactive elements</li>
              <li><strong>Quick Practice:</strong> Agent offers 2-3 question micro-quiz or interactive exercise</li>
              <li><strong>Immediate Feedback:</strong> Agent provides instant feedback and explanations</li>
              <li><strong>Progress Tracking:</strong> Agent updates streak, completion status, and learning history</li>
              <li><strong>Spaced Repetition:</strong> Agent schedules reviews at optimal intervals for retention</li>
              <li><strong>Learning Paths:</strong> Agent creates sequential micro-lessons that build on each other</li>
            </ol>

            <h3>Endpoint</h3>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/education.micro_learning_agent/chat</code>
            </div>

            <h3>Request Format</h3>
            <h4>Headers</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  'X-API-Key': 'your_api_key_here',
  'Content-Type': 'application/json'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h4>Request Body</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "optional-uuid-or-null",
  "message": "I want to learn Python basics in 10 minutes"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  conversation_id: null,
  message: 'I want to learn Python basics in 10 minutes'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h3>Example: Starting Micro-Learning</h3>
            <div class="code-block">
              <pre class="json-example">{{ getMicroLearningExample() }}</pre>
              <button @click="copyToClipboard(getMicroLearningExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Tip:</strong> The agent adapts lesson depth based on available time. Specify "5 minutes", "10 minutes", 
              or "15 minutes" to get appropriately sized lessons. The agent maintains conversation context to build sequential 
              learning paths.
            </p>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "Agent's response with micro-lesson content",
  "agent_id": "uuid-string"
}, null, 2) }}</pre>
            </div>
          </section>

          <!-- Quick Start Section -->
          <section id="quick-start" class="docs-section-main">
            <h2>Quick Start Guide</h2>
            <p class="section-description">
              Get started in 3 simple steps:
            </p>
            <ol class="flow-list">
              <li><strong>Create an API Key:</strong> Go to the API Keys page and create a new key (universal or agent-specific)</li>
              <li><strong>Choose an Agent:</strong> Select the agent slug you want to use (e.g., <code>education.personal_tutor</code>)</li>
              <li><strong>Make Your First Request:</strong> Send a POST request to the chat endpoint with your API key</li>
            </ol>

            <h3>Complete Example (JavaScript)</h3>
            <div class="code-block">
              <pre class="js-example">{{ getQuickStartExample() }}</pre>
              <button 
                @click="copyToClipboard(getQuickStartExample(), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>
          </section>

          <!-- Code Examples Section -->
          <section id="code-examples" class="docs-section-main">
            <h2>Code Examples</h2>
            
            <div class="example-section">
              <h3>cURL</h3>
              <div class="code-block">
                <pre class="curl-example">{{ getCurlExample() }}</pre>
                <button 
                  @click="copyToClipboard(getCurlExample(), false)" 
                  class="btn-copy-inline"
                >
                  📋
                </button>
              </div>
            </div>

            <div class="example-section">
              <h3>JavaScript (Fetch API)</h3>
              <div class="code-block">
                <pre class="js-example">{{ getJsExample() }}</pre>
                <button 
                  @click="copyToClipboard(getJsExample(), false)" 
                  class="btn-copy-inline"
                >
                  📋
                </button>
              </div>
            </div>

            <div class="example-section">
              <h3>Python (requests)</h3>
              <div class="code-block">
                <pre class="python-example">{{ getPythonExample() }}</pre>
                <button 
                  @click="copyToClipboard(getPythonExample(), false)" 
                  class="btn-copy-inline"
                >
                  📋
                </button>
              </div>
            </div>

            <div class="example-section">
              <h3>Node.js (axios)</h3>
              <div class="code-block">
                <pre class="node-example">{{ getNodeExample() }}</pre>
                <button 
                  @click="copyToClipboard(getNodeExample(), false)" 
                  class="btn-copy-inline"
                >
                  📋
                </button>
              </div>
            </div>
          </section>

          <!-- Error Codes Section -->
          <section id="errors" class="docs-section-main">
            <h2>Error Codes</h2>
            <div class="error-codes-table">
              <div class="error-row">
                <code class="status-code">400</code>
                <span class="error-desc">Bad Request - Invalid request body or parameters</span>
              </div>
              <div class="error-row">
                <code class="status-code">401</code>
                <span class="error-desc">Unauthorized - Missing or invalid API key</span>
              </div>
              <div class="error-row">
                <code class="status-code">404</code>
                <span class="error-desc">Not Found - Agent not found or API key not authorized for this agent</span>
              </div>
              <div class="error-row">
                <code class="status-code">429</code>
                <span class="error-desc">Too Many Requests - Rate limit exceeded</span>
              </div>
              <div class="error-row">
                <code class="status-code">500</code>
                <span class="error-desc">Internal Server Error - Server-side error</span>
              </div>
            </div>

            <h3>Important Notes</h3>
            <ul class="docs-notes">
              <li><strong>Universal vs Agent-Specific Keys:</strong> API keys can be universal (work with all agents) or agent-specific. Universal keys are more flexible but agent-specific keys provide better security.</li>
              <li><strong>Conversation Context:</strong> Include the same <code>conversation_id</code> in subsequent requests to maintain conversation history.</li>
              <li><strong>Rate Limits:</strong> Each API key has a configurable rate limit (default: 60 requests/minute). Exceeding the limit will result in a 429 error.</li>
              <li><strong>Security:</strong> Keep your API keys secure. They are shown only once when created. If lost, you'll need to create a new key.</li>
              <li><strong>Error Handling:</strong> The API returns standard HTTP status codes. Check the response status before processing the body.</li>
              <li><strong>Base URL:</strong> Make sure to use the correct base URL. For production: <code>https://agentic-platform.namatechnologlies.com</code>, for development: <code>http://localhost:8009</code></li>
              <li><strong>Domain Whitelisting:</strong> If you've configured domain whitelisting for your API key, ensure requests include the <code>Origin</code> header matching your whitelisted domain.</li>
              <li><strong>Quiz Generation:</strong> Quiz requests generate ALL questions in a single API call for efficiency. No need to make multiple requests.</li>
              <li><strong>Response Time:</strong> Agent responses typically take 2-10 seconds depending on complexity. Quiz generation may take 5-15 seconds for complete quizzes.</li>
            </ul>
          </section>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const copied = ref(false)
const activeTab = ref('overview')

const baseUrl = computed(() => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8009'
})

const tabs = [
  { id: 'overview', label: 'Overview', icon: '📋' },
  { id: 'personal-tutor', label: 'Personal Tutor', icon: '👨‍🏫' },
  { id: 'course-creation', label: 'Course Creation', icon: '📚' },
  { id: 'language-practice', label: 'Language Practice', icon: '🌐' },
  { id: 'micro-learning', label: 'Micro-Learning', icon: '📖' },
  { id: 'quick-start', label: 'Quick Start', icon: '🚀' },
  { id: 'code-examples', label: 'Code Examples', icon: '💻' },
  { id: 'errors', label: 'Error Codes', icon: '⚠️' }
]

function scrollToSection(sectionId: string) {
  const element = document.getElementById(sectionId)
  const scrollContainer = document.querySelector('.docs-content')
  
  if (element && scrollContainer) {
    const containerRect = scrollContainer.getBoundingClientRect()
    const elementRect = element.getBoundingClientRect()
    const headerOffset = 100
    const offsetPosition = elementRect.top - containerRect.top + scrollContainer.scrollTop - headerOffset

    scrollContainer.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    })
    activeTab.value = sectionId
  }
}

function handleScroll() {
  const sections = tabs.map(tab => ({
    id: tab.id,
    element: document.getElementById(tab.id)
  })).filter(s => s.element !== null)

  const scrollContainer = document.querySelector('.docs-content')
  if (!scrollContainer) return

  const scrollPosition = scrollContainer.scrollTop + 200

  for (let i = sections.length - 1; i >= 0; i--) {
    const section = sections[i]
    if (section.element) {
      const rect = section.element.getBoundingClientRect()
      const containerRect = scrollContainer.getBoundingClientRect()
      const elementTop = rect.top - containerRect.top + scrollContainer.scrollTop
      const elementBottom = elementTop + rect.height
      
      if (scrollPosition >= elementTop - 100 && scrollPosition < elementBottom) {
        activeTab.value = section.id
        break
      }
    }
  }
}

onMounted(() => {
  const scrollContainer = document.querySelector('.docs-content')
  if (scrollContainer) {
    scrollContainer.addEventListener('scroll', handleScroll)
    handleScroll() // Initial check
  }
})

onUnmounted(() => {
  const scrollContainer = document.querySelector('.docs-content')
  if (scrollContainer) {
    scrollContainer.removeEventListener('scroll', handleScroll)
  }
})

function getCurlExample(): string {
  return `curl -X POST "${baseUrl.value}/api/v1/public/agents/{agent_slug}/chat" \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Hello, how can you help me?",
    "conversation_id": null
  }'`
}

function getJsExample(): string {
  return `fetch("${baseUrl.value}/api/v1/public/agents/{agent_slug}/chat", {
  method: "POST",
  headers: {
    "X-API-Key": "your_api_key_here",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    message: "Hello, how can you help me?",
    conversation_id: null
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error("Error:", error));`
}

function getPythonExample(): string {
  return `import requests

url = "${baseUrl.value}/api/v1/public/agents/{agent_slug}/chat"
headers = {
    "X-API-Key": "your_api_key_here",
    "Content-Type": "application/json"
}
data = {
    "message": "Hello, how can you help me?",
    "conversation_id": None
}

response = requests.post(url, headers=headers, json=data)
print(response.json())`
}

function getNodeExample(): string {
  return `const axios = require('axios');

const url = "${baseUrl.value}/api/v1/public/agents/{agent_slug}/chat";
const headers = {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
};
const data = {
  message: "Hello, how can you help me?",
  conversation_id: null
};

axios.post(url, data, { headers })
  .then(response => console.log(response.data))
  .catch(error => console.error("Error:", error));`
}

function getQuizExample(): string {
  return `// Request a quiz from Personal Tutor Agent
POST ${baseUrl.value}/api/v1/public/agents/education.personal_tutor/chat
Headers: {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}
Body: {
  "conversation_id": "your_conversation_id_or_null",
  "message": "Generate a quiz about photosynthesis with 5 multiple choice questions at medium difficulty level"
}

// Response contains ALL questions in one response:
// **Question 1:** What is the primary pigment in photosynthesis?
// A) Chlorophyll
// B) Carotene
// C) Xanthophyll
// D) Anthocyanin
// **Answer:** A
// [All 5 questions follow...]`
}

function getCourseCreationExample(): string {
  return `// Start course creation workflow
POST ${baseUrl.value}/api/v1/public/agents/education.course_creation_agent/chat
Headers: {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}
Body: {
  "conversation_id": null,  // New conversation
  "message": "I want to create a course on Python programming for beginners"
}

// Agent will ask follow-up questions. Maintain conversation_id:
// Next request:
Body: {
  "conversation_id": "conversation_id_from_previous_response",
  "message": "The course should be 8 weeks long, for complete beginners"
}

// Continue the conversation to build the complete course structure`
}

function getLanguagePracticeExample(): string {
  return `// Start language learning journey
POST ${baseUrl.value}/api/v1/public/agents/education.language_practice_agent/chat
Headers: {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}
Body: {
  "conversation_id": null,
  "message": "I want to learn Spanish"
}

// Agent will guide through:
// 1. Proficiency assessment
// 2. Goal setting
// 3. Vocabulary building
// 4. Grammar practice
// 5. Conversation scenarios
// Maintain conversation_id throughout to preserve progress`
}

function getMicroLearningExample(): string {
  return `// Start micro-learning session
POST ${baseUrl.value}/api/v1/public/agents/education.micro_learning_agent/chat
Headers: {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}
Body: {
  "conversation_id": null,
  "message": "I want to learn Python basics in 10 minutes"
}

// Agent will:
// 1. Generate focused 10-minute lesson
// 2. Provide interactive exercises
// 3. Offer quick micro-quiz (2-3 questions)
// 4. Track progress and streaks
// 5. Schedule spaced repetition reviews
// Maintain conversation_id throughout to build learning path`
}

function getQuickStartExample(): string {
  return `// Step 1: Make your first API call
const response = await fetch("${baseUrl.value}/api/v1/public/agents/education.personal_tutor/chat", {
  method: "POST",
  headers: {
    "X-API-Key": "your_api_key_here",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    conversation_id: null,  // Creates new conversation
    message: "Hello, I want to learn about algebra"
  })
});

const data = await response.json();
console.log("Conversation ID:", data.conversation_id);
console.log("Agent Response:", data.message);

// Step 2: Continue the conversation using the same conversation_id
const response2 = await fetch("${baseUrl.value}/api/v1/public/agents/education.personal_tutor/chat", {
  method: "POST",
  headers: {
    "X-API-Key": "your_api_key_here",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    conversation_id: data.conversation_id,  // Use ID from previous response
    message: "Can you generate a quiz with 5 questions?"
  })
});

const data2 = await response2.json();
console.log("Quiz:", data2.message);`
}

function getQuizResponseExample(): string {
  return `{
  "conversation_id": "uuid-string",
  "message": "**Question 1:** What is 2 + 2?\nA) 3\nB) 4\nC) 5\nD) 6\n**Answer:** B\n\n**Question 2:** What is the capital of France?\nA) London\nB) Berlin\nC) Paris\nD) Madrid\n**Answer:** C\n\n[More questions...]",
  "agent_id": "uuid-string"
}`
}

function getQuizParserExample(): string {
  return `// Parse quiz response
function parseQuiz(quizText) {
  const questions = [];
  const questionRegex = /\\*\\*Question (\\d+):\\*\\*\\s*([^\\*]+?)(?=\\*\\*Question|\\*\\*Answer:|$)/gs;
  const answerRegex = /\\*\\*Answer:\\*\\*\\s*([A-D])/g;
  
  let match;
  while ((match = questionRegex.exec(quizText)) !== null) {
    const questionNum = parseInt(match[1]);
    const questionText = match[2].trim();
    
    // Extract options (A), B), C), D))
    const options = [];
    const optionRegex = /^([A-D])\\)\\s*(.+)$/gm;
    let optionMatch;
    while ((optionMatch = optionRegex.exec(questionText)) !== null) {
      options.push({
        letter: optionMatch[1],
        text: optionMatch[2].trim()
      });
    }
    
    // Find answer
    const answerMatch = quizText.substring(match.index).match(/\\*\\*Answer:\\*\\*\\s*([A-D])/);
    const answer = answerMatch ? answerMatch[1] : null;
    
    questions.push({
      number: questionNum,
      question: questionText.split(/^[A-D]\\)/gm)[0].trim(),
      options: options,
      answer: answer
    });
  }
  
  return questions;
}

// Usage
const response = await fetch("${baseUrl.value}/api/v1/public/agents/education.personal_tutor/chat", {
  method: "POST",
  headers: {
    "X-API-Key": "your_api_key_here",
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    conversation_id: null,
    message: "Generate a quiz about math with 5 questions"
  })
});

const data = await response.json();
const questions = parseQuiz(data.message);
console.log("Parsed questions:", questions);`
}

function getCompleteWorkflowExample(): string {
  return `// Complete workflow: Learning session with Personal Tutor
async function learningSession() {
  const apiKey = "your_api_key_here";
  const baseUrl = "${baseUrl.value}";
  let conversationId = null;
  
  // Step 1: Start conversation
  let response = await fetch(\`\${baseUrl}/api/v1/public/agents/education.personal_tutor/chat\`, {
    method: "POST",
    headers: {
      "X-API-Key": apiKey,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      conversation_id: null,
      message: "I want to learn about photosynthesis"
    })
  });
  let data = await response.json();
  conversationId = data.conversation_id;
  console.log("Agent:", data.message);
  
  // Step 2: Ask for explanation
  response = await fetch(\`\${baseUrl}/api/v1/public/agents/education.personal_tutor/chat\`, {
    method: "POST",
    headers: {
      "X-API-Key": apiKey,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      conversation_id: conversationId,  // Maintain context
      message: "Can you explain how photosynthesis works step by step?"
    })
  });
  data = await response.json();
  console.log("Explanation:", data.message);
  
  // Step 3: Request a quiz
  response = await fetch(\`\${baseUrl}/api/v1/public/agents/education.personal_tutor/chat\`, {
    method: "POST",
    headers: {
      "X-API-Key": apiKey,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      conversation_id: conversationId,  // Same conversation
      message: "Generate a quiz about photosynthesis with 5 multiple choice questions at medium difficulty"
    })
  });
  data = await response.json();
  console.log("Quiz:", data.message);
  // Parse and display quiz questions...
}

learningSession();`
}

function getListAgentsExample(): string {
  return `// Get list of available agents
GET ${baseUrl.value}/api/v1/public/agents
Headers: {
  "X-API-Key": "your_api_key_here"
}

// Response:
[
  {
    "id": "uuid",
    "name": "Personal Tutor",
    "slug": "education.personal_tutor",
    "description": "One-on-one tutor that explains concepts...",
    "category": "education"
  },
  {
    "id": "uuid",
    "name": "Course Creation Agent",
    "slug": "education.course_creation_agent",
    "description": "A personal tutor agent that guides...",
    "category": "education"
  },
  // ... more agents
]`
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (error) {
    console.error('Failed to copy:', error)
  }
}

function goBack() {
  router.push('/api-keys')
}
</script>

<style scoped>
.api-documentation-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  background-attachment: fixed;
  position: relative;
}

.page-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 24px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
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
  font-size: 32px;
  font-weight: 700;
  margin: 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.docs-layout {
  display: flex;
  min-height: calc(100vh - 80px);
  position: relative;
  z-index: 1;
}

.docs-sidebar {
  width: 280px;
  min-width: 280px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  padding: 24px 0;
  position: sticky;
  top: 0;
  height: calc(100vh - 80px);
  overflow-y: auto;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 16px;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
  width: 100%;
}

.nav-tab:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateX(4px);
}

.nav-tab.active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8));
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.tab-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.tab-label {
  flex: 1;
}

.docs-content {
  flex: 1;
  padding: 40px;
  overflow-y: auto;
  height: calc(100vh - 80px);
  scroll-behavior: smooth;
}

.documentation-container {
  display: flex;
  flex-direction: column;
  gap: 40px;
  max-width: 900px;
  margin: 0 auto;
}

.docs-section-main {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 32px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  scroll-margin-top: 100px;
  position: relative;
}

.docs-section-main h2 {
  color: white;
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 16px 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.docs-section-main h3 {
  color: white;
  font-size: 20px;
  font-weight: 600;
  margin: 24px 0 12px 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.section-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  line-height: 1.8;
  margin: 0 0 20px 0;
}

.section-description code,
.section-description strong {
  color: white;
  font-weight: 600;
}

.code-block {
  position: relative;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  overflow-x: auto;
  margin: 16px 0;
}

.code-block code,
.code-block pre {
  color: #e0e0e0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.url-code {
  font-size: 14px;
  color: #fff;
  font-weight: 600;
}

.btn-copy-inline {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 6px 10px;
  background: rgba(102, 126, 234, 0.8);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-copy-inline:hover {
  background: rgba(102, 126, 234, 1);
  transform: scale(1.05);
}

.docs-note {
  margin: 12px 0 0 0;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  line-height: 1.6;
}

.docs-note code {
  background: rgba(255, 255, 255, 0.2);
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #fff;
  font-weight: 600;
}

.endpoint-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 16px 0;
  flex-wrap: wrap;
}

.method-badge {
  display: inline-block;
  padding: 6px 14px;
  background: rgba(76, 175, 80, 0.8);
  color: white;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  border: 1px solid rgba(76, 175, 80, 0.5);
}

.endpoint-url {
  color: white;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 600;
}

.example-section {
  margin-bottom: 32px;
}

.example-section:last-child {
  margin-bottom: 0;
}

.json-example,
.curl-example,
.js-example,
.python-example,
.node-example {
  margin: 0;
  padding: 0;
  background: transparent;
  color: #e0e0e0;
}

.docs-notes {
  margin: 0;
  padding-left: 24px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 15px;
  line-height: 2;
}

.docs-notes li {
  margin-bottom: 12px;
}

.docs-notes code {
  background: rgba(255, 255, 255, 0.2);
  padding: 3px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #fff;
  font-weight: 600;
}

.docs-notes strong {
  color: white;
  font-weight: 600;
}

.error-codes-table {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.error-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.status-code {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(244, 67, 54, 0.8);
  color: white;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  font-family: 'Courier New', monospace;
  min-width: 50px;
  text-align: center;
}

.error-desc {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  flex: 1;
}

.agent-flow-section {
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.agent-flow-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.agent-flow-section h3 {
  color: white;
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 16px 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.agent-flow-section h4 {
  color: white;
  font-size: 18px;
  font-weight: 600;
  margin: 24px 0 12px 0;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

.flow-list {
  margin: 16px 0;
  padding-left: 24px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 15px;
  line-height: 2;
}

.flow-list li {
  margin-bottom: 12px;
}

.flow-list strong {
  color: white;
  font-weight: 600;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .docs-layout {
    flex-direction: column;
  }

  .docs-sidebar {
    width: 100%;
    min-width: 100%;
    height: auto;
    position: relative;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
    padding: 16px 0;
  }

  .sidebar-nav {
    flex-direction: row;
    overflow-x: auto;
    padding: 0 16px;
    gap: 8px;
  }

  .nav-tab {
    white-space: nowrap;
    min-width: fit-content;
  }

  .nav-tab:hover {
    transform: translateY(-2px);
  }

  .docs-content {
    max-width: 100%;
    padding: 24px 16px;
  }

  .tab-content {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 16px 20px;
  }

  h1 {
    font-size: 24px;
  }

  .docs-section-main {
    padding: 24px 20px;
  }

  .docs-section-main h2 {
    font-size: 24px;
  }

  .docs-section-main h3 {
    font-size: 18px;
  }
}
</style>

