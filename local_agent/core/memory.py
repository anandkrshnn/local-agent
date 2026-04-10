"""Vector Memory with DuckDB VSS for Semantic Search"""

import json
import time
import uuid
from typing import List, Dict, Any, Optional
import numpy as np

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    raise ImportError("DuckDB required for vector memory. Install: pip install duckdb")

class VectorMemory:
    """Semantic memory using DuckDB VSS extension"""
    
    def __init__(self, db_path: str = "agent_memory.duckdb", embedding_dim: int = 384):
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self.conn = duckdb.connect(db_path)
        self._init_extensions()
        self._init_tables()
    
    def _init_extensions(self):
        """Load VSS extension for vector similarity search"""
        try:
            self.conn.execute("INSTALL vss;")
            self.conn.execute("LOAD vss;")
        except Exception as e:
            print(f"⚠️ VSS extension not available: {e}")
            print("   Install: duckdb -c 'INSTALL vss;'")
    
    def _init_tables(self):
        """Create memory tables with vector support"""
        # Create sequence for auto-incrementing ID (Antigravity Fix)
        try:
            self.conn.execute("CREATE SEQUENCE IF NOT EXISTS event_id_seq START 1")
        except Exception:
            pass

        # Event memory table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS event_memory (
                id INTEGER PRIMARY KEY DEFAULT nextval('event_id_seq'),
                timestamp DOUBLE,
                event_type VARCHAR,
                event_data VARCHAR,
                embedding FLOAT[{dim}],
                outcome VARCHAR,
                trace_id VARCHAR
            )
        """.format(dim=self.embedding_dim))
        
        # Create HNSW index for fast similarity search
        try:
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_event_embedding 
                ON event_memory USING HNSW (embedding)
            """)
        except Exception:
            pass  # Index might already exist or VSS not fully loaded
        
        # Create regular indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON event_memory(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON event_memory(event_type)")
        
        self.conn.commit()
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using a local model or fallback"""
        # For now, use a simple TF-IDF style fallback
        # In production, integrate with sentence-transformers or Ollama embeddings
        import hashlib
        hash_val = hashlib.md5(text.encode()).hexdigest()
        np.random.seed(int(hash_val[:8], 16))
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()
    
    def store(self, event_type: str, event_data: Dict, trace_id: str = None, text: str = None) -> int:
        """Store an event with its embedding for semantic search"""
        if text is None:
            text = json.dumps(event_data)
        
        embedding = self._generate_embedding(text)
        trace_id = trace_id or str(uuid.uuid4())
        
        result = self.conn.execute("""
            INSERT INTO event_memory (timestamp, event_type, event_data, embedding, outcome, trace_id)
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING id
        """, [time.time(), event_type, json.dumps(event_data), embedding, "stored", trace_id])
        
        self.conn.commit()
        return result.fetchone()[0]
    
    def search_semantic(self, query: str, limit: int = 5) -> List[Dict]:
        """Semantic search using vector similarity"""
        query_embedding = self._generate_embedding(query)
        
        try:
            # Use VSS for similarity search
            results = self.conn.execute("""
                SELECT 
                    id,
                    event_type,
                    event_data,
                    timestamp,
                    array_distance(embedding, ?::FLOAT[{dim}]) as distance
                FROM event_memory
                ORDER BY distance ASC
                LIMIT ?
            """.format(dim=self.embedding_dim), [query_embedding, limit]).fetchall()
            
            return [{
                "id": r[0],
                "type": r[1],
                "data": json.loads(r[2]),
                "timestamp": r[3],
                "similarity": 1 - r[4]  # Convert distance to similarity
            } for r in results]
        except Exception as e:
            # Fallback to keyword search if VSS fails
            return self.search_keyword(query, limit)
    
    def search_keyword(self, query: str, limit: int = 5) -> List[Dict]:
        """Fallback keyword search"""
        results = self.conn.execute("""
            SELECT id, event_type, event_data, timestamp
            FROM event_memory
            WHERE event_data LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, [f'%{query}%', limit]).fetchall()
        
        return [{
            "id": r[0],
            "type": r[1],
            "data": json.loads(r[2]),
            "timestamp": r[3],
            "similarity": None
        } for r in results]
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """Get most recent events"""
        results = self.conn.execute("""
            SELECT id, event_type, event_data, timestamp
            FROM event_memory
            ORDER BY timestamp DESC
            LIMIT ?
        """, [limit]).fetchall()
        
        return [{
            "id": r[0],
            "type": r[1],
            "data": json.loads(r[2]),
            "timestamp": r[3]
        } for r in results]
    
    def get_by_type(self, event_type: str, limit: int = 10) -> List[Dict]:
        """Get events by type"""
        results = self.conn.execute("""
            SELECT id, event_type, event_data, timestamp
            FROM event_memory
            WHERE event_type = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, [event_type, limit]).fetchall()
        
        return [{
            "id": r[0],
            "type": r[1],
            "data": json.loads(r[2]),
            "timestamp": r[3]
        } for r in results]
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        result = self.conn.execute("SELECT COUNT(*) FROM event_memory").fetchone()
        total = result[0]
        
        result = self.conn.execute("""
            SELECT event_type, COUNT(*) as cnt 
            FROM event_memory 
            GROUP BY event_type 
            ORDER BY cnt DESC 
            LIMIT 5
        """).fetchall()
        
        return {
            "total_events": total,
            "event_types": [{"type": r[0], "count": r[1]} for r in result],
            "embedding_dim": self.embedding_dim
        }
    
    def clear(self):
        """Clear all memory (for testing)"""
        self.conn.execute("DELETE FROM event_memory")
        self.conn.commit()
