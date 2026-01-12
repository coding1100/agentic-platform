from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.pronunciation import PronunciationAssessmentRequest, PronunciationAssessmentResponse
from app.services.langchain_client import LangchainAgentService
from app.services.gemini import GeminiClient

router = APIRouter()


@router.post("/{agent_id}", response_model=ChatResponse)
async def chat(
    agent_id: UUID,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to an agent and get a response."""
    # Verify agent ownership or prebuilt access
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        (
            (Agent.user_id == current_user.id)
            | (Agent.is_prebuilt.is_(True) & Agent.is_active.is_(True))
        ),
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Get or create conversation
    conversation = None
    if chat_request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == chat_request.conversation_id,
            Conversation.user_id == current_user.id,
            Conversation.agent_id == agent_id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = Conversation(
            agent_id=agent_id,
            user_id=current_user.id,
            title=chat_request.message[:50] if len(chat_request.message) > 50 else chat_request.message
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        # If agent has a greeting message, add it to the conversation
        if agent.greeting_message:
            greeting_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=agent.greeting_message,
            )
            db.add(greeting_message)
            db.commit()
    
    # Get recent message history BEFORE saving current message (last 10 messages for context and performance)
    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )

    # Reverse to get chronological order
    recent_messages.reverse()

    # Save user message AFTER getting history
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=chat_request.message,
    )
    db.add(user_message)
    db.commit()

    # Generate response using LangChain + Gemini (tools enabled for prebuilt agents)
    try:
        agent_service = LangchainAgentService()
        assistant_response = agent_service.generate_response(
            agent=agent,
            history=recent_messages,
            latest_input=chat_request.message,
        )
        if not assistant_response or not isinstance(assistant_response, str):
            raise ValueError(f"Invalid response type: {type(assistant_response)}")
        
        # Log response for debugging (first 200 chars)
        print(f"Agent response preview: {assistant_response[:200]}...")
        
        # For quiz requests, ensure response is properly formatted
        if "quiz" in chat_request.message.lower() or "question" in chat_request.message.lower():
            # Check if response contains quiz format
            if "**Question 1:**" not in assistant_response and "Question 1:" not in assistant_response:
                print("WARNING: Quiz requested but response doesn't contain Question 1 format")
                print(f"Full response: {assistant_response[:500]}")
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error generating response: {error_trace}")  # Log to console for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}",
        )

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT,
        content=assistant_response,
    )
    db.add(assistant_message)
    db.commit()

    # Update conversation updated_at
    from datetime import datetime

    conversation.updated_at = datetime.utcnow()
    db.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        message=assistant_response,
        agent_id=agent_id,
    )


@router.post("/pronunciation-assessment", response_model=PronunciationAssessmentResponse)
async def assess_pronunciation(
    assessment_request: PronunciationAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assess pronunciation of a word or phrase using Gemini AI."""
    try:
        # Use Gemini to assess pronunciation
        gemini_client = GeminiClient()
        
        # Create a detailed prompt for pronunciation assessment
        prompt = f"""You are an expert language pronunciation assessor. Assess the pronunciation of the following:

Target word/phrase: {assessment_request.word_or_phrase}
User's spoken transcript: {assessment_request.user_transcript}
Target language: {assessment_request.language}

Provide a detailed pronunciation assessment in the following JSON format:
{{
    "overall_score": <0-100 integer>,
    "accuracy_score": <0-100 integer>,
    "fluency_score": <0-100 integer>,
    "intonation_score": <0-100 integer>,
    "stress_score": <0-100 integer>,
    "clarity_score": <0-100 integer>,
    "feedback": "<detailed feedback string>",
    "suggestions": ["<suggestion1>", "<suggestion2>", "<suggestion3>"],
    "correct_pronunciation": "<correct pronunciation guide>",
    "user_pronunciation": "{assessment_request.user_transcript}",
    "phonetic_comparison": "<phonetic comparison if applicable>"
}}

Focus on:
1. Phonetic accuracy (how close the sounds are)
2. Stress patterns (word stress)
3. Intonation (pitch and melody)
4. Clarity (how clear the pronunciation is)
5. Fluency (natural flow)

Be encouraging but honest. Provide specific, actionable feedback."""

        response = gemini_client.generate_response(
            system_prompt="You are an expert language pronunciation assessor. Always respond with valid JSON in the exact format specified.",
            messages=[{"role": "user", "content": prompt}],
            model="gemini-2.5-pro",
            temperature=0.3
        )
        
        # Try to parse JSON from response
        import json
        import re
        
        # Extract JSON from response (handle cases where response has extra text)
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            assessment_data = json.loads(json_str)
        else:
            # Fallback: create assessment from response text
            assessment_data = {
                "overall_score": 75,
                "accuracy_score": 75,
                "fluency_score": 75,
                "intonation_score": 75,
                "stress_score": 75,
                "clarity_score": 75,
                "feedback": response[:500] if len(response) > 500 else response,
                "suggestions": ["Practice the word slowly", "Focus on stress patterns", "Listen to native pronunciation"],
                "correct_pronunciation": assessment_request.word_or_phrase,
                "user_pronunciation": assessment_request.user_transcript,
                "phonetic_comparison": None
            }
        
        # Ensure all required fields are present and within valid ranges
        def clamp_score(score: int) -> int:
            return max(0, min(100, int(score)))
        
        return PronunciationAssessmentResponse(
            overall_score=clamp_score(assessment_data.get("overall_score", 75)),
            accuracy_score=clamp_score(assessment_data.get("accuracy_score", 75)),
            fluency_score=clamp_score(assessment_data.get("fluency_score", 75)),
            intonation_score=clamp_score(assessment_data.get("intonation_score", 75)),
            stress_score=clamp_score(assessment_data.get("stress_score", 75)),
            clarity_score=clamp_score(assessment_data.get("clarity_score", 75)),
            feedback=assessment_data.get("feedback", "Pronunciation assessment completed."),
            suggestions=assessment_data.get("suggestions", []),
            correct_pronunciation=assessment_data.get("correct_pronunciation", assessment_request.word_or_phrase),
            user_pronunciation=assessment_data.get("user_pronunciation", assessment_request.user_transcript),
            phonetic_comparison=assessment_data.get("phonetic_comparison")
        )
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error assessing pronunciation: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assessing pronunciation: {str(e)}",
        )

