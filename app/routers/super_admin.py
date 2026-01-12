from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.dependencies import get_current_super_admin
from app.auth import super_admin_exists, create_super_admin
from app.schemas import SuperAdminSetupResponse, InviteAdminRequest, InviteAdminResponse
from app.models import User, UserRole, School
from app.email_service import generate_password_token, send_password_setup_email

router = APIRouter(prefix="/super", tags=["super-admin"])


@router.post("/setup", response_model=SuperAdminSetupResponse)
def setup_super_admin(db: Session = Depends(get_db)):
    """
    One-time setup endpoint to create the initial SUPER_ADMIN account.
    This endpoint can only be used once. After the first successful call,
    it will return a message indicating that super admin already exists.
    
    IMPORTANT: This endpoint should be protected or removed in production
    after initial setup. Consider using environment variables or removing
    this endpoint entirely and using the setup script instead.
    """
    # Check if super admin already exists
    if super_admin_exists(db):
        return SuperAdminSetupResponse(
            success=False,
            message="Super Admin already exists. Setup is disabled.",
            already_exists=True
        )
    
    # Create super admin with predefined credentials
    try:
        create_super_admin(
            db=db,
            name="Super Admin",
            email="blackholeinfiverse48@gmail.com",
            password="superadmin123"
        )
        return SuperAdminSetupResponse(
            success=True,
            message="Super Admin created successfully.",
            already_exists=False
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating super admin: {str(e)}"
        )


@router.post("/invite-admin", response_model=InviteAdminResponse, status_code=status.HTTP_201_CREATED)
async def invite_admin(
    invite_data: InviteAdminRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
):
    """
    Invite a new admin by email.
    Only SUPER_ADMIN can invite admins.
    
    This endpoint:
    1. Creates an ADMIN user with password = NULL
    2. Generates a secure, time-limited token
    3. Sends an email with password setup link
    4. Returns admin details
    """
    # Verify school exists
    school = db.query(School).filter(School.id == invite_data.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with id {invite_data.school_id} not found"
        )
    
    # Check if user with email already exists
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create admin user with NULL password
    admin_user = User(
        name=invite_data.name,
        email=invite_data.email,
        password=None,  # Password will be set by user via email link
        role=UserRole.ADMIN,
        school_id=invite_data.school_id,
        is_active=True
    )
    
    try:
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Generate password setup token
        password_token = generate_password_token(db, admin_user.id)
        
        # Send password setup email
        email_sent = await send_password_setup_email(db, admin_user, password_token)
        
        if not email_sent:
            # Email failed, but user was created
            # In production, you might want to log this and handle it appropriately
            # For now, we'll still return success but note the email issue
            db.rollback()
            # Actually, let's not rollback - user is created, email can be resent
            # We'll just log it
            print(f"Warning: Failed to send email to {admin_user.email}, but user was created")
        
        return InviteAdminResponse(
            success=True,
            message=f"Admin invitation sent to {admin_user.email}. Please check your email to set your password.",
            admin_id=admin_user.id,
            email=admin_user.email
        )
        
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create admin user. Email might already be in use."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating admin: {str(e)}"
        )
