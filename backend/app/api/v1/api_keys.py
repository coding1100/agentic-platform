from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import generate_api_key, hash_api_key
from app.models.user import User
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyUsageStats, ApiKeyUpdate

router = APIRouter()


@router.get("", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all API keys for the current user."""
    api_keys = db.query(ApiKey).filter(ApiKey.user_id == current_user.id).all()
    return api_keys


@router.post("", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key. If agent_id is null, creates a universal key for all agents.

    New keys embed their database ID in the plain key to allow O(1) lookup while
    keeping the stored value hashed.
    """
    agent = None
    agent_slug = None
    
    # If agent_id is provided, verify agent ownership or prebuilt access
    if api_key_data.agent_id:
        from app.models.agent import Agent
        agent = db.query(Agent).filter(
            Agent.id == api_key_data.agent_id,
            (
                (Agent.user_id == current_user.id)
                | (Agent.is_prebuilt.is_(True) & Agent.is_active.is_(True))
            ),
        ).first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or you don't have access to it"
            )
        agent_slug = agent.slug
    
    # Create API key record with temporary hash; the final key will embed the DB ID.
    temp_plain = generate_api_key()
    temp_hash = hash_api_key(temp_plain)
    
    api_key = ApiKey(
        user_id=current_user.id,
        agent_id=api_key_data.agent_id,  # Can be None for universal keys
        key_hash=temp_hash,
        name=api_key_data.name,
        expires_at=api_key_data.expires_at,
        rate_limit_per_minute=api_key_data.rate_limit_per_minute,
        allowed_origins=api_key_data.allowed_origins,  # Can be None for allow all
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Now that we have the DB ID, generate the final plain key and hash.
    # Format: ak_<uuidhex>_<random>
    final_plain = f"ak_{api_key.id.hex}_{generate_api_key()}"
    api_key.key_hash = hash_api_key(final_plain)
    db.commit()
    db.refresh(api_key)
    
    # Return response with the plain key (only shown once)
    response = ApiKeyResponse(
        id=api_key.id,
        agent_id=api_key.agent_id,
        name=api_key.name,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        total_requests=api_key.total_requests,
        allowed_origins=api_key.allowed_origins,
        key=final_plain,  # Include plain key only on creation
        agent_slug=agent_slug  # Include agent slug for URL generation (null for universal keys)
    )
    
    return response


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific API key by ID."""
    from app.models.agent import Agent
    api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    agent = db.query(Agent).filter(Agent.id == api_key.agent_id).first()
    return ApiKeyResponse(
        id=api_key.id,
        agent_id=api_key.agent_id,
        name=api_key.name,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        total_requests=api_key.total_requests,
        agent_slug=agent.slug if agent else None
    )


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an API key."""
    api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    db.delete(api_key)
    db.commit()
    
    return None


@router.patch("/{api_key_id}/toggle", response_model=ApiKeyResponse)
async def toggle_api_key(
    api_key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle API key active status."""
    from app.models.agent import Agent
    api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = not api_key.is_active
    db.commit()
    db.refresh(api_key)
    
    agent = db.query(Agent).filter(Agent.id == api_key.agent_id).first()
    return ApiKeyResponse(
        id=api_key.id,
        agent_id=api_key.agent_id,
        name=api_key.name,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        total_requests=api_key.total_requests,
        allowed_origins=api_key.allowed_origins,
        agent_slug=agent.slug if agent else None
    )


@router.get("/{api_key_id}/usage", response_model=ApiKeyUsageStats)
async def get_api_key_usage(
    api_key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage statistics for an API key."""
    api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Calculate requests today and this month
    today = datetime.utcnow().date()
    month_start = datetime.utcnow().replace(day=1).date()
    
    # For now, we'll use total_requests as a proxy
    # In a production system, you'd want to track requests in a separate table
    requests_today = 0  # TODO: Implement proper tracking
    requests_this_month = api_key.total_requests  # TODO: Implement proper tracking
    
    return ApiKeyUsageStats(
        total_requests=api_key.total_requests,
        last_used_at=api_key.last_used_at,
        requests_today=requests_today,
        requests_this_month=requests_this_month
    )


@router.patch("/{api_key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    api_key_id: UUID,
    update_data: ApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an API key (name, allowed origins, active status, rate limit)."""
    from app.models.agent import Agent
    
    api_key = db.query(ApiKey).filter(
        ApiKey.id == api_key_id,
        ApiKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    # Update fields if provided
    if update_data.name is not None:
        api_key.name = update_data.name
    
    if update_data.is_active is not None:
        api_key.is_active = update_data.is_active
    
    if update_data.rate_limit_per_minute is not None:
        api_key.rate_limit_per_minute = update_data.rate_limit_per_minute
    
    # Handle allowed_origins: empty list means allow all (set to None)
    if update_data.allowed_origins is not None:
        api_key.allowed_origins = update_data.allowed_origins if len(update_data.allowed_origins) > 0 else None
    
    db.commit()
    db.refresh(api_key)
    
    agent = db.query(Agent).filter(Agent.id == api_key.agent_id).first()
    return ApiKeyResponse(
        id=api_key.id,
        agent_id=api_key.agent_id,
        name=api_key.name,
        is_active=api_key.is_active,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        total_requests=api_key.total_requests,
        allowed_origins=api_key.allowed_origins,
        agent_slug=agent.slug if agent else None
    )

