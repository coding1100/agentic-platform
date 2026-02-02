from typing import List, Any
import warnings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import settings
from app.models.agent import Agent
from app.models.message import Message

# Suppress specific warnings from langchain/google libraries
warnings.filterwarnings('ignore', message='.*Unrecognized FinishReason enum value.*')
warnings.filterwarnings('ignore', message='.*Unrecognized role.*')
warnings.filterwarnings('ignore', message='.*Gemini produced an empty response.*')


class LangchainAgentService:
  """Simplified LangChain wrapper around Gemini - uses simple chain for all agents."""

  def __init__(self) -> None:
    if not settings.GEMINI_API_KEY:
      raise ValueError("GEMINI_API_KEY must be set in environment variables")
    self._api_key = settings.GEMINI_API_KEY

  def _build_llm(self, agent: Agent) -> ChatGoogleGenerativeAI:
    """Build the ChatGoogleGenerativeAI LLM instance."""
    return ChatGoogleGenerativeAI(
      model=agent.model,
      temperature=agent.temperature,
      google_api_key=self._api_key,
    )

  def _build_chain(self, agent: Agent) -> Any:
    """Build a simple chain for all agents."""
    llm = self._build_llm(agent)
    system_instructions = agent.system_prompt or ""

    # Simple prompt with chat history support.
    # Always include system instructions to keep agent behavior consistent.
    if system_instructions:
      prompt = ChatPromptTemplate.from_messages(
        [
          ("system", system_instructions),
          MessagesPlaceholder(variable_name="chat_history"),
          ("human", "{input}"),
        ]
      )
    else:
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
    # Limit history to last 8 messages for performance
    recent_history = history[-8:] if len(history) > 8 else history
    
    messages: List[Any] = []
    
    # Process history messages - filter out invalid ones
    for m in recent_history:
      # Skip messages with empty or invalid content
      if not m.content or not m.content.strip():
        continue
      
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
        messages[-1].content += f"\n\n{m.content}"
      else:
        # Add new message
        if current_role == "user":
          messages.append(HumanMessage(content=m.content.strip()))
        elif current_role == "assistant":
          messages.append(AIMessage(content=m.content.strip()))
    
    # If latest_input is provided, merge with last user message or add as new
    if latest_input and latest_input.strip():
      if messages and isinstance(messages[-1], HumanMessage):
        # Merge with last user message
        messages[-1].content += f"\n\n{latest_input.strip()}"
      else:
        # Add as new user message
        messages.append(HumanMessage(content=latest_input.strip()))
    
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
    is_quiz_request = (
      "quiz" in latest_lower or 
      "generate" in latest_lower and ("question" in latest_lower or "mcq" in latest_lower) or
      "multiple choice" in latest_lower
    )
    
    is_exam_request = (
      "practice exam" in latest_lower or
      "create_practice_exam" in latest_lower or
      ("generate" in latest_lower and "exam" in latest_lower and "practice" in latest_lower)
    )
    
    # If it's an exam request for exam prep agent, generate directly
    if is_exam_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS, _create_practice_exam
      if agent.slug == PREBUILT_AGENT_SLUGS["exam_prep_agent"]:
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
          print(f"🎯 Intercepting exam request: exam_type={exam_type}, subject={subject}, num_questions={num_questions}, difficulty={difficulty}")
          exam_output = _create_practice_exam(
            exam_type=exam_type,
            subject=subject,
            num_questions=num_questions,
            time_limit=time_limit,
            difficulty=difficulty
          )
          print(f"✅ Exam generated successfully, length: {len(exam_output)} chars")
          print(f"📝 Exam preview: {exam_output[:300]}...")
          return exam_output
        except Exception as e:
          import traceback
          print(f"❌ Exam generation tool failed: {traceback.format_exc()}")
          # Fallback to normal generation if tool fails
          print(f"Exam generation tool failed, falling back to normal generation: {str(e)}")
    
    # Check for schedule, weak areas, and topic review requests - intercept and generate directly
    is_schedule_request = (
      "create_study_schedule" in latest_lower or
      ("study" in latest_lower and "schedule" in latest_lower)
    )
    
    is_weak_areas_request = (
      "identify_weak_areas" in latest_lower or
      ("weak" in latest_lower and "area" in latest_lower and "analysis" in latest_lower)
    )
    
    is_topic_review_request = (
      "generate_topic_review" in latest_lower or
      ("topic" in latest_lower and "review" in latest_lower)
    )

    is_micro_lesson_request = (
      "generate_micro_lesson" in latest_lower or
      ("micro-lesson" in latest_lower or "micro lesson" in latest_lower) and "lesson" in latest_lower
    )
    
    # If it's a schedule request for exam prep agent, generate directly
    if is_schedule_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS, _create_study_schedule
      if agent.slug == PREBUILT_AGENT_SLUGS["exam_prep_agent"]:
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
            print(f"🎯 Intercepting schedule request: exam_date={exam_date}, subjects={subjects}, hours_per_day={hours_per_day}, current_level={current_level}")
            schedule_output = _create_study_schedule(
              exam_date=exam_date,
              subjects=subjects,
              hours_per_day=hours_per_day,
              current_level=current_level
            )
            print(f"✅ Schedule generated successfully, length: {len(schedule_output)} chars")
            return schedule_output
          except Exception as e:
            import traceback
            print(f"❌ Schedule generation tool failed: {traceback.format_exc()}")
    
    # If it's a weak areas request for exam prep agent, generate directly
    if is_weak_areas_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS, _identify_weak_areas
      if agent.slug == PREBUILT_AGENT_SLUGS["exam_prep_agent"]:
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
          print(f"🎯 Intercepting weak areas request: subject={subject}, exam_type={exam_type}")
          weak_areas_output = _identify_weak_areas(
            subject=subject,
            practice_results=practice_results,
            exam_type=exam_type
          )
          print(f"✅ Weak areas analysis generated successfully, length: {len(weak_areas_output)} chars")
          return weak_areas_output
        except Exception as e:
          import traceback
          print(f"❌ Weak areas analysis tool failed: {traceback.format_exc()}")
    
    # If it's a topic review request for exam prep agent, generate directly
    if is_topic_review_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS, _generate_topic_review
      if agent.slug == PREBUILT_AGENT_SLUGS["exam_prep_agent"]:
        import re
        # Extract parameters
        topic_match = re.search(r'topic[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        topic = topic_match.group(1).strip().strip('"') if topic_match else "General Topic"
        
        difficulty_match = re.search(r'difficulty[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        difficulty = difficulty_match.group(1).strip().strip('"') if difficulty_match else "medium"
        
        review_type_match = re.search(r'review_type[:\s]+"?([^",\n]+)"?', latest_input, re.IGNORECASE)
        review_type = review_type_match.group(1).strip().strip('"') if review_type_match else "comprehensive"
        
        try:
          print(f"🎯 Intercepting topic review request: topic={topic}, difficulty={difficulty}, review_type={review_type}")
          topic_review_output = _generate_topic_review(
            topic=topic,
            difficulty=difficulty,
            review_type=review_type
          )
          print(f"✅ Topic review generated successfully, length: {len(topic_review_output)} chars")
          return topic_review_output
        except Exception as e:
          import traceback
          print(f"❌ Topic review tool failed: {traceback.format_exc()}")

    # If it's a micro-lesson request for micro learning agent, generate directly
    if is_micro_lesson_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS, _generate_micro_lesson
      if agent.slug == PREBUILT_AGENT_SLUGS["micro_learning_agent"]:
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
          print(f"🎯 Intercepting micro-lesson request: topic={topic}, time_minutes={time_minutes}, difficulty={difficulty}")
          lesson_output = _generate_micro_lesson(
            topic=topic,
            time_minutes=time_minutes,
            difficulty=difficulty
          )
          print(f"✅ Micro-lesson generated successfully, length: {len(lesson_output)} chars")
          return lesson_output
        except Exception as e:
          import traceback
          print(f"❌ Micro-lesson tool failed: {traceback.format_exc()}")
    
    # If it's a quiz request for prebuilt agents, generate directly
    if is_quiz_request and agent.is_prebuilt:
      from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS
      if agent.slug in [PREBUILT_AGENT_SLUGS["personal_tutor"], 
                        PREBUILT_AGENT_SLUGS["course_creation_agent"],
                        PREBUILT_AGENT_SLUGS["language_practice_agent"]]:
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
          print(f"Quiz generation tool failed, falling back to normal generation: {str(e)}")
    
    # Tool-wired flow for Course Creation Agent: intercept common intents and delegate
    # directly to the prebuilt tools for fast, deterministic behavior.
    from app.tools.prebuilt_agents import PREBUILT_AGENT_SLUGS
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
      
    except AttributeError as e:
      # Handle finish_reason AttributeError (unrecognized enum value from Gemini)
      error_str = str(e).lower()
      if "'int' object has no attribute 'name'" in str(e) or "finish_reason" in error_str:
        print(f"Warning: Unrecognized finish_reason from Gemini, attempting fallback...")
        # Try using the LLM directly without the chain to bypass the finish_reason processing
        try:
          llm = self._build_llm(agent)
          # Build a simple prompt from history and current input
          prompt_parts = []
          for msg in history_for_chain:
            if isinstance(msg, HumanMessage):
              prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
              prompt_parts.append(f"Assistant: {msg.content}")
          
          prompt_parts.append(f"User: {current_input}")
          prompt_parts.append("Assistant:")
          
          full_prompt = "\n".join(prompt_parts)
          if agent.system_prompt:
            full_prompt = f"{agent.system_prompt}\n\n{full_prompt}"
          
          # Use invoke directly on LLM
          result = llm.invoke(full_prompt)
          output = result.content if hasattr(result, 'content') else str(result)
          
          # Clean quiz output if present
          if "**Question 1:**" in output or "Question 1:" in output:
            quiz_start = output.find("**Question 1:**")
            if quiz_start == -1:
              quiz_start = output.find("Question 1:")
            if quiz_start > 0:
              output = output[quiz_start:].strip()
          
          return output
        except Exception as fallback_error:
          print(f"Fallback also failed: {str(fallback_error)}")
          # Final fallback: Use raw Google Generative AI SDK to bypass LangChain entirely
          try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            
            # Build conversation history in Gemini format
            conversation_parts = []
            
            # Add system prompt to first message if available
            system_context = agent.system_prompt or ""
            
            # Convert history to Gemini format
            for msg in history_for_chain:
              if isinstance(msg, HumanMessage):
                conversation_parts.append({"role": "user", "parts": [msg.content]})
              elif isinstance(msg, AIMessage):
                conversation_parts.append({"role": "model", "parts": [msg.content]})
            
            # Add current input
            conversation_parts.append({"role": "user", "parts": [current_input]})
            
            # Initialize model
            model_instance = genai.GenerativeModel(
              model_name=agent.model,
              generation_config={
                "temperature": agent.temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
              }
            )
            
            # Prepend system context to first user message if exists
            if system_context.strip() and conversation_parts and conversation_parts[0]["role"] == "user":
              conversation_parts[0]["parts"][0] = f"{system_context.strip()}\n\n{conversation_parts[0]['parts'][0]}"
            
            # Start chat with history (all but last message)
            if len(conversation_parts) > 1:
              chat = model_instance.start_chat(history=conversation_parts[:-1])
              # Send the last message (current user message)
              response = chat.send_message(conversation_parts[-1]["parts"][0])
            else:
              # No history, just send the message
              prompt = system_context.strip() + "\n\n" + conversation_parts[0]["parts"][0] if system_context.strip() else conversation_parts[0]["parts"][0]
              response = model_instance.generate_content(prompt)
            
            output = response.text
            
            # Clean quiz output if present
            if "**Question 1:**" in output or "Question 1:" in output:
              quiz_start = output.find("**Question 1:**")
              if quiz_start == -1:
                quiz_start = output.find("Question 1:")
              if quiz_start > 0:
                output = output[quiz_start:].strip()
            
            return output
          except Exception as final_error:
            print(f"Final fallback also failed: {str(final_error)}")
            # Last resort: return a simple error message
            raise Exception(f"Error generating response (finish_reason issue): {str(e)}. All fallback attempts failed. Please try again.") from e
      else:
        raise Exception(f"Error generating response: {str(e)}") from e
      
    except Exception as e:
      error_str = str(e).lower()
      
      # If we get consecutive messages error, retry with minimal history
      if "multiple messages" in error_str:
        # Retry with just the latest input, no history
        try:
          result = chain.invoke(
            {
              "input": latest_input,
              "chat_history": [],
            }
          )
          return result.content if hasattr(result, 'content') else str(result)
        except:
          pass
      
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
      if agent.system_prompt:
        full_prompt = f"{agent.system_prompt}\n\n{full_prompt}"

      async for chunk in llm.astream(full_prompt):
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        if content:
          yield content
    except Exception as e:
      # Surface a concise error message to the streaming client.
      yield f"Error: {str(e)}"
