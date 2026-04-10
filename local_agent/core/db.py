"""
Unified Database Layer - Central connection management
Supports SQLite (development) and PostgreSQL (production)
"""

import os
import sqlite3
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Central database manager for all connections.
    Automatically switches between SQLite and PostgreSQL based on DB_TYPE.
    """
    
    _instance = None
    _engine = None
    _session_factory = None
    _connection_pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.db_type = os.getenv("DB_TYPE", "sqlite").lower()
            self._init_engine()
    
    def _init_engine(self):
        """Initialize database engine based on DB_TYPE"""
        if self.db_type == "postgres":
            self._init_postgres()
        else:
            self._init_sqlite()
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection pool"""
        try:
            import psycopg2
            from psycopg2 import pool
            
            postgres_url = os.getenv("DATABASE_URL")
            if not postgres_url:
                raise ValueError("DATABASE_URL environment variable required for PostgreSQL")
            
            # Parse connection parameters
            result = urlparse(postgres_url)
            connection_params = {
                "database": result.path[1:],
                "user": result.username,
                "password": result.password,
                "host": result.hostname,
                "port": result.port or 5432
            }
            
            self._connection_pool = pool.SimpleConnectionPool(
                1, 20, **connection_params
            )
            logger.info(f"✅ PostgreSQL connection pool initialized: {result.hostname}:{result.port}")
            
        except ImportError:
            raise ImportError("psycopg2 required for PostgreSQL. Install with: pip install psycopg2-binary")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    def _init_sqlite(self):
        """Initialize SQLite with connection pooling"""
        sqlite_path = os.getenv("SQLITE_PATH", "./data/local_agent.db")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        
        # SQLite doesn't need a pool - we'll create connections on demand
        self._sqlite_path = sqlite_path
        logger.info(f"📁 SQLite database initialized: {sqlite_path}")
    
    @contextmanager
    def get_connection(self):
        """Get a database connection (context manager)"""
        if self.db_type == "postgres":
            conn = self._connection_pool.getconn()
            try:
                yield conn
            finally:
                self._connection_pool.putconn(conn)
        else:
            conn = sqlite3.connect(self._sqlite_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    @contextmanager
    def get_cursor(self):
        """Get a database cursor (context manager)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def execute(self, sql: str, params: tuple = None):
        """Execute SQL with automatic commit"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor
    
    def execute_many(self, sql: str, params_list: list):
        """Execute multiple SQL statements"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(sql, params_list)
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    def create_tables(self, schema_sql: str):
        """Create tables from schema with cross-database compatibility"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if self.db_type == "sqlite":
                    cursor.executescript(schema_sql)
                else:
                    # For Postgres, we need to split by semicolon for basic script execution
                    # More primitive than executescript, but works for our standard schema.sql
                    for statement in schema_sql.split(';'):
                        if statement.strip():
                            cursor.execute(statement)
                conn.commit()
                logger.info(f"✅ Database tables created ({self.db_type})")
            except Exception as e:
                logger.error(f"Failed to create tables: {e}")
                raise
    
    def backup(self, backup_path: str = None):
        """Create database backup"""
        if self.db_type == "postgres":
            self._backup_postgres(backup_path)
        else:
            self._backup_sqlite(backup_path)
    
    def _backup_postgres(self, backup_path: str = None):
        """Backup PostgreSQL database"""
        import subprocess
        from datetime import datetime
        
        if not backup_path:
            backup_path = f"./data/backups/postgres_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        postgres_url = os.getenv("DATABASE_URL")
        result = urlparse(postgres_url)
        
        cmd = [
            "pg_dump",
            "-h", result.hostname,
            "-p", str(result.port or 5432),
            "-U", result.username,
            "-d", result.path[1:],
            "-f", backup_path
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = result.password
        
        subprocess.run(cmd, env=env, check=True)
        logger.info(f"✅ PostgreSQL backup created: {backup_path}")
    
    def _backup_sqlite(self, backup_path: str = None):
        """Backup SQLite database"""
        import shutil
        from datetime import datetime
        
        if not backup_path:
            backup_path = f"./data/backups/sqlite_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(self._sqlite_path, backup_path)
        logger.info(f"✅ SQLite backup created: {backup_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            "db_type": self.db_type,
            "connected": True
        }
        
        if self.db_type == "postgres":
            stats["pool_size"] = self._connection_pool.minconn
            stats["max_connections"] = self._connection_pool.maxconn
        else:
            stats["path"] = self._sqlite_path
        
        return stats

# Singleton instance
db_manager = DatabaseManager()
