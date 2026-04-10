"""
Database Manager - Connection and Session Management
Supports both SQLite (dev) and PostgreSQL (production)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and sessions"""
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._engine is None:
            self._init_engine()
    
    def _init_engine(self):
        """Initialize database engine based on environment"""
        # Check for PostgreSQL URL (production)
        postgres_url = os.getenv("DATABASE_URL")
        
        if postgres_url and postgres_url.startswith("postgresql"):
            logger.info("🐘 Using PostgreSQL database")
            self._engine = create_engine(
                postgres_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true"
            )
        else:
            # Fallback to SQLite (development)
            logger.info("📁 Using SQLite database (development mode)")
            sqlite_path = os.getenv("SQLITE_PATH", "./local_agent.db")
            self._engine = create_engine(
                f"sqlite:///{sqlite_path}",
                connect_args={"check_same_thread": False},
                echo=os.getenv("SQL_ECHO", "false").lower() == "true"
            )
        
        self._session_factory = sessionmaker(bind=self._engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self._session_factory()
    
    def get_engine(self):
        """Get the database engine"""
        return self._engine
    
    def create_tables(self):
        """Create all tables (development only)"""
        from .models import Base
        Base.metadata.create_all(self._engine)
        logger.info("✅ Database tables created")
    
    def drop_tables(self):
        """Drop all tables (development only)"""
        from .models import Base
        Base.metadata.drop_all(self._engine)
        logger.info("⚠️ Database tables dropped")
    
    def is_postgres(self) -> bool:
        """Check if using PostgreSQL"""
        return "postgresql" in str(self._engine.url)

# Singleton instance
db_manager = DatabaseManager()
