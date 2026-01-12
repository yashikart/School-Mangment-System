from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from datetime import datetime
import enum
from app.database import Base, engine


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    PARENT = "PARENT"
    STUDENT = "STUDENT"


# Create the ENUM type in PostgreSQL if it doesn't exist
user_role_enum = PG_ENUM(UserRole, name="user_role", create_type=True)


class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="school")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=True)  # Hashed password (nullable until set)
    role = Column(user_role_enum, nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    school = relationship("School", back_populates="users")
    password_tokens = relationship("PasswordToken", back_populates="user", cascade="all, delete-orphan")

class PasswordToken(Base):
    __tablename__ = "password_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="password_tokens")
