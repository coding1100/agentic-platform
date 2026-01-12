from typing import List
from langchain_core.tools import Tool


PREBUILT_AGENT_SLUGS = {
  "personal_tutor": "education.personal_tutor",
  "course_creation_agent": "education.course_creation_agent",
  "language_practice_agent": "education.language_practice_agent",
}


def _generate_quiz(topic: str, difficulty: str = "medium", num_questions: int = 5) -> str:
  """Generate a complete quiz directly using Gemini API in a single call.
  
  This function directly calls Gemini to generate ALL quiz questions at once,
  avoiding multiple API calls. The agent should use this tool when quiz is requested.
  
  Args:
    topic: The subject/topic for the quiz
    difficulty: Difficulty level (easy, medium, hard)
    num_questions: Number of questions to generate (default: 5)
  
  Returns:
    Complete quiz with all questions in the exact format specified.
  """
  try:
    # Ensure num_questions is an integer (handle type conversion safely)
    if isinstance(num_questions, str):
      try:
        num_questions = int(num_questions)
      except (ValueError, TypeError):
        num_questions = 5
    elif not isinstance(num_questions, (int, float)):
      num_questions = 5
    
    difficulty = str(difficulty).lower() if difficulty else "medium"
    topic = str(topic) if topic else "general knowledge"
    num_questions = max(1, min(20, int(num_questions)))  # Limit between 1-20
    
    # Import Gemini client to generate quiz directly
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    # Create a focused prompt for quiz generation
    quiz_prompt = f"""Generate a complete multiple-choice quiz with {num_questions} questions about "{topic}" at {difficulty} difficulty level.

CRITICAL REQUIREMENTS - FOLLOW EXACTLY:
1. Start IMMEDIATELY with **Question 1:** - NO text before it
2. NO preamble, NO introduction, NO conversational text
3. NO emojis, NO special characters except **Question** and **Answer** markers
4. Each question must have exactly 4 options labeled A), B), C), D)
5. Each option must be on its own line
6. Include **Answer:** [letter] immediately after each question's options
7. End after the last answer - NO closing text

OUTPUT FORMAT (generate ALL {num_questions} questions in this exact format):

**Question 1:** [Your complete first question here]
A) [First option - must be plausible]
B) [Second option - must be plausible]
C) [Third option - must be plausible]
D) [Fourth option - must be plausible]
**Answer:** [A, B, C, or D]

**Question 2:** [Your complete second question here]
A) [First option]
B) [Second option]
C) [Third option]
D) [Fourth option]
**Answer:** [A, B, C, or D]

[Continue for all {num_questions} questions...]

Generate the complete quiz now:"""
    
    # Generate quiz in a single API call using GeminiClient
    quiz_content = gemini_client.generate_response(
      system_prompt="You are a quiz generator. Generate complete multiple-choice quizzes following the exact format specified.",
      messages=[{"role": "user", "content": quiz_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    # Clean the response to ensure it starts with Question 1
    if quiz_content:
      # Find the first question marker
      question_start = quiz_content.find("**Question 1:**")
      if question_start == -1:
        question_start = quiz_content.find("Question 1:")
      
      if question_start > 0:
        quiz_content = quiz_content[question_start:].strip()
      
      # Ensure it ends properly (remove any trailing text after last answer)
      # Find the last **Answer:** marker
      last_answer_pos = quiz_content.rfind("**Answer:**")
      if last_answer_pos == -1:
        last_answer_pos = quiz_content.rfind("Answer:")
      
      if last_answer_pos > 0:
        # Extract up to 50 characters after the last answer (to include the answer letter)
        remaining = quiz_content[last_answer_pos:]
        lines = remaining.split('\n')
        if len(lines) > 0:
          # Keep the answer line and remove everything after
          answer_line = lines[0].strip()
          quiz_content = quiz_content[:last_answer_pos] + answer_line
    
    return quiz_content if quiz_content else f"**Question 1:** Quiz generation failed. Please try again.\nA) Option A\nB) Option B\nC) Option C\nD) Option D\n**Answer:** A"
    
  except Exception as e:
    # Fallback: return a template if direct generation fails
    import traceback
    print(f"Error in _generate_quiz: {traceback.format_exc()}")
    # Return a simple template as fallback
    try:
      num_questions = max(1, min(20, int(num_questions) if isinstance(num_questions, (int, float, str)) else 5))
    except:
      num_questions = 5
    return f"**Question 1:** Error generating quiz. Please try again.\nA) Option A\nB) Option B\nC) Option C\nD) Option D\n**Answer:** A"


def _build_study_plan(goal: str, weeks: int = 4) -> str:
  """Create a high-level weekly study plan outline."""
  weeks = max(1, min(52, int(weeks)))
  lines = [f"# Study plan for: {goal}", ""]
  for i in range(1, weeks + 1):
    lines.append(f"## Week {i}")
    lines.append(f"- Learning objective for week {i} related to {goal}.")
    lines.append("- Key resources (to be refined by the agent).")
    lines.append("- Practice / project work.")
    lines.append("")
  return "\n".join(lines)


# Course Creation Agent Tools
def _create_course_structure(course_title: str, learning_objectives: str, duration_weeks: int = 8) -> str:
  """Create a structured course outline with modules, lessons, and learning objectives.
  
  Args:
    course_title: The title of the course
    learning_objectives: Comma-separated list of learning objectives
    duration_weeks: Number of weeks the course should span (default: 8)
  
  Returns:
    A structured course outline template.
  """
  duration_weeks = max(1, min(52, int(duration_weeks)))
  objectives = [obj.strip() for obj in learning_objectives.split(",")]
  
  template = f"""COURSE STRUCTURE PARAMETERS:
Course Title: {course_title}
Duration: {duration_weeks} weeks
Learning Objectives: {', '.join(objectives)}

YOU MUST NOW GENERATE THE COMPLETE COURSE STRUCTURE FOLLOWING THIS FORMAT:

# {course_title}

## Course Overview
- Duration: {duration_weeks} weeks
- Learning Objectives:
{chr(10).join(f'  - {obj}' for obj in objectives)}

## Course Modules

[Generate {duration_weeks // 2 if duration_weeks >= 4 else 2} modules, each with 2-4 lessons]

### Module 1: [Module Name]
**Learning Goals:**
- [Goal 1]
- [Goal 2]

**Lessons:**
1. [Lesson 1 Title]
   - Topics covered: [topic 1, topic 2]
   - Duration: [X hours]
   - Assessment: [type]

2. [Lesson 2 Title]
   - Topics covered: [topic 1, topic 2]
   - Duration: [X hours]
   - Assessment: [type]

[Continue for all modules...]

## Assessment Strategy
- Formative assessments: [description]
- Summative assessments: [description]
- Final project/capstone: [description]

## Resources and Materials
- Required readings: [list]
- Recommended resources: [list]
- Tools and software: [list]"""
  
  return template


def _create_learning_assessment(topic: str, assessment_type: str = "comprehensive", num_questions: int = 10) -> str:
  """Create a learning assessment for a specific topic.
  
  Args:
    topic: The topic/subject for the assessment
    assessment_type: Type of assessment (diagnostic, formative, summative, comprehensive)
    num_questions: Number of questions (default: 10)
  
  Returns:
    Assessment parameters and structure.
  """
  num_questions = max(5, min(50, int(num_questions)))
  assessment_type = assessment_type.lower()
  
  template = f"""LEARNING ASSESSMENT PARAMETERS:
Topic: {topic}
Assessment Type: {assessment_type}
Number of Questions: {num_questions}

YOU MUST NOW GENERATE THE COMPLETE ASSESSMENT FOLLOWING THIS FORMAT:

# {assessment_type.title()} Assessment: {topic}

## Assessment Overview
- Topic: {topic}
- Type: {assessment_type}
- Total Questions: {num_questions}
- Estimated Time: [X minutes]

## Questions

[Generate {num_questions} questions with variety: multiple choice, short answer, essay, practical exercises]

**Question 1:** [Question text]
[If MCQ: Provide 4 options A-D]
**Answer:** [Answer or rubric]

[Continue for all questions...]

## Scoring Rubric
- [Criteria 1]: [Points/Percentage]
- [Criteria 2]: [Points/Percentage]
- [Criteria 3]: [Points/Percentage]

## Feedback Guidelines
- [Guideline for providing constructive feedback]
- [Areas to focus on for improvement]"""
  
  return template


def _create_concept_map(main_concept: str, related_concepts: str = "") -> str:
  """Generate a concept map showing relationships between concepts.
  
  Args:
    main_concept: The central concept
    related_concepts: Comma-separated list of related concepts (optional, can be auto-generated)
  
  Returns:
    Concept map structure in text format.
  """
  if related_concepts:
    concepts = [c.strip() for c in related_concepts.split(",")]
  else:
    concepts = []
  
  template = f"""CONCEPT MAP PARAMETERS:
Main Concept: {main_concept}
Related Concepts: {', '.join(concepts) if concepts else '[Auto-generate based on main concept]'}

YOU MUST NOW GENERATE THE COMPLETE CONCEPT MAP FOLLOWING THIS FORMAT:

# Concept Map: {main_concept}

## Central Concept
**{main_concept}**

## Primary Relationships

### Direct Connections
- **{main_concept}** → [Related Concept 1]
  - Relationship: [Type of relationship]
  - Description: [How they connect]

- **{main_concept}** → [Related Concept 2]
  - Relationship: [Type of relationship]
  - Description: [How they connect]

### Secondary Relationships
- [Related Concept 1] → [Sub-concept 1]
- [Related Concept 1] → [Sub-concept 2]
- [Related Concept 2] → [Sub-concept 3]

## Concept Hierarchy
```
{main_concept}
├── [Primary Branch 1]
│   ├── [Sub-concept 1.1]
│   └── [Sub-concept 1.2]
├── [Primary Branch 2]
│   ├── [Sub-concept 2.1]
│   └── [Sub-concept 2.2]
└── [Primary Branch 3]
    └── [Sub-concept 3.1]
```

## Learning Path Recommendations
1. Start with: [Starting concept]
2. Then explore: [Next concepts in order]
3. Advanced topics: [Advanced concepts]

## Key Relationships Summary
- [Relationship 1]: [Brief description]
- [Relationship 2]: [Brief description]
- [Relationship 3]: [Brief description]"""
  
  return template


def _create_workflow_automation(workflow_name: str, steps: str, automation_type: str = "learning") -> str:
  """Create an automated workflow for course creation or learning processes.
  
  Args:
    workflow_name: Name of the workflow
    steps: Comma-separated list of workflow steps
    automation_type: Type of workflow (learning, assessment, content_creation, course_delivery)
  
  Returns:
    Workflow automation structure.
  """
  step_list = [s.strip() for s in steps.split(",")]
  
  template = f"""WORKFLOW AUTOMATION PARAMETERS:
Workflow Name: {workflow_name}
Type: {automation_type}
Steps: {', '.join(step_list)}

YOU MUST NOW GENERATE THE COMPLETE WORKFLOW FOLLOWING THIS FORMAT:

# Automated Workflow: {workflow_name}

## Workflow Overview
- **Name:** {workflow_name}
- **Type:** {automation_type}
- **Total Steps:** {len(step_list)}
- **Estimated Duration:** [X hours/days]

## Workflow Steps

### Step 1: {step_list[0] if step_list else '[Step 1 Name]'}
**Description:** [What happens in this step]
**Automation:** [How this step is automated]
**Dependencies:** [What must be completed before this]
**Output:** [What this step produces]
**Validation:** [How to validate this step completed successfully]

### Step 2: {step_list[1] if len(step_list) > 1 else '[Step 2 Name]'}
**Description:** [What happens in this step]
**Automation:** [How this step is automated]
**Dependencies:** [What must be completed before this]
**Output:** [What this step produces]
**Validation:** [How to validate this step completed successfully]

[Continue for all steps...]

## Automation Triggers
- **Start Trigger:** [What initiates this workflow]
- **Step Triggers:** [What triggers each subsequent step]
- **Completion Trigger:** [What indicates workflow completion]

## Error Handling
- **Retry Logic:** [How to handle failures]
- **Fallback Actions:** [What to do if step fails]
- **Notification Rules:** [When to alert stakeholders]

## Monitoring and Auditing
- **Key Metrics:** [What to track]
- **Success Criteria:** [How to measure success]
- **Audit Log Points:** [What to log for security/auditing]"""
  
  return template


def _create_meeting_notes_template(meeting_type: str = "course_planning", participants: str = "") -> str:
  """Generate a structured template for meeting notes related to course creation.
  
  Args:
    meeting_type: Type of meeting (course_planning, review, assessment_design, etc.)
    participants: Comma-separated list of participants (optional)
  
  Returns:
    Meeting notes template structure.
  """
  if participants:
    participant_list = [p.strip() for p in participants.split(",")]
  else:
    participant_list = []
  
  template = f"""MEETING NOTES TEMPLATE PARAMETERS:
Meeting Type: {meeting_type}
Participants: {', '.join(participant_list) if participant_list else '[To be filled]'}

YOU MUST NOW GENERATE THE MEETING NOTES TEMPLATE FOLLOWING THIS FORMAT:

# Meeting Notes: {meeting_type.replace('_', ' ').title()}

## Meeting Information
- **Date:** [Date]
- **Time:** [Start time] - [End time]
- **Type:** {meeting_type.replace('_', ' ').title()}
- **Participants:** {', '.join(participant_list) if participant_list else '[List participants]'}
- **Facilitator:** [Name]

## Agenda
1. [Agenda item 1]
2. [Agenda item 2]
3. [Agenda item 3]

## Discussion Points

### Topic 1: [Topic Name]
- **Key Points:**
  - [Point 1]
  - [Point 2]
- **Decisions Made:**
  - [Decision 1]
- **Action Items:**
  - [Action 1] - Owner: [Name] - Due: [Date]

### Topic 2: [Topic Name]
- **Key Points:**
  - [Point 1]
  - [Point 2]
- **Decisions Made:**
  - [Decision 1]
- **Action Items:**
  - [Action 1] - Owner: [Name] - Due: [Date]

## Decisions Summary
1. [Decision 1]
2. [Decision 2]
3. [Decision 3]

## Action Items
| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| [Task 1] | [Owner] | [Date] | [Status] |
| [Task 2] | [Owner] | [Date] | [Status] |

## Next Steps
- [Next step 1]
- [Next step 2]

## Follow-up Required
- [Follow-up item 1]
- [Follow-up item 2]"""
  
  return template


def _validate_course_content(course_structure: str, validation_criteria: str = "comprehensive") -> str:
  """Validate course content against educational standards and best practices.
  
  Args:
    course_structure: Description or summary of the course structure
    validation_criteria: Type of validation (comprehensive, accessibility, learning_objectives, assessment_alignment)
  
  Returns:
    Validation report with recommendations.
  """
  template = f"""COURSE VALIDATION PARAMETERS:
Course Structure: {course_structure[:200]}...
Validation Criteria: {validation_criteria}

YOU MUST NOW GENERATE THE VALIDATION REPORT FOLLOWING THIS FORMAT:

# Course Content Validation Report

## Validation Overview
- **Validation Type:** {validation_criteria.replace('_', ' ').title()}
- **Date:** [Date]
- **Status:** [Pass/Needs Review/Fail]

## Validation Criteria Check

### Learning Objectives Alignment
- ✅/❌ **Clear Learning Objectives:** [Assessment]
- ✅/❌ **Measurable Outcomes:** [Assessment]
- ✅/❌ **Appropriate Difficulty Level:** [Assessment]

### Content Quality
- ✅/❌ **Content Accuracy:** [Assessment]
- ✅/❌ **Content Currency:** [Assessment]
- ✅/❌ **Content Completeness:** [Assessment]

### Assessment Alignment
- ✅/❌ **Assessments Match Objectives:** [Assessment]
- ✅/❌ **Variety of Assessment Types:** [Assessment]
- ✅/❌ **Clear Rubrics:** [Assessment]

### Accessibility & Inclusivity
- ✅/❌ **Accessible Format:** [Assessment]
- ✅/❌ **Multiple Learning Styles:** [Assessment]
- ✅/❌ **Cultural Sensitivity:** [Assessment]

## Issues Found
1. **Issue:** [Description]
   - **Severity:** [High/Medium/Low]
   - **Recommendation:** [How to fix]

2. **Issue:** [Description]
   - **Severity:** [High/Medium/Low]
   - **Recommendation:** [How to fix]

## Recommendations
- [Recommendation 1]
- [Recommendation 2]
- [Recommendation 3]

## Overall Assessment
**Score:** [X/100]
**Status:** [Pass/Needs Review/Fail]
**Next Steps:** [What needs to be done]"""
  
  return template


# Language Practice Agent Tools
def _create_vocabulary_set(language: str, level: str, category: str = "general", num_words: int = 20) -> str:
  """Create a vocabulary set with words, translations, and example sentences.
  
  Args:
    language: Target language (e.g., spanish, french, german)
    level: Proficiency level (beginner, intermediate, advanced)
    category: Word category (general, business, travel, food, etc.)
    num_words: Number of words to generate (default: 20)
  
  Returns:
    Vocabulary set template with words, translations, phonetics, and examples.
  """
  num_words = max(5, min(50, int(num_words)))
  
  template = f"""VOCABULARY SET PARAMETERS:
Language: {language}
Level: {level}
Category: {category}
Number of Words: {num_words}

YOU MUST NOW GENERATE THE COMPLETE VOCABULARY SET FOLLOWING THIS FORMAT:

# Vocabulary Set: {category.title()} ({level})

## Words

[Generate {num_words} words with the following for each:]

**Word 1:** [Target language word]
- **Translation:** [English translation]
- **Phonetic:** [IPA phonetic transcription]
- **Category:** {category}
- **Example Sentence:** [Sentence in target language using this word]
- **Example Translation:** [English translation of example]
- **Difficulty:** [1-5 scale based on level]

[Continue for all {num_words} words...]

## Study Tips
- [Tip 1 for memorizing these words]
- [Tip 2 for practicing pronunciation]
- [Tip 3 for using in context]"""
  
  return template


def _create_grammar_exercise(language: str, topic: str, level: str, exercise_type: str = "fill-blank") -> str:
  """Create a grammar exercise for a specific topic.
  
  Args:
    language: Target language
    topic: Grammar topic (e.g., present_tense, past_tense, articles, prepositions)
    level: Difficulty level (beginner, intermediate, advanced)
    exercise_type: Type of exercise (fill-blank, multiple-choice, sentence-construction, transformation)
  
  Returns:
    Grammar exercise with questions and explanations.
  """
  template = f"""GRAMMAR EXERCISE PARAMETERS:
Language: {language}
Topic: {topic}
Level: {level}
Exercise Type: {exercise_type}

YOU MUST NOW GENERATE THE COMPLETE GRAMMAR EXERCISE FOLLOWING THIS FORMAT:

# Grammar Exercise: {topic.replace('_', ' ').title()}

## Topic Overview
[Brief explanation of the grammar rule]

## Exercise

**Question 1:** [Exercise question based on type]
[If fill-blank: Show sentence with blank]
[If multiple-choice: Show question with 4 options A-D]
[If sentence-construction: Show words to arrange]
[If transformation: Show sentence to transform]

**Answer:** [Correct answer]
**Explanation:** [Why this is correct, grammar rule applied]

[Continue with 5-10 questions...]

## Key Rules
- [Rule 1]
- [Rule 2]
- [Rule 3]

## Common Mistakes to Avoid
- [Mistake 1]
- [Mistake 2]"""
  
  return template


def _create_conversation_scenario(language: str, situation: str, level: str) -> str:
  """Create a conversation practice scenario.
  
  Args:
    language: Target language
    situation: Real-world situation (restaurant, airport, hotel, shopping, etc.)
    level: Proficiency level
  
  Returns:
    Conversation scenario with dialogues and cultural context.
  """
  template = f"""CONVERSATION SCENARIO PARAMETERS:
Language: {language}
Situation: {situation}
Level: {level}

YOU MUST NOW GENERATE THE COMPLETE CONVERSATION SCENARIO FOLLOWING THIS FORMAT:

# Conversation Practice: {situation.title()}

## Scenario Context
[Describe the situation and setting]

## Cultural Notes
[Important cultural context for this situation]

## Dialogue

**Native Speaker:** [First line in target language]
**Translation:** [English translation]
**Your Response:** [Suggested response in target language]
**Translation:** [English translation]

[Continue dialogue with 8-12 exchanges...]

## Key Phrases
- [Useful phrase 1]: [Translation] - [When to use]
- [Useful phrase 2]: [Translation] - [When to use]
- [Useful phrase 3]: [Translation] - [When to use]

## Practice Tips
- [Tip for practicing this conversation]
- [Tip for pronunciation]
- [Tip for natural flow]"""
  
  return template


def _create_pronunciation_exercise(language: str, focus: str, level: str) -> str:
  """Create a pronunciation practice exercise.
  
  Args:
    language: Target language
    focus: Focus area (vowels, consonants, stress, intonation, specific_sounds)
    level: Difficulty level
  
  Returns:
    Pronunciation exercise with words, phonetics, and practice tips.
  """
  template = f"""PRONUNCIATION EXERCISE PARAMETERS:
Language: {language}
Focus: {focus}
Level: {level}

YOU MUST NOW GENERATE THE COMPLETE PRONUNCIATION EXERCISE FOLLOWING THIS FORMAT:

# Pronunciation Practice: {focus.replace('_', ' ').title()}

## Focus Area
[Explanation of the pronunciation focus]

## Practice Words/Phrases

**Word 1:** [Word in target language]
- **Phonetic:** [IPA transcription]
- **Audio Guide:** [Description of how to pronounce]
- **Common Mistakes:** [What learners often get wrong]
- **Practice Tip:** [How to practice this sound]

[Continue with 10-15 words/phrases...]

## Tongue Twisters (if appropriate)
[Include 2-3 tongue twisters for advanced practice]

## Practice Exercises
1. **Minimal Pairs:** [Words that differ by one sound]
2. **Stress Patterns:** [Words showing stress patterns]
3. **Intonation Practice:** [Sentences for intonation]

## Feedback Guidelines
- [What to listen for when practicing]
- [How to self-assess]
- [When to seek native speaker feedback]"""
  
  return template


def _assess_proficiency_level(language: str, responses: str) -> str:
  """Assess user's language proficiency based on placement test responses.
  
  Args:
    language: Target language
    responses: User's responses to placement test questions
  
  Returns:
    Proficiency assessment with CEFR level and recommendations.
  """
  template = f"""PROFICIENCY ASSESSMENT PARAMETERS:
Language: {language}
User Responses: {responses[:500]}...

YOU MUST NOW GENERATE THE COMPLETE ASSESSMENT FOLLOWING THIS FORMAT:

# Language Proficiency Assessment

## Overall Level
**CEFR Level:** [A1/A2/B1/B2/C1/C2]
**Proficiency:** [Beginner/Elementary/Intermediate/Upper-Intermediate/Advanced]

## Skill Breakdown
- **Vocabulary:** [Level] - [Assessment]
- **Grammar:** [Level] - [Assessment]
- **Reading:** [Level] - [Assessment]
- **Writing:** [Level] - [Assessment]
- **Speaking:** [Level] - [Assessment]
- **Listening:** [Level] - [Assessment]

## Strengths
- [Strength 1]
- [Strength 2]
- [Strength 3]

## Areas for Improvement
- [Area 1] - [Recommendation]
- [Area 2] - [Recommendation]
- [Area 3] - [Recommendation]

## Recommended Learning Path
1. [First step]
2. [Second step]
3. [Third step]

## Next Steps
[Specific actions to take based on assessment]"""
  
  return template


def get_tools_for_agent_slug(slug: str) -> List[Tool]:
  """Return LangChain tools enabled for a given prebuilt agent slug."""
  tools: List[Tool] = []

  if slug == PREBUILT_AGENT_SLUGS["personal_tutor"]:
    tools.append(
      Tool(
        name="generate_quiz",
        func=_generate_quiz,
        description=(
          "Generate a structured Multiple Choice Question (MCQ) quiz for a given topic and difficulty. "
          "The tool returns a template that you MUST expand into complete MCQs with exactly 4 options (A, B, C, D) per question. "
          "Format: **Question N:** [question] followed by A), B), C), D) options on separate lines, then **Answer:** [letter]. "
          "Args: topic (str), difficulty (str: easy/medium/hard, default='medium'), num_questions (int, default=5)."
        ),
      )
    )
    tools.append(
      Tool(
        name="build_study_plan",
        func=_build_study_plan,
        description="Create a weekly study plan outline for a specific learning goal.",
      )
    )

  elif slug == PREBUILT_AGENT_SLUGS["course_creation_agent"]:
    tools.append(
      Tool(
        name="create_course_structure",
        func=_create_course_structure,
        description=(
          "Create a comprehensive course structure with modules, lessons, learning objectives, and assessment strategy. "
          "Args: course_title (str), learning_objectives (str, comma-separated), duration_weeks (int, default=8)."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_learning_assessment",
        func=_create_learning_assessment,
        description=(
          "Create a learning assessment (diagnostic, formative, summative, or comprehensive) for a specific topic. "
          "Includes questions, scoring rubrics, and feedback guidelines. "
          "Args: topic (str), assessment_type (str: diagnostic/formative/summative/comprehensive, default='comprehensive'), num_questions (int, default=10)."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_concept_map",
        func=_create_concept_map,
        description=(
          "Generate a concept map showing relationships between concepts, hierarchies, and learning paths. "
          "Args: main_concept (str), related_concepts (str, comma-separated, optional)."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_workflow_automation",
        func=_create_workflow_automation,
        description=(
          "Create an automated workflow for course creation, learning processes, or content delivery. "
          "Includes triggers, error handling, and monitoring. "
          "Args: workflow_name (str), steps (str, comma-separated), automation_type (str: learning/assessment/content_creation/course_delivery, default='learning')."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_meeting_notes_template",
        func=_create_meeting_notes_template,
        description=(
          "Generate structured meeting notes templates for course planning, reviews, or assessment design meetings. "
          "Args: meeting_type (str: course_planning/review/assessment_design, default='course_planning'), participants (str, comma-separated, optional)."
        ),
      )
    )
    tools.append(
      Tool(
        name="validate_course_content",
        func=_validate_course_content,
        description=(
          "Validate course content against educational standards, accessibility requirements, and best practices. "
          "Provides validation report with recommendations. "
          "Args: course_structure (str), validation_criteria (str: comprehensive/accessibility/learning_objectives/assessment_alignment, default='comprehensive')."
        ),
      )
    )
    # Include quiz and study plan tools for Course Creation Agent as well
    tools.append(
      Tool(
        name="generate_quiz",
        func=_generate_quiz,
        description=(
          "Generate a structured Multiple Choice Question (MCQ) quiz for a given topic and difficulty. "
          "The tool returns a template that you MUST expand into complete MCQs with exactly 4 options (A, B, C, D) per question. "
          "Format: **Question N:** [question] followed by A), B), C), D) options on separate lines, then **Answer:** [letter]. "
          "Args: topic (str), difficulty (str: easy/medium/hard, default='medium'), num_questions (int, default=5)."
        ),
      )
    )
    tools.append(
      Tool(
        name="build_study_plan",
        func=_build_study_plan,
        description="Create a weekly study plan outline for a specific learning goal.",
      )
    )

  elif slug == PREBUILT_AGENT_SLUGS["language_practice_agent"]:
    tools.append(
      Tool(
        name="create_vocabulary_set",
        func=_create_vocabulary_set,
        description=(
          "Create a vocabulary set with words, translations, phonetics, and example sentences for spaced repetition learning. "
          "Args: language (str), level (str: beginner/intermediate/advanced), category (str: general/business/travel/food, default='general'), num_words (int, default=20)."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_grammar_exercise",
        func=_create_grammar_exercise,
        description=(
          "Create grammar exercises with explanations for practicing specific grammar topics. "
          "Args: language (str), topic (str: present_tense/past_tense/articles, etc.), level (str), exercise_type (str: fill-blank/multiple-choice/sentence-construction/transformation, default='fill-blank')."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_conversation_scenario",
        func=_create_conversation_scenario,
        description=(
          "Create realistic conversation scenarios for practice with dialogues and cultural context. "
          "Args: language (str), situation (str: restaurant/airport/hotel/shopping, etc.), level (str)."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_pronunciation_exercise",
        func=_create_pronunciation_exercise,
        description=(
          "Create pronunciation practice exercises focusing on specific sounds, stress patterns, or intonation. "
          "Args: language (str), focus (str: vowels/consonants/stress/intonation, etc.), level (str)."
        ),
      )
    )
    tools.append(
      Tool(
        name="assess_proficiency_level",
        func=_assess_proficiency_level,
        description=(
          "Assess user's language proficiency level based on placement test responses. Returns CEFR level and personalized recommendations. "
          "Args: language (str), responses (str: user's test responses)."
        ),
      )
    )
    # Include quiz and study plan tools for Language Practice Agent
    tools.append(
      Tool(
        name="generate_quiz",
        func=_generate_quiz,
        description=(
          "Generate a structured Multiple Choice Question (MCQ) quiz for vocabulary or grammar practice. "
          "Args: topic (str), difficulty (str: easy/medium/hard, default='medium'), num_questions (int, default=5)."
        ),
      )
    )
    tools.append(
      Tool(
        name="build_study_plan",
        func=_build_study_plan,
        description="Create a weekly study plan outline for language learning goals.",
      )
    )

  return tools


