"""
SQLAlchemy Models for PostgreSQL
Enterprise-grade database schema with relationships
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    Text, DateTime, ForeignKey, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# ============================================================
# USER MODELS
# ============================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    settings = Column(JSON, default={})
    
    # Relationships
    roles = relationship("UserRole", back_populates="user")
    workspaces = relationship("WorkspaceMember", back_populates="user")
    messages = relationship("Message", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    permissions = Column(JSON, default=[])  # JSON array of permissions
    
    # Relationships
    users = relationship("UserRole", back_populates="role")

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")
    workspace = relationship("Workspace")

# ============================================================
# WORKSPACE MODELS
# ============================================================

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    owner_id = Column(String(36), ForeignKey("users.id"))
    settings = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("WorkspaceMember", back_populates="workspace")
    shared_chats = relationship("SharedChat", back_populates="workspace")
    knowledge_bases = relationship("KnowledgeBase", back_populates="workspace")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    
    workspace_id = Column(String(36), ForeignKey("workspaces.id"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    role = Column(String(50), default="member")  # admin, member, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspaces")

# ============================================================
# CHAT & MESSAGE MODELS
# ============================================================

class SharedChat(Base):
    __tablename__ = "shared_chats"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"))
    name = Column(String(200), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="shared_chats")
    creator = relationship("User", foreign_keys=[created_by])
    messages = relationship("Message", back_populates="chat")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    chat_id = Column(String(36), ForeignKey("shared_chats.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat = relationship("SharedChat", back_populates="messages")
    user = relationship("User", back_populates="messages")

# ============================================================
# KNOWLEDGE BASE MODELS
# ============================================================

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"))
    name = Column(String(200), nullable=False)
    description = Column(Text)
    vector_db_path = Column(String(500))
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    document_count = Column(Integer, default=0)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="knowledge_bases")
    creator = relationship("User", foreign_keys=[created_by])

# ============================================================
# AUDIT & COMPLIANCE MODELS
# ============================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(100))
    details = Column(JSON, default={})
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    previous_hash = Column(String(64))
    hash = Column(String(64), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    retention_date = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")

# ============================================================
# PLUGIN MODELS
# ============================================================

class PluginRegistry(Base):
    __tablename__ = "plugin_registry"
    
    id = Column(Integer, primary_key=True)
    plugin_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    version = Column(String(50), nullable=False)
    author = Column(String(200))
    description = Column(Text)
    repository_url = Column(String(500))
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    installed_at = Column(DateTime)
    updated_at = Column(DateTime)
    is_enabled = Column(Boolean, default=True)
    metadata = Column(JSON, default={})

class UserPlugin(Base):
    __tablename__ = "user_plugins"
    
    user_id = Column(String(36), ForeignKey("users.id"), primary_key=True)
    plugin_id = Column(String(100), primary_key=True)
    installed_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON, default={})

# Create indexes for performance
Index('idx_messages_created_at', Message.created_at)
Index('idx_audit_logs_created_at', AuditLog.created_at)
Index('idx_audit_logs_user_id', AuditLog.user_id)
Index('idx_workspace_members_user', WorkspaceMember.user_id)
Index('idx_user_roles_user', UserRole.user_id)
