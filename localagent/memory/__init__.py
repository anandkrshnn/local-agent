import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

import threading

# Global singleton for embedding model to prevent reloading weights on every vault switch
_EMBEDDER_CACHE = None
_EMBEDDER_LOCK = threading.Lock()

def get_embedder():
    """Thread-safe lazy initializer for the shared embedding model."""
    global _EMBEDDER_CACHE
    with _EMBEDDER_LOCK:
        if _EMBEDDER_CACHE is None:
            try:
                from sentence_transformers import SentenceTransformer
                # Lightweight local embeddings
                _EMBEDDER_CACHE = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception:
                return None
        return _EMBEDDER_CACHE

class MemoryEngine:
    """Unified memory engine with SQL events and semantic vector search using DuckDB VSS, featuring Vault Encryption."""

    def __init__(self, db_path: str = "agent_memory.duckdb", key_manager=None):
        self.db_path = db_path
        self.key_manager = key_manager
        self.conn = None # Lazy connected
        self.embedder = None # Self reference to shared cache
        self.initialized = False

    def _init_connection(self):
        try:
            import duckdb
        except ImportError:
            return None

        config = {'hnsw_enable_experimental_persistence': 'true'}
        try:
            return duckdb.connect(self.db_path, config=config)
        except Exception:
            conn = duckdb.connect(self.db_path)
            try:
                conn.execute("SET hnsw_enable_experimental_persistence = true;")
            except Exception: pass
            return conn

    def _init_embedder(self):
        return get_embedder()

    def _lazy_init(self, needs_vss: bool = False):
        """Perform real initialization only when needed."""
        if self.conn is None:
            self.conn = self._init_connection()
            if self.conn is None:
                raise ImportError("DuckDB not available")

        if not self.initialized:
            # Basic tables
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
            self.initialized = True

        if needs_vss:
            try:
                # Install and Load VSS extension (once per connection)
                self.conn.execute("INSTALL vss; LOAD vss;")
                # HNSW Cosine Similarity Index
                self.conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_embedding 
                    ON events USING HNSW (embedding) 
                    WITH (metric = 'cosine')
                """)
            except:
                pass

    def _encrypt_payload(self, data_str: str) -> str:
        """Internal helper to encrypt payload using key manager."""
        if self.key_manager and self.key_manager.is_encrypted():
            return self.key_manager.encrypt(data_str)
        return data_str

    def _decrypt_payload(self, data_str: str) -> str:
        """Internal helper to decrypt payload with graceful fallback."""
        if self.key_manager and self.key_manager.is_encrypted():
            try:
                return self.key_manager.decrypt(data_str)
            except Exception as e:
                return data_str
        return data_str

    def remember(self, event_type: str, payload: Dict[str, Any], text_for_embedding: Optional[str] = None):
        """Store an event and generate semantic embedding if available. Payload is encrypted at rest."""
        self._lazy_init(needs_vss=True)
        
        if text_for_embedding is None:
            text_for_embedding = f"{event_type}: {json.dumps(payload)}"

        # Lazy load embedder via shared cache
        if self.embedder is None:
            self.embedder = self._init_embedder()

        embedding = None
        if self.embedder:
            try:
                embedding = self.embedder.encode(text_for_embedding).tolist()
            except:
                embedding = None

        # Encrypt the payload before storage
        encrypted_payload = self._encrypt_payload(json.dumps(payload))

        if embedding is not None:
            self.conn.execute(
                "INSERT INTO events (ts, event_type, payload, embedding) VALUES (?, ?, ?, ?)",
                [time.time(), event_type, encrypted_payload, embedding]
            )
        else:
            self.conn.execute(
                "INSERT INTO events (ts, event_type, payload) VALUES (?, ?, ?)",
                (time.time(), event_type, encrypted_payload)
            )
        self.conn.commit()

    def recall_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        """Perform semantic recall using vector similarity. Results are decrypted on the fly."""
        self._lazy_init(needs_vss=True)
        
        # Lazy load embedder
        if self.embedder is None:
            self.embedder = self._init_embedder()

        if not self.embedder:
            return [{"status": "semantic_search_disabled", "reason": "Embedder not available"}]

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
                    "payload": json.loads(self._decrypt_payload(row[1])),
                    "score": float(row[2])
                }
                for row in results
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def recall_recent(self, limit: int = 10) -> List[Dict]:
        """Fetch the most recent events from memory. Results are decrypted on the fly."""
        self._lazy_init()
        rows = self.conn.execute(
            "SELECT event_type, payload, ts FROM events ORDER BY ts DESC LIMIT ?",
            [limit]
        ).fetchall()

        return [
            {"event_type": r[0], "payload": json.loads(self._decrypt_payload(r[1])), "timestamp": r[2]}
            for r in rows
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Return memory statistics."""
        if self.conn is None:
            return {"total_events": 0, "encryption_active": False, "status": "dormant"}
            
        count = self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        encryption_active = self.key_manager.is_encrypted() if self.key_manager else False
        return {
            "total_events": count,
            "encryption_active": encryption_active
        }

    def close(self):
        """Gracefully close the database connection."""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
            self.conn = None
            self.initialized = False

