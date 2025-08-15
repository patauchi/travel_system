"""
Users Module Endpoints
API endpoints for user-related operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from uuid import UUID

from database import get_db
from shared_auth import get_current_user, check_permission, validate_tenant_access
from .models import User, Role, Permission, Team
from .schemas import (
    UserCreate, UserUpdate, UserResponse,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse,
    TeamCreate, TeamUpdate, TeamResponse,
    LoginRequest, LoginResponse, PasswordResetRequest, ChangePasswordRequest
)

router = APIRouter()

# ============================================
# User Endpoints
# ============================================

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a new user"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data.email) | (User.username == user_data.username)
        ).first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )

        # Create new user
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            phone_secondary=user_data.phone_secondary,
            department=user_data.department,
            title=user_data.title,
            employee_id=user_data.employee_id,
            timezone=user_data.timezone,
            language=user_data.language,
            currency=user_data.currency,
            password_hash="hashed_password",  # TODO: Implement proper password hashing
            created_by=current_user.get("user_id") or current_user.get("id")
        )

        # Add roles if specified
        if user_data.role_ids:
            roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
            db_user.roles = roles

        # Add teams if specified
        if user_data.team_ids:
            teams = db.query(Team).filter(Team.id.in_(user_data.team_ids)).all()
            db_user.teams = teams

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Convert to response model while session is still active
        user_response = UserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            full_name=db_user.full_name,
            phone=db_user.phone,
            phone_secondary=db_user.phone_secondary,
            avatar_url=db_user.avatar_url,
            bio=db_user.bio,
            department=db_user.department,
            title=db_user.title,
            employee_id=db_user.employee_id,
            timezone=db_user.timezone,
            language=db_user.language,
            currency=db_user.currency,
            status=db_user.status,
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            email_verified_at=db_user.email_verified_at,
            last_login_at=db_user.last_login_at,
            last_activity_at=db_user.last_activity_at,
            two_factor_enabled=db_user.two_factor_enabled if db_user.two_factor_enabled is not None else False,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            roles=db_user.roles if db_user.roles else [],
            teams=db_user.teams if db_user.teams else []
        )

        return user_response


@router.get("/", response_model=List[UserResponse])
async def list_users(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    department: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """List users with optional filtering"""
    from shared_auth import safe_tenant_session
    from sqlalchemy.orm import joinedload
    from datetime import datetime

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        query = db.query(User).options(
            joinedload(User.roles),
            joinedload(User.teams)
        )

        if active_only:
            query = query.filter(User.is_active == True)

        if department:
            query = query.filter(User.department == department)

        users = query.offset(skip).limit(limit).all()

        # Convert to response models while session is still active
        result = []
        for user in users:
            user_dict = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.full_name,
                "phone": user.phone,
                "phone_secondary": user.phone_secondary,
                "avatar_url": user.avatar_url,
                "bio": user.bio,
                "department": user.department,
                "title": user.title,
                "employee_id": user.employee_id,
                "timezone": user.timezone or "UTC",
                "language": user.language or "en",
                "currency": user.currency or "USD",
                "status": user.status,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "email_verified_at": user.email_verified_at,
                "last_login_at": user.last_login_at,
                "last_activity_at": user.last_activity_at,
                "two_factor_enabled": user.two_factor_enabled if user.two_factor_enabled is not None else False,
                "created_at": user.created_at or datetime.utcnow(),
                "updated_at": user.updated_at or datetime.utcnow(),
                "roles": user.roles if user.roles else [],
                "teams": user.teams if user.teams else []
            }
            result.append(UserResponse(**user_dict))

        return result


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific user by ID"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Convert to response model while session is still active
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            phone=user.phone,
            phone_secondary=user.phone_secondary,
            avatar_url=user.avatar_url,
            bio=user.bio,
            department=user.department,
            title=user.title,
            employee_id=user.employee_id,
            timezone=user.timezone,
            language=user.language,
            currency=user.currency,
            status=user.status,
            is_active=user.is_active,
            is_verified=user.is_verified,
            email_verified_at=user.email_verified_at,
            last_login_at=user.last_login_at,
            last_activity_at=user.last_activity_at,
            two_factor_enabled=user.two_factor_enabled if user.two_factor_enabled is not None else False,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=user.roles if user.roles else [],
            teams=user.teams if user.teams else []
        )

        return user_response


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Update a user's information"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

    # Update fields
        # Update user fields
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field not in ['role_ids', 'team_ids']:  # Handle these separately
                setattr(db_user, field, value)

        # Update roles if specified
        if user_data.role_ids is not None:
            roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
            db_user.roles = roles

        # Update teams if specified
        if user_data.team_ids is not None:
            teams = db.query(Team).filter(Team.id.in_(user_data.team_ids)).all()
            db_user.teams = teams

        db_user.updated_by = current_user.get("user_id") or current_user.get("id")
        db.commit()
        db.refresh(db_user)

        # Convert to response model while session is still active
        user_response = UserResponse(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            full_name=db_user.full_name,
            phone=db_user.phone,
            phone_secondary=db_user.phone_secondary,
            avatar_url=db_user.avatar_url,
            bio=db_user.bio,
            department=db_user.department,
            title=db_user.title,
            employee_id=db_user.employee_id,
            timezone=db_user.timezone,
            language=db_user.language,
            currency=db_user.currency,
            status=db_user.status,
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            email_verified_at=db_user.email_verified_at,
            last_login_at=db_user.last_login_at,
            last_activity_at=db_user.last_activity_at,
            two_factor_enabled=db_user.two_factor_enabled if db_user.two_factor_enabled is not None else False,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            roles=db_user.roles if db_user.roles else [],
            teams=db_user.teams if db_user.teams else []
        )

        return user_response


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    tenant_slug: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a user (soft delete)"""
    from shared_auth import safe_tenant_session

    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    with safe_tenant_session(tenant_slug) as db:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Soft delete
        from datetime import datetime
        db_user.deleted_at = datetime.utcnow()
        db_user.deleted_by = current_user.get("user_id") or current_user.get("id")
        db_user.is_active = False

        db.commit()

        return None

