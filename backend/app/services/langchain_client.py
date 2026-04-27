from typing import List, Any
import warnings
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import settings
from app.models.agent import Agent
from app.models.message import Message
from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS

# Suppress specific warnings from langchain/google libraries
warnings.filterwarnings('ignore', message='.*Unrecognized FinishReason enum value.*')
warnings.filterwarnings('ignore', message='.*Unrecognized role.*')
warnings.filterwarnings('ignore', message='.*Gemini produced an empty response.*')

MAX_HISTORY_MESSAGES = 8
MAX_MESSAGE_CHARS = 4000
MAX_INPUT_CHARS = 8000
logger = logging.getLogger("app.services.langchain_client")


class LangchainAgentService:
  """Simplified LangChain wrapper around Gemini - uses simple chain for all agents."""

  def __init__(self) -> None:
    if not settings.GEMINI_API_KEY:
      raise ValueError("GEMINI_API_KEY must be set in environment variables")
    self._api_key = settings.GEMINI_API_KEY

  def _build_llm(self, agent: Agent) -> ChatGoogleGenerativeAI:
    """Build the ChatGoogleGenerativeAI LLM instance."""
    max_tokens = settings.LLM_MAX_OUTPUT_TOKENS
    if getattr(agent, "category", None) in {"education", "career"}:
      max_tokens = settings.LLM_MAX_OUTPUT_TOKENS_LONGFORM

    return ChatGoogleGenerativeAI(
      model=agent.model,
      temperature=agent.temperature,
      google_api_key=self._api_key,
      max_output_tokens=max_tokens,
      max_retries=1,
      timeout=45,
    )

  def _build_chain(self, agent: Agent) -> Any:
    """Build a simple chain for all agents."""
    llm = self._build_llm(agent)
    # Gemini chat history does not support system-role messages. Always use
    # user/assistant history and inject system instructions into the input.
    prompt = ChatPromptTemplate.from_messages(
      [
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
      ]
    )
    
    chain = prompt | llm
    return chain

  def _history_to_messages(self, history: List[Message], latest_input: str = None) -> List[Any]:
    """Convert database Message objects to LangChain message objects.
    
    Merges consecutive messages from the same role (Gemini requirement).
    If latest_input is provided, it's merged with the last user message if present.
    Filters out invalid messages (empty content or invalid roles).
    """
    # Limit history size and content to control latency and memory usage.
    recent_history = history[-MAX_HISTORY_MESSAGES:] if len(history) > MAX_HISTORY_MESSAGES else history
    
    messages: List[Any] = []
    
    # Process history messages - filter out invalid ones
    for m in recent_history:
      # Skip messages with empty or invalid content
      if not m.content or not m.content.strip():
        continue
      content = m.content.strip()[:MAX_MESSAGE_CHARS]
      
      # Validate role
      try:
        current_role = m.role.value if hasattr(m.role, 'value') else str(m.role)
        if not current_role or current_role not in ['user', 'assistant', 'system']:
          continue
      except (AttributeError, ValueError):
        # Skip messages with invalid roles
        continue
      
      # Skip system messages (they're handled separately)
      if current_role == "system":
        continue
      
      # Add new message or merge with last if same role
      if messages and messages[-1].__class__.__name__ == ("HumanMessage" if current_role == "user" else "AIMessage"):
        # Merge with last message of same type
        messages[-1].content += f"\n\n{content}"
      else:
        # Add new message
        if current_role == "user":
          messages.append(HumanMessage(content=content))
        elif current_role == "assistant":
          messages.append(AIMessage(content=content))
    
    # If latest_input is provided, merge with last user message or add as new
    if latest_input and latest_input.strip():
      truncated_input = latest_input.strip()[:MAX_INPUT_CHARS]
      if messages and isinstance(messages[-1], HumanMessage):
        # Merge with last user message
        messages[-1].content += f"\n\n{truncated_input}"
      else:
        # Add as new user message
        messages.append(HumanMessage(content=truncated_input))
    
    return messages

  def generate_response(
    self,
    agent: Agent,
    history: List[Message],
    latest_input: str,
  ) -> str:
    """
    Simplified LangChain agent - uses simple chain for all agents.
    Merges history properly to avoid consecutive same-role messages.
    
    For quiz/exam requests, intercepts and generates directly in a single call.
    """
    # Check if this is a quiz/exam request - intercept and generate directly
    latest_lower = latest_input.lower() if latest_input else ""
    agent_slug = agent.slug if agent.is_prebuilt else None

    is_exam_agent = agent_slug == PREBUILT_AGENT_SLUGS["exam_prep_agent"]
    is_micro_agent = agent_slug == PREBUILT_AGENT_SLUGS["micro_learning_agent"]
    is_quiz_agent = agent_slug in {
      PREBUILT_AGENT_SLUGS["personal_tutor"],
      PREBUILT_AGENT_SLUGS["course_creation_agent"],
      PREBUILT_AGENT_SLUGS["language_practice_agent"],
    }

    is_quiz_request = is_quiz_agent and (
      "quiz" in latest_lower or
      ("generate" in latest_lower and ("question" in latest_lower or "mcq" in latest_lower)) or
      "multiple choice" in latest_lower
    )

    is_exam_request = is_exam_agent and (
      "practice exam" in latest_lower or
      "create_practice_exam" in latest_lower or
      ("generate" in latest_lower and "exam" in latest_lower and "practice" in latest_lower)
    )
    
    # If it's an exam request for exam prep agent, generate directly
    if is_exam_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import _create_practice_exam
      if is_exam_agent:
        # Extract exam parameters from the request - handle multiple formats
        import re
        
        # Try to extract from structured format first (exam_type: "value")
        exam_type_match = re.search(r'exam_type[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        if not exam_type_match:
          # Try to extract from natural language (e.g., "for SAT exam", "for GRE")
          exam_type_match = re.search(r'(?:for|in)\s+([A-Z][A-Z\s]+?)(?:\s+exam|\s+in|$)', latest_input, re.IGNORECASE)
        exam_type = exam_type_match.group(1).strip().strip('"') if exam_type_match else "General Exam"
        
        # Try to extract subject
        subject_match = re.search(r'subject[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        if not subject_match:
          # Try to extract from natural language (e.g., "in Mathematics", "in Math")
          subject_match = re.search(r'(?:in|for)\s+([A-Z][a-z\s]+?)(?:\s+on|\s+with|\s+exam|$)', latest_input, re.IGNORECASE)
        subject = subject_match.group(1).strip().strip('"') if subject_match else "General Knowledge"
        
        # Extract num_questions
        num_questions_match = re.search(r'num_questions[:\s]+(\d+)', latest_input, re.IGNORECASE)
        if not num_questions_match:
          num_questions_match = re.search(r'(\d+)\s*(?:questions?|questions)', latest_input, re.IGNORECASE)
        num_questions = int(num_questions_match.group(1)) if num_questions_match else 20
        
        # Extract time_limit
        time_limit_match = re.search(r'time_limit[:\s]+(\d+)', latest_input, re.IGNORECASE)
        if not time_limit_match:
          time_limit_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', latest_input, re.IGNORECASE)
        time_limit = int(time_limit_match.group(1)) if time_limit_match else 60
        
        # Extract difficulty
        difficulty_match = re.search(r'difficulty[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        if not difficulty_match:
          difficulty_match = re.search(r'(easy|medium|hard|beginner|intermediate|advanced)', latest_input, re.IGNORECASE)
        difficulty = difficulty_match.group(1).strip().lower().strip('"') if difficulty_match else "medium"
        if difficulty in ["beginner"]:
          difficulty = "easy"
        elif difficulty in ["intermediate"]:
          difficulty = "medium"
        elif difficulty in ["advanced"]:
          difficulty = "hard"
        
        # Generate exam directly using the tool (single API call)
        try:
          logger.debug(
            "Intercepting exam request exam_type=%s subject=%s num_questions=%s difficulty=%s",
            exam_type, subject, num_questions, difficulty
          )
          exam_output = _create_practice_exam(
            exam_type=exam_type,
            subject=subject,
            num_questions=num_questions,
            time_limit=time_limit,
            difficulty=difficulty
          )
          logger.debug("Exam generated successfully length=%s", len(exam_output))
          return exam_output
        except Exception as e:
          import traceback
          logger.exception("Exam generation tool failed")
          # Fallback to normal generation if tool fails
          logger.warning("Exam tool failed; falling back to normal generation: %s", str(e))
    
    # Check for schedule, weak areas, and topic review requests - intercept and generate directly
    is_schedule_request = is_exam_agent and (
      "create_study_schedule" in latest_lower or
      ("study" in latest_lower and "schedule" in latest_lower)
    )
    
    is_weak_areas_request = is_exam_agent and (
      "identify_weak_areas" in latest_lower or
      ("weak" in latest_lower and "area" in latest_lower and "analysis" in latest_lower)
    )
    
    is_topic_review_request = is_exam_agent and (
      "generate_topic_review" in latest_lower or
      ("topic" in latest_lower and "review" in latest_lower)
    )

    is_micro_lesson_request = is_micro_agent and (
      "generate_micro_lesson" in latest_lower or
      ("micro-lesson" in latest_lower or "micro lesson" in latest_lower) and "lesson" in latest_lower
    )
    
    # If it's a schedule request for exam prep agent, generate directly
    if is_schedule_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import _create_study_schedule
      if is_exam_agent:
        import re
        # Extract parameters
        exam_date_match = re.search(r'exam_date[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        exam_date = exam_date_match.group(1).strip().strip('"') if exam_date_match else None
        
        subjects_match = re.search(r'subjects[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        subjects = subjects_match.group(1).strip().strip('"') if subjects_match else "General"
        
        hours_match = re.search(r'hours_per_day[:\s]+(\d+)', latest_input, re.IGNORECASE)
        hours_per_day = int(hours_match.group(1)) if hours_match else 2
        
        level_match = re.search(r'current_level[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        current_level = level_match.group(1).strip().strip('"') if level_match else "intermediate"
        
        if exam_date:
          try:
            logger.debug(
              "Intercepting schedule request exam_date=%s subjects=%s hours_per_day=%s current_level=%s",
              exam_date, subjects, hours_per_day, current_level
            )
            schedule_output = _create_study_schedule(
              exam_date=exam_date,
              subjects=subjects,
              hours_per_day=hours_per_day,
              current_level=current_level
            )
            logger.debug("Schedule generated successfully length=%s", len(schedule_output))
            return schedule_output
          except Exception as e:
            import traceback
            logger.exception("Schedule generation tool failed")
    
    # If it's a weak areas request for exam prep agent, generate directly
    if is_weak_areas_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import _identify_weak_areas
      if is_exam_agent:
        import re
        # Extract parameters
        subject_match = re.search(r'subject[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        subject = subject_match.group(1).strip().strip('"') if subject_match else "General"
        
        # Extract practice_results - handle multi-line content
        practice_results_match = re.search(r'practice_results[:\s]+"([^"]+)"', latest_input, re.IGNORECASE | re.DOTALL)
        if not practice_results_match:
          # Try without quotes - capture until next parameter or end
          practice_results_match = re.search(r'practice_results[:\s]+(.+?)(?=\n- [a-z_]+:|$)', latest_input, re.IGNORECASE | re.DOTALL)
        if not practice_results_match:
          # Try to find any practice results text in the message
          practice_results_match = re.search(r'practice_results[:\s]+(.+)', latest_input, re.IGNORECASE | re.DOTALL)
        practice_results = practice_results_match.group(1).strip().strip('"') if practice_results_match else "No results provided"
        
        exam_type_match = re.search(r'exam_type[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        exam_type = exam_type_match.group(1).strip().strip('"') if exam_type_match else "general"
        
        try:
          logger.debug("Intercepting weak areas request subject=%s exam_type=%s", subject, exam_type)
          weak_areas_output = _identify_weak_areas(
            subject=subject,
            practice_results=practice_results,
            exam_type=exam_type
          )
          logger.debug("Weak areas analysis generated successfully length=%s", len(weak_areas_output))
          return weak_areas_output
        except Exception as e:
          import traceback
          logger.exception("Weak areas analysis tool failed")
    
    # If it's a topic review request for exam prep agent, generate directly
    if is_topic_review_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import _generate_topic_review
      if is_exam_agent:
        import re
        # Extract parameters
        topic_match = re.search(r'topic[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        topic = topic_match.group(1).strip().strip('"') if topic_match else "General Topic"
        
        difficulty_match = re.search(r'difficulty[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        difficulty = difficulty_match.group(1).strip().strip('"') if difficulty_match else "medium"
        
        review_type_match = re.search(r'review_type[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        review_type = review_type_match.group(1).strip().strip('"') if review_type_match else "comprehensive"
        
        try:
          logger.debug(
            "Intercepting topic review request topic=%s difficulty=%s review_type=%s",
            topic, difficulty, review_type
          )
          topic_review_output = _generate_topic_review(
            topic=topic,
            difficulty=difficulty,
            review_type=review_type
          )
          logger.debug("Topic review generated successfully length=%s", len(topic_review_output))
          return topic_review_output
        except Exception as e:
          import traceback
          logger.exception("Topic review tool failed")

    # If it's a micro-lesson request for micro learning agent, generate directly
    if is_micro_lesson_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import _generate_micro_lesson
      if is_micro_agent:
        import re
        # Extract parameters
        topic_match = re.search(r'topic[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        if not topic_match:
          topic_match = re.search(r'(?:about|on|for)\s+([^,\.\n]+)', latest_input, re.IGNORECASE)
        topic = topic_match.group(1).strip().strip('"') if topic_match else "General Topic"

        minutes_match = re.search(r'time_minutes[:\s]+(\d+)', latest_input, re.IGNORECASE)
        if not minutes_match:
          minutes_match = re.search(r'(\d+)\s*(?:minutes?|mins?)', latest_input, re.IGNORECASE)
        time_minutes = int(minutes_match.group(1)) if minutes_match else 10

        difficulty_match = re.search(r'difficulty[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        if not difficulty_match:
          difficulty_match = re.search(r'(easy|medium|hard|beginner|intermediate|advanced)', latest_input, re.IGNORECASE)
        difficulty = difficulty_match.group(1).strip().lower().strip('"') if difficulty_match else "medium"
        if difficulty in ["beginner"]:
          difficulty = "easy"
        elif difficulty in ["intermediate"]:
          difficulty = "medium"
        elif difficulty in ["advanced"]:
          difficulty = "hard"

        try:
          logger.debug(
            "Intercepting micro-lesson request topic=%s time_minutes=%s difficulty=%s",
            topic, time_minutes, difficulty
          )
          lesson_output = _generate_micro_lesson(
            topic=topic,
            time_minutes=time_minutes,
            difficulty=difficulty
          )
          logger.debug("Micro-lesson generated successfully length=%s", len(lesson_output))
          return lesson_output
        except Exception as e:
          import traceback
          logger.exception("Micro-lesson tool failed")
    
    # If it's a quiz request for prebuilt agents, generate directly
    if is_quiz_request and agent.is_prebuilt:
      if is_quiz_agent:
        # Extract quiz parameters from the request
        import re
        topic_match = re.search(r'(?:about|on|for)\s+([^,\.\?]+?)(?:\s+with|\s+at|\s+of|$)', latest_input, re.IGNORECASE)
        topic = topic_match.group(1).strip() if topic_match else "general knowledge"
        
        difficulty_match = re.search(r'(easy|medium|hard|beginner|intermediate|advanced)', latest_input, re.IGNORECASE)
        difficulty = difficulty_match.group(1).lower() if difficulty_match else "medium"
        if difficulty in ["beginner"]:
          difficulty = "easy"
        elif difficulty in ["intermediate"]:
          difficulty = "medium"
        elif difficulty in ["advanced"]:
          difficulty = "hard"
        
        num_match = re.search(r'(\d+)\s*(?:questions?|mcqs?)', latest_input, re.IGNORECASE)
        num_questions = int(num_match.group(1)) if num_match else 5
        
        # Generate quiz directly using the tool (single API call)
        from app.tools.prebuilt_agents import _generate_quiz
        try:
          quiz_output = _generate_quiz(topic=topic, difficulty=difficulty, num_questions=num_questions)
          # Keep answers in the response - they're needed for validation
          # Answers will be hidden in the UI but available for validation
          return quiz_output
        except Exception as e:
          # Fallback to normal generation if tool fails
          logger.warning("Quiz generation tool failed; falling back to normal generation: %s", str(e))
    
    # Tool-wired flow for Course Creation Agent: intercept common intents and delegate
    # directly to the prebuilt tools for fast, deterministic behavior.
    if agent.is_prebuilt and agent.slug == PREBUILT_AGENT_SLUGS["course_creation_agent"]:
      import re
      from app.tools.prebuilt_agents import (
        _create_course_structure,
        _create_learning_assessment,
        _create_concept_map,
        _create_workflow_automation,
        _create_meeting_notes_template,
        _validate_course_content,
      )

      text = latest_lower

      # 1) Course structure / outline
      if ("course structure" in text or "course outline" in text or "create_course_structure" in text):
        # Try to extract course title, objectives, and duration
        title_match = re.search(r'(?:course\s+title|for\s+course|about)\s*[:\-"]?\s*([^"\n,]+)', latest_input, re.IGNORECASE)
        course_title = title_match.group(1).strip() if title_match else latest_input[:80]

        objectives_match = re.search(r'(?:learning objectives?|objectives?)\s*[:\-]\s*(.+)', latest_input, re.IGNORECASE)
        if objectives_match:
          learning_objectives = objectives_match.group(1).strip()
        else:
          learning_objectives = course_title

        weeks_match = re.search(r'(?:duration|weeks?)\s*[:\-]?\s*(\d+)', latest_input, re.IGNORECASE)
        duration_weeks = int(weeks_match.group(1)) if weeks_match else 8

        return _create_course_structure(
          course_title=course_title,
          learning_objectives=learning_objectives,
          duration_weeks=duration_weeks,
        )

      # 2) Learning assessment
      if ("learning assessment" in text or "assessment" in text or "create_learning_assessment" in text):
        topic_match = re.search(r'(?:topic|for)\s*[:\-"]?\s*([^"\n,]+)', latest_input, re.IGNORECASE)
        topic = topic_match.group(1).strip() if topic_match else "General Topic"

        assessment_type_match = re.search(r'(diagnostic|formative|summative|comprehensive)', latest_input, re.IGNORECASE)
        assessment_type = assessment_type_match.group(1).lower() if assessment_type_match else "comprehensive"

        num_q_match = re.search(r'(\d+)\s*(?:questions?|items?)', latest_input, re.IGNORECASE)
        num_questions = int(num_q_match.group(1)) if num_q_match else 10

        return _create_learning_assessment(
          topic=topic,
          assessment_type=assessment_type,
          num_questions=num_questions,
        )

      # 3) Concept map
      if ("concept map" in text or "concept mapping" in text or "create_concept_map" in text):
        main_match = re.search(r'(?:main concept|for)\s*[:\-"]?\s*([^"\n,]+)', latest_input, re.IGNORECASE)
        main_concept = main_match.group(1).strip() if main_match else "Main Concept"

        related_match = re.search(r'(?:related concepts?|subtopics?)\s*[:\-]\s*(.+)', latest_input, re.IGNORECASE)
        related_concepts = related_match.group(1).strip() if related_match else ""

        return _create_concept_map(
          main_concept=main_concept,
          related_concepts=related_concepts,
        )

      # 4) Workflow automation
      if ("workflow" in text or "automation" in text or "create_workflow_automation" in text):
        wf_name_match = re.search(r'(?:workflow name|for workflow|workflow)\s*[:\-"]?\s*([^"\n,]+)', latest_input, re.IGNORECASE)
        workflow_name = wf_name_match.group(1).strip() if wf_name_match else "Course Creation Workflow"

        steps_match = re.search(r'(?:steps?)\s*[:\-]\s*(.+)', latest_input, re.IGNORECASE)
        steps = steps_match.group(1).strip() if steps_match else "Plan course,Design modules,Create lessons,Publish course"

        wf_type_match = re.search(r'(learning|assessment|content_creation|course_delivery)', latest_input, re.IGNORECASE)
        automation_type = wf_type_match.group(1).lower() if wf_type_match else "learning"

        return _create_workflow_automation(
          workflow_name=workflow_name,
          steps=steps,
          automation_type=automation_type,
        )

      # 5) Meeting notes templates
      if ("meeting notes" in text or "notes template" in text or "create_meeting_notes_template" in text):
        mt_type_match = re.search(r'(course_planning|review|assessment_design)', latest_input, re.IGNORECASE)
        meeting_type = mt_type_match.group(1).lower() if mt_type_match else "course_planning"

        participants_match = re.search(r'(?:participants?)\s*[:\-]\s*(.+)', latest_input, re.IGNORECASE)
        participants = participants_match.group(1).strip() if participants_match else ""

        return _create_meeting_notes_template(
          meeting_type=meeting_type,
          participants=participants,
        )

      # 6) Course validation
      if ("validate course" in text or "course validation" in text or "validate_course_content" in text):
        structure_match = re.search(r'(?:course structure|outline|description)\s*[:\-]\s*(.+)', latest_input, re.IGNORECASE | re.DOTALL)
        course_structure = structure_match.group(1).strip() if structure_match else latest_input

        criteria_match = re.search(r'(comprehensive|accessibility|learning_objectives|assessment_alignment)', latest_input, re.IGNORECASE)
        validation_criteria = criteria_match.group(1).lower() if criteria_match else "comprehensive"

        return _validate_course_content(
          course_structure=course_structure,
          validation_criteria=validation_criteria,
        )

    # Structured, tool-driven flow for Skill Gap Agent.
    # The frontend sends workflow actions in JSON payloads using:
    #   SKILL_GAP_REQUEST
    #   { "action": "...", "payload": { ... } }
    if agent.is_prebuilt and agent.slug == PREBUILT_AGENT_SLUGS.get("skill_gap_agent"):
      import json
      from app.tools.prebuilt_agents import _generate_skill_gap_agent_response

      text = latest_input or ""
      marker = "SKILL_GAP_REQUEST"
      marker_used = marker in text

      if marker_used:
        json_start = text.find("{", text.find(marker))
        if json_start != -1:
          payload_str = text[json_start:].strip()
          try:
            payload = json.loads(payload_str)
          except Exception:
            payload = {}
        else:
          payload = {}
      else:
        try:
          payload = json.loads(text)
        except Exception:
          payload = {}

      action = ""
      action_payload = {}
      if isinstance(payload, dict):
        action = str(payload.get("action") or "").strip().lower()
        if isinstance(payload.get("payload"), dict):
          action_payload = dict(payload.get("payload") or {})
        else:
          action_payload = dict(payload)
          action_payload.pop("action", None)

      if action in {
        "profile_baseline",
        "identify_skill_gaps",
        "build_development_plan",
        "weekly_progress_checkin",
        "readiness_assessment",
      }:
        try:
          return _generate_skill_gap_agent_response(action=action, payload=action_payload)
        except Exception as e:
          import traceback
          logger.exception("Skill gap tool failed")
          return (
            '{"action":"'
            + action
            + '","status":"error","error":"internal_error","message":"'
            + str(e).replace('"', '\\"')
            + '"}'
          )

      if marker_used:
        return (
          '{"action":"unknown","status":"error","error":"invalid_payload",'
          '"message":"SKILL_GAP_REQUEST must include a valid action."}'
        )

    # Structured, tool-driven flow for Fitness Coach Agent.
    # The frontend sends workflow actions in JSON payloads using:
    #   FITNESS_COACH_REQUEST
    #   { "action": "...", "payload": { ... } }
    if agent.is_prebuilt and agent.slug == PREBUILT_AGENT_SLUGS.get("fitness_coach_agent"):
      import json
      from app.tools.prebuilt_agents import _generate_fitness_coach_response

      text = latest_input or ""
      marker = "FITNESS_COACH_REQUEST"
      marker_used = marker in text

      if marker_used:
        json_start = text.find("{", text.find(marker))
        if json_start != -1:
          payload_str = text[json_start:].strip()
          try:
            payload = json.loads(payload_str)
          except Exception:
            payload = {}
        else:
          payload = {}
      else:
        try:
          payload = json.loads(text)
        except Exception:
          payload = {}

      action = ""
      action_payload = {}
      if isinstance(payload, dict):
        action = str(payload.get("action") or "").strip().lower()
        if isinstance(payload.get("payload"), dict):
          action_payload = dict(payload.get("payload") or {})
          for key, value in payload.items():
            if key in {"action", "payload"}:
              continue
            action_payload.setdefault(key, value)
        else:
          action_payload = dict(payload)
          action_payload.pop("action", None)

      if action in {
        "profile_baseline",
        "generate_adaptive_plan",
        "quick_workout_burst",
        "log_workout_feedback",
        "challenge_mode",
        "progress_reassessment",
      }:
        try:
          return _generate_fitness_coach_response(action=action, payload=action_payload)
        except Exception as e:
          import traceback
          logger.exception("Fitness coach tool failed")
          return (
            '{"action":"'
            + action
            + '","status":"error","error":"internal_error","message":"'
            + str(e).replace('"', '\\"')
            + '"}'
          )

      if marker_used:
        return (
          '{"action":"unknown","status":"error","error":"invalid_payload",'
          '"message":"FITNESS_COACH_REQUEST must include a valid action."}'
        )

    # Structured, tool-driven flow for Career Coach Agent.
    # The frontend sends workflow actions in JSON payloads using:
    #   CAREER_COACH_REQUEST
    #   { "action": "...", "payload": { ... } }
    # Backward-compatible flat payloads are also accepted.
    if agent.is_prebuilt and agent.slug == PREBUILT_AGENT_SLUGS.get("career_coach_agent"):
      import json
      from app.tools.prebuilt_agents import _generate_career_coach_response

      text = latest_input or ""
      marker = "CAREER_COACH_REQUEST"
      marker_used = marker in text

      if marker_used:
        json_start = text.find("{", text.find(marker))
        if json_start != -1:
          payload_str = text[json_start:].strip()
          try:
            payload = json.loads(payload_str)
          except Exception:
            payload = {}
        else:
          payload = {}
      else:
        # Fallback for direct JSON requests.
        try:
          payload = json.loads(text)
        except Exception:
          payload = {}

      action = ""
      action_payload = {}
      if isinstance(payload, dict):
        action = str(payload.get("action") or "").strip().lower()
        if isinstance(payload.get("payload"), dict):
          action_payload = dict(payload.get("payload") or {})
          # Allow mixed payloads where some fields are still top-level.
          for key, value in payload.items():
            if key in {"action", "payload"}:
              continue
            action_payload.setdefault(key, value)
        else:
          action_payload = dict(payload)
          action_payload.pop("action", None)

      if action in {
        "intake_assessment",
        "opportunity_strategy",
        "skill_gap_analysis",
        "build_roadmap",
        "weekly_checkin",
        "interview_readiness",
      }:
        try:
          return _generate_career_coach_response(action=action, payload=action_payload)
        except Exception as e:
          import traceback
          logger.exception("Career coach tool failed")
          return (
            '{"action":"'
            + action
            + '","status":"error","error":"internal_error","message":"'
            + str(e).replace('"', '\\"')
            + '"}'
          )

      # If user sent the structured marker but payload/action is invalid, fail fast.
      if marker_used:
        return (
          '{"action":"unknown","status":"error","error":"invalid_payload",'
          '"message":"CAREER_COACH_REQUEST must include a valid action."}'
        )

    # Structured, tool-driven flow for Resume Review Agent.
    # This agent is NOT a free-form chatbot: the frontend sends structured payloads
    # (JSON) and we delegate directly to the resume review tool for deterministic output.
    if agent.is_prebuilt and agent.slug == PREBUILT_AGENT_SLUGS.get("resume_review_agent"):
      import json
      from app.tools.prebuilt_agents import _generate_resume_review

      text = latest_input or ""

      # Primary contract: a marker followed by a JSON payload.
      # Example:
      #   RESUME_REVIEW_REQUEST
      #   { "action": "review_resume", "resume_text": "...", ... }
      marker = "RESUME_REVIEW_REQUEST"
      if marker in text:
        json_start = text.find("{", text.find(marker))
        if json_start != -1:
          payload_str = text[json_start:].strip()
          try:
            payload = json.loads(payload_str)
          except Exception:
            payload = {}
        else:
          payload = {}
      else:
        # Fallback: try to interpret the whole text as JSON if possible.
        try:
          payload = json.loads(text)
        except Exception:
          payload = {}

      action = ""
      if isinstance(payload, dict):
        action = str(payload.get("action") or "").lower()

      if action == "review_resume":
        resume_text = str(payload.get("resume_text") or "").strip()
        job_description = str(payload.get("job_description") or "").strip()
        target_role = str(payload.get("target_role") or "").strip()
        seniority = str(payload.get("seniority") or "mid").strip().lower()

        try:
          return _generate_resume_review(
            resume_text=resume_text,
            job_description=job_description,
            target_role=target_role,
            seniority=seniority,
          )
        except Exception as e:
          import traceback
          logger.exception("Resume review tool failed")
          return (
            '{"error":"internal_error",'
            f'"message":"Unexpected error while generating resume review: {str(e)}","overall_score":0,"ats_score":0}}'
          )
    # Build messages with latest_input merged properly
    chat_history = self._history_to_messages(history, latest_input)
    
    # Use simple chain for all agents
    chain = self._build_chain(agent)
    
    try:
      # Extract the latest input from merged messages
      if chat_history and isinstance(chat_history[-1], HumanMessage):
        current_input = chat_history[-1].content
        # Remove it from history for the chain
        history_for_chain = chat_history[:-1]
      else:
        current_input = latest_input
        history_for_chain = chat_history

      # Defensive: ensure only Human/AI messages are passed to Gemini.
      history_for_chain = [
        msg for msg in history_for_chain
        if isinstance(msg, (HumanMessage, AIMessage))
      ]

      # Inject system instructions into the current input to avoid system-role messages.
      if settings.SYSTEM_PROMPT_MAX_CHARS > 0:
        system_prompt = (agent.system_prompt or "")[:settings.SYSTEM_PROMPT_MAX_CHARS]
      else:
        system_prompt = agent.system_prompt or ""
      if system_prompt:
        current_input = f"{system_prompt}\n\n{current_input}" if current_input else system_prompt
      current_input = (current_input or "")[:MAX_INPUT_CHARS]
      
      result = chain.invoke(
        {
          "input": current_input,
          "chat_history": history_for_chain,
        }
      )
      output = result.content if hasattr(result, 'content') else str(result)
      
      # Clean quiz output if present - only remove preamble, keep answers for validation
      if "**Question 1:**" in output or "Question 1:" in output:
        quiz_start = output.find("**Question 1:**")
        if quiz_start == -1:
          quiz_start = output.find("Question 1:")
        if quiz_start > 0:
          output = output[quiz_start:].strip()
      
      return output
      
    except Exception as e:
      error_str = str(e).lower()
      if "'int' object has no attribute 'name'" in error_str or "finish_reason" in error_str:
        logger.warning("Gemini finish_reason parsing failed in LangChain; using SDK fallback")
        try:
          from app.services.gemini import GeminiClient
          gemini_client = GeminiClient()
          message_payload = []
          for msg in history_for_chain:
            if isinstance(msg, HumanMessage):
              message_payload.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
              message_payload.append({"role": "assistant", "content": msg.content})
          message_payload.append({"role": "user", "content": current_input})
          output = gemini_client.generate_response(
            system_prompt=agent.system_prompt or "",
            messages=message_payload,
            model=agent.model,
            temperature=agent.temperature,
            max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS_LONGFORM if getattr(agent, "category", None) in {"education", "career"} else settings.LLM_MAX_OUTPUT_TOKENS,
          )
          return output
        except Exception as fallback_error:
          raise Exception(
            f"Error generating response (finish_reason parsing issue): {str(fallback_error)}"
          ) from e
      
      raise Exception(f"Error generating response: {str(e)}") from e

  async def stream_response(
    self,
    agent: Agent,
    history: List[Message],
    latest_input: str,
  ):
    """Generate streaming response - optimized to avoid extra chain overhead."""
    chat_history = self._history_to_messages(history, latest_input)

    # Build simple text prompt from history and latest input, similar to the
    # non-streaming fallback path, to minimize LangChain pipeline overhead.
    try:
      if chat_history and isinstance(chat_history[-1], HumanMessage):
        current_input = chat_history[-1].content
        history_for_prompt = chat_history[:-1]
      else:
        current_input = latest_input
        history_for_prompt = chat_history

      llm = self._build_llm(agent)

      prompt_parts = []
      for msg in history_for_prompt:
        if isinstance(msg, HumanMessage):
          prompt_parts.append(f"User: {msg.content}")
        elif isinstance(msg, AIMessage):
          prompt_parts.append(f"Assistant: {msg.content}")

      prompt_parts.append(f"User: {current_input}")
      prompt_parts.append("Assistant:")

      full_prompt = "\n".join(prompt_parts)
      if settings.SYSTEM_PROMPT_MAX_CHARS > 0:
        system_prompt = (agent.system_prompt or "")[:settings.SYSTEM_PROMPT_MAX_CHARS]
      else:
        system_prompt = agent.system_prompt or ""
      if system_prompt:
        full_prompt = f"{system_prompt}\n\n{full_prompt}"

      async for chunk in llm.astream(full_prompt):
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        if content:
          yield content
    except Exception as e:
      # Surface a concise error message to the streaming client.
      yield f"Error: {str(e)}"
