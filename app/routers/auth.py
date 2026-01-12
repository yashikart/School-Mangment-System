from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_password_hash
from app.config import settings
from app.schemas import (
    LoginRequest, Token, SetPasswordRequest, SetPasswordResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    ChangePasswordRequest, ChangePasswordResponse
)
from app.models import User, UserRole
from app.email_service import (
    validate_password_token, mark_token_as_used,
    generate_password_token, send_password_reset_email
)
from app.dependencies import get_current_user
from app.auth import verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    Supports both OAuth2 form data (username/password) and JSON (email/password).
    Token contains: user_id, role, school_id
    
    Note: In Swagger UI, 'username' field should contain the email address.
    """
    # OAuth2PasswordRequestForm uses 'username' field, but we use email
    # So we treat 'username' as email
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),  # JWT standard requires sub to be string
            "role": user.role.value,
            "school_id": user.school_id
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-json", response_model=Token)
def login_json(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Alternative login endpoint using JSON body (email/password).
    Use this for programmatic API access or frontend integrations.
    """
    # First check if user exists
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check specific issues for better error messages
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive. Please contact administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.password is None:
        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password not set. Please check your email for password setup link.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password not set. Please contact administrator.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # Now authenticate
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
            "school_id": user.school_id
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/set-password", response_model=SetPasswordResponse)
def set_password(
    request: SetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Set password for a user using a password setup token.
    This endpoint is used when a user receives an invitation email
    and needs to set their password for the first time.
    """
    # Validate token
    password_token = validate_password_token(db, request.token)
    
    # Get user
    user = db.query(User).filter(User.id == password_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate password (basic validation - you can add more rules)
    if len(request.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Hash and set password
    hashed_password = get_password_hash(request.password)
    user.password = hashed_password
    
    # Mark token as used
    mark_token_as_used(db, password_token)
    
    # Commit changes
    db.commit()
    
    return SetPasswordResponse(
        success=True,
        message="Password set successfully. You can now log in."
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset. Sends an email with a reset link.
    Works for all user roles (TEACHER, STUDENT, PARENT, ADMIN).
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success message (security: don't reveal if email exists)
    if not user:
        return ForgotPasswordResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )
    
    # Check if user is active
    if not user.is_active:
        return ForgotPasswordResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )
    
    # Generate password reset token
    password_token = generate_password_token(db, user.id)
    
    # Send password reset email
    email_sent = await send_password_reset_email(db, user, password_token)
    
    if email_sent:
        return ForgotPasswordResponse(
            success=True,
            message="If an account with that email exists, a password reset link has been sent."
        )
    else:
        return ForgotPasswordResponse(
            success=False,
            message="Failed to send password reset email. Please try again later."
        )


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using a password reset token.
    This endpoint is used when a user clicks the reset link from their email.
    """
    # Validate token
    password_token = validate_password_token(db, request.token)
    
    # Get user
    user = db.query(User).filter(User.id == password_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Hash and set new password
    hashed_password = get_password_hash(request.new_password)
    user.password = hashed_password
    
    # Mark token as used
    mark_token_as_used(db, password_token)
    
    # Commit changes
    db.commit()
    
    return ResetPasswordResponse(
        success=True,
        message="Password reset successfully. You can now log in with your new password."
    )


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change password for logged-in users.
    Requires the current password to be provided.
    """
    # Verify current password
    if not current_user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password set. Please use password reset instead."
        )
    
    if not verify_password(request.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long"
        )
    
    # Check if new password is different from current
    if verify_password(request.new_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )
    
    # Hash and set new password
    hashed_password = get_password_hash(request.new_password)
    current_user.password = hashed_password
    
    # Commit changes
    db.commit()
    
    return ChangePasswordResponse(
        success=True,
        message="Password changed successfully."
    )
