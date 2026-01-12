from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_api_key_user
from app.models.user import User
from app.models.agent import Agent
from app.models.api_key import ApiKey
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.agent import AgentResponse
from app.services.langchain_client import LangchainAgentService
from datetime import datetime

router = APIRouter()


@router.get("/agents", response_model=List[AgentResponse])
async def list_public_agents(
    user_and_key: tuple[User, ApiKey] = Depends(get_api_key_user),
    db: Session = Depends(get_db)
):
    """List all available prebuilt agents (public API)."""
    current_user, api_key = user_and_key
    
    # If agent_id is null, return all prebuilt agents (universal key)
    if api_key.agent_id is None:
        agents = db.query(Agent).filter(
            Agent.is_prebuilt.is_(True),
            Agent.is_active.is_(True)
        ).all()
        return agents
    
    # Otherwise, return only the agent associated with this API key
    agent = db.query(Agent).filter(Agent.id == api_key.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent associated with API key not found"
        )
    return [agent]


@router.get("/agents/{agent_slug}", response_model=AgentResponse)
async def get_public_agent(
    agent_slug: str,
    user_and_key: tuple[User, ApiKey] = Depends(get_api_key_user),
    db: Session = Depends(get_db)
):
    """Get a specific agent by slug (public API)."""
    current_user, api_key = user_and_key
    
    # Find the agent by slug
    agent = db.query(Agent).filter(
        Agent.slug == agent_slug,
        Agent.is_prebuilt.is_(True),
        Agent.is_active.is_(True),
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # If API key is agent-specific, verify it matches
    if api_key.agent_id is not None and api_key.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is not authorized for this agent"
        )
    
    return agent


@router.post("/agents/{agent_slug}/chat", response_model=ChatResponse)
async def public_chat(
    agent_slug: str,
    chat_request: ChatRequest,
    user_and_key: tuple[User, ApiKey] = Depends(get_api_key_user),
    db: Session = Depends(get_db)
):
    """Send a message to an agent via public API (using agent slug)."""
    current_user, api_key = user_and_key
    
    # Find the agent by slug
    agent = db.query(Agent).filter(
        Agent.slug == agent_slug,
        Agent.is_prebuilt.is_(True),
        Agent.is_active.is_(True),
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # If API key is agent-specific, verify it matches
    if api_key.agent_id is not None and api_key.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is not authorized for this agent"
        )
    
    # Get or create conversation
    conversation = None
    if chat_request.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == chat_request.conversation_id,
            Conversation.user_id == current_user.id,
            Conversation.agent_id == agent.id
        ).first()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    else:
        # Create new conversation
        conversation = Conversation(
            agent_id=agent.id,
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
    
    # Get recent message history (last 10 messages for context)
    recent_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Reverse to get chronological order
    recent_messages.reverse()
    
    # Save user message
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
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error generating response: {error_trace}")
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
    conversation.updated_at = datetime.utcnow()
    db.commit()
    
    return ChatResponse(
        conversation_id=conversation.id,
        message=assistant_response,
        agent_id=agent.id,
    )


@router.post("/agents/{agent_slug}/conversations", response_model=dict)
async def create_public_conversation(
    agent_slug: str,
    title: Optional[str] = None,
    user_and_key: tuple[User, ApiKey] = Depends(get_api_key_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation for an agent (public API)."""
    current_user, api_key = user_and_key
    
    # Find the agent by slug
    agent = db.query(Agent).filter(
        Agent.slug == agent_slug,
        Agent.is_prebuilt.is_(True),
        Agent.is_active.is_(True),
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # If API key is agent-specific, verify it matches
    if api_key.agent_id is not None and api_key.agent_id != agent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is not authorized for this agent"
        )
    
    # Create conversation
    conversation = Conversation(
        agent_id=agent.id,
        user_id=current_user.id,
        title=title or "New Conversation"
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
    
    return {
        "id": conversation.id,
        "agent_id": agent.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat()
    }


@router.get("/conversations/{conversation_id}", response_model=dict)
async def get_public_conversation(
    conversation_id: UUID,
    user_and_key: tuple[User, ApiKey] = Depends(get_api_key_user),
    db: Session = Depends(get_db)
):
    """Get a conversation with its messages (public API)."""
    current_user, api_key = user_and_key
    
    # Find the conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # If API key is agent-specific, verify it matches the conversation's agent
    if api_key.agent_id is not None and api_key.agent_id != conversation.agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key is not authorized for this conversation's agent"
        )
    
    # Get all messages
    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc()).all()
    
    return {
        "id": conversation.id,
        "agent_id": conversation.agent_id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "id": str(msg.id),
                "role": msg.role.value,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }

