"""
Interactive API Documentation Portal
OpenAPI/Swagger with developer guides
"""

from fastapi import APIRouter, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from pathlib import Path
import json

def configure_documentation(app: FastAPI):
    """Configure interactive API documentation"""
    
    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Local Agent v4.0 API",
            version="4.0.0",
            description="""
            ## Local Agent v4.0 - Enterprise AI Platform
            
            ### Authentication
            Most endpoints require API key authentication via `X-API-Key` header or Bearer JWT.
            
            ### Rate Limits
            - 60 requests per minute for authenticated users
            - 10 requests per minute for unauthenticated
            
            ### Features
            - 🤖 Chat completions with RAG
            - 📚 Knowledge base management
            - 👥 Team collaboration
            - 🔌 Plugin ecosystem
            - 📊 Analytics & monitoring
            """,
            routes=app.routes,
        )
        
        # Add security scheme
        openapi_schema["components"]["securitySchemes"] = {
            "APIKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Swagger UI
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - API Documentation",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )
    
    # ReDoc
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
        )
    
    # Developer guides endpoint
    @app.get("/api/docs/guides")
    async def get_developer_guides():
        guides_dir = Path(__file__).parent.parent / "docs" / "guides"
        guides = []
        
        if guides_dir.exists():
            for md_file in guides_dir.glob("*.md"):
                with open(md_file) as f:
                    content = f.read()
                    guides.append({
                        "title": md_file.stem.replace("_", " ").title(),
                        "filename": md_file.name,
                        "content": content[:500] + "..." if len(content) > 500 else content
                    })
        
        return {"guides": guides}
    
    # API changelog
    @app.get("/api/docs/changelog")
    async def get_changelog():
        changelog_file = Path(__file__).parent.parent / "docs" / "CHANGELOG.md"
        if changelog_file.exists():
            with open(changelog_file) as f:
                content = f.read()
            return {"changelog": content}
        return {"changelog": "# Changelog\n\n## v4.0.0 - Initial Release"}
