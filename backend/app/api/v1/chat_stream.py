from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatRequest
from app.services.langchain_client import LangchainAgentService
import json
from datetime import datetime

router = APIRouter()


@router.post("/{agent_id}/stream")
async def chat_stream(
    agent_id: UUID,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream chat responses using Server-Sent Events (SSE) compatible with Vercel AI SDK."""
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
    
    # Get recent message history
    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )
    recent_messages.reverse()
    
    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER,
        content=chat_request.message,
    )
    db.add(user_message)
    db.commit()
    
    # Generate streaming response
    agent_service = LangchainAgentService()
    full_response = ""
    
    async def generate():
        nonlocal full_response
        try:
            async for chunk in agent_service.stream_response(
                agent=agent,
                history=recent_messages,
                latest_input=chat_request.message,
            ):
                if chunk:
                    full_response += chunk
                    # Format as SSE (Server-Sent Events) compatible with Vercel AI SDK
                    # Format: data: {"id":"...","object":"chat.completion.chunk","choices":[{"delta":{"content":"chunk"}}]}
                    data = {
                        "id": str(conversation.id),
                        "object": "chat.completion.chunk",
                        "created": int(datetime.utcnow().timestamp()),
                        "model": agent.model,
                        "choices": [{
                            "index": 0,
                            "delta": {"content": chunk},
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            
            # Send final chunk with finish_reason
            final_data = {
                "id": str(conversation.id),
                "object": "chat.completion.chunk",
                "created": int(datetime.utcnow().timestamp()),
                "model": agent.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            yield "data: [DONE]\n\n"
            
            # Save assistant message after streaming completes
            assistant_message = Message(
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=full_response,
            )
            db.add(assistant_message)
            conversation.updated_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            error_data = {
                "error": {
                    "message": str(e),
                    "type": type(e).__name__
                }
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

