"""
Authentication & User Management for Sprint 5
JWT-based authentication with role-based access control
"""

import jwt
from local_agent.core.db import db_manager
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends
import secrets
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from pydantic import BaseModel, EmailStr
import os
import time
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
DB_PATH = os.getenv("DB_PATH", "local_agent.db")

# API Key Security (Sprint 4)
API_KEY = os.getenv("AGENT_API_KEY")
if not API_KEY:
    API_KEY = secrets.token_urlsafe(32)
    print(f"⚠️ No API key set. Generated: {API_KEY}")

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify the API key for protected endpoints"""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key

class RateLimiter:
    """Simple rate limiter for API endpoints"""
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def check_rate_limit(self, key: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        self.requests[key] = [t for t in self.requests[key] if t > minute_ago]
        if len(self.requests[key]) >= self.requests_per_minute:
            return False
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter(requests_per_minute=60)

# Password hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

# JWT tokens
def create_access_token(data: Dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Security scheme
security = HTTPBearer(auto_error=False)

# ============================================================
# DATABASE HELPERS
# ============================================================

@contextmanager
def get_db():
    with db_manager.get_connection() as conn:
        yield conn

# ============================================================
# USER MODELS
# ============================================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str] = None
    roles: List[str] = []
    workspaces: List[Dict] = []

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserResponse] = None

# ============================================================
# USER CRUD OPERATIONS
# ============================================================

def create_user(user_data: UserCreate) -> Dict:
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", 
                       (user_data.email, user_data.username))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        password_hash = hash_password(user_data.password)
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_data.username, user_data.email, password_hash, user_data.full_name, 
              datetime.utcnow().timestamp()))
        
        user_id = cursor.lastrowid
        conn.commit()
    
    # Assign default role
    assign_role(user_id, "user")
    
    return {"id": user_id, "username": user_data.username, "email": user_data.email, "full_name": user_data.full_name}

def authenticate_user(email: str, password: str) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return None
    
    if verify_password(password, user['password_hash']):
        return dict(user)
    return None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, full_name, avatar_url, is_active FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_roles(user_id: int, workspace_id: int = None) -> List[str]:
    conn = get_db()
    cursor = conn.cursor()
    
    if workspace_id:
        cursor.execute("""
            SELECT r.name FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = ? AND (ur.workspace_id = ? OR ur.workspace_id IS NULL)
        """, (user_id, workspace_id))
    else:
        cursor.execute("""
            SELECT r.name FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = ? AND ur.workspace_id IS NULL
        """, (user_id,))
    
    roles = [row[0] for row in cursor.fetchall()]
    conn.close()
    return roles

def assign_role(user_id: int, role_name: str, workspace_id: int = None):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get role ID
    cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
    role = cursor.fetchone()
    if not role:
        # Create default roles if not exists
        init_roles()
        cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
        role = cursor.fetchone()
    
    cursor.execute("""
        INSERT OR IGNORE INTO user_roles (user_id, role_id, workspace_id)
        VALUES (?, ?, ?)
    """, (user_id, role['id'], workspace_id))
    
    conn.commit()
    conn.close()

def init_roles():
    """Initialize default roles"""
    conn = get_db()
    cursor = conn.cursor()
    
    default_roles = [
        ("admin", "Full system access", ['*']),
        ("user", "Standard user access", ['read', 'write', 'chat']),
        ("viewer", "Read-only access", ['read']),
        ("team_admin", "Team workspace admin", ['workspace:*']),
    ]
    
    for name, description, permissions in default_roles:
        cursor.execute("""
            INSERT OR IGNORE INTO roles (name, description, permissions)
            VALUES (?, ?, ?)
        """, (name, description, str(permissions)))
    
    conn.commit()
    conn.close()

# ============================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = Depends(api_key_header)
) -> Dict:
    # 1. Try JWT
    if credentials:
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id:
            user = get_user_by_id(int(user_id))
            if user:
                return user
    
    # 2. Try API Key
    if api_key and api_key == API_KEY:
        # Return a system virtual user
        return {
            "id": 0,
            "username": "system_admin",
            "email": "admin@local-agent",
            "full_name": "System Administrator",
            "is_active": True,
            "is_admin": True
        }
    
    raise HTTPException(
        status_code=401, 
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_active_user(current_user: Dict = Depends(get_current_user)) -> Dict:
    if not current_user.get('is_active'):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: str):
    """Dependency factory for role-based access"""
    async def role_checker(current_user: Dict = Depends(get_current_active_user)):
        # System admin bypassed
        if current_user.get('is_admin'):
            return current_user
            
        roles = get_user_roles(current_user['id'])
        if required_role in roles or 'admin' in roles:
            return current_user
            
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return role_checker

def require_workspace_permission(workspace_id: int, permission: str):
    """Dependency for workspace-level permissions"""
    async def permission_checker(current_user: Dict = Depends(get_current_active_user)):
        roles = get_user_roles(current_user['id'], workspace_id)
        if 'admin' in roles or permission in roles:
            return current_user
        raise HTTPException(status_code=403, detail="Insufficient workspace permissions")
    return permission_checker
