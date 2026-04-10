import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False


class MemoryEngine:
    """Unified memory engine with SQL events and semantic vector search using DuckDB VSS"""

    def __init__(self, db_path: str = "agent_memory.duckdb"):
        self.db_path = db_path
        self.conn = self._init_connection()
        self.embedder = self._init_embedder()
        self._init_tables()

    def _init_connection(self):
        if DUCKDB_AVAILABLE:
            config = {'hnsw_enable_experimental_persistence': 'true'}
            try:
                # Direct file connection (no global singleton)
                return duckdb.connect(self.db_path, config=config)
            except Exception:
                conn = duckdb.connect(self.db_path)
                try:
                    conn.execute("SET hnsw_enable_experimental_persistence = true;")
                except Exception: pass
                return conn
        else:
            import sqlite3
            return sqlite3.connect(self.db_path.replace(".duckdb", ".db"))

    def _init_embedder(self):
        if EMBEDDING_AVAILABLE and DUCKDB_AVAILABLE:
            try:
                # Lightweight local embeddings
                return SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                return None
        return None

    def _init_tables(self):
        if DUCKDB_AVAILABLE:
            # Install and Load VSS extension
            self.conn.execute("INSTALL vss; LOAD vss;")

            # Auto-increment using sequences
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS events_id_seq START 1")
            
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY DEFAULT nextval('events_id_seq'),
                    ts DOUBLE,
                    event_type VARCHAR,
                    payload VARCHAR,
                    embedding FLOAT[384]
                )
            """)

            # HNSW Cosine Similarity Index
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_embedding 
                ON events USING HNSW (embedding) 
                WITH (metric = 'cosine')
            """)
        else:
            # SQLite fallback (no vectors)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY,
                    ts REAL,
                    event_type TEXT,
                    payload TEXT
                )
            """)
        self.conn.commit()

    def remember(self, event_type: str, payload: Dict[str, Any], text_for_embedding: Optional[str] = None):
        """Store an event and generate semantic embedding if available."""
        if text_for_embedding is None:
            text_for_embedding = f"{event_type}: {json.dumps(payload)}"

        embedding = None
        if self.embedder:
            try:
                embedding = self.embedder.encode(text_for_embedding).tolist()
            except:
                embedding = None

        if DUCKDB_AVAILABLE and embedding is not None:
            self.conn.execute(
                "INSERT INTO events (ts, event_type, payload, embedding) VALUES (?, ?, ?, ?)",
                [time.time(), event_type, json.dumps(payload), embedding]
            )
        else:
            self.conn.execute(
                "INSERT INTO events (ts, event_type, payload) VALUES (?, ?, ?)",
                (time.time(), event_type, json.dumps(payload))
            )
        self.conn.commit()

    def recall_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic recall using vector similarity."""
        if not (DUCKDB_AVAILABLE and self.embedder):
            return [{"status": "semantic_search_disabled", "reason": "DuckDB or sentence-transformers not available"}]

        try:
            query_embedding = self.embedder.encode(query).tolist()
            results = self.conn.execute("""
                SELECT 
                    event_type,
                    payload,
                    array_cosine_similarity(embedding, ?::FLOAT[384]) as score
                FROM events
                ORDER BY score DESC
                LIMIT ?
            """, [query_embedding, top_k]).fetchall()

            return [
                {
                    "event_type": row[0],
                    "payload": json.loads(row[1]),
                    "score": float(row[2])
                }
                for row in results
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def recall_recent(self, limit: int = 10) -> List[Dict]:
        """Fetch the most recent events from memory."""
        rows = self.conn.execute(
            "SELECT event_type, payload, ts FROM events ORDER BY ts DESC LIMIT ?",
            [limit]
        ).fetchall()

        return [
            {"event_type": r[0], "payload": json.loads(r[1]), "timestamp": r[2]}
            for r in rows
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Return memory statistics."""
        count = self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        return {"total_events": count}

    def close(self):
        """Gracefully close the database connection."""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
