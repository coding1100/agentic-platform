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
              Our pre-built agents are <strong>AI-based services and tools</strong>, not human-delivered teachers,
              tutors, or coaches. They follow structured workflows, maintain context across sessions,
              and support multi-step product experiences. API keys can be <strong>universal</strong> 
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
                Available agents: <code>education.personal_tutor</code>, <code>education.course_creation_agent</code>, <code>education.language_practice_agent</code>, <code>education.micro_learning_agent</code>, <code>education.exam_prep_agent</code>, <code>career.resume_review_agent</code>, <code>career.career_coach_agent</code>, <code>career.skill_gap_agent</code>, <code>health.fitness_coach_agent</code>
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
              <li><strong>Domain Whitelisting:</strong> Optional security feature. Restrict API key usage to specific web origins (e.g., <code>https://yourdomain.com</code> — scheme + domain only, no ports/paths). Leave empty to allow all origins. Server-to-server calls are allowed even when no <code>Origin</code> header is present.</li>
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
            <h2>Tutor Tool Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>education.personal_tutor</code><br>
              The Tutor Tool is an <strong>AI-powered learning workflow</strong>, not a human-delivered tutoring service.
              The primary product flow is <code>Subject + Academic Level -> Choose Action -> Results Workspace</code>.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Setup:</strong> Collect <code>subject</code> and <code>academic_level</code> with exact level values <code>high_school</code>, <code>college</code>, and <code>phd</code>.</li>
              <li><strong>Choose Action:</strong> The learner selects <code>ask_question</code>, <code>upload_notes</code>, or <code>practice</code>.</li>
              <li><strong>Structured AI Output:</strong> The Tutor Tool returns <code>explanation</code>, <code>steps</code>, and <code>practice_set</code>. <code>upload_notes</code> also returns <code>summary</code>.</li>
              <li><strong>Progress Tracking:</strong> Workspace state persists subject, academic level, optional hidden <code>learner_name</code>, recent sources, results, and progress metrics.</li>
              <li><strong>Optional Follow-Up Chat:</strong> Use the standard chat stream only for follow-up conversation after the main Tutor action completes.</li>
            </ol>

            <h3>Endpoints</h3>
            <div class="endpoint-info">
              <code class="method-badge">GET</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/tutor/{agent_id}/workspace</code>
            </div>
            <div class="endpoint-info">
              <code class="method-badge">PUT</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/tutor/{agent_id}/workspace</code>
            </div>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/tutor/{agent_id}/execute</code>
            </div>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/chat/{agent_id}/stream</code>
            </div>
            <p class="docs-note">
              The structured Tutor endpoints are authenticated dashboard APIs and use <code>Authorization: Bearer ...</code>.
              The public slug endpoint remains available for generic chat integrations, but the primary Tutor experience should use the structured Tutor APIs above.
            </p>

            <h3>Request Format</h3>
            <h4>Headers</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "Authorization": "Bearer your_jwt_token",
  "Content-Type": "application/json"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  Authorization: 'Bearer your_jwt_token',
  'Content-Type': 'application/json'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h4>Workspace State Example</h4>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "subject": "Organic Chemistry",
  "academic_level": "college",
  "learner_name": "Hidden learner identity from frontend",
  "selected_action": "practice",
  "selected_mode": "practice_quiz_generator",
  "progress": {
    "sessions_completed": 4,
    "practice_sessions_attempted": 3,
    "practice_sessions_completed": 2,
    "source_sessions": 1,
    "average_score": 84,
    "weak_topics": [
      "Reaction mechanisms"
    ],
    "mastery_by_topic": {
      "Stoichiometry": 91,
      "Reaction mechanisms": 62
    },
    "recent_activity": [
      "2026-04-22 14:20 - practice in Organic Chemistry"
    ],
    "next_recommended_action": "Upload notes for source-based review"
  },
  "recent_sources": [],
  "recent_results": []
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  subject: 'Organic Chemistry',
  academic_level: 'college',
  learner_name: 'Hidden learner identity from frontend',
  selected_action: 'practice',
  selected_mode: 'practice_quiz_generator',
  progress: {
    sessions_completed: 4,
    practice_sessions_attempted: 3,
    practice_sessions_completed: 2,
    source_sessions: 1,
    average_score: 84,
    weak_topics: ['Reaction mechanisms'],
    mastery_by_topic: {
      Stoichiometry: 91,
      'Reaction mechanisms': 62
    },
    recent_activity: ['2026-04-22 14:20 - practice in Organic Chemistry'],
    next_recommended_action: 'Upload notes for source-based review'
  },
  recent_sources: [],
  recent_results: []
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>
            <p class="docs-note">
              <code>learner_name</code> is optional and can be supplied invisibly by the frontend for continuity and progress tracking.
              It is never required to unlock the Tutor flow and should not appear as a visible onboarding field.
            </p>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ getQuizResponseExample() }}</pre>
              <button @click="copyToClipboard(getQuizResponseExample(), false)" class="btn-copy-inline">ðŸ“‹</button>
            </div>

            <h3>Example: Run Structured Tutor Action</h3>
            <div class="code-block">
              <pre class="json-example">{{ getQuizExample() }}</pre>
              <button @click="copyToClipboard(getQuizExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Notes:</strong> Main Tutor actions run through <code>/execute</code> in a single API call.
              Notes and PDFs should be converted to text client-side, and only source metadata should be persisted in workspace state.
            </p>

            <h3>Practice Set Handling</h3>
            <p class="section-description">
              Practice and quiz results can be graded locally in the frontend to avoid extra API round trips for every answer:
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
            <p class="section-description">
              This example loads the saved workspace, persists hidden learner context, executes a Tutor action, and then opens optional follow-up streaming chat.
            </p>
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

          <!-- Exam Prep Agent Section -->
          <section id="exam-prep" class="docs-section-main">
            <h2>Exam Prep Agent Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>education.exam_prep_agent</code><br>
              A personal tutor that helps you prepare for exams with practice tests, study schedules, 
              progress tracking, and exam strategies. Perfect for standardized tests, certification exams, 
              and academic exams.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Discovery Phase:</strong> Agent understands exam type, date, subject, and user's current level</li>
              <li><strong>Baseline Assessment:</strong> Agent assesses current knowledge through diagnostic questions</li>
              <li><strong>Study Plan Creation:</strong> Agent creates personalized study schedule leading up to exam date</li>
              <li><strong>Practice Exam Generation:</strong> Agent generates full-length practice exams for regular practice</li>
              <li><strong>Progress Analysis:</strong> Agent tracks progress and identifies weak areas after each practice</li>
              <li><strong>Targeted Review:</strong> Agent provides focused review sessions for weak areas</li>
              <li><strong>Strategy Guidance:</strong> Agent provides exam-taking strategies and time management tips</li>
              <li><strong>Readiness Assessment:</strong> Agent predicts exam readiness based on practice performance</li>
            </ol>

            <h3>Endpoint</h3>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/education.exam_prep_agent/chat</code>
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
  "message": "I'm preparing for the SAT Math exam on 2024-06-15"
}, null, 2) }}</pre>
              <button 
                @click="copyToClipboard(JSON.stringify({
  conversation_id: null,
  message: 'I\'m preparing for the SAT Math exam on 2024-06-15'
}, null, 2), false)" 
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h3>Example: Starting Exam Preparation</h3>
            <div class="code-block">
              <pre class="json-example">{{ getExamPrepExample() }}</pre>
              <button @click="copyToClipboard(getExamPrepExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Tip:</strong> The agent maintains conversation context throughout your exam preparation journey. 
              After creating a study schedule, you can ask for practice exams, track your progress, and get targeted 
              reviews without repeating information. The agent adapts to different exam types (SAT, GRE, certifications, etc.).
            </p>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "Agent's response with study schedule, practice exam, or progress analysis",
  "agent_id": "uuid-string"
}, null, 2) }}</pre>
            </div>

            <h3>Key Features</h3>
            <ul class="docs-notes">
              <li><strong>Practice Exams:</strong> Full-length exams with time limits, answer keys, and scoring rubrics</li>
              <li><strong>Study Schedules:</strong> Personalized daily/weekly plans based on exam date and available time</li>
              <li><strong>Progress Tracking:</strong> Monitor improvement over time with readiness assessment</li>
              <li><strong>Weak Area Analysis:</strong> Identify topics needing more focus based on practice results</li>
              <li><strong>Exam Strategies:</strong> Time management, question prioritization, and test-taking tips</li>
              <li><strong>Topic Reviews:</strong> Focused review sessions for specific topics with examples and practice</li>
            </ul>
          </section>

          <!-- Resume Review Agent Section -->
          <section id="resume-review" class="docs-section-main">
            <h2>Resume Review Agent Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>career.resume_review_agent</code><br>
              An ATS-optimized resume reviewer that returns structured, actionable feedback and rewrite suggestions.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Provide Resume:</strong> Send resume text (plain text) and optional job description</li>
              <li><strong>Role Context:</strong> Specify target role and seniority for calibrated feedback</li>
              <li><strong>ATS Review:</strong> Agent analyzes keyword match, impact, and formatting</li>
              <li><strong>Structured Output:</strong> Receive JSON report with scores, keywords, and rewrites</li>
            </ol>

            <h3>Endpoint</h3>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/career.resume_review_agent/chat</code>
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
  "message": "RESUME_REVIEW_REQUEST\\n{ \"action\": \"review_resume\", \"resume_text\": \"Paste resume text here\", \"job_description\": \"Optional job description\", \"target_role\": \"Senior Backend Engineer\", \"seniority\": \"mid\" }"
}, null, 2) }}</pre>
              <button
                @click="copyToClipboard(JSON.stringify({
  conversation_id: null,
  message: 'RESUME_REVIEW_REQUEST\\n' + JSON.stringify({
    action: 'review_resume',
    resume_text: 'Paste resume text here',
    job_description: 'Optional job description',
    target_role: 'Senior Backend Engineer',
    seniority: 'mid'
  })
}, null, 2), false)"
                class="btn-copy-inline"
              >
                📋
              </button>
            </div>

            <h3>Example: Requesting a Resume Review</h3>
            <div class="code-block">
              <pre class="json-example">{{ getResumeReviewExample() }}</pre>
              <button @click="copyToClipboard(getResumeReviewExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Tip:</strong> Use the <code>RESUME_REVIEW_REQUEST</code> marker to get a strict JSON response
              for dashboards and automated parsing.
            </p>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "{...json report...}",
  "agent_id": "uuid-string"
}, null, 2) }}</pre>
            </div>

            <h3>Key Features</h3>
            <ul class="docs-notes">
              <li><strong>Overall & ATS Scores:</strong> 0-100 scoring for quality and match</li>
              <li><strong>Keyword Gap Analysis:</strong> Missing skills/phrases from the job description</li>
              <li><strong>Rewrite Suggestions:</strong> Improved summary, experience bullets, and skills</li>
              <li><strong>Formatting Checks:</strong> ATS-friendly structure guidance</li>
            </ul>
          </section>

          <!-- Career Coach Agent Section -->
          <section id="career-coach" class="docs-section-main">
            <h2>Career Coach Agent Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>career.career_coach_agent</code><br>
              A structured career strategy agent for professionals that supports role direction, opportunity strategy,
              interview readiness, and weekly execution with action-oriented outputs.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Career Intake:</strong> Capture current role, target role, constraints, and goals</li>
              <li><strong>Opportunity Strategy:</strong> Define positioning, channel mix, and market-facing next moves</li>
              <li><strong>Roadmap Design:</strong> Build a practical 30/60/90-day plan with milestones and risks</li>
              <li><strong>Weekly Execution:</strong> Run check-ins and recalibrate plan based on progress</li>
              <li><strong>Interview Readiness:</strong> Generate a focused prep plan and question bank strategy</li>
            </ol>

            <h3>Endpoint</h3>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/career.career_coach_agent/chat</code>
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
              <pre class="json-example">{{ getCareerCoachRequestBodyExample() }}</pre>
              <button @click="copyToClipboard(getCareerCoachRequestBodyExample(), false)" class="btn-copy-inline">📋</button>
            </div>
            <p class="docs-note">
              <strong>Tip:</strong> Use the <code>CAREER_COACH_REQUEST</code> marker with a structured
              <code>action</code> and <code>payload</code> for deterministic, machine-readable outputs.
            </p>

            <h3>Example: Building a Career Roadmap</h3>
            <div class="code-block">
              <pre class="json-example">{{ getCareerCoachExample() }}</pre>
              <button @click="copyToClipboard(getCareerCoachExample(), false)" class="btn-copy-inline">📋</button>
            </div>

            <h3>Supported Actions</h3>
            <ul class="docs-notes">
              <li><code>intake_assessment</code>: structured profile and baseline career direction</li>
              <li><code>opportunity_strategy</code>: role-market positioning, channel mix, and 30-day experiments</li>
              <li><code>build_roadmap</code>: time-bound roadmap with milestones and guardrails</li>
              <li><code>weekly_checkin</code>: progress tracking, blockers, and next-week plan</li>
              <li><code>interview_readiness</code>: role-specific preparation strategy and practice plan</li>
            </ul>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "{...json strategy report...}",
  "agent_id": "uuid-string"
}, null, 2) }}</pre>
            </div>
          </section>

          <!-- Skill Gap Agent Section -->
          <section id="skill-gap" class="docs-section-main">
            <h2>Skill Gap Agent Integration</h2>
            <p class="section-description">
              <strong>Agent Slug:</strong> <code>career.skill_gap_agent</code><br>
              A structured employee development agent that identifies missing skills, prioritizes capability gaps,
              and builds measurable upskilling plans.
            </p>

            <h3>Typical Workflow</h3>
            <ol class="flow-list">
              <li><strong>Profile Baseline:</strong> Capture current role, skills, evidence, and constraints</li>
              <li><strong>Gap Identification:</strong> Compare current capabilities with target-role expectations</li>
              <li><strong>Development Plan:</strong> Build a timeline-based plan with weekly evidence outputs</li>
              <li><strong>Weekly Check-In:</strong> Track progress, blockers, and plan adjustments</li>
              <li><strong>Readiness Assessment:</strong> Measure readiness and remaining competency gaps</li>
            </ol>

            <h3>Endpoint</h3>
            <div class="endpoint-info">
              <code class="method-badge">POST</code>
              <code class="endpoint-url">{{ baseUrl }}/api/v1/public/agents/career.skill_gap_agent/chat</code>
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
                Copy
              </button>
            </div>

            <h4>Request Body</h4>
            <div class="code-block">
              <pre class="json-example">{{ getSkillGapRequestBodyExample() }}</pre>
              <button @click="copyToClipboard(getSkillGapRequestBodyExample(), false)" class="btn-copy-inline">Copy</button>
            </div>
            <p class="docs-note">
              <strong>Tip:</strong> Use the <code>SKILL_GAP_REQUEST</code> marker with a structured
              <code>action</code> and <code>payload</code> for deterministic, machine-readable outputs.
            </p>

            <h3>Example: Identifying Skill Gaps</h3>
            <div class="code-block">
              <pre class="json-example">{{ getSkillGapExample() }}</pre>
              <button @click="copyToClipboard(getSkillGapExample(), false)" class="btn-copy-inline">Copy</button>
            </div>

            <h3>Supported Actions</h3>
            <ul class="docs-notes">
              <li><code>profile_baseline</code>: build current capability snapshot and focus areas</li>
              <li><code>identify_skill_gaps</code>: prioritize missing skills and quick wins for target role</li>
              <li><code>build_development_plan</code>: generate timeline-based upskilling plan</li>
              <li><code>weekly_progress_checkin</code>: assess execution progress and adjustments</li>
              <li><code>readiness_assessment</code>: evaluate target-role readiness with competency breakdown</li>
            </ul>

            <h3>Response Format</h3>
            <div class="code-block">
              <pre class="json-example">{{ JSON.stringify({
  "conversation_id": "uuid-string",
  "message": "{...json skill gap report...}",
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
              <li><strong>Domain Whitelisting:</strong> Whitelisting is enforced only when an <code>Origin</code> (or <code>Referer</code>) header is present. Browser calls include this automatically; server-to-server calls typically do not and are allowed. If you want strict origin enforcement, send a matching <code>Origin</code> header.</li>
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
  return import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8009' : window.location.origin)
})

const tabs = [
  { id: 'overview', label: 'Overview', icon: '📋' },
  { id: 'personal-tutor', label: 'Tutor Tool', icon: '👨‍🏫' },
  { id: 'course-creation', label: 'Course Creation', icon: '📚' },
  { id: 'language-practice', label: 'Language Practice', icon: '🌐' },
  { id: 'micro-learning', label: 'Micro-Learning', icon: '📖' },
  { id: 'exam-prep', label: 'Exam Prep', icon: '📝' },
  { id: 'resume-review', label: 'Resume Review', icon: '📄' },
  { id: 'career-coach', label: 'Career Coach', icon: '🧭' },
  { id: 'skill-gap', label: 'Skill Gap', icon: 'SG' },
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
  return `// Execute a structured Tutor action
POST ${baseUrl.value}/api/v1/tutor/{agent_id}/execute
Headers: {
  "Authorization": "Bearer your_jwt_token",
  "Content-Type": "application/json"
}
Body: {
  "action": "practice",
  "learning_mode": "practice_quiz_generator",
  "subject": "Photosynthesis",
  "academic_level": "high_school",
  "learner_name": "Hidden learner identity from frontend",
  "prompt": "Create a focused review set for the light-dependent reactions.",
  "question_count": 5,
  "practice_format": "multiple_choice"
}

// The response includes explanation, steps, key_concepts,
// suggested_next_actions, and a structured practice_set.`
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

function getExamPrepExample(): string {
  return `// Start exam preparation journey
POST ${baseUrl.value}/api/v1/public/agents/education.exam_prep_agent/chat
Headers: {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}
Body: {
  "conversation_id": null,
  "message": "I'm preparing for the SAT Math exam on 2024-06-15. I can study 2 hours per day."
}

// Agent will guide through:
// 1. Understanding exam requirements
// 2. Creating personalized study schedule
// 3. Generating practice exams
// 4. Tracking progress over time
// 5. Identifying weak areas
// 6. Providing targeted reviews
// 7. Sharing exam-taking strategies
// Maintain conversation_id throughout to preserve progress and context`
}

function getResumeReviewExample(): string {
  return `// Request resume review with structured payload
POST ${baseUrl.value}/api/v1/public/agents/career.resume_review_agent/chat
Headers: {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}
Body: {
  "conversation_id": null,
  "message": "RESUME_REVIEW_REQUEST
{
  \\"action\\": \\"review_resume\\",
  \\"resume_text\\": \\"<paste resume text here>\\",
  \\"job_description\\": \\"<optional job description>\\",
  \\"target_role\\": \\"Senior Backend Engineer\\",
  \\"seniority\\": \\"mid\\"
}"
}

// Response message contains a JSON report with scores, keywords, and rewrites.
// Keep the same conversation_id for follow-up questions.`
}

function getCareerCoachRequestBodyExample(): string {
  return JSON.stringify({
    conversation_id: 'optional-uuid-or-null',
    message: 'CAREER_COACH_REQUEST\n' + JSON.stringify({
      action: 'opportunity_strategy',
      payload: {
        current_role: 'Product Analyst',
        target_role: 'Senior Product Manager',
        years_experience: 4,
        weekly_hours: 6,
        timeline_weeks: 12,
        current_skills: ['Stakeholder communication', 'Analytics'],
        achievements: ['Led roadmap prioritization for 2 product launches'],
        constraints: [
          'Limited weekday availability'
        ],
        career_interests: ['B2B SaaS product strategy', 'People leadership']
      }
    })
  }, null, 2)
}

function getCareerCoachExample(): string {
  return `// Build an opportunity strategy with structured payload
POST ${baseUrl.value}/api/v1/public/agents/career.career_coach_agent/chat
Headers: {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}
Body: {
  "conversation_id": null,
  "message": "CAREER_COACH_REQUEST
{
  \\"action\\": \\"opportunity_strategy\\",
  \\"payload\\": {
    \\"current_role\\": \\"Software Engineer\\",
    \\"target_role\\": \\"Engineering Manager\\",
    \\"years_experience\\": 6,
    \\"weekly_hours\\": 6,
    \\"timeline_weeks\\": 16,
    \\"current_skills\\": [\\"System design\\", \\"Execution\\"],
    \\"constraints\\": [\\"Can allocate 6 hours/week\\"]
  }
}"
}

// Response message contains structured JSON with positioning, role tracks, channel mix, and experiments.
// Reuse conversation_id for follow-up actions like "weekly_checkin" or "interview_readiness".`
}

function getSkillGapRequestBodyExample(): string {
  return JSON.stringify({
    conversation_id: 'optional-uuid-or-null',
    message: 'SKILL_GAP_REQUEST\n' + JSON.stringify({
      action: 'identify_skill_gaps',
      payload: {
        current_role: 'Backend Engineer',
        target_role: 'Senior Backend Engineer',
        years_experience: 4,
        weekly_learning_hours: 5,
        current_skills: [
          'API design',
          'Database fundamentals',
          'Service debugging'
        ],
        role_expectations: [
          'Distributed systems',
          'Performance tuning',
          'Technical leadership'
        ],
        constraints: [
          'Can commit 5 hours per week'
        ]
      }
    })
  }, null, 2)
}

function getSkillGapExample(): string {
  return `// Identify employee skill gaps with structured payload
POST ${baseUrl.value}/api/v1/public/agents/career.skill_gap_agent/chat
Headers: {
  "X-API-Key": "your_api_key_here",
  "Content-Type": "application/json"
}
Body: {
  "conversation_id": null,
  "message": "SKILL_GAP_REQUEST
{
  \\"action\\": \\"identify_skill_gaps\\",
  \\"payload\\": {
    \\"current_role\\": \\"Data Analyst\\",
    \\"target_role\\": \\"Senior Data Analyst\\",
    \\"years_experience\\": 3,
    \\"current_skills\\": [\\"SQL\\", \\"Tableau\\", \\"Stakeholder reporting\\"],
    \\"role_expectations\\": [\\"Experiment design\\", \\"Advanced statistics\\", \\"Data storytelling\\"]
  }
}"
}

// Response message contains JSON with prioritized gaps, quick wins, and development recommendations.
// Reuse conversation_id for actions like "build_development_plan" and "weekly_progress_checkin".`
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
  "action": "practice",
  "learning_mode": "practice_quiz_generator",
  "subject": "Photosynthesis",
  "academic_level": "high_school",
  "learner_name": "Hidden learner identity from frontend",
  "summary": null,
  "explanation": "Photosynthesis converts light energy into stored chemical energy. Focus first on where the light-dependent reactions happen and what outputs they produce.",
  "steps": [
    "Review chloroplast structure and identify the thylakoid membrane.",
    "Track how light excites electrons in photosystem II and photosystem I.",
    "Check how ATP and NADPH support the Calvin cycle."
  ],
  "practice_set": {
    "title": "Photosynthesis review set",
    "instructions": "Answer each question, then compare your choice with the key.",
    "questions": [
      {
        "id": "q1",
        "prompt": "Where do the light-dependent reactions take place?",
        "type": "multiple_choice",
        "concept": "Light-dependent reactions",
        "options": [
          { "id": "A", "text": "Thylakoid membrane" },
          { "id": "B", "text": "Mitochondrial matrix" },
          { "id": "C", "text": "Ribosome" },
          { "id": "D", "text": "Golgi apparatus" }
        ],
        "answer": "A",
        "explanation": "Photosystems and the electron transport chain are embedded in the thylakoid membrane."
      }
    ]
  },
  "key_concepts": [
    "Light-dependent reactions",
    "ATP and NADPH",
    "Chloroplast structure"
  ],
  "progress_snapshot": {
    "sessions_completed": 5,
    "practice_sessions_attempted": 4,
    "practice_sessions_completed": 3,
    "source_sessions": 1,
    "average_score": 86,
    "weak_topics": ["Calvin cycle"],
    "mastery_by_topic": {
      "Light-dependent reactions": 90,
      "Calvin cycle": 63
    },
    "recent_activity": [
      "2026-04-22 14:40 - practice in Photosynthesis"
    ],
    "next_recommended_action": "Upload notes for source-based review"
  },
  "suggested_next_actions": [
    "Ask for a simpler explanation of the Calvin cycle",
    "Generate a mixed practice set",
    "Upload notes for source-based learning"
  ]
}`
}

function getQuizParserExample(): string {
  return `// Grade a Tutor practice_set locally
function gradePracticeSet(practiceSet, answers) {
  const results = practiceSet.questions.map((question) => {
    const submitted = answers[question.id];
    const expected = question.answer?.trim().toLowerCase();
    const received = String(submitted || '').trim().toLowerCase();
    const isCorrect = expected ? received === expected : false;

    return {
      id: question.id,
      concept: question.concept || 'General',
      correct: isCorrect
    };
  });

  const total = results.length || 1;
  const correct = results.filter((item) => item.correct).length;
  const weakTopics = [...new Set(results.filter((item) => !item.correct).map((item) => item.concept))];
  const masteredTopics = [...new Set(results.filter((item) => item.correct).map((item) => item.concept))];

  return {
    score: Math.round((correct / total) * 100),
    weakTopics,
    masteredTopics
  };
}

// Usage
const result = gradePracticeSet(tutorResponse.practice_set, {
  q1: "A",
  q2: "chlorophyll absorbs light"
});

console.log(result.score, result.weakTopics, result.masteredTopics);`
}

function getCompleteWorkflowExample(): string {
  return `// Complete workflow: structured Tutor session + optional chat stream
async function tutorSession(agentId, token) {
  const baseUrl = "${baseUrl.value}";
  const headers = {
    "Authorization": \`Bearer \${token}\`,
    "Content-Type": "application/json"
  };

  // Step 1: Load saved workspace
  let response = await fetch(\`\${baseUrl}/api/v1/tutor/\${agentId}/workspace\`, {
    headers
  });
  let workspace = await response.json();

  // Step 2: Persist hidden learner identity from the frontend if available
  workspace = {
    ...workspace,
    subject: workspace.subject || "Photosynthesis",
    academic_level: workspace.academic_level || "high_school",
    learner_name: "Hidden learner identity from frontend"
  };

  await fetch(\`\${baseUrl}/api/v1/tutor/\${agentId}/workspace\`, {
    method: "PUT",
    headers,
    body: JSON.stringify(workspace)
  });

  // Step 3: Run the main Tutor action
  response = await fetch(\`\${baseUrl}/api/v1/tutor/\${agentId}/execute\`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      action: "upload_notes",
      learning_mode: "source_based_learning",
      subject: "Photosynthesis",
      academic_level: "high_school",
      learner_name: workspace.learner_name,
      source_kind: "pdf",
      source_name: "chapter-3.pdf",
      source_text: "Paste or extract PDF text here",
      prompt: "Summarize the source, explain the core process, and generate practice."
    })
  });

  const tutorResult = await response.json();
  console.log(tutorResult.summary);
  console.log(tutorResult.explanation);
  console.log(tutorResult.practice_set.questions);

  // Step 4: Optional follow-up chat stream after the structured Tutor response
  const streamResponse = await fetch(\`\${baseUrl}/api/v1/chat/\${agentId}/stream\`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      conversation_id: null,
      message: "Give me one more analogy for photosystem II."
    })
  });

  const reader = streamResponse.body.getReader();
  const decoder = new TextDecoder();
  let streamed = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    streamed += decoder.decode(value, { stream: true });
  }

  console.log(streamed);
}`
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
    "description": "AI-powered Tutor Tool for structured explanations, notes, and practice...",
    "category": "education"
  },
  {
    "id": "uuid",
    "name": "Course Creation Agent",
    "slug": "education.course_creation_agent",
    "description": "A personal tutor agent that guides...",
    "category": "education"
  },
  {
    "id": "uuid",
    "name": "Career Coach Agent",
    "slug": "career.career_coach_agent",
    "description": "Structured career strategy and execution coaching...",
    "category": "career"
  },
  {
    "id": "uuid",
    "name": "Skill Gap Agent",
    "slug": "career.skill_gap_agent",
    "description": "Employee capability gap detection and development planning...",
    "category": "career"
  },
  {
    "id": "uuid",
    "name": "Resume Review Agent",
    "slug": "career.resume_review_agent",
    "description": "ATS-optimized resume review agent with structured feedback...",
    "category": "career"
  },
  {
    "id": "uuid",
    "name": "Fitness Coach Agent",
    "slug": "health.fitness_coach_agent",
    "description": "Adaptive workout coaching with weekly feedback-driven adjustments...",
    "category": "health"
  },
  // ... more agents
]`
}

async function copyToClipboard(text: string, _inline: boolean = false) {
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
