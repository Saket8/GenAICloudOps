from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    VIEWER = "VIEWER" 
    OPERATOR = "OPERATOR"
    CLOUD_ADMIN = "CLOUD_ADMIN"
    APP_ADMIN = "APP_ADMIN"
    SECURITY_ADMIN = "SECURITY_ADMIN"
    SYS_ADMIN = "SYS_ADMIN"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    
    # Status fields
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserRole.user_id")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permissions - granular control for different modules
    can_view_dashboard = Column(Boolean, default=True)
    can_view_alerts = Column(Boolean, default=True)
    can_approve_remediation = Column(Boolean, default=False)
    can_execute_remediation = Column(Boolean, default=False)
    can_manage_users = Column(Boolean, default=False)
    can_manage_roles = Column(Boolean, default=False)
    can_view_access_analyzer = Column(Boolean, default=True)
    can_view_pod_analyzer = Column(Boolean, default=True)
    can_view_cost_analyzer = Column(Boolean, default=True)
    can_use_chatbot = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role")
    
    def __repr__(self):
        return f"<Role(name='{self.name}', display_name='{self.display_name}')>"

class UserRole(Base):
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    # Optional: role assignment metadata
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"