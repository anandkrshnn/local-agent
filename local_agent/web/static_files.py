"""
Static file serving with PyInstaller support
"""

import sys
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

def get_base_path():
    """Get base path for static files (works with PyInstaller)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys._MEIPASS)
    else:
        # Running as script
        return Path(__file__).parent.parent.parent

def mount_frontend(app):
    """Mount React production build with PyInstaller support"""
    
    base_path = get_base_path()
    frontend_dist = base_path / "local_agent" / "web" / "static"
    
    # Also check alternative locations for development
    if not frontend_dist.exists():
        frontend_dist = Path("frontend/dist")
    
    if frontend_dist.exists() and (frontend_dist / "index.html").exists():
        logger.info(f"✅ Frontend build found at: {frontend_dist}")
        
        assets_path = frontend_dist / "assets"
        if assets_path.exists():
            app.mount("/assets", StaticFiles(directory=assets_path), name="assets")
        
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if full_path.startswith("api") or full_path.startswith("ws") or full_path.startswith("docs"):
                raise HTTPException(status_code=404)
            
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            
            raise HTTPException(status_code=404)
        
        @app.get("/")
        async def serve_root():
            index_path = frontend_dist / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"message": "Local Agent API", "docs": "/docs"}
    else:
        logger.warning("⚠️ Frontend build not found")
    
    return app
