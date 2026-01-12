from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.agent import Agent
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.schemas.conversation import ConversationCreate, ConversationResponse

router = APIRouter()


@router.get("/agent/{agent_id}", response_model=List[ConversationResponse])
async def list_conversations(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all conversations for a specific agent."""
    # Verify agent exists and user has access (owned or prebuilt)
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
    
    # Return conversations for this user and agent
    conversations = db.query(Conversation).filter(
        Conversation.agent_id == agent_id,
        Conversation.user_id == current_user.id
    ).all()
    
    return conversations


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation for an agent."""
    # Verify agent ownership or prebuilt access
    agent = db.query(Agent).filter(
        Agent.id == conversation_data.agent_id,
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
    
    new_conversation = Conversation(
        agent_id=conversation_data.agent_id,
        user_id=current_user.id,
        title=conversation_data.title
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    
    # If agent has a greeting message, add it to the conversation
    if agent.greeting_message:
        greeting_message = Message(
            conversation_id=new_conversation.id,
            role=MessageRole.ASSISTANT,
            content=agent.greeting_message,
        )
        db.add(greeting_message)
        db.commit()
    
    return new_conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a conversation with all messages (only if owned by current user)."""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation

