import json
from typing import List
from langchain_core.tools import Tool


PREBUILT_AGENT_SLUGS = {
  "personal_tutor": "education.personal_tutor",
  "course_creation_agent": "education.course_creation_agent",
  "language_practice_agent": "education.language_practice_agent",
  "micro_learning_agent": "education.micro_learning_agent",
  "exam_prep_agent": "education.exam_prep_agent",
  "resume_review_agent": "career.resume_review_agent",
  "career_coach_agent": "career.career_coach_agent",
  "skill_gap_agent": "career.skill_gap_agent",
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
1. ALL questions MUST be specifically about "{topic}" - do NOT include questions about unrelated topics
2. Start IMMEDIATELY with **Question 1:** - NO text before it
3. NO preamble, NO introduction, NO conversational text
4. NO emojis, NO special characters except **Question** and **Answer** markers
5. Each question must have exactly 4 options labeled A), B), C), D)
6. Each option must be on its own line
7. Include **Answer:** [letter] immediately after each question's options
8. End after the last answer - NO closing text

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


def _generate_micro_lesson(topic: str, time_minutes: int = 5, difficulty: str = "medium") -> str:
  """Generate a focused micro-lesson (5-15 minutes) on a specific topic.
  
  This function generates bite-sized lessons optimized for busy learners.
  Lessons are structured, focused, and time-efficient.
  
  Args:
    topic: The subject/topic for the lesson
    time_minutes: Available time in minutes (5, 10, or 15)
    difficulty: Difficulty level (easy, medium, hard)
  
  Returns:
    Complete micro-lesson with concept, explanation, examples, and key takeaways.
  """
  try:
    # Validate and normalize inputs
    time_minutes = max(5, min(15, int(time_minutes))) if isinstance(time_minutes, (int, float, str)) else 5
    if isinstance(time_minutes, str):
      try:
        time_minutes = int(time_minutes)
      except (ValueError, TypeError):
        time_minutes = 5
    time_minutes = max(5, min(15, time_minutes))
    
    difficulty = str(difficulty).lower() if difficulty else "medium"
    topic = str(topic) if topic else "general knowledge"
    
    # Import Gemini client
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    # Create lesson prompt based on time
    depth_map = {
      5: "brief overview with 1-2 key concepts",
      10: "detailed explanation with 2-3 key concepts and examples",
      15: "comprehensive lesson with 3-4 concepts, multiple examples, and practical applications"
    }
    
    lesson_prompt = f"""Generate a focused {time_minutes}-minute micro-lesson about "{topic}" at {difficulty} difficulty level.

CRITICAL REQUIREMENTS:
1. Keep the lesson focused and time-efficient ({depth_map.get(time_minutes, 'brief overview')})
2. Structure: Concept → Explanation → Example → Key Takeaways
3. Include 1-2 practical examples relevant to the topic
4. End with "**Key Takeaways:**" section with 3-5 bullet points
5. Make content engaging and easy to digest
6. NO preamble, NO introduction text - start directly with the concept
7. Use clear, concise language suitable for busy learners

OUTPUT FORMAT:

**Concept:** [Main concept name]

**Explanation:**
[Clear, focused explanation of the concept - {time_minutes} minutes worth of content]

**Example:**
[Practical example or real-world application]

**Key Takeaways:**
• [Takeaway 1]
• [Takeaway 2]
• [Takeaway 3]
[Add more as needed]

Generate the lesson now:"""
    
    lesson_content = gemini_client.generate_response(
      system_prompt="You are a micro-learning expert. Create focused, time-efficient lessons for busy learners.",
      messages=[{"role": "user", "content": lesson_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    return lesson_content if lesson_content else f"**Concept:** {topic}\n\n**Explanation:**\nA brief overview of {topic}.\n\n**Key Takeaways:**\n• Understanding {topic} is important\n• Practice helps mastery"
    
  except Exception as e:
    import traceback
    print(f"Error in _generate_micro_lesson: {traceback.format_exc()}")
    return f"Error generating lesson: {str(e)}. Please try again."


def _create_flashcards(topic: str, num_cards: int = 5) -> str:
  """Create flashcards for spaced repetition learning.
  
  Generates flashcards with questions/concepts on one side and answers/explanations on the other.
  
  Args:
    topic: The subject/topic for flashcards
    num_cards: Number of flashcards to generate (default: 5)
  
  Returns:
    Formatted flashcards ready for spaced repetition review.
  """
  try:
    # Validate inputs
    num_cards = max(3, min(10, int(num_cards))) if isinstance(num_cards, (int, float, str)) else 5
    if isinstance(num_cards, str):
      try:
        num_cards = int(num_cards)
      except (ValueError, TypeError):
        num_cards = 5
    num_cards = max(3, min(10, num_cards))
    
    topic = str(topic) if topic else "general knowledge"
    
    # Import Gemini client
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    flashcard_prompt = f"""Create {num_cards} flashcards about "{topic}" for spaced repetition learning.

CRITICAL REQUIREMENTS:
1. Each flashcard should have a clear question/concept and concise answer
2. Format: **Card N:** followed by Q: and A: sections
3. Keep answers brief and memorable (1-2 sentences max)
4. Focus on key concepts and important facts
5. NO preamble - start directly with Card 1
6. End after the last card - NO closing text

OUTPUT FORMAT:

**Card 1:**
Q: [Question or concept]
A: [Brief answer/explanation]

**Card 2:**
Q: [Question or concept]
A: [Brief answer/explanation]

[Continue for all {num_cards} cards...]

Generate the flashcards now:"""
    
    flashcard_content = gemini_client.generate_response(
      system_prompt="You are a flashcard creation expert. Create effective flashcards for spaced repetition learning.",
      messages=[{"role": "user", "content": flashcard_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    return flashcard_content if flashcard_content else f"**Card 1:**\nQ: What is {topic}?\nA: {topic} is an important concept to learn."
    
  except Exception as e:
    import traceback
    print(f"Error in _create_flashcards: {traceback.format_exc()}")
    return f"Error creating flashcards: {str(e)}. Please try again."


# Exam Prep Agent Tools
def _create_practice_exam(exam_type: str, subject: str, num_questions: int = 50, time_limit: int = 60, difficulty: str = "medium") -> str:
  """Create a full-length practice exam with various question types.
  
  Args:
    exam_type: Type of exam (SAT, GRE, Certification, Final Exam, etc.)
    subject: Subject/topic for the exam
    num_questions: Number of questions (default: 50)
    time_limit: Time limit in minutes (default: 60)
    difficulty: Difficulty level (easy, medium, hard, default: "medium")
  
  Returns:
    Complete practice exam with questions, answer key, and scoring rubric.
  """
  try:
    num_questions = max(10, min(100, int(num_questions))) if isinstance(num_questions, (int, float, str)) else 50
    if isinstance(num_questions, str):
      try:
        num_questions = int(num_questions)
      except (ValueError, TypeError):
        num_questions = 50
    num_questions = max(10, min(100, num_questions))
    
    time_limit = max(15, min(300, int(time_limit))) if isinstance(time_limit, (int, float, str)) else 60
    if isinstance(time_limit, str):
      try:
        time_limit = int(time_limit)
      except (ValueError, TypeError):
        time_limit = 60
    time_limit = max(15, min(300, time_limit))
    
    difficulty = str(difficulty).lower() if difficulty else "medium"
    exam_type = str(exam_type) if exam_type else "General Exam"
    subject = str(subject) if subject else "General Knowledge"
    
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    exam_prompt = f"""Create a complete practice exam for {exam_type} in {subject}.

CRITICAL REQUIREMENTS - FOLLOW EXACTLY:
1. Generate ALL {num_questions} questions in ONE response
2. Start IMMEDIATELY with **Question 1:** - NO text before it
3. NO preamble, NO introduction, NO conversational text like "Here is", "Excellent", etc.
4. NO emojis or special characters (except **Question** and **Answer** markers)
5. Each question must have exactly 4 options labeled A), B), C), D) for multiple choice
6. Include **Answer:** [letter] immediately after each question's options
7. Generate ALL questions in ONE response - do NOT generate questions one by one
8. End after the last answer - NO closing text

OUTPUT FORMAT (start directly with Question 1, NO text before):

**Question 1:** [Complete multiple choice question]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
**Answer:** [A, B, C, or D]

**Question 2:** [Complete question - can be multiple choice or short answer]
A) [Option A] (if multiple choice)
B) [Option B]
C) [Option C]
D) [Option D]
**Answer:** [Answer]

[Continue for ALL {num_questions} questions...]

**Question {num_questions}:** [Last question]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
**Answer:** [Answer]

STRICT REQUIREMENTS:
- Start directly with **Question 1:** - NO text before it
- Generate ALL {num_questions} questions in ONE response
- Every question must have exactly 4 options labeled A), B), C), D)
- Each option must be on its own line
- Include **Answer:** [Letter] immediately after each question's options
- NO explanations, NO discussions, NO introductory text, NO closing text
- NO emojis, NO special characters except **Question** and **Answer** markers
- NO phrases like 'Of course', 'I can help', 'Here is', 'Excellent', etc.

Generate the complete exam now starting with **Question 1:**"""
    
    exam_content = gemini_client.generate_response(
      system_prompt="You are an exam creation expert. Create comprehensive practice exams following the exact format specified. DO NOT add any preamble, introduction, or conversational text. Start directly with the exam format.",
      messages=[{"role": "user", "content": exam_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    # Clean the response to ensure it starts with Question 1
    if exam_content:
      # Find the first question marker
      question_start = exam_content.find("**Question 1:**")
      if question_start == -1:
        question_start = exam_content.find("Question 1:")
      if question_start == -1:
        # Try to find any numbered question
        import re
        first_question_match = re.search(r'(?:Question|**Question)\s+1[:\-]', exam_content, re.IGNORECASE)
        if first_question_match:
          question_start = first_question_match.start()
      
      if question_start > 0:
        # Keep instructions if they're close to the start, otherwise remove preamble
        if question_start > 500:
          exam_content = exam_content[question_start:].strip()
        else:
          # Instructions are part of the exam, keep them
          pass
      
      # Ensure it ends properly (remove any trailing text after last answer)
      # Find the last **Answer:** marker
      last_answer_pos = exam_content.rfind("**Answer:**")
      if last_answer_pos == -1:
        last_answer_pos = exam_content.rfind("Answer:")
      
      if last_answer_pos > 0:
        # Extract up to 100 characters after the last answer (to include the answer letter and explanation)
        remaining = exam_content[last_answer_pos:]
        lines = remaining.split('\n')
        # Keep answer lines but remove everything after scoring rubric or unrelated content
        rubric_pos = remaining.find("Scoring Rubric")
        if rubric_pos > 0:
          exam_content = exam_content[:last_answer_pos] + remaining[:rubric_pos + 200]  # Keep rubric
        else:
          # Keep up to 3 lines after answer
          answer_section = '\n'.join(lines[:3])
          exam_content = exam_content[:last_answer_pos] + answer_section
    
    return exam_content if exam_content else f"# Practice Exam: {exam_type} - {subject}\n\n## Exam Instructions\n- Time Limit: {time_limit} minutes\n- Total Questions: {num_questions}\n\n## Questions\n**Question 1:** [Question text]\nA) Option A\nB) Option B\nC) Option C\nD) Option D\n\n## Answer Key\n**Question 1:** A - [Explanation]"
    
  except Exception as e:
    import traceback
    print(f"Error in _create_practice_exam: {traceback.format_exc()}")
    return f"Error creating practice exam: {str(e)}. Please try again."


def _create_study_schedule(exam_date: str, subjects: str, hours_per_day: int = 2, current_level: str = "intermediate") -> str:
  """Create a personalized study schedule leading up to the exam date.
  
  Args:
    exam_date: Exam date in YYYY-MM-DD format
    subjects: Comma-separated list of subjects/topics to study
    hours_per_day: Hours available for study per day (default: 2)
    current_level: Current knowledge level (beginner, intermediate, advanced, default: "intermediate")
  
  Returns:
    Weekly study schedule with daily goals, topic breakdown, and milestones.
  """
  try:
    from datetime import datetime, timedelta
    
    hours_per_day = max(1, min(12, int(hours_per_day))) if isinstance(hours_per_day, (int, float, str)) else 2
    if isinstance(hours_per_day, str):
      try:
        hours_per_day = int(hours_per_day)
      except (ValueError, TypeError):
        hours_per_day = 2
    hours_per_day = max(1, min(12, hours_per_day))
    
    current_level = str(current_level).lower() if current_level else "intermediate"
    subjects_list = [s.strip() for s in str(subjects).split(",")] if subjects else ["General Topics"]
    
    # Parse exam date
    try:
      exam_dt = datetime.strptime(str(exam_date), "%Y-%m-%d")
      today = datetime.now()
      days_until_exam = (exam_dt - today).days
      if days_until_exam < 1:
        days_until_exam = 30  # Default to 30 days if date is invalid
      weeks_until_exam = max(1, days_until_exam // 7)
    except:
      days_until_exam = 30
      weeks_until_exam = 4
    
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    schedule_prompt = f"""Create a personalized study schedule for an exam on {exam_date}.

PARAMETERS:
- Days until exam: {days_until_exam} days ({weeks_until_exam} weeks)
- Subjects to study: {', '.join(subjects_list)}
- Hours per day: {hours_per_day} hours
- Current level: {current_level}

CRITICAL REQUIREMENTS:
1. Create a week-by-week breakdown
2. Prioritize topics by importance and difficulty
3. Include practice exam dates
4. Schedule review sessions
5. Set milestone checkpoints
6. Adapt to available study time
7. Start IMMEDIATELY with schedule overview - NO preamble

OUTPUT FORMAT:

# Study Schedule: Exam on {exam_date}

## Schedule Overview
- **Exam Date:** {exam_date}
- **Days Remaining:** {days_until_exam} days
- **Study Hours/Day:** {hours_per_day} hours
- **Total Study Hours:** {days_until_exam * hours_per_day} hours
- **Subjects:** {', '.join(subjects_list)}

## Weekly Breakdown

### Week 1 (Days 1-7)
**Focus:** [Primary focus for this week]
**Daily Goals:**
- Day 1: [Topic 1] - {hours_per_day} hours
- Day 2: [Topic 2] - {hours_per_day} hours
- Day 3: [Topic 3] - {hours_per_day} hours
- Day 4: Review Day - {hours_per_day} hours
- Day 5: [Topic 4] - {hours_per_day} hours
- Day 6: [Topic 5] - {hours_per_day} hours
- Day 7: Practice Questions - {hours_per_day} hours

**Milestone:** [Milestone for this week]

[Continue for all {weeks_until_exam} weeks...]

### Final Week (Last 7 days)
**Focus:** Review and exam strategies
- Day 1-3: Comprehensive review
- Day 4: Full practice exam
- Day 5-6: Weak area focus
- Day 7: Final review and strategies

## Practice Exam Schedule
- Week {weeks_until_exam // 2}: First practice exam
- Week {weeks_until_exam - 1}: Second practice exam
- Final week: Final practice exam

## Milestones
- [ ] Week 1: Complete [milestone]
- [ ] Week 2: Complete [milestone]
- [ ] Week {weeks_until_exam}: Ready for exam

Generate the complete study schedule now:"""
    
    schedule_content = gemini_client.generate_response(
      system_prompt="You are a study schedule expert. Create personalized, realistic study schedules for exam preparation.",
      messages=[{"role": "user", "content": schedule_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    return schedule_content if schedule_content else f"# Study Schedule: Exam on {exam_date}\n\n## Schedule Overview\n- Days Remaining: {days_until_exam} days\n- Study Hours/Day: {hours_per_day} hours\n\n## Weekly Breakdown\n[Study schedule will be generated]"
    
  except Exception as e:
    import traceback
    print(f"Error in _create_study_schedule: {traceback.format_exc()}")
    return f"Error creating study schedule: {str(e)}. Please try again."


def _identify_weak_areas(subject: str, practice_results: str, exam_type: str = "general") -> str:
  """Analyze practice test results and identify areas needing improvement.
  
  Args:
    subject: Subject/topic area
    practice_results: Structured text or description of practice test results (scores by topic, question types, etc.)
    exam_type: Type of exam (default: "general")
  
  Returns:
    Analysis report with weak areas, recommendations, and improvement strategies.
  """
  try:
    subject = str(subject) if subject else "General"
    exam_type = str(exam_type) if exam_type else "General Exam"
    practice_results = str(practice_results) if practice_results else "No results provided"
    
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    analysis_prompt = f"""Analyze practice exam results and identify weak areas for improvement.

PARAMETERS:
- Subject: {subject}
- Exam Type: {exam_type}
- Practice Results: {practice_results[:500]}

CRITICAL REQUIREMENTS:
1. Identify weak areas ranked by priority
2. Provide specific topics needing focus
3. Recommend targeted study materials
4. Suggest improvement strategies
5. Set realistic improvement goals
6. Start IMMEDIATELY with analysis summary - NO preamble

OUTPUT FORMAT:

# Weak Area Analysis: {subject}

## Overall Performance Summary
- **Overall Score:** [Score/Percentage]
- **Strongest Areas:** [List 2-3]
- **Weakest Areas:** [List 2-3]

## Weak Areas (Ranked by Priority)

### 1. [Weak Area 1] - HIGH PRIORITY
**Current Performance:** [Score/Percentage]
**Why This Matters:** [Explanation]
**Specific Topics to Focus On:**
- [Topic 1]
- [Topic 2]
- [Topic 3]

**Recommended Study Materials:**
- [Material 1]
- [Material 2]

**Improvement Strategy:**
- [Strategy 1]
- [Strategy 2]
- [Strategy 3]

**Target Improvement:** [Goal score/percentage]

### 2. [Weak Area 2] - MEDIUM PRIORITY
[Same structure as above]

### 3. [Weak Area 3] - LOW PRIORITY
[Same structure as above]

## Improvement Action Plan
1. **Immediate Actions (This Week):**
   - [Action 1]
   - [Action 2]

2. **Short-term Goals (Next 2 Weeks):**
   - [Goal 1]
   - [Goal 2]

3. **Long-term Goals (Before Exam):**
   - [Goal 1]
   - [Goal 2]

## Recommended Study Sequence
1. Start with: [Weak Area 1]
2. Then focus on: [Weak Area 2]
3. Finally review: [Weak Area 3]

Generate the complete analysis now:"""
    
    analysis_content = gemini_client.generate_response(
      system_prompt="You are an exam preparation analyst. Analyze practice results and provide actionable improvement recommendations.",
      messages=[{"role": "user", "content": analysis_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    return analysis_content if analysis_content else f"# Weak Area Analysis: {subject}\n\n## Overall Performance Summary\n- Weakest Areas: [To be analyzed from practice results]\n\n## Weak Areas\n[Analysis will be generated based on practice results]"
    
  except Exception as e:
    import traceback
    print(f"Error in _identify_weak_areas: {traceback.format_exc()}")
    return f"Error analyzing weak areas: {str(e)}. Please try again."


def _create_exam_strategies(exam_type: str, subject: str, question_format: str = "mixed") -> str:
  """Provide exam-taking strategies and tips for specific exam types.
  
  Args:
    exam_type: Type of exam (SAT, GRE, Certification, etc.)
    subject: Subject area
    question_format: Question format (MCQ, essay, mixed, default: "mixed")
  
  Returns:
    Comprehensive strategy guide with time management, question prioritization, and tips.
  """
  try:
    exam_type = str(exam_type) if exam_type else "General Exam"
    subject = str(subject) if subject else "General"
    question_format = str(question_format).lower() if question_format else "mixed"
    
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    strategy_prompt = f"""Create comprehensive exam-taking strategies for {exam_type} in {subject}.

PARAMETERS:
- Exam Type: {exam_type}
- Subject: {subject}
- Question Format: {question_format}

CRITICAL REQUIREMENTS:
1. Provide proven exam-taking strategies
2. Include time management techniques
3. Explain question prioritization
4. Cover answer elimination strategies
5. Include stress management tips
6. List common pitfalls to avoid
7. Start IMMEDIATELY with strategy overview - NO preamble

OUTPUT FORMAT:

# Exam Strategies: {exam_type} - {subject}

## Strategy Overview
- **Exam Type:** {exam_type}
- **Question Format:** {question_format}
- **Key Focus:** [Main strategy focus]

## Time Management Strategies

### Overall Time Allocation
- **Reading Instructions:** [Time]
- **Question Review:** [Time]
- **Answering Questions:** [Time]
- **Review Time:** [Time]

### Per-Question Time Budget
- Multiple Choice: [Time per question]
- Short Answer: [Time per question]
- Essay: [Time per question]

### Time Management Techniques
1. **Pacing Strategy:**
   - [Technique 1]
   - [Technique 2]

2. **Time Checkpoints:**
   - At 25%: [Checkpoint]
   - At 50%: [Checkpoint]
   - At 75%: [Checkpoint]

## Question Prioritization

### Priority Order
1. **High Priority:** [Question types/topics]
2. **Medium Priority:** [Question types/topics]
3. **Low Priority:** [Question types/topics]

### Answer Strategy
- **Easy Questions First:** [Strategy]
- **Skip and Return:** [When to skip]
- **Guess Strategy:** [When and how to guess]

## Answer Elimination Techniques

### For Multiple Choice
1. **Process of Elimination:**
   - [Technique 1]
   - [Technique 2]

2. **Common Distractors:**
   - [Distractor pattern 1]
   - [Distractor pattern 2]

## Stress Management

### Before the Exam
- [Tip 1]
- [Tip 2]
- [Tip 3]

### During the Exam
- [Tip 1]
- [Tip 2]
- [Tip 3]

### If You Feel Overwhelmed
- [Strategy 1]
- [Strategy 2]

## Common Pitfalls to Avoid
1. [Pitfall 1] - [How to avoid]
2. [Pitfall 2] - [How to avoid]
3. [Pitfall 3] - [How to avoid]

## Subject-Specific Tips for {subject}
- [Tip 1]
- [Tip 2]
- [Tip 3]

## Final Exam Day Checklist
- [ ] Get adequate sleep
- [ ] Eat a healthy breakfast
- [ ] Arrive early
- [ ] Bring required materials
- [ ] Stay calm and focused

Generate the complete strategy guide now:"""
    
    strategy_content = gemini_client.generate_response(
      system_prompt="You are an exam strategy expert. Provide proven exam-taking strategies and techniques.",
      messages=[{"role": "user", "content": strategy_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    return strategy_content if strategy_content else f"# Exam Strategies: {exam_type} - {subject}\n\n## Time Management Strategies\n- Budget time per question\n- Leave time for review\n\n## Question Prioritization\n- Answer easy questions first\n- Skip difficult questions and return\n\n## Common Pitfalls to Avoid\n[List of common mistakes]"
    
  except Exception as e:
    import traceback
    print(f"Error in _create_exam_strategies: {traceback.format_exc()}")
    return f"Error creating exam strategies: {str(e)}. Please try again."


def _generate_topic_review(topic: str, difficulty: str = "medium", review_type: str = "comprehensive") -> str:
  """Create a focused review session for a specific topic.
  
  Args:
    topic: Topic/subject to review
    difficulty: Difficulty level (easy, medium, hard, default: "medium")
    review_type: Type of review (concept, example, practice, comprehensive, default: "comprehensive")
  
  Returns:
    Review content with key concepts, examples, practice questions, and common mistakes.
  """
  try:
    topic = str(topic) if topic else "General Topic"
    difficulty = str(difficulty).lower() if difficulty else "medium"
    review_type = str(review_type).lower() if review_type else "comprehensive"
    
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    review_prompt = f"""Create a focused review session for the topic: {topic}.

PARAMETERS:
- Topic: {topic}
- Difficulty: {difficulty}
- Review Type: {review_type}

CRITICAL REQUIREMENTS:
1. Provide key concepts summary
2. Include important formulas/rules (if applicable)
3. Show worked examples
4. Provide actionable study items (NOT practice questions)
5. List common mistakes
6. Start IMMEDIATELY with topic overview - NO preamble

OUTPUT FORMAT:

# Topic Review: {topic}

## Topic Overview
[Brief overview of the topic and its importance]

## Key Concepts

### Concept 1: [Concept Name]
**Definition:** [Clear definition]
**Key Points:**
- [Point 1]
- [Point 2]
- [Point 3]

### Concept 2: [Concept Name]
[Same structure]

## Important Formulas/Rules
[If applicable, list key formulas or rules]

**Formula 1:** [Formula]
- **When to Use:** [Explanation]
- **Example:** [Worked example]

## Worked Examples

### Example 1: [Example Type]
**Problem:** [Problem statement]
**Solution:**
[Step-by-step solution]
**Key Takeaway:** [What to learn from this example]

### Example 2: [Example Type]
[Same structure]

## Actionable Study Items

### Immediate Actions (Do This First)
1. **Review:** [Specific concept or formula to review]
2. **Practice:** [Specific type of problem to practice]
3. **Memorize:** [Key formula or rule to memorize]

### Study Tasks (This Week)
1. **Focus Area:** [Specific topic to focus on]
   - **Action:** [Concrete action item]
   - **Resources:** [Recommended materials or methods]
   - **Time:** [Suggested time allocation]

2. **Focus Area:** [Another specific topic]
   - **Action:** [Concrete action item]
   - **Resources:** [Recommended materials or methods]
   - **Time:** [Suggested time allocation]

### Preparation Checklist
- [ ] Master [specific concept]
- [ ] Complete [specific practice type]
- [ ] Review [specific examples]
- [ ] Understand [specific application]

## Common Mistakes to Avoid
1. **Mistake 1:** [Description] - **How to Avoid:** [Solution]
2. **Mistake 2:** [Description] - **How to Avoid:** [Solution]
3. **Mistake 3:** [Description] - **How to Avoid:** [Solution]

## Quick Reference
- [Key point 1]
- [Key point 2]
- [Key point 3]

## Recommended Study Sequence
1. Start with: [First actionable item]
2. Then focus on: [Second actionable item]
3. Finally review: [Third actionable item]

Generate the complete topic review now:"""
    
    review_content = gemini_client.generate_response(
      system_prompt="You are a topic review expert. Create comprehensive, focused review sessions for exam preparation.",
      messages=[{"role": "user", "content": review_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    return review_content if review_content else f"# Topic Review: {topic}\n\n## Key Concepts\n[Key concepts for {topic}]\n\n## Important Points\n- [Point 1]\n- [Point 2]\n\n## Practice Questions\n[Practice questions for {topic}]"
    
  except Exception as e:
    import traceback
    print(f"Error in _generate_topic_review: {traceback.format_exc()}")
    return f"Error generating topic review: {str(e)}. Please try again."


def _track_progress(exam_type: str, practice_scores: str, target_score: int = None, exam_date: str = None) -> str:
  """Track and visualize exam preparation progress over time.
  
  Args:
    exam_type: Type of exam
    practice_scores: List of practice exam scores over time (comma-separated or structured text)
    target_score: Target score to achieve (optional)
    exam_date: Exam date in YYYY-MM-DD format (optional)
  
  Returns:
    Progress report with trends, readiness assessment, and recommendations.
  """
  try:
    exam_type = str(exam_type) if exam_type else "General Exam"
    practice_scores = str(practice_scores) if practice_scores else "No scores provided"
    
    target_score_str = f"{target_score}" if target_score else "Not specified"
    exam_date_str = exam_date if exam_date else "Not specified"
    
    from app.services.gemini import GeminiClient
    gemini_client = GeminiClient()
    
    progress_prompt = f"""Analyze exam preparation progress and provide a comprehensive progress report.

PARAMETERS:
- Exam Type: {exam_type}
- Practice Scores: {practice_scores}
- Target Score: {target_score_str}
- Exam Date: {exam_date_str}

CRITICAL REQUIREMENTS:
1. Calculate score trends over time
2. Assess improvement rate
3. Calculate readiness percentage
4. Identify milestones achieved
5. Provide recommendations
6. Start IMMEDIATELY with progress summary - NO preamble

OUTPUT FORMAT:

# Progress Report: {exam_type}

## Progress Summary
- **Current Score:** [Latest score]
- **Target Score:** {target_score_str}
- **Improvement:** [Improvement percentage/points]
- **Readiness Level:** [Percentage]% ready
- **Status:** [On Track/Needs Improvement/Excellent]

## Score Trends

### Score History
- Practice 1: [Score] - [Date]
- Practice 2: [Score] - [Date]
- Practice 3: [Score] - [Date]
- [Continue for all scores...]

### Trend Analysis
- **Overall Trend:** [Increasing/Decreasing/Stable]
- **Average Score:** [Average]
- **Best Score:** [Best score]
- **Improvement Rate:** [Points per practice/test]

## Readiness Assessment

### Current Readiness: [X]%
**Breakdown:**
- Knowledge Mastery: [X]%
- Test-Taking Skills: [X]%
- Time Management: [X]%
- Confidence Level: [X]%

### Readiness Prediction
Based on current progress, you are [X]% likely to achieve your target score.

## Milestones Achieved
- [✓] [Milestone 1]
- [✓] [Milestone 2]
- [ ] [Milestone 3] - [Progress]

## Areas of Improvement
1. [Area 1]: [Current status] → [Target]
2. [Area 2]: [Current status] → [Target]

## Recommendations

### Immediate Actions
- [Action 1]
- [Action 2]

### Study Focus
- [Focus area 1]
- [Focus area 2]

### Practice Schedule
- [Recommendation for practice frequency]

## Motivation & Next Steps
[Encouraging message and next steps]

Generate the complete progress report now:"""
    
    progress_content = gemini_client.generate_response(
      system_prompt="You are a progress tracking expert. Analyze exam preparation progress and provide actionable insights.",
      messages=[{"role": "user", "content": progress_prompt}],
      model="gemini-2.5-pro",
      temperature=0.7
    )
    
    return progress_content if progress_content else f"# Progress Report: {exam_type}\n\n## Progress Summary\n- Current Score: [To be calculated from practice scores]\n- Target Score: {target_score_str}\n- Readiness Level: [X]%\n\n## Score Trends\n[Score trend analysis will be generated]"
    
  except Exception as e:
    import traceback
    print(f"Error in _track_progress: {traceback.format_exc()}")
    return f"Error tracking progress: {str(e)}. Please try again."


def _generate_resume_review(
  resume_text: str,
  job_description: str = "",
  target_role: str = "",
  seniority: str = "mid"
) -> str:
  """
  Analyze a resume against a target role and optional job description, returning a
  structured JSON report optimized for ATS-style screening and human readability.

  This tool is designed to be called by the Resume Review Agent from a structured UI,
  not from free-form chat. It always returns a single JSON object (no markdown).

  Args:
    resume_text: The full plain-text resume content.
    job_description: The job description or posting to match against (optional but recommended).
    target_role: The intended role/title (e.g., 'Senior Backend Engineer').
    seniority: One of: 'junior', 'mid', 'senior', 'lead', used to calibrate expectations.

  Returns:
    A JSON string with this shape (keys are stable and safe to rely on in the UI):

    {
      "overall_score": 0-100,
      "ats_score": 0-100,
      "match_summary": "1-2 paragraph overview",
      "strengths": [ "...", "..." ],
      "weaknesses": [ "...", "..." ],
      "missing_keywords": [ "...", "..." ],
      "formatting_issues": [ "...", "..." ],
      "recommendations": [ "...", "..." ],
      "sections_to_improve": {
        "summary": { "current": "...", "suggested": "...", "reason": "..." },
        "experience": [
          { "current": "...", "suggested": "...", "reason": "..." }
        ],
        "skills": { "current": "...", "suggested": "...", "reason": "..." }
      }
    }
  """
  from app.services.gemini import GeminiClient

  # Defensive normalization
  resume_text = (resume_text or "").strip()
  job_description = (job_description or "").strip()
  target_role = (target_role or "").strip()
  seniority = (seniority or "mid").strip().lower()

  if not resume_text:
    return (
      '{"error":"resume_text_required",'
      '"message":"Resume text is required for analysis.","overall_score":0,"ats_score":0}'
    )

  if seniority not in ["junior", "entry", "mid", "senior", "lead"]:
    seniority = "mid"

  # Build a single, explicit prompt for Gemini with a strict JSON-only contract.
  prompt_parts: List[str] = []
  prompt_parts.append("You are an expert resume reviewer and ATS optimization specialist.")
  prompt_parts.append(
    "Your job is to evaluate the candidate's resume ONLY for the specified target role "
    "and optional job description, focusing on ATS keyword match, clarity, impact, and structure."
  )
  prompt_parts.append("")
  prompt_parts.append("CRITICAL RESPONSE FORMAT REQUIREMENTS:")
  prompt_parts.append("- Respond with a SINGLE valid JSON object.")
  prompt_parts.append("- DO NOT include any markdown, explanations, or surrounding text.")
  prompt_parts.append("- Use only double quotes for JSON keys and string values.")
  prompt_parts.append("- Do NOT include comments, trailing commas, or non-JSON content.")
  prompt_parts.append("")
  prompt_parts.append("The JSON object MUST have EXACTLY these top-level keys:")
  prompt_parts.append(
    '{'
    '"overall_score": number between 0 and 100,'
    '"ats_score": number between 0 and 100,'
    '"match_summary": string,'
    '"strengths": string array,'
    '"weaknesses": string array,'
    '"missing_keywords": string array,'
    '"formatting_issues": string array,'
    '"recommendations": string array,'
    '"sections_to_improve": {'
      '"summary": { "current": string, "suggested": string, "reason": string },'
      '"experience": [ { "current": string, "suggested": string, "reason": string } ],'
      '"skills": { "current": string, "suggested": string, "reason": string }'
    '}'
    '}'
  )
  prompt_parts.append("")
  prompt_parts.append("Guidelines:")
  prompt_parts.append("- Be specific and actionable in weaknesses and recommendations.")
  prompt_parts.append("- Missing keywords should be important skills/phrases from the job description.")
  prompt_parts.append(
    "- Formatting issues should focus on things that can break ATS parsing or hurt readability "
    "(e.g., tables, columns, images, inconsistent headings, dense blocks of text)."
  )
  prompt_parts.append(
    "- When suggesting improved bullets in `sections_to_improve.experience`, use strong, "
    "metric-driven, action-oriented statements aligned with the target role and seniority."
  )
  prompt_parts.append("")
  prompt_parts.append(f"Target role (can be empty): {target_role or 'Not specified'}")
  prompt_parts.append(f"Seniority level (junior/mid/senior/lead): {seniority}")
  prompt_parts.append("")
  prompt_parts.append("Job description (may be empty):")
  prompt_parts.append(job_description or "[Not provided]")
  prompt_parts.append("")
  prompt_parts.append("Candidate resume:")
  prompt_parts.append(resume_text)
  prompt_parts.append("")
  prompt_parts.append("Now produce the JSON object described above.")

  full_prompt = "\n".join(prompt_parts)

  try:
    gemini_client = GeminiClient()
    content = gemini_client.generate_response(
      system_prompt=(
        "You are an experienced recruiter and ATS optimization expert. "
        "You ONLY output valid JSON objects according to the user's schema."
      ),
      messages=[{"role": "user", "content": full_prompt}],
      model="gemini-2.5-pro",
      temperature=0.3,
    )

    # Best-effort trimming: if the model accidentally adds text before/after JSON, slice it.
    if not content:
      return (
        '{"error":"generation_failed",'
        '"message":"Resume review generation failed. Please try again.","overall_score":0,"ats_score":0}'
      )

    content = content.strip()
    first_brace = content.find("{")
    last_brace = content.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
      content = content[first_brace : last_brace + 1].strip()

    return content
  except Exception as e:
    import traceback
    print(f"Error in _generate_resume_review: {traceback.format_exc()}")
    return (
      '{"error":"internal_error",'
      f'"message":"Unexpected error while generating resume review: {str(e)}","overall_score":0,"ats_score":0}}'
    )


def _extract_first_json_object(text: str) -> str:
  """Best-effort extraction of the first top-level JSON object from text."""
  if not text:
    return ""
  start = text.find("{")
  end = text.rfind("}")
  if start == -1 or end == -1 or end <= start:
    return ""
  return text[start : end + 1].strip()


def _parse_json_payload(payload_json: str) -> dict:
  """Parse a JSON payload safely, supporting wrapped text."""
  raw = (payload_json or "").strip()
  if not raw:
    return {}
  try:
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, dict) else {}
  except Exception:
    candidate = _extract_first_json_object(raw)
    if not candidate:
      return {}
    try:
      parsed = json.loads(candidate)
      return parsed if isinstance(parsed, dict) else {}
    except Exception:
      return {}


def _normalize_string_list(value) -> List[str]:
  """Normalize list-like input (list/string) to non-empty string list."""
  if value is None:
    return []
  if isinstance(value, list):
    return [str(item).strip() for item in value if str(item).strip()]
  if isinstance(value, str):
    separators = [",", "\n", ";"]
    normalized = value
    for sep in separators[1:]:
      normalized = normalized.replace(sep, separators[0])
    return [item.strip() for item in normalized.split(separators[0]) if item.strip()]
  return [str(value).strip()] if str(value).strip() else []


def _coerce_int(value, default: int, minimum: int = 0, maximum: int = 520) -> int:
  """Coerce a value into a bounded integer."""
  try:
    parsed = int(float(value))
  except Exception:
    parsed = default
  return max(minimum, min(maximum, parsed))


def _career_coach_error(action: str, code: str, message: str) -> str:
  """Return a stable JSON error payload for Career Coach flows."""
  return json.dumps(
    {
      "action": action,
      "status": "error",
      "error": code,
      "message": message,
    },
    ensure_ascii=False,
  )


def _generate_career_coach_response(action: str, payload: dict) -> str:
  """
  Generate structured JSON outputs for Career Coach agent actions.

  Supported actions:
    - intake_assessment
    - opportunity_strategy
    - build_roadmap
    - weekly_checkin
    - interview_readiness
  """
  from app.services.gemini import GeminiClient

  raw_action = (action or "").strip().lower()
  action_aliases = {
    # Backward compatibility with previously exposed action naming.
    "skill_gap_analysis": "opportunity_strategy",
  }
  action = action_aliases.get(raw_action, raw_action)
  allowed_actions = {
    "intake_assessment",
    "opportunity_strategy",
    "build_roadmap",
    "weekly_checkin",
    "interview_readiness",
  }
  if action not in allowed_actions:
    return _career_coach_error(
      action=action or "unknown",
      code="invalid_action",
      message="Unsupported career coach action.",
    )

  payload = payload if isinstance(payload, dict) else {}

  list_like_keys = [
    "current_skills",
    "achievements",
    "constraints",
    "career_interests",
    "target_skills",
    "completed_topics",
    "completed_tasks",
    "blocked_tasks",
    "wins",
    "interview_types",
  ]
  normalized_payload = dict(payload)
  for key in list_like_keys:
    if key in normalized_payload:
      normalized_payload[key] = _normalize_string_list(normalized_payload.get(key))

  if "years_experience" in normalized_payload:
    normalized_payload["years_experience"] = _coerce_int(
      normalized_payload.get("years_experience"), default=0, minimum=0, maximum=50
    )
  if "timeline_weeks" in normalized_payload:
    normalized_payload["timeline_weeks"] = _coerce_int(
      normalized_payload.get("timeline_weeks"), default=12, minimum=2, maximum=104
    )
  if "weekly_hours" in normalized_payload:
    normalized_payload["weekly_hours"] = _coerce_int(
      normalized_payload.get("weekly_hours"), default=6, minimum=1, maximum=80
    )
  if "week_number" in normalized_payload:
    normalized_payload["week_number"] = _coerce_int(
      normalized_payload.get("week_number"), default=1, minimum=1, maximum=520
    )
  if "time_spent_hours" in normalized_payload:
    normalized_payload["time_spent_hours"] = _coerce_int(
      normalized_payload.get("time_spent_hours"), default=0, minimum=0, maximum=100
    )

  if action in {"opportunity_strategy", "build_roadmap", "interview_readiness"}:
    target_role = str(normalized_payload.get("target_role") or "").strip()
    if not target_role:
      return _career_coach_error(
        action=action,
        code="target_role_required",
        message="target_role is required for this action.",
      )

  if action == "intake_assessment":
    content_available = any(
      bool(str(normalized_payload.get(key) or "").strip())
      for key in ["current_role", "target_role", "current_skills", "achievements", "career_interests"]
    )
    if not content_available:
      return _career_coach_error(
        action=action,
        code="insufficient_input",
        message=(
          "Provide at least one of current_role, target_role, current_skills, "
          "achievements, or career_interests."
        ),
      )

  def _normalize_topic_label(value: str) -> str:
    import re

    lowered = str(value or "").strip().lower()
    lowered = re.sub(r"[^a-z0-9\s]+", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered

  def _collect_expected_week_topics(roadmap_report: dict, week_number: int) -> List[str]:
    if not isinstance(roadmap_report, dict):
      return []

    weekly_plan = roadmap_report.get("weekly_plan")
    if not isinstance(weekly_plan, list):
      return []

    current_week_plan = None
    for item in weekly_plan:
      if not isinstance(item, dict):
        continue
      plan_week = _coerce_int(item.get("week"), default=-1, minimum=-1, maximum=520)
      if plan_week == week_number:
        current_week_plan = item
        break

    if not isinstance(current_week_plan, dict):
      return []

    candidates: List[str] = []
    candidates.extend(_normalize_string_list(current_week_plan.get("topics")))
    if not candidates:
      candidates.extend(_normalize_string_list(current_week_plan.get("tasks")))

    focus = str(current_week_plan.get("focus") or "").strip()
    if focus:
      candidates.append(focus)

    deduped: List[str] = []
    seen = set()
    for candidate in candidates:
      normalized = _normalize_topic_label(candidate)
      if not normalized or normalized in seen:
        continue
      seen.add(normalized)
      deduped.append(str(candidate).strip())
    return deduped

  if action == "weekly_checkin":
    completed_topics = _normalize_string_list(normalized_payload.get("completed_topics"))
    normalized_payload["completed_topics"] = completed_topics
    if not completed_topics:
      return _career_coach_error(
        action=action,
        code="completed_topics_required",
        message="Provide completed_topics for the weekly check-in.",
      )

    roadmap_report = normalized_payload.get("roadmap_report")
    if not isinstance(roadmap_report, dict):
      return _career_coach_error(
        action=action,
        code="roadmap_required",
        message="roadmap_report is required for weekly_checkin.",
      )

    week_number = _coerce_int(normalized_payload.get("week_number"), default=1, minimum=1, maximum=520)
    expected_topics = _collect_expected_week_topics(roadmap_report, week_number)
    normalized_payload["expected_week_topics"] = expected_topics

    matched_topics: List[str] = []
    unmatched_topics: List[str] = []
    normalized_expected = [_normalize_topic_label(item) for item in expected_topics]

    if normalized_expected:
      for provided_topic in completed_topics:
        provided_normalized = _normalize_topic_label(provided_topic)
        has_match = any(
          provided_normalized and (
            provided_normalized in expected_normalized or expected_normalized in provided_normalized
          )
          for expected_normalized in normalized_expected
        )
        if has_match:
          matched_topics.append(provided_topic)
        else:
          unmatched_topics.append(provided_topic)

      normalized_payload["matched_roadmap_topics"] = matched_topics
      normalized_payload["unmatched_topics"] = unmatched_topics

      if not matched_topics:
        return _career_coach_error(
          action=action,
          code="topic_mismatch",
          message=(
            "completed_topics must align with roadmap topics for this week. "
            f"Expected topics include: {', '.join(expected_topics[:8])}"
          ),
        )

  schema_by_action = {
    "intake_assessment": """{
  "action": "intake_assessment",
  "status": "ok",
  "profile_summary": "string",
  "professional_brand": "string",
  "strengths_to_leverage": ["string"],
  "risks_to_address": ["string"],
  "recommended_career_paths": [
    { "path": "string", "fit_score": 0, "rationale": "string", "first_steps": ["string"] }
  ],
  "immediate_priorities": ["string"],
  "ninety_day_focus": ["string"],
  "metrics_to_track": [
    { "metric": "string", "target": "string", "cadence": "weekly|biweekly|monthly" }
  ],
  "assumptions": ["string"],
  "confidence_score": 0
}""",
    "opportunity_strategy": """{
  "action": "opportunity_strategy",
  "status": "ok",
  "target_role": "string",
  "market_fit_score": 0,
  "strategy_summary": "string",
  "positioning_statement": "string",
  "top_role_tracks": [
    {
      "role_title": "string",
      "fit_score": 0,
      "why_fit": "string",
      "entry_points": ["string"]
    }
  ],
  "application_channel_mix": [
    { "channel": "referrals|direct_apply|recruiter_outreach|community", "target_share": "string", "weekly_actions": ["string"] }
  ],
  "market_signals_to_watch": ["string"],
  "networking_plan": ["string"],
  "portfolio_narrative": ["string"],
  "thirty_day_experiments": [
    { "experiment": "string", "success_metric": "string", "time_budget_hours": 0 }
  ],
  "risks_and_countermoves": [
    { "risk": "string", "countermove": "string" }
  ],
  "assumptions": ["string"]
}""",
    "build_roadmap": """{
  "action": "build_roadmap",
  "status": "ok",
  "target_role": "string",
  "timeline_weeks": 0,
  "roadmap_summary": "string",
  "phases": [
    {
      "phase_name": "string",
      "start_week": 0,
      "end_week": 0,
      "goal": "string",
      "key_topics": ["string"],
      "milestones": ["string"],
      "deliverables": ["string"],
      "success_criteria": ["string"]
    }
  ],
  "weekly_plan": [
    {
      "week": 0,
      "focus": "string",
      "topics": ["string"],
      "tasks": ["string"],
      "time_budget_hours": 0,
      "output": "string"
    }
  ],
  "application_strategy": {
    "start_week": 0,
    "target_applications_per_week": 0,
    "target_referrals_per_month": 0,
    "company_tiers": ["string"]
  },
  "review_cadence": { "weekly_checkin": "string", "monthly_review": "string" },
  "burnout_guardrails": ["string"],
  "assumptions": ["string"]
}""",
    "weekly_checkin": """{
  "action": "weekly_checkin",
  "status": "ok",
  "week_number": 0,
  "progress_score": 0,
  "progress_status": "on_track|at_risk|off_track",
  "completed_topics": ["string"],
  "matched_roadmap_topics": ["string"],
  "unmatched_topics": ["string"],
  "topic_alignment_note": "string",
  "wins": ["string"],
  "blockers": [{ "blocker": "string", "impact": "string", "next_step": "string", "owner": "string" }],
  "plan_adjustments": [{ "change": "string", "reason": "string" }],
  "next_week_plan": ["string"],
  "motivation_note": "string",
  "escalate_if": ["string"],
  "assumptions": ["string"]
}""",
    "interview_readiness": """{
  "action": "interview_readiness",
  "status": "ok",
  "target_role": "string",
  "readiness_score": 0,
  "readiness_breakdown": [{ "area": "string", "score": 0, "gap": "string" }],
  "top_question_themes": [
    { "theme": "string", "sample_questions": ["string"], "what_good_looks_like": ["string"] }
  ],
  "story_bank": [{ "story_title": "string", "competencies": ["string"], "outline": ["string"] }],
  "technical_round_plan": ["string"],
  "behavioral_round_plan": ["string"],
  "mock_schedule": [{ "week": 0, "focus": "string", "session_goal": "string" }],
  "negotiation_prep": ["string"],
  "final_30_day_checklist": ["string"],
  "assumptions": ["string"]
}""",
  }

  action_guidance = {
    "intake_assessment": (
      "Use the profile details to produce a realistic baseline, clear positioning, "
      "and concrete priorities tailored to the user's context."
    ),
    "opportunity_strategy": (
      "Build a role-market strategy focused on positioning, channel mix, narrative, and measurable experiments. "
      "Do not do detailed skill-gap diagnostics in this action."
    ),
    "build_roadmap": (
      "Produce a practical execution plan with measurable weekly outputs and a sustainable workload. "
      "Each week must include explicit topics that can be used for weekly check-in validation."
    ),
    "weekly_checkin": (
      "Evaluate momentum against the roadmap for the specific week. "
      "Use completed_topics and report roadmap-topic alignment before proposing adjustments."
    ),
    "interview_readiness": (
      "Assess readiness by interview dimension, include practical drills, and create a focused preparation sequence."
    ),
  }

  prompt = "\n".join(
    [
      "You are an elite Career Coach for working professionals.",
      "You provide structured, execution-focused advice grounded in the user's input.",
      "Do not provide generic motivational filler. Be specific and practical.",
      "",
      f"ACTION: {action}",
      "",
      "INPUT PAYLOAD (JSON):",
      json.dumps(normalized_payload, ensure_ascii=False, indent=2),
      "",
      "RESPONSE CONTRACT:",
      "- Return ONLY one valid JSON object.",
      "- Do not add markdown fences or explanatory text outside JSON.",
      "- Do not use placeholders (no <...>, no [insert ...]).",
      "- Use concrete recommendations tied to the payload.",
      "- Keep lists concise but actionable.",
      "",
      "ACTION-SPECIFIC GUIDANCE:",
      action_guidance[action],
      "",
      "JSON SCHEMA (keys must match exactly):",
      schema_by_action[action],
    ]
  )

  try:
    gemini_client = GeminiClient()
    content = gemini_client.generate_response(
      system_prompt=(
        "You are a structured career strategy engine. "
        "Return strict JSON only, following the user-provided schema exactly."
      ),
      messages=[{"role": "user", "content": prompt}],
      model="gemini-2.5-pro",
      temperature=0.35,
    )
  except Exception as e:
    return _career_coach_error(
      action=action,
      code="generation_failed",
      message=f"Failed to generate career coach response: {str(e)}",
    )

  if not content:
    return _career_coach_error(
      action=action,
      code="empty_response",
      message="Model returned an empty response.",
    )

  candidate = _extract_first_json_object(content.strip())
  if not candidate:
    return _career_coach_error(
      action=action,
      code="invalid_json",
      message="Model response did not contain a valid JSON object.",
    )

  try:
    parsed = json.loads(candidate)
  except Exception:
    return _career_coach_error(
      action=action,
      code="invalid_json",
      message="Model response was not valid JSON.",
    )

  if not isinstance(parsed, dict):
    return _career_coach_error(
      action=action,
      code="invalid_schema",
      message="Model response must be a JSON object.",
    )

  def _as_string_list(value) -> List[str]:
    if isinstance(value, list):
      return [str(item).strip() for item in value if str(item).strip()]
    return _normalize_string_list(value)

  def _as_object_list(value) -> List[dict]:
    if not isinstance(value, list):
      return []
    return [item for item in value if isinstance(item, dict)]

  if action == "intake_assessment":
    parsed["strengths_to_leverage"] = _as_string_list(parsed.get("strengths_to_leverage"))
    parsed["risks_to_address"] = _as_string_list(parsed.get("risks_to_address"))
    parsed["immediate_priorities"] = _as_string_list(parsed.get("immediate_priorities"))
    parsed["ninety_day_focus"] = _as_string_list(parsed.get("ninety_day_focus"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    parsed["confidence_score"] = _coerce_int(parsed.get("confidence_score"), default=0, minimum=0, maximum=100)
    paths = []
    for item in _as_object_list(parsed.get("recommended_career_paths")):
      paths.append(
        {
          "path": str(item.get("path") or "").strip(),
          "fit_score": _coerce_int(item.get("fit_score"), default=0, minimum=0, maximum=100),
          "rationale": str(item.get("rationale") or "").strip(),
          "first_steps": _as_string_list(item.get("first_steps")),
        }
      )
    parsed["recommended_career_paths"] = paths
    metrics = []
    for item in _as_object_list(parsed.get("metrics_to_track")):
      metrics.append(
        {
          "metric": str(item.get("metric") or "").strip(),
          "target": str(item.get("target") or "").strip(),
          "cadence": str(item.get("cadence") or "").strip(),
        }
      )
    parsed["metrics_to_track"] = metrics

  elif action == "opportunity_strategy":
    parsed["market_fit_score"] = _coerce_int(parsed.get("market_fit_score"), default=0, minimum=0, maximum=100)
    parsed["market_signals_to_watch"] = _as_string_list(parsed.get("market_signals_to_watch"))
    parsed["networking_plan"] = _as_string_list(parsed.get("networking_plan"))
    parsed["portfolio_narrative"] = _as_string_list(parsed.get("portfolio_narrative"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    parsed["top_role_tracks"] = _as_object_list(parsed.get("top_role_tracks"))
    parsed["application_channel_mix"] = _as_object_list(parsed.get("application_channel_mix"))
    parsed["thirty_day_experiments"] = _as_object_list(parsed.get("thirty_day_experiments"))
    parsed["risks_and_countermoves"] = _as_object_list(parsed.get("risks_and_countermoves"))

  elif action == "build_roadmap":
    parsed["timeline_weeks"] = _coerce_int(parsed.get("timeline_weeks"), default=12, minimum=2, maximum=104)
    phases = []
    for item in _as_object_list(parsed.get("phases")):
      phases.append(
        {
          "phase_name": str(item.get("phase_name") or "").strip(),
          "start_week": _coerce_int(item.get("start_week"), default=1, minimum=1, maximum=104),
          "end_week": _coerce_int(item.get("end_week"), default=1, minimum=1, maximum=104),
          "goal": str(item.get("goal") or "").strip(),
          "key_topics": _as_string_list(item.get("key_topics")),
          "milestones": _as_string_list(item.get("milestones")),
          "deliverables": _as_string_list(item.get("deliverables")),
          "success_criteria": _as_string_list(item.get("success_criteria")),
        }
      )
    parsed["phases"] = phases

    weekly_plan = []
    for item in _as_object_list(parsed.get("weekly_plan")):
      focus = str(item.get("focus") or "").strip()
      topics = _as_string_list(item.get("topics"))
      tasks = _as_string_list(item.get("tasks"))
      if not topics and tasks:
        topics = tasks[:3]
      if not topics and focus:
        topics = [focus]
      weekly_plan.append(
        {
          "week": _coerce_int(item.get("week"), default=1, minimum=1, maximum=104),
          "focus": focus,
          "topics": topics,
          "tasks": tasks,
          "time_budget_hours": _coerce_int(item.get("time_budget_hours"), default=0, minimum=0, maximum=80),
          "output": str(item.get("output") or "").strip(),
        }
      )
    parsed["weekly_plan"] = weekly_plan
    parsed["burnout_guardrails"] = _as_string_list(parsed.get("burnout_guardrails"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    if not isinstance(parsed.get("application_strategy"), dict):
      parsed["application_strategy"] = {}
    if not isinstance(parsed.get("review_cadence"), dict):
      parsed["review_cadence"] = {}

  elif action == "weekly_checkin":
    parsed["week_number"] = _coerce_int(parsed.get("week_number"), default=1, minimum=1, maximum=520)
    parsed["progress_score"] = _coerce_int(parsed.get("progress_score"), default=0, minimum=0, maximum=100)
    parsed["completed_topics"] = _as_string_list(
      parsed.get("completed_topics") or normalized_payload.get("completed_topics")
    )
    parsed["matched_roadmap_topics"] = _as_string_list(
      parsed.get("matched_roadmap_topics") or normalized_payload.get("matched_roadmap_topics")
    )
    parsed["unmatched_topics"] = _as_string_list(
      parsed.get("unmatched_topics") or normalized_payload.get("unmatched_topics")
    )
    parsed["topic_alignment_note"] = str(parsed.get("topic_alignment_note") or "").strip()
    if not parsed["topic_alignment_note"]:
      if parsed["unmatched_topics"]:
        parsed["topic_alignment_note"] = "Some completed topics are outside this week's roadmap scope."
      else:
        parsed["topic_alignment_note"] = "Completed topics align with this week's roadmap focus."
    parsed["wins"] = _as_string_list(parsed.get("wins"))
    parsed["next_week_plan"] = _as_string_list(parsed.get("next_week_plan"))
    parsed["escalate_if"] = _as_string_list(parsed.get("escalate_if"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    parsed["blockers"] = _as_object_list(parsed.get("blockers"))
    parsed["plan_adjustments"] = _as_object_list(parsed.get("plan_adjustments"))

  elif action == "interview_readiness":
    parsed["readiness_score"] = _coerce_int(parsed.get("readiness_score"), default=0, minimum=0, maximum=100)
    parsed["technical_round_plan"] = _as_string_list(parsed.get("technical_round_plan"))
    parsed["behavioral_round_plan"] = _as_string_list(parsed.get("behavioral_round_plan"))
    parsed["negotiation_prep"] = _as_string_list(parsed.get("negotiation_prep"))
    parsed["final_30_day_checklist"] = _as_string_list(parsed.get("final_30_day_checklist"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    parsed["readiness_breakdown"] = _as_object_list(parsed.get("readiness_breakdown"))
    parsed["top_question_themes"] = _as_object_list(parsed.get("top_question_themes"))
    parsed["story_bank"] = _as_object_list(parsed.get("story_bank"))
    parsed["mock_schedule"] = _as_object_list(parsed.get("mock_schedule"))

  parsed["action"] = action
  parsed.setdefault("status", "ok")
  return json.dumps(parsed, ensure_ascii=False)


def _assess_career_profile(profile_json: str) -> str:
  """Run intake assessment for the Career Coach agent."""
  payload = _parse_json_payload(profile_json)
  return _generate_career_coach_response("intake_assessment", payload)


def _analyze_career_opportunity_strategy(
  profile_json: str,
  target_role: str = "",
  job_description: str = "",
) -> str:
  """Build a role-market opportunity strategy against a target role."""
  payload = _parse_json_payload(profile_json)
  if target_role:
    payload["target_role"] = target_role
  if job_description:
    payload["job_description"] = job_description
  return _generate_career_coach_response("opportunity_strategy", payload)


def _analyze_career_skill_gap(
  profile_json: str,
  target_role: str = "",
  job_description: str = "",
) -> str:
  """Backward-compatible alias for legacy skill-gap action naming."""
  return _analyze_career_opportunity_strategy(
    profile_json=profile_json,
    target_role=target_role,
    job_description=job_description,
  )


def _generate_career_roadmap(
  profile_json: str,
  target_role: str = "",
  timeline_weeks: int = 12,
  weekly_hours: int = 6,
) -> str:
  """Generate a structured career execution roadmap."""
  payload = _parse_json_payload(profile_json)
  if target_role:
    payload["target_role"] = target_role
  payload["timeline_weeks"] = timeline_weeks
  payload["weekly_hours"] = weekly_hours
  return _generate_career_coach_response("build_roadmap", payload)


def _evaluate_weekly_career_progress(checkin_json: str) -> str:
  """Evaluate weekly execution progress and return course corrections."""
  payload = _parse_json_payload(checkin_json)
  return _generate_career_coach_response("weekly_checkin", payload)


def _create_interview_readiness_plan(
  profile_json: str,
  target_role: str = "",
  interview_types: str = "",
) -> str:
  """Assess interview readiness and produce a focused prep plan."""
  payload = _parse_json_payload(profile_json)
  if target_role:
    payload["target_role"] = target_role
  if interview_types:
    payload["interview_types"] = _normalize_string_list(interview_types)
  return _generate_career_coach_response("interview_readiness", payload)


def _skill_gap_agent_error(action: str, code: str, message: str) -> str:
  """Return a stable JSON error payload for Skill Gap agent flows."""
  return json.dumps(
    {
      "action": action,
      "status": "error",
      "error": code,
      "message": message,
    },
    ensure_ascii=False,
  )


def _generate_skill_gap_agent_response(action: str, payload: dict) -> str:
  """
  Generate structured JSON outputs for Skill Gap agent actions.

  Supported actions:
    - profile_baseline
    - identify_skill_gaps
    - build_development_plan
    - weekly_progress_checkin
    - readiness_assessment
  """
  from app.services.gemini import GeminiClient

  action = (action or "").strip().lower()
  allowed_actions = {
    "profile_baseline",
    "identify_skill_gaps",
    "build_development_plan",
    "weekly_progress_checkin",
    "readiness_assessment",
  }
  if action not in allowed_actions:
    return _skill_gap_agent_error(
      action=action or "unknown",
      code="invalid_action",
      message="Unsupported skill gap action.",
    )

  payload = payload if isinstance(payload, dict) else {}
  normalized_payload = dict(payload)

  list_like_keys = [
    "current_skills",
    "target_skills",
    "constraints",
    "focus_areas",
    "projects",
    "learning_preferences",
    "role_expectations",
    "completed_activities",
    "blocked_activities",
    "wins",
    "support_needed",
    "evidence_links",
    "manager_feedback",
    "peer_feedback",
  ]
  for key in list_like_keys:
    if key in normalized_payload:
      normalized_payload[key] = _normalize_string_list(normalized_payload.get(key))

  if "years_experience" in normalized_payload:
    normalized_payload["years_experience"] = _coerce_int(
      normalized_payload.get("years_experience"), default=0, minimum=0, maximum=50
    )
  if "timeline_weeks" in normalized_payload:
    normalized_payload["timeline_weeks"] = _coerce_int(
      normalized_payload.get("timeline_weeks"), default=12, minimum=2, maximum=104
    )
  if "weekly_learning_hours" in normalized_payload:
    normalized_payload["weekly_learning_hours"] = _coerce_int(
      normalized_payload.get("weekly_learning_hours"), default=5, minimum=1, maximum=80
    )
  if "week_number" in normalized_payload:
    normalized_payload["week_number"] = _coerce_int(
      normalized_payload.get("week_number"), default=1, minimum=1, maximum=520
    )
  if "learning_hours_spent" in normalized_payload:
    normalized_payload["learning_hours_spent"] = _coerce_int(
      normalized_payload.get("learning_hours_spent"), default=0, minimum=0, maximum=120
    )

  if action in {"identify_skill_gaps", "build_development_plan", "readiness_assessment"}:
    target_role = str(normalized_payload.get("target_role") or "").strip()
    if not target_role:
      return _skill_gap_agent_error(
        action=action,
        code="target_role_required",
        message="target_role is required for this action.",
      )

  if action == "profile_baseline":
    has_content = (
      bool(str(normalized_payload.get("current_role") or "").strip())
      or bool(str(normalized_payload.get("target_role") or "").strip())
      or bool(normalized_payload.get("current_skills"))
      or bool(normalized_payload.get("projects"))
      or bool(str(normalized_payload.get("performance_notes") or "").strip())
    )
    if not has_content:
      return _skill_gap_agent_error(
        action=action,
        code="insufficient_input",
        message=(
          "Provide at least one of current_role, target_role, current_skills, "
          "projects, or performance_notes."
        ),
      )

  schema_by_action = {
    "profile_baseline": """{
  "action": "profile_baseline",
  "status": "ok",
  "profile_summary": "string",
  "current_capability_snapshot": [
    { "skill": "string", "current_level": "string", "evidence": "string" }
  ],
  "strengths": ["string"],
  "risks": ["string"],
  "focus_areas": ["string"],
  "manager_alignment_questions": ["string"],
  "confidence_score": 0,
  "assumptions": ["string"]
}""",
    "identify_skill_gaps": """{
  "action": "identify_skill_gaps",
  "status": "ok",
  "target_role": "string",
  "overall_gap_score": 0,
  "critical_skill_gaps": [
    {
      "skill": "string",
      "priority": "high|medium|low",
      "current_level": "string",
      "target_level": "string",
      "business_impact": "string",
      "development_recommendation": "string"
    }
  ],
  "adjacent_skills_to_build": ["string"],
  "role_expectation_keywords": ["string"],
  "quick_wins": ["string"],
  "manager_support_requests": ["string"],
  "assumptions": ["string"]
}""",
    "build_development_plan": """{
  "action": "build_development_plan",
  "status": "ok",
  "target_role": "string",
  "timeline_weeks": 0,
  "plan_summary": "string",
  "phases": [
    {
      "phase_name": "string",
      "start_week": 0,
      "end_week": 0,
      "goal": "string",
      "deliverables": ["string"],
      "activities": ["string"],
      "success_criteria": ["string"]
    }
  ],
  "weekly_learning_plan": [
    {
      "week": 0,
      "focus": "string",
      "activities": ["string"],
      "time_budget_hours": 0,
      "evidence_output": "string"
    }
  ],
  "enablement_resources": [
    { "resource_type": "course|mentor|project|reading|practice", "name": "string", "purpose": "string", "estimated_hours": 0 }
  ],
  "manager_checkpoints": [
    { "week": 0, "agenda": "string", "expected_outcomes": ["string"] }
  ],
  "risk_mitigation": ["string"],
  "assumptions": ["string"]
}""",
    "weekly_progress_checkin": """{
  "action": "weekly_progress_checkin",
  "status": "ok",
  "week_number": 0,
  "progress_score": 0,
  "trajectory": "on_track|at_risk|off_track",
  "wins": ["string"],
  "blockers": [
    { "blocker": "string", "impact": "string", "next_step": "string", "owner": "string" }
  ],
  "plan_adjustments": [
    { "change": "string", "reason": "string", "effective_week": 0 }
  ],
  "next_week_priorities": ["string"],
  "support_needed": ["string"],
  "assumptions": ["string"]
}""",
    "readiness_assessment": """{
  "action": "readiness_assessment",
  "status": "ok",
  "target_role": "string",
  "readiness_score": 0,
  "competency_breakdown": [
    { "competency": "string", "score": 0, "gap": "string", "evidence_needed": "string" }
  ],
  "strongest_signals": ["string"],
  "remaining_gaps": ["string"],
  "thirty_day_focus": ["string"],
  "stakeholder_alignment_plan": ["string"],
  "decision_risks": ["string"],
  "assumptions": ["string"]
}""",
  }

  action_guidance = {
    "profile_baseline": (
      "Build an objective baseline of current capabilities and readiness risks using only the provided context."
    ),
    "identify_skill_gaps": (
      "Prioritize missing skills by business impact and expected role outcomes. Focus on what closes gaps fastest."
    ),
    "build_development_plan": (
      "Create a practical, time-bound upskilling plan for a working employee with measurable weekly outputs."
    ),
    "weekly_progress_checkin": (
      "Assess progress honestly, identify blockers concretely, and propose specific plan adjustments."
    ),
    "readiness_assessment": (
      "Evaluate promotion or role-readiness across competencies and define the shortest path to close remaining gaps."
    ),
  }

  prompt = "\n".join(
    [
      "You are an expert Skill Gap Agent for employees.",
      "You produce structured, execution-focused development guidance.",
      "Avoid generic advice and avoid motivational filler.",
      "",
      f"ACTION: {action}",
      "",
      "INPUT PAYLOAD (JSON):",
      json.dumps(normalized_payload, ensure_ascii=False, indent=2),
      "",
      "RESPONSE CONTRACT:",
      "- Return ONLY one valid JSON object.",
      "- Do not add markdown fences or explanatory text outside JSON.",
      "- Do not use placeholders (no <...>, no [insert ...]).",
      "- Recommendations must be grounded in the payload and role expectations.",
      "- Keep outputs concise, practical, and measurable.",
      "",
      "ACTION-SPECIFIC GUIDANCE:",
      action_guidance[action],
      "",
      "JSON SCHEMA (keys must match exactly):",
      schema_by_action[action],
    ]
  )

  try:
    gemini_client = GeminiClient()
    content = gemini_client.generate_response(
      system_prompt=(
        "You are a structured workforce capability engine. "
        "Return strict JSON only, following the requested schema exactly."
      ),
      messages=[{"role": "user", "content": prompt}],
      model="gemini-2.5-pro",
      temperature=0.3,
    )
  except Exception as e:
    return _skill_gap_agent_error(
      action=action,
      code="generation_failed",
      message=f"Failed to generate skill gap response: {str(e)}",
    )

  if not content:
    return _skill_gap_agent_error(
      action=action,
      code="empty_response",
      message="Model returned an empty response.",
    )

  candidate = _extract_first_json_object(content.strip())
  if not candidate:
    return _skill_gap_agent_error(
      action=action,
      code="invalid_json",
      message="Model response did not contain a valid JSON object.",
    )

  try:
    parsed = json.loads(candidate)
  except Exception:
    return _skill_gap_agent_error(
      action=action,
      code="invalid_json",
      message="Model response was not valid JSON.",
    )

  if not isinstance(parsed, dict):
    return _skill_gap_agent_error(
      action=action,
      code="invalid_schema",
      message="Model response must be a JSON object.",
    )

  def _as_string_list(value) -> List[str]:
    if isinstance(value, list):
      return [str(item).strip() for item in value if str(item).strip()]
    return _normalize_string_list(value)

  def _as_object_list(value) -> List[dict]:
    if not isinstance(value, list):
      return []
    return [item for item in value if isinstance(item, dict)]

  if action == "profile_baseline":
    parsed["strengths"] = _as_string_list(parsed.get("strengths"))
    parsed["risks"] = _as_string_list(parsed.get("risks"))
    parsed["focus_areas"] = _as_string_list(parsed.get("focus_areas"))
    parsed["manager_alignment_questions"] = _as_string_list(parsed.get("manager_alignment_questions"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    parsed["confidence_score"] = _coerce_int(parsed.get("confidence_score"), default=0, minimum=0, maximum=100)
    capability_items = []
    for item in _as_object_list(parsed.get("current_capability_snapshot")):
      capability_items.append(
        {
          "skill": str(item.get("skill") or "").strip(),
          "current_level": str(item.get("current_level") or "").strip(),
          "evidence": str(item.get("evidence") or "").strip(),
        }
      )
    parsed["current_capability_snapshot"] = capability_items

  elif action == "identify_skill_gaps":
    parsed["overall_gap_score"] = _coerce_int(parsed.get("overall_gap_score"), default=0, minimum=0, maximum=100)
    parsed["adjacent_skills_to_build"] = _as_string_list(parsed.get("adjacent_skills_to_build"))
    parsed["role_expectation_keywords"] = _as_string_list(parsed.get("role_expectation_keywords"))
    parsed["quick_wins"] = _as_string_list(parsed.get("quick_wins"))
    parsed["manager_support_requests"] = _as_string_list(parsed.get("manager_support_requests"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    critical_gaps = []
    for item in _as_object_list(parsed.get("critical_skill_gaps")):
      critical_gaps.append(
        {
          "skill": str(item.get("skill") or "").strip(),
          "priority": str(item.get("priority") or "").strip(),
          "current_level": str(item.get("current_level") or "").strip(),
          "target_level": str(item.get("target_level") or "").strip(),
          "business_impact": str(item.get("business_impact") or "").strip(),
          "development_recommendation": str(item.get("development_recommendation") or "").strip(),
        }
      )
    parsed["critical_skill_gaps"] = critical_gaps

  elif action == "build_development_plan":
    parsed["timeline_weeks"] = _coerce_int(parsed.get("timeline_weeks"), default=12, minimum=2, maximum=104)
    parsed["phases"] = _as_object_list(parsed.get("phases"))
    parsed["weekly_learning_plan"] = _as_object_list(parsed.get("weekly_learning_plan"))
    parsed["enablement_resources"] = _as_object_list(parsed.get("enablement_resources"))
    parsed["manager_checkpoints"] = _as_object_list(parsed.get("manager_checkpoints"))
    parsed["risk_mitigation"] = _as_string_list(parsed.get("risk_mitigation"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))

  elif action == "weekly_progress_checkin":
    parsed["week_number"] = _coerce_int(parsed.get("week_number"), default=1, minimum=1, maximum=520)
    parsed["progress_score"] = _coerce_int(parsed.get("progress_score"), default=0, minimum=0, maximum=100)
    parsed["wins"] = _as_string_list(parsed.get("wins"))
    parsed["next_week_priorities"] = _as_string_list(parsed.get("next_week_priorities"))
    parsed["support_needed"] = _as_string_list(parsed.get("support_needed"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    parsed["blockers"] = _as_object_list(parsed.get("blockers"))
    parsed["plan_adjustments"] = _as_object_list(parsed.get("plan_adjustments"))

  elif action == "readiness_assessment":
    parsed["readiness_score"] = _coerce_int(parsed.get("readiness_score"), default=0, minimum=0, maximum=100)
    parsed["strongest_signals"] = _as_string_list(parsed.get("strongest_signals"))
    parsed["remaining_gaps"] = _as_string_list(parsed.get("remaining_gaps"))
    parsed["thirty_day_focus"] = _as_string_list(parsed.get("thirty_day_focus"))
    parsed["stakeholder_alignment_plan"] = _as_string_list(parsed.get("stakeholder_alignment_plan"))
    parsed["decision_risks"] = _as_string_list(parsed.get("decision_risks"))
    parsed["assumptions"] = _as_string_list(parsed.get("assumptions"))
    competency_breakdown = []
    for item in _as_object_list(parsed.get("competency_breakdown")):
      competency_breakdown.append(
        {
          "competency": str(item.get("competency") or "").strip(),
          "score": _coerce_int(item.get("score"), default=0, minimum=0, maximum=100),
          "gap": str(item.get("gap") or "").strip(),
          "evidence_needed": str(item.get("evidence_needed") or "").strip(),
        }
      )
    parsed["competency_breakdown"] = competency_breakdown

  parsed["action"] = action
  parsed.setdefault("status", "ok")
  return json.dumps(parsed, ensure_ascii=False)


def _build_skill_gap_baseline(profile_json: str) -> str:
  """Create a current-state capability baseline for an employee."""
  payload = _parse_json_payload(profile_json)
  return _generate_skill_gap_agent_response("profile_baseline", payload)


def _identify_employee_skill_gaps(
  profile_json: str,
  target_role: str = "",
  role_expectations: str = "",
) -> str:
  """Identify prioritized skill gaps for a target role."""
  payload = _parse_json_payload(profile_json)
  if target_role:
    payload["target_role"] = target_role
  if role_expectations:
    payload["role_expectations"] = _normalize_string_list(role_expectations)
  return _generate_skill_gap_agent_response("identify_skill_gaps", payload)


def _build_skill_development_plan(
  profile_json: str,
  target_role: str = "",
  timeline_weeks: int = 12,
  weekly_learning_hours: int = 5,
) -> str:
  """Build a structured upskilling plan for an employee."""
  payload = _parse_json_payload(profile_json)
  if target_role:
    payload["target_role"] = target_role
  payload["timeline_weeks"] = timeline_weeks
  payload["weekly_learning_hours"] = weekly_learning_hours
  return _generate_skill_gap_agent_response("build_development_plan", payload)


def _run_skill_gap_weekly_checkin(checkin_json: str) -> str:
  """Evaluate weekly execution progress for the skill development plan."""
  payload = _parse_json_payload(checkin_json)
  return _generate_skill_gap_agent_response("weekly_progress_checkin", payload)


def _assess_skill_readiness(
  profile_json: str,
  target_role: str = "",
) -> str:
  """Assess readiness for the target role using capability evidence."""
  payload = _parse_json_payload(profile_json)
  if target_role:
    payload["target_role"] = target_role
  return _generate_skill_gap_agent_response("readiness_assessment", payload)


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

  elif slug == PREBUILT_AGENT_SLUGS["micro_learning_agent"]:
    tools.append(
      Tool(
        name="generate_micro_lesson",
        func=_generate_micro_lesson,
        description=(
          "Generate a focused micro-lesson (5-15 minutes) on a specific topic. "
          "Lessons are structured with concept, explanation, examples, and key takeaways. "
          "Args: topic (str), time_minutes (int: 5/10/15, default=5), difficulty (str: easy/medium/hard, default='medium')."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_flashcards",
        func=_create_flashcards,
        description=(
          "Create flashcards for spaced repetition learning. "
          "Generates Q&A format flashcards for key concepts. "
          "Args: topic (str), num_cards (int: 3-10, default=5)."
        ),
      )
    )
    tools.append(
      Tool(
        name="generate_quiz",
        func=_generate_quiz,
        description=(
          "Generate a quick 2-3 question micro-quiz for instant feedback after lessons. "
          "Args: topic (str), difficulty (str: easy/medium/hard, default='medium'), num_questions (int: 2-3 for micro-learning, default=2)."
        ),
      )
    )
    tools.append(
      Tool(
        name="build_study_plan",
        func=_build_study_plan,
        description="Create a daily/weekly micro-learning schedule with time slots and topics.",
      )
    )

  elif slug == PREBUILT_AGENT_SLUGS["exam_prep_agent"]:
    tools.append(
      Tool(
        name="create_practice_exam",
        func=_create_practice_exam,
        description=(
          "Create a full-length practice exam with various question types (MCQ, short answer, essay). "
          "Includes time limits, answer key, and scoring rubric. "
          "Args: exam_type (str: SAT/GRE/Certification/etc.), subject (str), num_questions (int, default=50), time_limit (int, minutes, default=60), difficulty (str: easy/medium/hard, default='medium')."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_study_schedule",
        func=_create_study_schedule,
        description=(
          "Create a personalized study schedule leading up to the exam date. "
          "Includes daily goals, topic breakdown, practice exam dates, and milestones. "
          "Args: exam_date (str: YYYY-MM-DD), subjects (str, comma-separated), hours_per_day (int, default=2), current_level (str: beginner/intermediate/advanced, default='intermediate')."
        ),
      )
    )
    tools.append(
      Tool(
        name="identify_weak_areas",
        func=_identify_weak_areas,
        description=(
          "Analyze practice test results and identify areas needing improvement. "
          "Provides ranked weak areas, specific topics to focus on, and improvement strategies. "
          "Args: subject (str), practice_results (str: scores by topic/structured results), exam_type (str, optional)."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_exam_strategies",
        func=_create_exam_strategies,
        description=(
          "Provide comprehensive exam-taking strategies including time management, question prioritization, "
          "answer elimination techniques, and stress management tips. "
          "Args: exam_type (str), subject (str), question_format (str: MCQ/essay/mixed, default='mixed')."
        ),
      )
    )
    tools.append(
      Tool(
        name="generate_topic_review",
        func=_generate_topic_review,
        description=(
          "Create a focused review session for a specific topic with key concepts, examples, practice questions, "
          "and common mistakes. "
          "Args: topic (str), difficulty (str: easy/medium/hard, default='medium'), review_type (str: concept/example/practice/comprehensive, default='comprehensive')."
        ),
      )
    )
    tools.append(
      Tool(
        name="track_progress",
        func=_track_progress,
        description=(
          "Track and visualize exam preparation progress over time. "
          "Provides score trends, readiness assessment, milestones, and recommendations. "
          "Args: exam_type (str), practice_scores (str: list of scores over time), target_score (int, optional), exam_date (str: YYYY-MM-DD, optional)."
        ),
      )
    )
    # Include shared tools
    tools.append(
      Tool(
        name="generate_quiz",
        func=_generate_quiz,
        description=(
          "Generate quick practice quizzes for specific topics. "
          "Args: topic (str), difficulty (str: easy/medium/hard, default='medium'), num_questions (int, default=5)."
        ),
      )
    )
    tools.append(
      Tool(
        name="build_study_plan",
        func=_build_study_plan,
        description="Create a high-level study plan outline for exam preparation goals.",
      )
    )

  elif slug == PREBUILT_AGENT_SLUGS["career_coach_agent"]:
    tools.append(
      Tool(
        name="assess_career_profile",
        func=_assess_career_profile,
        description=(
          "Run a structured intake assessment for a working professional and return JSON with "
          "career positioning, priorities, risks, and metrics. "
          "Args: profile_json (str, JSON object with profile/context fields)."
        ),
      )
    )
    tools.append(
      Tool(
        name="analyze_career_opportunity_strategy",
        func=_analyze_career_opportunity_strategy,
        description=(
          "Build role-market opportunity strategy against a target role and return prioritized JSON output. "
          "Args: profile_json (str), target_role (str, optional), job_description (str, optional)."
        ),
      )
    )
    tools.append(
      Tool(
        name="generate_career_roadmap",
        func=_generate_career_roadmap,
        description=(
          "Generate a measurable weekly career roadmap with milestones and application strategy. "
          "Args: profile_json (str), target_role (str, optional), timeline_weeks (int, default=12), "
          "weekly_hours (int, default=6)."
        ),
      )
    )
    tools.append(
      Tool(
        name="evaluate_weekly_career_progress",
        func=_evaluate_weekly_career_progress,
        description=(
          "Evaluate weekly progress and produce JSON with blockers, adjustments, and next-week plan. "
          "Args: checkin_json (str, JSON object with weekly execution details)."
        ),
      )
    )
    tools.append(
      Tool(
        name="create_interview_readiness_plan",
        func=_create_interview_readiness_plan,
        description=(
          "Assess interview readiness for a target role and return a focused preparation plan in JSON. "
          "Args: profile_json (str), target_role (str, optional), interview_types (str, comma-separated, optional)."
        ),
      )
    )

  elif slug == PREBUILT_AGENT_SLUGS["skill_gap_agent"]:
    tools.append(
      Tool(
        name="build_skill_gap_baseline",
        func=_build_skill_gap_baseline,
        description=(
          "Build a current-state capability baseline for an employee and return structured JSON. "
          "Args: profile_json (str, JSON object with employee profile/context fields)."
        ),
      )
    )
    tools.append(
      Tool(
        name="identify_employee_skill_gaps",
        func=_identify_employee_skill_gaps,
        description=(
          "Identify and prioritize employee skill gaps for a target role. "
          "Args: profile_json (str), target_role (str, optional), role_expectations (str, comma-separated, optional)."
        ),
      )
    )
    tools.append(
      Tool(
        name="build_skill_development_plan",
        func=_build_skill_development_plan,
        description=(
          "Create a time-bound skill development plan with weekly outcomes and manager checkpoints. "
          "Args: profile_json (str), target_role (str, optional), timeline_weeks (int, default=12), "
          "weekly_learning_hours (int, default=5)."
        ),
      )
    )
    tools.append(
      Tool(
        name="run_skill_gap_weekly_checkin",
        func=_run_skill_gap_weekly_checkin,
        description=(
          "Evaluate weekly progress on the development plan and return blockers and adjustments in JSON. "
          "Args: checkin_json (str, JSON object with weekly execution details)."
        ),
      )
    )
    tools.append(
      Tool(
        name="assess_skill_readiness",
        func=_assess_skill_readiness,
        description=(
          "Assess readiness for a target role across core competencies and return structured JSON. "
          "Args: profile_json (str), target_role (str, optional)."
        ),
      )
    )

  elif slug == PREBUILT_AGENT_SLUGS["resume_review_agent"]:
    tools.append(
      Tool(
        name="generate_resume_review",
        func=_generate_resume_review,
        description=(
          "Analyze a candidate resume against a target role and optional job description, "
          "returning a structured JSON report optimized for ATS-style screening and "
          "human-readable feedback. "
          "Args: resume_text (str, required), job_description (str, optional), "
          "target_role (str, optional), seniority (str: junior/mid/senior/lead, default='mid')."
        ),
      )
    )

  return tools
