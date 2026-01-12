<template>
  <div class="api-documentation-page">
    <header class="page-header">
      <div class="header-left">
        <button @click="goBack" class="btn-back">← Back</button>
        <h1>📚 API Documentation</h1>
      </div>
    </header>

    <main class="page-content">
      <div class="documentation-container">
        <!-- Overview Section -->
        <section class="docs-section-main">
          <h2>Overview</h2>
          <p class="section-description">
            This API allows external platforms to interact with AI agents through REST endpoints. 
            Our pre-built agents are <strong>not simple chatbots</strong> - they follow structured workflows 
            and guide users through multi-step processes. Each agent maintains conversation context 
            and provides personalized, tutor-like interactions.
          </p>
          <p class="section-description">
            <strong>Important:</strong> API keys can now be <strong>universal</strong> (work with all agents) 
            or <strong>agent-specific</strong>. When creating a key, you can choose to make it universal 
            or tie it to a specific agent.
          </p>
        </section>

        <!-- Pre-built Agents Section -->
        <section class="docs-section-main">
          <h2>Pre-built Agents & Their Flows</h2>
          
          <div class="agent-flow-section">
            <h3>1. Personal Tutor Agent</h3>
            <p class="section-description">
              <strong>Slug:</strong> <code>education.personal_tutor</code><br>
              A one-on-one tutor that explains concepts step-by-step, creates practice quizzes, 
              and builds study plans. This agent follows a structured learning flow.
            </p>
            
            <h4>Typical Flow:</h4>
            <ol class="flow-list">
              <li><strong>Initial Greeting:</strong> Agent introduces itself and asks what the user wants to learn</li>
              <li><strong>Topic Selection:</strong> User specifies a topic (e.g., "I want to learn about photosynthesis")</li>
              <li><strong>Concept Explanation:</strong> Agent explains concepts step-by-step with check-point questions</li>
              <li><strong>Practice Quiz:</strong> Agent generates quizzes with multiple questions in a single response</li>
              <li><strong>Study Plan:</strong> Agent can create personalized study plans</li>
            </ol>
            
            <h4>Example: Requesting a Quiz</h4>
            <div class="code-block">
              <pre class="json-example">{{ getQuizExample() }}</pre>
              <button @click="copyToClipboard(getQuizExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Note:</strong> The agent generates ALL quiz questions in a single API call. 
              The response will contain all questions formatted as:<br>
              <code>**Question 1:** [question] ... **Answer:** [letter]</code>
            </p>
          </div>

          <div class="agent-flow-section">
            <h3>2. Course Creation Agent</h3>
            <p class="section-description">
              <strong>Slug:</strong> <code>education.course_creation_agent</code><br>
              A personal tutor that guides users through creating comprehensive courses with 
              learning assessments, concept maps, workflow automation, and validation.
            </p>
            
            <h4>Typical Flow:</h4>
            <ol class="flow-list">
              <li><strong>Discovery Phase:</strong> Agent asks about learning objectives, target audience, duration, format</li>
              <li><strong>Structure Design:</strong> Agent creates course outline with modules and lessons</li>
              <li><strong>Concept Mapping:</strong> Agent visualizes relationships between topics</li>
              <li><strong>Assessment Design:</strong> Agent creates diagnostic, formative, and summative assessments</li>
              <li><strong>Workflow Creation:</strong> Agent designs automated workflows for course delivery</li>
              <li><strong>Validation:</strong> Agent validates content against educational standards</li>
            </ol>
            
            <h4>Example: Starting Course Creation</h4>
            <div class="code-block">
              <pre class="json-example">{{ getCourseCreationExample() }}</pre>
              <button @click="copyToClipboard(getCourseCreationExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Important:</strong> Maintain the same <code>conversation_id</code> throughout the entire 
              course creation process to preserve context and workflow state.
            </p>
          </div>

          <div class="agent-flow-section">
            <h3>3. Language Practice Agent</h3>
            <p class="section-description">
              <strong>Slug:</strong> <code>education.language_practice_agent</code><br>
              A personal tutor that guides users through language learning with vocabulary, 
              grammar, conversation, and pronunciation practice.
            </p>
            
            <h4>Typical Flow:</h4>
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
            
            <h4>Example: Starting Language Learning</h4>
            <div class="code-block">
              <pre class="json-example">{{ getLanguagePracticeExample() }}</pre>
              <button @click="copyToClipboard(getLanguagePracticeExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Tip:</strong> The agent maintains conversation context, so you can build on previous 
              interactions. For example, after selecting a language, you can ask for vocabulary without 
              repeating the language selection.
            </p>
          </div>
        </section>

        <!-- Base URL Section -->
        <section class="docs-section-main">
          <h2>Base URL</h2>
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
            Available agents: <code>education.personal_tutor</code>, <code>education.course_creation_agent</code>, <code>education.language_practice_agent</code>
          </p>
        </section>

        <!-- Authentication Section -->
        <section class="docs-section-main">
          <h2>Authentication</h2>
          <p class="section-description">
            All requests require an API key in the <code>X-API-Key</code> header. 
            API keys are agent-specific and can be created from the API Keys page.
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
        </section>

        <!-- Endpoint Section -->
        <section class="docs-section-main">
          <h2>Send Message to Agent</h2>
          <div class="endpoint-info">
            <code class="method-badge">POST</code>
            <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/{agent_slug}/chat</code>
          </div>
          
          <h3>Request Headers</h3>
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

          <h3>Request Body</h3>
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

          <h3>Response</h3>
          <div class="code-block">
            <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "Agent's response text",
  "agent_id": "uuid-string"
}, null, 2) }}</pre>
          </div>
        </section>

        <!-- Code Examples Section -->
        <section class="docs-section-main">
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

        <!-- Important Notes Section -->
        <section class="docs-section-main">
          <h2>Important Notes</h2>
          <ul class="docs-notes">
            <li><strong>Universal vs Agent-Specific Keys:</strong> API keys can be universal (work with all agents) or agent-specific. Universal keys are more flexible but agent-specific keys provide better security.</li>
            <li><strong>Conversation Context:</strong> Include the same <code>conversation_id</code> in subsequent requests to maintain conversation history.</li>
            <li><strong>Rate Limits:</strong> Each API key has a configurable rate limit (default: 60 requests/minute). Exceeding the limit will result in a 429 error.</li>
            <li><strong>Security:</strong> Keep your API keys secure. They are shown only once when created. If lost, you'll need to create a new key.</li>
            <li><strong>Error Handling:</strong> The API returns standard HTTP status codes. Check the response status before processing the body.</li>
            <li><strong>Base URL:</strong> Make sure to use the correct base URL. For development: <code>http://localhost:8009</code></li>
          </ul>
        </section>

        <!-- Error Codes Section -->
        <section class="docs-section-main">
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
        </section>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const copied = ref(false)

const baseUrl = computed(() => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8009'
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

.page-content {
  max-width: 1000px;
  margin: 40px auto;
  padding: 0 20px;
  position: relative;
  z-index: 1;
}

.documentation-container {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.docs-section-main {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 32px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
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
</style>

