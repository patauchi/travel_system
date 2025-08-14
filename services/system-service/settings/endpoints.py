"""
Settings Module Endpoints
API endpoints for settings and audit log operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from database import get_db
from shared_auth import get_current_user, require_permission, get_current_tenant
from .models import Setting, AuditLog
from .schemas import (
    SettingCreate, SettingUpdate, SettingResponse, SettingFilter,
    SettingBulkUpdate, ConfigurationExport, ConfigurationImport,
    ConfigurationImportResult, AuditLogCreate, AuditLogResponse,
    AuditLogFilter, SystemHealthResponse, SystemInfoResponse
)

router = APIRouter()

# ============================================
# Setting Endpoints
# ============================================

@router.post("/settings", response_model=SettingResponse, status_code=status.HTTP_201_CREATED)
async def create_setting(
    setting_data: SettingCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new setting"""
    # Check if setting already exists
    existing_setting = db.query(Setting).filter(
        and_(Setting.category == setting_data.category, Setting.key == setting_data.key)
    ).first()

    if existing_setting:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Setting {setting_data.category}.{setting_data.key} already exists"
        )

    # Create new setting
    db_setting = Setting(
        category=setting_data.category,
        key=setting_data.key,
        value=setting_data.value,
        value_type=setting_data.value_type,
        display_name=setting_data.display_name,
        description=setting_data.description,
        is_public=setting_data.is_public,
        is_encrypted=setting_data.is_encrypted,
        is_system=setting_data.is_system,
        validation_rules=setting_data.validation_rules,
        allowed_values=setting_data.allowed_values,
        default_value=setting_data.default_value,
        meta_data=setting_data.meta_data,
        updated_by=current_user.id
    )

    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)

    # Create audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="setting_created",
        resource_type="setting",
        resource_id=str(db_setting.id),
        resource_name=f"{db_setting.category}.{db_setting.key}",
        changes={"created": setting_data.dict()},
        result="success"
    )

    return db_setting


@router.get("/settings", response_model=List[SettingResponse])
async def list_settings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    key: Optional[str] = Query(None),
    value_type: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    is_system: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List settings with filtering and pagination"""
    query = db.query(Setting)

    # Apply filters
    if category:
        query = query.filter(Setting.category == category)

    if key:
        query = query.filter(Setting.key == key)

    if value_type:
        query = query.filter(Setting.value_type == value_type)

    if is_public is not None:
        query = query.filter(Setting.is_public == is_public)

    if is_system is not None:
        query = query.filter(Setting.is_system == is_system)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Setting.display_name.ilike(search_term),
                Setting.description.ilike(search_term),
                Setting.category.ilike(search_term),
                Setting.key.ilike(search_term)
            )
        )

    settings = query.offset(skip).limit(limit).all()
    return settings


@router.get("/settings/{setting_id}", response_model=SettingResponse)
async def get_setting(
    setting_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific setting by ID"""
    setting = db.query(Setting).filter(Setting.id == setting_id).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    return setting


@router.get("/settings/by-key/{category}/{key}", response_model=SettingResponse)
async def get_setting_by_key(
    category: str,
    key: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a setting by category and key"""
    setting = db.query(Setting).filter(
        and_(Setting.category == category, Setting.key == key)
    ).first()

    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting {category}.{key} not found"
        )

    return setting


@router.put("/settings/{setting_id}", response_model=SettingResponse)
async def update_setting(
    setting_id: UUID,
    setting_data: SettingUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Update a setting"""
    db_setting = db.query(Setting).filter(Setting.id == setting_id).first()
    if not db_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )

    # Check if it's a system setting and prevent modification of critical fields
    if db_setting.is_system:
        restricted_fields = ['category', 'key', 'is_system']
        update_dict = setting_data.dict(exclude_unset=True)
        if any(field in update_dict for field in restricted_fields):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot modify protected fields of system settings"
            )

    # Store old values for audit
    old_values = db_setting.to_dict()

    # Update fields
    update_data = setting_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_setting, field, value)

    db_setting.updated_by = current_user.id
    db.commit()
    db.refresh(db_setting)

    # Create audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="setting_updated",
        resource_type="setting",
        resource_id=str(db_setting.id),
        resource_name=f"{db_setting.category}.{db_setting.key}",
        changes={"before": old_values, "after": db_setting.to_dict()},
        result="success"
    )

    return db_setting


