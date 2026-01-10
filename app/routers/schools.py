from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, or_
from app.database import get_db
from app.dependencies import get_current_super_admin
from app.models import School, User, UserRole
from app.schemas import UserResponse
from app.auth import get_password_hash
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/schools", tags=["schools"])


class SchoolCreate(BaseModel):
    name: str
    address: str = None
    phone: str = None
    email: EmailStr = None


class SchoolResponse(BaseModel):
    id: int
    name: str
    address: str = None
    phone: str = None
    email: str = None
    
    class Config:
        from_attributes = True


class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    school_id: int


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class AdminUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    school_id: Optional[int] = None


@router.post("/", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
def create_school(
    school_data: SchoolCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Create a new school.
    Only SUPER_ADMIN can create schools.
    """
    school = School(
        name=school_data.name,
        address=school_data.address,
        phone=school_data.phone,
        email=school_data.email
    )
    try:
        db.add(school)
        db.commit()
        db.refresh(school)
        return school
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School with this information already exists or invalid data."
        )


@router.get("/", response_model=List[SchoolResponse])
def list_schools(
    search: Optional[str] = Query(None, description="Search by name, address, email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    List all schools with optional search.
    Only SUPER_ADMIN can view all schools.
    """
    query = db.query(School)
    
    if search:
        search_filter = or_(
            School.name.ilike(f"%{search}%"),
            School.address.ilike(f"%{search}%"),
            School.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    schools = query.all()
    return schools


# Admin routes must come BEFORE {school_id} routes to avoid route conflicts
@router.get("/admins", response_model=List[UserResponse])
def list_all_admins(
    search: Optional[str] = Query(None, description="Search by name or email"),
    school_id: Optional[int] = Query(None, description="Filter by school ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    List all school admins (users with ADMIN role) with optional search and filter.
    Only SUPER_ADMIN can view all admins.
    """
    query = db.query(User).filter(User.role == UserRole.ADMIN)
    
    if school_id:
        query = query.filter(User.school_id == school_id)
    
    if search:
        search_filter = or_(
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    admins = query.all()
    return admins


@router.get("/admins/{admin_id}", response_model=UserResponse)
def get_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Get a specific admin by ID.
    Only SUPER_ADMIN can view admin details.
    """
    admin = db.query(User).filter(User.id == admin_id, User.role == UserRole.ADMIN).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with id {admin_id} not found"
        )
    return admin


@router.put("/admins/{admin_id}", response_model=UserResponse)
def update_admin(
    admin_id: int,
    admin_data: AdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Update an admin's information.
    Only SUPER_ADMIN can update admins.
    """
    admin = db.query(User).filter(User.id == admin_id, User.role == UserRole.ADMIN).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with id {admin_id} not found"
        )
    
    # Update only provided fields
    if admin_data.name is not None:
        admin.name = admin_data.name
    if admin_data.email is not None:
        admin.email = admin_data.email
    if admin_data.password is not None:
        admin.password = get_password_hash(admin_data.password)
    if admin_data.school_id is not None:
        # Verify school exists
        school = db.query(School).filter(School.id == admin_data.school_id).first()
        if not school:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"School with id {admin_data.school_id} not found"
            )
        admin.school_id = admin_data.school_id
    
    try:
        db.commit()
        db.refresh(admin)
        return admin
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update admin. Email might already be in use."
        )


@router.delete("/admins/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Delete an admin.
    Only SUPER_ADMIN can delete admins.
    """
    admin = db.query(User).filter(User.id == admin_id, User.role == UserRole.ADMIN).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Admin with id {admin_id} not found"
        )
    
    try:
        db.delete(admin)
        db.commit()
        return None
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete admin."
        )


@router.get("/{school_id}", response_model=SchoolResponse)
def get_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Get a specific school by ID.
    Only SUPER_ADMIN can view school details.
    """
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with id {school_id} not found"
        )
    return school


@router.put("/{school_id}", response_model=SchoolResponse)
def update_school(
    school_id: int,
    school_data: SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Update a school's information.
    Only SUPER_ADMIN can update schools.
    """
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with id {school_id} not found"
        )
    
    # Update only provided fields
    if school_data.name is not None:
        school.name = school_data.name
    if school_data.address is not None:
        school.address = school_data.address
    if school_data.phone is not None:
        school.phone = school_data.phone
    if school_data.email is not None:
        school.email = school_data.email
    
    try:
        db.commit()
        db.refresh(school)
        return school
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update school. Email might already be in use."
        )


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Delete a school.
    Only SUPER_ADMIN can delete schools.
    Note: This will fail if there are users associated with the school.
    """
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with id {school_id} not found"
        )
    
    # Check if school has associated users
    user_count = db.query(User).filter(User.school_id == school_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete school. There are {user_count} user(s) associated with this school."
        )
    
    try:
        db.delete(school)
        db.commit()
        return None
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete school."
        )


@router.post("/{school_id}/admins", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_school_admin(
    school_id: int,
    admin_data: AdminCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Create a school admin for a specific school.
    Only SUPER_ADMIN can create school admins.
    
    IMPORTANT: This endpoint prevents creating SUPER_ADMIN role.
    """
    # Verify school exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with id {school_id} not found"
        )
    
    # Ensure school_id matches
    if admin_data.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="school_id in path and body must match"
        )
    
    # Check if user with email already exists
    existing_user = db.query(User).filter(User.email == admin_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create admin user
    hashed_password = get_password_hash(admin_data.password)
    admin_user = User(
        name=admin_data.name,
        email=admin_data.email,
        password=hashed_password,
        role=UserRole.ADMIN,  # Only ADMIN role, never SUPER_ADMIN
        school_id=school_id
    )
    
    try:
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        return admin_user
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create admin user. Email might already be in use."
        )


@router.get("/{school_id}/admins", response_model=List[UserResponse])
def list_school_admins(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    List all admins for a specific school.
    Only SUPER_ADMIN can view school admins.
    """
    # Verify school exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with id {school_id} not found"
        )
    
    admins = db.query(User).filter(
        User.role == UserRole.ADMIN,
        User.school_id == school_id
    ).all()
    return admins
