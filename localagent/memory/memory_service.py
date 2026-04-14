from typing import Dict, Any, List
from localagent.memory.lancedb_store import LanceDBStore
from localagent.memory.promotion_pipeline import MemoryPromotionPipeline
from localagent.broker import LocalPermissionBroker

class MemoryService:
    def __init__(self, broker: LocalPermissionBroker, lancedb_path: str, duckdb_path: str, key_manager=None):
        self.lancedb_store = LanceDBStore(db_path=lancedb_path, key_manager=key_manager)
        self.promotion_pipeline = MemoryPromotionPipeline(self.lancedb_store)
        self.broker = broker
        self.key_manager = key_manager
        from localagent.memory import MemoryEngine
        self.legacy_memory = MemoryEngine(db_path=duckdb_path, key_manager=key_manager)

    def get_governed_context(self, user_query: str, session_context: Dict[str, Any]):
        """Governed retrieval: LPB check + Sensitivity filtering + LanceDB Search."""

        # 1. LPB retrieval-time authorization check
        perm = self.broker.request_permission(
            intent="read_memory",
            resource="semantic_memory",
            context=session_context
        )

        if not perm.get("granted", False):
            return {"memories": [], "reason": "access_denied_by_lpb"}

        # 2. Semantic retrieval from memory_items (LanceDB)
        # In a real system, we'd use vector search. For now, we fetch and filter.
        all_items = self.lancedb_store.get_memory_items()
        
        authorized_memories = []
        for item in all_items:
            # Governance Logic:
            # - High: Only if status == "approved"
            # - Medium/Low: Always if authorized by LPB
            if item.get("sensitivity") == "High" and item.get("status") != "approved":
                continue
                
            authorized_memories.append({
                "body": item["body"],
                "sensitivity": item["sensitivity"],
                "kind": item.get("memory_type"),
                "confidence": item["confidence"]
            })

        # 3. Fallback/Supplement with Hot Memory (DuckDB) for recent tool results
        hot_results = self.legacy_memory.recall_similar(user_query, top_k=3)
        for h in hot_results:
            if "error" in h or "status" in h: continue
            
            body = h.get("text") or ""
            if not body:
                payload = h.get("payload", {})
                body = payload.get("content") or payload.get("text") or str(payload)
                
            authorized_memories.append({
                "body": body,
                "sensitivity": "Low", # Default hot memory to Low sensitivity
                "kind": "recent_history",
                "confidence": h.get("score", 0.5)
            })

        return {
            "memories": authorized_memories[:7], # Limit context size
            "reason": "authorized",
            "retrieval_count": len(authorized_memories)
        }

    def refresh_hot_cache(self):
        """Rebuild DuckDB hot memory from approved LanceDB items."""
        if not self.legacy_memory: return
        
        # 1. Get approved items from LanceDB
        approved_items = self.lancedb_store.get_memory_items(status="approved")
        
        # 2. Clear current DuckDB state (if possible/needed, or just append)
        # Note: MemoryEngine.remember handles indexing automatically
        for item in approved_items:
            self.legacy_memory.remember(
                event_type="canonical_memory",
                payload={"body": item["body"], "kind": item.get("memory_type")},
                text_for_embedding=item["body"]
            )
        print(f"🔥 [MemoryService] Hot cache refreshed with {len(approved_items)} items.")

    def close(self):
        """Shutdown all memory engines."""
        if hasattr(self, 'legacy_memory') and self.legacy_memory:
            self.legacy_memory.close()
        if hasattr(self, 'lancedb_store') and self.lancedb_store:
            self.lancedb_store.close()
