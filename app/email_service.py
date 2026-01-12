"""
Email service for sending password setup emails.
"""
import secrets
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi import HTTPException, status
from app.config import settings
from app.models import User, PasswordToken


# Email configuration
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=None,
)


async def send_password_setup_email(
    db: Session,
    user: User,
    password_token: PasswordToken
) -> bool:
    """
    Send password setup email to the user.
    
    Args:
        db: Database session
        user: User object
        password_token: PasswordToken object
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Create password setup link
        setup_link = f"{settings.FRONTEND_URL}/set-password?token={password_token.token}"
        
        # Email content
        subject = "Set Your Password - School Management System"
        body = f"""
        Hello {user.name},
        
        You have been invited to join the School Management System as an Administrator.
        
        Please set your password by clicking on the following link:
        {setup_link}
        
        This link will expire in {settings.PASSWORD_TOKEN_EXPIRE_MINUTES} minutes.
        
        If you did not request this invitation, please ignore this email.
        
        Best regards,
        School Management System
        """
        
        # Create message
        message = MessageSchema(
            subject=subject,
            recipients=[user.email],
            body=body,
            subtype=MessageType.plain,
        )
        
        # Send email
        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"[EMAIL] Successfully sent password setup email to {user.email}")
        print(f"[EMAIL] Setup link: {setup_link}")
        return True
        
    except Exception as e:
        # Log error with full details
        print(f"[EMAIL ERROR] Failed to send email to {user.email}")
        print(f"[EMAIL ERROR] Error type: {type(e).__name__}")
        print(f"[EMAIL ERROR] Error message: {str(e)}")
        import traceback
        print(f"[EMAIL ERROR] Traceback:")
        traceback.print_exc()
        return False


def generate_password_token(db: Session, user_id: int) -> PasswordToken:
    """
    Generate a secure, unique token for password setup.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        PasswordToken: Created password token
    """
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_TOKEN_EXPIRE_MINUTES)
    
    # Create password token
    password_token = PasswordToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        is_used=False
    )
    
    db.add(password_token)
    db.commit()
    db.refresh(password_token)
    
    return password_token


def validate_password_token(db: Session, token: str) -> PasswordToken:
    """
    Validate a password setup token.
    
    Args:
        db: Database session
        token: Token string
        
    Returns:
        PasswordToken: Valid password token
        
    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    password_token = db.query(PasswordToken).filter(PasswordToken.token == token).first()
    
    if not password_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token"
        )
    
    if password_token.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has already been used"
        )
    
    if password_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )
    
    return password_token


def mark_token_as_used(db: Session, password_token: PasswordToken) -> None:
    """
    Mark a password token as used.
    
    Args:
        db: Database session
        password_token: PasswordToken object
    """
    password_token.is_used = True
    db.commit()
