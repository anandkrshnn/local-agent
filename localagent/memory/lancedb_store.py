from pathlib import Path
import lancedb
import pyarrow as pa
from datetime import datetime
import uuid
import json
from typing import Dict, Any, List

class LanceDBStore:
    """Immutable episodic log using LanceDB as canonical storage, featuring Vault Encryption."""

    def __init__(self, db_path: str, key_manager=None):
        self.db_path = Path(db_path).resolve()
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.key_manager = key_manager
        
        self.db = None
        self.episodes = None

    def _lazy_init(self):
        if self.db is not None:
            return

        import lancedb
        import pyarrow as pa
        self.db = lancedb.connect(str(self.db_path))

        # 1. Episodes Table (Canonical Event Log)
        if "episodes" not in self.db.table_names():
            schema = pa.schema([
                ("episode_id", pa.string()),
                ("session_id", pa.string()),
                ("user_id", pa.string()),
                ("event_ts", pa.timestamp('us')),
                ("event_type", pa.string()),
                ("actor", pa.string()),
                ("content_text", pa.string()),
                ("content_json", pa.string()),      # JSON serialized as string
                ("tool_name", pa.string()),
                ("resource_ref", pa.string()),
                ("sensitivity_label", pa.string()),
                ("provenance", pa.string()),        # JSON string for provenance
                ("created_at", pa.timestamp('us')),
            ])
            self.db.create_table("episodes", schema=schema)
        self.episodes = self.db.open_table("episodes")

        # 2. Memory Items Table (Governed Fact Store)
        if "memory_items" not in self.db.table_names():
            schema = pa.schema([
                ("memory_id", pa.string()),
                ("body", pa.string()),
                ("memory_type", pa.string()),      # preference, fact, task, secret
                ("sensitivity", pa.string()),      # High, Medium, Low
                ("confidence", pa.float32()),
                ("status", pa.string()),           # candidate, approved, rejected
                ("source_episode_id", pa.string()),
                ("vector", pa.list_(pa.float32(), 384)),
                ("metadata_json", pa.string()),
                ("created_at", pa.timestamp('us')),
            ])
            self.db.create_table("memory_items", schema=schema)
        self.memory_items = self.db.open_table("memory_items")

    def _encrypt(self, data_str: str) -> str:
        if self.key_manager and self.key_manager.is_encrypted() and data_str:
            return self.key_manager.encrypt(data_str)
        return data_str

    def _decrypt(self, data_str: str) -> str:
        if self.key_manager and self.key_manager.is_encrypted() and data_str:
            try:
                return self.key_manager.decrypt(data_str)
            except:
                return data_str
        return data_str

    def append_episode(self, data: Dict[str, Any]) -> str:
        """Append one immutable event to the episodic log. Sensitive fields are encrypted."""
        self._lazy_init()
        episode_id = str(uuid.uuid4())

        record = {
            "episode_id": episode_id,
            "session_id": data.get("session_id", "default"),
            "user_id": data.get("user_id", "local_user"),
            "event_ts": datetime.utcnow(),
            "event_type": data.get("event_type", "unknown"),
            "actor": data.get("actor", "user"),
            "content_text": self._encrypt(data.get("content_text", "")),
            "content_json": self._encrypt(data.get("content_json", "{}")),
            "tool_name": data.get("tool_name"),
            "resource_ref": data.get("resource_ref"),
            "sensitivity_label": data.get("sensitivity_label", "public"),
            "provenance": data.get("provenance", "{}"),
            "created_at": datetime.utcnow(),
        }

        self.episodes.add([record])
        return episode_id

    def promote_memory(self, item: Dict[str, Any], vector: List[float]):
        """Store a distilled memory item in LanceDB with vector embedding."""
        self._lazy_init()
        
        record = {
            "memory_id": item.get("memory_id", str(uuid.uuid4())),
            "body": self._encrypt(item.get("body", "")),
            "memory_type": item.get("memory_type", "fact"),
            "sensitivity": item.get("sensitivity", "Medium"),
            "confidence": float(item.get("confidence", 0.5)),
            "status": item.get("status", "candidate"),
            "source_episode_id": item.get("source_episode_id", ""),
            "vector": vector,
            "metadata_json": self._encrypt(json.dumps(item.get("metadata", {}))),
            "created_at": datetime.utcnow(),
        }
        
        self.memory_items.add([record])

    def get_memory_items(self, status: str = None) -> List[Dict]:
        """Fetch memory items and decrypt them."""
        self._lazy_init()
        query = self.memory_items.search()
        if status:
            results = query.where(f"status = '{status}'").to_list()
        else:
            results = query.to_list()
            
        for r in results:
            r["body"] = self._decrypt(r.get("body", ""))
            r["metadata"] = json.loads(self._decrypt(r.get("metadata_json", "{}")))
        return results

    def update_memory_status(self, memory_id: str, new_status: str):
        """Update the status of a memory item (e.g. approve or reject)."""
        self._lazy_init()
        self.memory_items.update(
            where=f"memory_id = '{memory_id}'",
            values={"status": new_status}
        )

    def delete_memory_item(self, memory_id: str):
        """Permanently forget a memory item."""
        self._lazy_init()
        self.memory_items.delete(f"memory_id = '{memory_id}'")

    def get_recent_episodes(self, limit: int = 20) -> List[Dict]:
        """Fetch recent episodes and decrypt if needed."""
        self._lazy_init()
        results = self.episodes.search().limit(limit).to_list()
        for r in results:
            r["content_text"] = self._decrypt(r.get("content_text", ""))
            r["content_json"] = self._decrypt(r.get("content_json", "{}"))
        return results

    def close(self):
        """Gracefully release the LanceDB connection."""
        self.episodes = None
        self.memory_items = None
        self.db = None
