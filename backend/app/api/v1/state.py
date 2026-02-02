from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import re
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.user_state import UserState
from app.schemas.state import UserStateUpsert, UserStateResponse

router = APIRouter()

_NAMESPACE_PATTERN = re.compile(r"^[a-zA-Z0-9._:-]{1,100}$")


def _validate_namespace(namespace: str) -> None:
    if not _NAMESPACE_PATTERN.match(namespace):
        raise HTTPException(
            status_code=400,
            detail="Invalid namespace. Use 1-100 chars: letters, numbers, dot, underscore, dash, colon."
        )


@router.get("/{namespace}", response_model=UserStateResponse)
def get_state(
    namespace: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get persisted state for a namespace. Returns empty data if not found."""
    _validate_namespace(namespace)
    state = db.query(UserState).filter(
        UserState.user_id == current_user.id,
        UserState.namespace == namespace,
    ).first()

    if not state:
        return UserStateResponse(namespace=namespace, data={}, updated_at=None)

    return UserStateResponse(
        namespace=state.namespace,
        data=state.data or {},
        updated_at=state.updated_at,
    )


@router.put("/{namespace}", response_model=UserStateResponse)
def upsert_state(
    namespace: str,
    payload: UserStateUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create or update persisted state for a namespace."""
    _validate_namespace(namespace)
    state = db.query(UserState).filter(
        UserState.user_id == current_user.id,
        UserState.namespace == namespace,
    ).first()

    if state:
        state.data = payload.data or {}
    else:
        state = UserState(
            user_id=current_user.id,
            namespace=namespace,
            data=payload.data or {},
        )
        db.add(state)

    db.commit()
    db.refresh(state)

    return UserStateResponse(
        namespace=state.namespace,
        data=state.data or {},
        updated_at=state.updated_at,
    )
