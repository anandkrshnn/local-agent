"""
Export/Import system for backups and migration
Exports sessions, memory, and configuration
"""

import json
import zipfile
import shutil
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from local_agent.core.db import db_manager

logger = logging.getLogger(__name__)

class ExportImportManager:
    """Manages backup and restore of consolidated agent data"""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        # Focus on unified data master
        self.main_db = Path(db_manager._sqlite_path)
        self.memory_db = self.data_dir / "agent_memory.duckdb"
        self.sandbox_dir = self.data_dir / "sandbox"
    
    def export_all(self, output_path: str = None) -> str:
        """Export unified database and memory to a zip file"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"local_agent_hardened_backup_{timestamp}.zip"
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Copy unified data master
            if self.main_db.exists():
                shutil.copy2(self.main_db, tmp_path / "local_agent.db")
            
            # Copy memory database
            if self.memory_db.exists():
                shutil.copy2(self.memory_db, tmp_path / "agent_memory.duckdb")
            
            # Export metadata
            metadata = {
                "export_date": datetime.now().isoformat(),
                "version": "4.0.0-hardened",
                "stats": self._get_stats()
            }
            with open(tmp_path / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create zip
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in tmp_path.iterdir():
                    zf.write(file_path, file_path.name)
        
        return output_path
    
    def import_all(self, zip_path: str) -> Dict[str, Any]:
        """Import agent data from a consolidated backup"""
        results = {"success": False, "imported_files": [], "errors": []}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(tmp_path)
            
            # Restore unified DB
            backup_db = tmp_path / "local_agent.db"
            if backup_db.exists():
                if self.main_db.exists():
                    shutil.copy2(self.main_db, self.main_db.with_suffix(".bak"))
                shutil.copy2(backup_db, self.main_db)
                results["imported_files"].append("local_agent.db")
            
            results["success"] = True
        return results
    
    def _get_stats(self) -> Dict:
        """Get stats from unified tables"""
        stats = {}
        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM active_sessions")
                stats["sessions_count"] = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COUNT(*) FROM session_messages")
                stats["messages_count"] = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COUNT(*) FROM audit_events")
                stats["audit_events_count"] = cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Failed to get export stats: {e}")
        return stats
