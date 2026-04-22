from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.agent import Agent
from app.models.user import User
from app.schemas.tutor import TutorExecuteRequest, TutorExecuteResponse, TutorWorkspaceState
from app.services.tutor import TutorWorkspaceService

router = APIRouter()


def _get_agent_for_user(db: Session, current_user: User, agent_id: UUID) -> Agent:
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
            detail="Agent not found",
        )
    return agent


@router.get("/{agent_id}/workspace", response_model=TutorWorkspaceState)
def get_tutor_workspace(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_agent_for_user(db, current_user, agent_id)
    service = TutorWorkspaceService()
    return service.get_workspace(db, current_user.id, agent_id)


@router.put("/{agent_id}/workspace", response_model=TutorWorkspaceState)
def save_tutor_workspace(
    agent_id: UUID,
    workspace: TutorWorkspaceState,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_agent_for_user(db, current_user, agent_id)
    service = TutorWorkspaceService()
    return service.save_workspace(db, current_user.id, agent_id, workspace)


@router.post("/{agent_id}/execute", response_model=TutorExecuteResponse)
def execute_tutor_action(
    agent_id: UUID,
    request: TutorExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_agent_for_user(db, current_user, agent_id)
    service = TutorWorkspaceService()
    return service.execute(db, current_user.id, agent_id, request)
