-- Sprint 5: Multi-Tenant Database Schema

-- ============================================================
-- USER MANAGEMENT
-- ============================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    created_at REAL DEFAULT (strftime('%s', 'now')),
    last_login REAL,
    settings TEXT DEFAULT '{}'
);

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    permissions TEXT DEFAULT '[]'  -- JSON array of permissions
);

-- User roles junction
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER,
    role_id INTEGER,
    workspace_id INTEGER,  -- NULL for global roles
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id, workspace_id)
);

-- ============================================================
-- WORKSPACE MANAGEMENT (Teams)
-- ============================================================

-- Workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    settings TEXT DEFAULT '{}',
    created_at REAL DEFAULT (strftime('%s', 'now')),
    updated_at REAL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

-- Workspace members
CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id INTEGER,
    user_id INTEGER,
    role TEXT DEFAULT 'member',  -- 'admin', 'member', 'viewer'
    joined_at REAL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    PRIMARY KEY (workspace_id, user_id)
);

-- ============================================================
-- SHARED RESOURCES
-- ============================================================

-- Shared chat sessions
CREATE TABLE IF NOT EXISTS shared_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    name TEXT NOT NULL,
    created_by INTEGER,
    created_at REAL DEFAULT (strftime('%s', 'now')),
    is_public BOOLEAN DEFAULT 0,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Shared knowledge bases
CREATE TABLE IF NOT EXISTS shared_knowledge_bases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    vector_db_path TEXT,
    created_by INTEGER,
    created_at REAL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- ============================================================
-- PLUGIN MARKETPLACE
-- ============================================================

-- Plugin registry (local cache of marketplace)
CREATE TABLE IF NOT EXISTS plugin_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    author TEXT,
    description TEXT,
    repository_url TEXT,
    downloads INTEGER DEFAULT 0,
    rating REAL DEFAULT 0,
    installed_at REAL,
    updated_at REAL,
    is_enabled BOOLEAN DEFAULT 1,
    metadata TEXT DEFAULT '{}'
);

-- User installed plugins
CREATE TABLE IF NOT EXISTS user_plugins (
    user_id INTEGER,
    plugin_id TEXT,
    installed_at REAL DEFAULT (strftime('%s', 'now')),
    is_active BOOLEAN DEFAULT 1,
    settings TEXT DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES users(id),
    PRIMARY KEY (user_id, plugin_id)
);

-- ============================================================
-- AUDIT & ACTIVITY
-- ============================================================

-- User activity log
CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp REAL DEFAULT (strftime('%s', 'now')),
    details TEXT DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================================
-- CORE SECURITY & SESSIONS
-- ============================================================

-- Permission Broker: Audit Log
CREATE TABLE IF NOT EXISTS broker_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    request_id TEXT,
    intent TEXT NOT NULL,
    resource TEXT,
    granted BOOLEAN,
    token TEXT,
    reason TEXT,
    context TEXT,
    response_time_ms REAL
);

-- Permission Broker: Policy Learning
CREATE TABLE IF NOT EXISTS broker_policy_learned (
    intent TEXT,
    resource_pattern TEXT,
    success_count INTEGER DEFAULT 0,
    last_updated REAL,
    PRIMARY KEY (intent, resource_pattern)
);

-- Persistent Sessions: Metadata
CREATE TABLE IF NOT EXISTS active_sessions (
    session_id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    last_active REAL NOT NULL,
    user_id TEXT,
    metadata TEXT DEFAULT '{}',
    is_active INTEGER DEFAULT 1
);

-- Persistent Sessions: Messages
CREATE TABLE IF NOT EXISTS session_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    timestamp REAL NOT NULL,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (session_id) REFERENCES active_sessions(session_id)
);

-- ============================================================
-- ENTERPRISE ANALYTICS
-- ============================================================

-- Usage Metrics & Metering
CREATE TABLE IF NOT EXISTS usage_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    workspace_id TEXT,
    metric_type TEXT NOT NULL,
    quantity REAL DEFAULT 0,
    timestamp REAL NOT NULL,
    cost REAL DEFAULT 0,
    metadata TEXT DEFAULT '{}'
);

-- Cost Rates Configuration
CREATE TABLE IF NOT EXISTS cost_rates (
    metric_type TEXT PRIMARY KEY,
    rate_per_unit REAL NOT NULL,
    updated_at REAL NOT NULL
);

-- ============================================================
-- ENTERPRISE & COMPLIANCE
-- ============================================================

-- Immutable Audit Trail (SOC2/HIPAA)
CREATE TABLE IF NOT EXISTS audit_events (
    id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    user_id TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    details TEXT,          -- Encrypted JSON
    ip_address TEXT,
    user_agent TEXT,
    previous_hash TEXT,
    hash TEXT UNIQUE NOT NULL,
    retention_date REAL
);

-- Real-time Sync Queue
CREATE TABLE IF NOT EXISTS sync_queue (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    message TEXT NOT NULL, -- JSON SyncMessage
    created_at REAL NOT NULL,
    synced_at REAL,
    retry_count INTEGER DEFAULT 0
);

-- Sync History (Conflict Resolution)
CREATE TABLE IF NOT EXISTS sync_history (
    id TEXT PRIMARY KEY,
    resource_type TEXT,
    resource_id TEXT,
    version INTEGER,
    data TEXT,
    updated_at REAL NOT NULL,
    device_id TEXT
);

-- Mobile Device Tokens
CREATE TABLE IF NOT EXISTS device_tokens (
    user_id TEXT NOT NULL,
    push_token TEXT PRIMARY KEY,
    device_name TEXT,
    os_version TEXT,
    registered_at REAL NOT NULL
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON workspace_members(user_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace ON workspace_members(workspace_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_user ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_timestamp ON user_activity(timestamp);

-- New Indexes for Hardened Deployment
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_user_pending ON sync_queue(user_id) WHERE synced_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_session_active ON active_sessions(user_id) WHERE is_active = 1;
CREATE INDEX IF NOT EXISTS idx_session_msgs ON session_messages(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_usage_workspace ON usage_metrics(workspace_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_broker_audit_time ON broker_audit_log(timestamp);
