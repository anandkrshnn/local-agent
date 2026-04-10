# init_demo.py
import sqlite3
import bcrypt
from datetime import datetime

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def init_demo():
    conn = sqlite3.connect("local_agent.db")
    cursor = conn.cursor()
    
    # Ensure users table exists (simplified)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password_hash TEXT,
            full_name TEXT,
            is_active INTEGER DEFAULT 1,
            is_admin INTEGER DEFAULT 0,
            created_at REAL
        )
    """)
    
    # Create demo user
    pw_hash = hash_password("demo123")
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, is_active, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("demo", "demo@example.com", pw_hash, "Demo User", 1, 1, datetime.utcnow().timestamp()))
        print("✅ Demo user created")
    except sqlite3.IntegrityError:
        print("ℹ️ Demo user already exists")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_demo()
