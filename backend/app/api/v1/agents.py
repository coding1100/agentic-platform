from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse

router = APIRouter()


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all agents for the current user."""
    # User-owned agents
    user_agents = db.query(Agent).filter(Agent.user_id == current_user.id).all()

    # Active prebuilt agents (shared across all users)
    prebuilt_agents = db.query(Agent).filter(
        Agent.is_prebuilt.is_(True),
        Agent.is_active.is_(True),
    ).all()

    agents = prebuilt_agents + user_agents
    return agents


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new agent."""
    new_agent = Agent(user_id=current_user.id, **agent_data.model_dump())
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get agent details (owned by current user or prebuilt)."""
    # Check if agent is owned by user or is a prebuilt agent
    agent = db.query(Agent).filter(
        Agent.id == agent_id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Allow access if owned by user or is prebuilt and active
    if agent.user_id != current_user.id and not (agent.is_prebuilt and agent.is_active):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an agent (only if owned by current user)."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db.commit()
    db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an agent (only if owned by current user and not pre-built)."""
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.user_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Prevent deleting pre-built agents
    if agent.is_prebuilt:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pre-built agents cannot be deleted"
        )
    
    db.delete(agent)
    db.commit()
    return None

