from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import super_admin_exists, create_super_admin
from app.schemas import SuperAdminSetupResponse

router = APIRouter(prefix="/super-admin", tags=["super-admin"])


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
