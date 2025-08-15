"""
Users Module Endpoints
API endpoints for user-related operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from database import get_db
from shared_auth import get_current_user, require_permission, get_current_tenant
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

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new user"""
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
        created_by=current_user.id
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

    return db_user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    department: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List users with pagination and filtering"""
    query = db.query(User)

    if active_only:
        query = query.filter(User.is_active == True)

    if department:
        query = query.filter(User.department == department)

    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Update a user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ['role_ids', 'team_ids']:
            setattr(db_user, field, value)

    # Update roles if specified
    if user_data.role_ids is not None:
        roles = db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
        db_user.roles = roles

    # Update teams if specified
    if user_data.team_ids is not None:
        teams = db.query(Team).filter(Team.id.in_(user_data.team_ids)).all()
        db_user.teams = teams

    db_user.updated_by = current_user.id
    db.commit()
    db.refresh(db_user)

    return db_user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Soft delete a user"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Soft delete
    from datetime import datetime
    db_user.deleted_at = datetime.utcnow()
    db_user.deleted_by = current_user.id
    db_user.is_active = False

    db.commit()


# ============================================
# Role Endpoints
# ============================================

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new role"""
    # Check if role already exists
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
        created_by=current_user.id
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List roles with pagination"""
    query = db.query(Role)

    if active_only:
        query = query.filter(Role.is_active == True)

    roles = query.offset(skip).limit(limit).all()
    return roles


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific role by ID"""
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    resource: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List permissions with filtering"""
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new team"""
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
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List teams with pagination"""
    query = db.query(Team)

    if active_only:
        query = query.filter(Team.is_active == True)

    teams = query.offset(skip).limit(limit).all()
    return teams


# ============================================
# Authentication Endpoints
# ============================================

@router.post("/auth/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
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
