#!/usr/bin/env python3
"""
Migration Script: SQLite to PostgreSQL
Transfers all data from local SQLite to production PostgreSQL
"""

import sqlite3
import psycopg2
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Configuration
SQLITE_PATH = os.getenv("SQLITE_PATH", "./local_agent.db")
POSTGRES_URL = os.getenv("DATABASE_URL")

def migrate_users(sqlite_conn, pg_conn):
    """Migrate users table"""
    print("📊 Migrating users...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM users")
    users = sqlite_cursor.fetchall()
    
    pg_cursor = pg_conn.cursor()
    for user in users:
        try:
            pg_cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, full_name, 
                                   avatar_url, is_active, is_verified, created_at, 
                                   last_login, settings)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, user)
        except Exception as e:
            print(f"  Error migrating user {user[1]}: {e}")
    
    pg_conn.commit()
    print(f"  ✅ Migrated {len(users)} users")

def migrate_workspaces(sqlite_conn, pg_conn):
    """Migrate workspaces table"""
    print("📊 Migrating workspaces...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM workspaces")
    workspaces = sqlite_cursor.fetchall()
    
    pg_cursor = pg_conn.cursor()
    for workspace in workspaces:
        try:
            pg_cursor.execute("""
                INSERT INTO workspaces (id, name, description, owner_id, settings, 
                                        created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, workspace)
        except Exception as e:
            print(f"  Error migrating workspace {workspace[1]}: {e}")
    
    pg_conn.commit()
    print(f"  ✅ Migrated {len(workspaces)} workspaces")

def migrate_messages(sqlite_conn, pg_conn):
    """Migrate messages table"""
    print("📊 Migrating messages...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM messages")
    messages = sqlite_cursor.fetchall()
    
    pg_cursor = pg_conn.cursor()
    for message in messages:
        try:
            pg_cursor.execute("""
                INSERT INTO messages (id, chat_id, user_id, role, content, 
                                      metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, message)
        except Exception as e:
            print(f"  Error migrating message {message[0]}: {e}")
    
    pg_conn.commit()
    print(f"  ✅ Migrated {len(messages)} messages")

def migrate_audit_logs(sqlite_conn, pg_conn):
    """Migrate audit logs"""
    print("📊 Migrating audit logs...")
    
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("SELECT * FROM audit_logs")
    logs = sqlite_cursor.fetchall()
    
    pg_cursor = pg_conn.cursor()
    for log in logs:
        try:
            pg_cursor.execute("""
                INSERT INTO audit_logs (id, user_id, action, resource_type, 
                                        resource_id, details, ip_address, 
                                        user_agent, previous_hash, hash, 
                                        created_at, retention_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, log)
        except Exception as e:
            print(f"  Error migrating log: {e}")
    
    pg_conn.commit()
    print(f"  ✅ Migrated {len(logs)} audit logs")

def main():
    print("=" * 60)
    print("🐘 SQLite to PostgreSQL Migration")
    print("=" * 60)
    
    # Check if PostgreSQL is configured
    if not POSTGRES_URL:
        print("❌ DATABASE_URL not set in environment")
        print("   Please set: DATABASE_URL=postgresql://user:pass@localhost/local_agent")
        return
    
    print(f"📁 Source: SQLite ({SQLITE_PATH})")
    print(f"🐘 Target: PostgreSQL")
    print("-" * 40)
    
    try:
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(SQLITE_PATH)
        print("✅ Connected to SQLite")
        
        # Connect to PostgreSQL
        pg_conn = psycopg2.connect(POSTGRES_URL)
        print("✅ Connected to PostgreSQL")
        
        # Run migrations
        migrate_users(sqlite_conn, pg_conn)
        migrate_workspaces(sqlite_conn, pg_conn)
        migrate_messages(sqlite_conn, pg_conn)
        migrate_audit_logs(sqlite_conn, pg_conn)
        
        print("-" * 40)
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        if sqlite_conn:
            sqlite_conn.close()
        if pg_conn:
            pg_conn.close()

if __name__ == "__main__":
    main()