# ============================================
# Role Endpoints
# ============================================

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    tenant_slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new role"""
    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    # Check if user already exists
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists"
        )

    # Create new role
    db_role = Role(
        name=role_data.name,
        display_name=role_data.display_name,
        description=role_data.description,
        priority=role_data.priority,
        max_users=role_data.max_users,
        meta_data=role_data.meta_data,
        is_active=role_data.is_active,
        created_by=current_user.get("user_id") or current_user.get("id")
    )

    # Add permissions if specified
    if role_data.permission_ids:
        permissions = db.query(Permission).filter(Permission.id.in_(role_data.permission_ids)).all()
        db_role.permissions = permissions

    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    return db_role


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List roles with pagination"""
    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    query = db.query(Role)

    if active_only:
        query = query.filter(Role.is_active == True)

    roles = query.offset(skip).limit(limit).all()
    return roles


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    tenant_slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific role by ID"""
    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role


# ============================================
# Permission Endpoints
# ============================================

@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    resource: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List permissions with filtering"""
    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    query = db.query(Permission)

    if resource:
        query = query.filter(Permission.resource == resource)

    if action:
        query = query.filter(Permission.action == action)

    permissions = query.offset(skip).limit(limit).all()
    return permissions


# ============================================
# Team Endpoints
# ============================================

@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    tenant_slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new team"""
    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    # Check if team already exists
    existing_team = db.query(Team).filter(Team.name == team_data.name).first()
    if existing_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team with this name already exists"
        )

    # Create new team
    db_team = Team(
        name=team_data.name,
        display_name=team_data.display_name,
        description=team_data.description,
        parent_team_id=team_data.parent_team_id,
        team_lead_id=team_data.team_lead_id,
        meta_data=team_data.meta_data,
        is_active=team_data.is_active
    )

    # Add members if specified
    if team_data.member_ids:
        members = db.query(User).filter(User.id.in_(team_data.member_ids)).all()
        db_team.members = members

    db.add(db_team)
    db.commit()
    db.refresh(db_team)

    return db_team


@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    tenant_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List teams with pagination"""
    # Validate tenant access first
    validate_tenant_access(current_user, tenant_slug)

    query = db.query(Team)

    if active_only:
        query = query.filter(Team.is_active == True)

    teams = query.offset(skip).limit(limit).all()
    return teams


# ============================================
# Authentication Endpoints
# ============================================

@router.post("/password/change", response_model=Dict[str, str])
async def change_password(
    password_data: ChangePasswordRequest,
    tenant_slug: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    # TODO: Implement password verification and hashing
    # Verify current password
    # Hash new password
    # Update user record

    return {"message": "Password changed successfully"}


@router.post("/auth/reset-password", status_code=status.HTTP_200_OK)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    user = db.query(User).filter(User.email == reset_data.email).first()
    if not user:
        # Don't reveal if user exists or not
        return {"message": "If the email exists, a reset link has been sent"}

    # TODO: Generate reset token and send email
    return {"message": "If the email exists, a reset link has been sent"}
