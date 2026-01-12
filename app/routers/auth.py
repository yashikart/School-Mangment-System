from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_password_hash
from app.config import settings
from app.schemas import LoginRequest, Token, SetPasswordRequest, SetPasswordResponse
from app.models import User
from app.email_service import validate_password_token, mark_token_as_used

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
