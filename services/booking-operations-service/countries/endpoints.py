"""
Countries module endpoints
Contains FastAPI endpoints for country management operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Dict, Any

from database import get_tenant_db
from shared_auth import get_current_user, check_tenant_slug_access
from .models import Country
from .schemas import (
    CountryResponse,
    CountryCreate,
    CountryUpdate,
    CountryListResponse
)

router = APIRouter()


@router.get("/tenants/{tenant_slug}/countries", response_model=CountryListResponse)
async def list_countries(
    tenant_slug: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    continent: str = Query(None, description="Filter by continent"),
    region: str = Query(None, description="Filter by region"),
    is_active: bool = Query(None, description="Filter by active status"),
    search: str = Query(None, description="Search in country name or code"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    List countries with filtering and pagination

    Args:
        tenant_slug: Tenant identifier
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        continent: Filter by continent
        region: Filter by region
        is_active: Filter by active status
        search: Search in country name or code
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of countries with pagination info
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Build query filters
    filters = []

    if continent:
        filters.append(Country.continent == continent)

    if region:
        filters.append(Country.region == region)

    if is_active is not None:
        filters.append(Country.is_active == is_active)

    if search:
        search_filter = f"%{search.lower()}%"
        filters.append(
            Country.name.ilike(search_filter) |
            Country.code.ilike(search_filter) |
            Country.code3.ilike(search_filter)
        )

    # Build query
    query = db.query(Country)
    if filters:
        query = query.filter(and_(*filters))

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    countries = query.offset(offset).limit(page_size).all()

    # Calculate pagination info
    total_pages = (total + page_size - 1) // page_size

    return CountryListResponse(
        countries=countries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/tenants/{tenant_slug}/countries/{country_id}", response_model=CountryResponse)
async def get_country(
    tenant_slug: str,
    country_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get a specific country by ID

    Args:
        tenant_slug: Tenant identifier
        country_id: Country ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Country details
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get country
    country = db.query(Country).filter(Country.id == country_id).first()

    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {country_id} not found"
        )

    return country


@router.post("/tenants/{tenant_slug}/countries", response_model=CountryResponse)
async def create_country(
    tenant_slug: str,
    country_data: CountryCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Create a new country

    Args:
        tenant_slug: Tenant identifier
        country_data: Country creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created country
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Check if country code already exists
    existing_country = db.query(Country).filter(
        (Country.code == country_data.code) |
        (Country.code3 == country_data.code3)
    ).first()

    if existing_country:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Country with code {country_data.code} or {country_data.code3} already exists"
        )

    # Create new country
    country = Country(**country_data.model_dump())

    db.add(country)
    db.commit()
    db.refresh(country)

    return country


@router.put("/tenants/{tenant_slug}/countries/{country_id}", response_model=CountryResponse)
async def update_country(
    tenant_slug: str,
    country_id: int,
    country_data: CountryUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Update an existing country

    Args:
        tenant_slug: Tenant identifier
        country_id: Country ID
        country_data: Country update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated country
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get existing country
    country = db.query(Country).filter(Country.id == country_id).first()

    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {country_id} not found"
        )

    # Check for duplicate codes if updating
    update_data = country_data.model_dump(exclude_unset=True)

    if 'code' in update_data or 'code3' in update_data:
        code_filters = []
        if 'code' in update_data:
            code_filters.append(Country.code == update_data['code'])
        if 'code3' in update_data:
            code_filters.append(Country.code3 == update_data['code3'])

        existing_country = db.query(Country).filter(
            Country.id != country_id
        ).filter(
            *code_filters if len(code_filters) == 1 else [Country.code.in_([update_data.get('code'), update_data.get('code3')])]
        ).first()

        if existing_country:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Country with the provided code already exists"
            )

    # Update country
    for field, value in update_data.items():
        setattr(country, field, value)

    db.commit()
    db.refresh(country)

    return country


@router.delete("/tenants/{tenant_slug}/countries/{country_id}")
async def delete_country(
    tenant_slug: str,
    country_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Delete a country

    Args:
        tenant_slug: Tenant identifier
        country_id: Country ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Deletion confirmation
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get country
    country = db.query(Country).filter(Country.id == country_id).first()

    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with ID {country_id} not found"
        )

    # Check if country has related destinations
    if country.destinations:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete country with existing destinations"
        )

    # Delete country
    db.delete(country)
    db.commit()

    return {"message": f"Country {country.name} deleted successfully"}


@router.get("/tenants/{tenant_slug}/countries/by-code/{country_code}", response_model=CountryResponse)
async def get_country_by_code(
    tenant_slug: str,
    country_code: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get a country by its ISO code (2 or 3 letter)

    Args:
        tenant_slug: Tenant identifier
        country_code: Country ISO code (2 or 3 letters)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Country details
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get country by code (supports both 2 and 3 letter codes)
    country = db.query(Country).filter(
        (Country.code == country_code.upper()) |
        (Country.code3 == country_code.upper())
    ).first()

    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Country with code {country_code} not found"
        )

    return country


@router.get("/tenants/{tenant_slug}/countries/continents", response_model=List[str])
async def get_continents(
    tenant_slug: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
):
    """
    Get list of all continents

    Args:
        tenant_slug: Tenant identifier
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of continents
    """
    # Check tenant access
    check_tenant_slug_access(current_user, tenant_slug)

    # Get distinct continents
    continents = db.query(Country.continent).filter(
        Country.continent.isnot(None),
        Country.is_active == True
    ).distinct().all()

    return [continent[0] for continent in continents if continent[0]]