@router.delete("/settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_setting(
    setting_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Delete a setting"""
    db_setting = db.query(Setting).filter(Setting.id == setting_id).first()
    if not db_setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )

    # Prevent deletion of system settings
    if db_setting.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete system settings"
        )

    # Store setting info for audit
    setting_info = db_setting.to_dict()

    db.delete(db_setting)
    db.commit()

    # Create audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="setting_deleted",
        resource_type="setting",
        resource_id=str(setting_id),
        resource_name=f"{setting_info['category']}.{setting_info['key']}",
        changes={"deleted": setting_info},
        result="success"
    )


@router.post("/settings/bulk-update", response_model=Dict[str, Any])
async def bulk_update_settings(
    bulk_data: SettingBulkUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Bulk update multiple settings"""
    results = {
        "updated": 0,
        "created": 0,
        "errors": [],
        "total": len(bulk_data.settings)
    }

    for setting_data in bulk_data.settings:
        try:
            # Check if setting exists
            existing_setting = db.query(Setting).filter(
                and_(
                    Setting.category == setting_data['category'],
                    Setting.key == setting_data['key']
                )
            ).first()

            if existing_setting:
                # Update existing setting
                for field, value in setting_data.items():
                    if field not in ['category', 'key']:  # Don't update key fields
                        setattr(existing_setting, field, value)
                existing_setting.updated_by = current_user.id
                results["updated"] += 1
            else:
                # Create new setting
                new_setting = Setting(**setting_data, updated_by=current_user.id)
                db.add(new_setting)
                results["created"] += 1

        except Exception as e:
            results["errors"].append({
                "setting": f"{setting_data.get('category', 'unknown')}.{setting_data.get('key', 'unknown')}",
                "error": str(e)
            })

    db.commit()

    # Create audit log
    await create_audit_log(
        db=db,
        user_id=current_user.id,
        action="settings_bulk_updated",
        resource_type="settings",
        changes={"results": results},
        result="success" if not results["errors"] else "partial"
    )

    return results


# ============================================
# Configuration Management Endpoints
# ============================================

@router.get("/settings/export/{category}", response_model=ConfigurationExport)
async def export_configuration(
    category: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Export configuration settings by category"""
    settings = db.query(Setting).filter(Setting.category == category).all()

    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No settings found for category: {category}"
        )

    return ConfigurationExport(
        exported_at=datetime.utcnow(),
        tenant_id=tenant_id,
        categories=[category],
        settings=[SettingResponse.from_orm(setting) for setting in settings]
    )


# ============================================
# Audit Log Endpoints
# ============================================

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List audit logs with filtering and pagination"""
    query = db.query(AuditLog)

    # Apply filters
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)

    if result:
        query = query.filter(AuditLog.result == result)

    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)

    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    # Order by most recent first
    query = query.order_by(AuditLog.created_at.desc())

    audit_logs = query.offset(skip).limit(limit).all()
    return audit_logs


@router.get("/audit-logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Get a specific audit log by ID"""
    audit_log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    return audit_log


# ============================================
# System Information Endpoints
# ============================================

@router.get("/health", response_model=SystemHealthResponse)
async def health_check(
    db: Session = Depends(get_db)
):
    """System health check"""
    checks = {}
    overall_status = "healthy"

    # Database check
    try:
        db.execute("SELECT 1")
        checks["database"] = {"status": "healthy", "message": "Database connection OK"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "unhealthy"

    # Settings check
    try:
        settings_count = db.query(func.count(Setting.id)).scalar()
        checks["settings"] = {
            "status": "healthy",
            "message": f"Settings service OK ({settings_count} settings)"
        }
    except Exception as e:
        checks["settings"] = {"status": "degraded", "message": str(e)}
        if overall_status == "healthy":
            overall_status = "degraded"

    return SystemHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        checks=checks,
        version="1.0.0",
        uptime_seconds=0  # TODO: Implement actual uptime tracking
    )


# ============================================
# Helper Functions
# ============================================

async def create_audit_log(
    db: Session,
    user_id: UUID,
    action: str,
    resource_type: str = None,
    resource_id: str = None,
    resource_name: str = None,
    changes: Dict[str, Any] = None,
    result: str = "success",
    error_message: str = None,
    duration_ms: int = None
):
    """Helper function to create audit log entries"""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        changes=changes,
        result=result,
        error_message=error_message,
        duration_ms=duration_ms
    )

    db.add(audit_log)
    # Note: Don't commit here, let the calling function handle the transaction
