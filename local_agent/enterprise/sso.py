"""
Enterprise SSO Integration
Supports OAuth2, LDAP, and SAML authentication
"""

import os
import jwt
import secrets
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import OAuth2AuthorizationCodeBearer
import httpx
import ldap3
from onelogin.saml2.auth import OneLogin_Saml2_Auth

# ============================================================
# OAuth2 Providers Configuration
# ============================================================

OAUTH_PROVIDERS = {
    "google": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "userinfo_url": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile"
    },
    "microsoft": {
        "client_id": os.getenv("MICROSOFT_CLIENT_ID"),
        "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET"),
        "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "userinfo_url": "https://graph.microsoft.com/v1.0/me",
        "scope": "openid email profile User.Read"
    },
    "github": {
        "client_id": os.getenv("GITHUB_CLIENT_ID"),
        "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
        "authorize_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "userinfo_url": "https://api.github.com/user",
        "scope": "read:user user:email"
    }
}

class SSOManager:
    """Manages SSO authentication for multiple providers"""
    
    def __init__(self):
        self.sessions = {}
    
    async def get_oauth_url(self, provider: str, redirect_uri: str) -> str:
        """Get OAuth2 authorization URL for provider"""
        if provider not in OAUTH_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")
        
        config = OAUTH_PROVIDERS[provider]
        state = secrets.token_urlsafe(32)
        
        # Store state for validation
        self.sessions[state] = {"provider": provider, "redirect_uri": redirect_uri}
        
        params = {
            "client_id": config["client_id"] or "",
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": config["scope"],
            "state": state
        }
        
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{config['authorize_url']}?{query}"
    
    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth2 callback and exchange code for user info"""
        session = self.sessions.get(state)
        if not session:
            raise HTTPException(400, "Invalid state")
        
        provider = session["provider"]
        config = OAUTH_PROVIDERS[provider]
        
        # Exchange code for token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                config["token_url"],
                data={
                    "client_id": config["client_id"],
                    "client_secret": config["client_secret"],
                    "code": code,
                    "redirect_uri": session["redirect_uri"],
                    "grant_type": "authorization_code"
                },
                headers={"Accept": "application/json"}
            )
            
            if token_response.status_code != 200:
                raise HTTPException(400, f"Token exchange failed: {token_response.text}")
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            # Get user info
            user_response = await client.get(
                config["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if user_response.status_code != 200:
                raise HTTPException(400, "Failed to get user info")
            
            user_data = user_response.json()
            
            # Normalize user data
            return self._normalize_user_data(provider, user_data, token_data)
    
    def _normalize_user_data(self, provider: str, user_data: Dict, token_data: Dict) -> Dict:
        """Normalize user data from different providers"""
        if provider == "google":
            return {
                "provider": provider,
                "provider_id": user_data.get("id") or user_data.get("sub"),
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "avatar": user_data.get("picture"),
                "access_token": token_data.get("access_token")
            }
        elif provider == "microsoft":
            return {
                "provider": provider,
                "provider_id": user_data.get("id"),
                "email": user_data.get("mail") or user_data.get("userPrincipalName"),
                "name": user_data.get("displayName"),
                "avatar": None,
                "access_token": token_data.get("access_token")
            }
        elif provider == "github":
            return {
                "provider": provider,
                "provider_id": str(user_data.get("id")),
                "email": user_data.get("email"),
                "name": user_data.get("name") or user_data.get("login"),
                "avatar": user_data.get("avatar_url"),
                "access_token": token_data.get("access_token")
            }
        return user_data
    
    def cleanup_session(self, state: str):
        """Clean up session state"""
        if state in self.sessions:
            del self.sessions[state]

    def list_providers(self) -> List[Dict]:
        """List available SSO providers and their status"""
        providers = []
        for name, config in OAUTH_PROVIDERS.items():
            providers.append({
                "name": name,
                "enabled": bool(config["client_id"] and config["client_secret"]),
                "authorize_url": config["authorize_url"]
            })
        return providers

# ============================================================
# LDAP Integration
# ============================================================

class LDAPManager:
    """LDAP/Active Directory authentication"""
    
    def __init__(self):
        self.server = os.getenv("LDAP_SERVER", "ldap://localhost")
        self.base_dn = os.getenv("LDAP_BASE_DN", "dc=example,dc=com")
        self.user_rdn = os.getenv("LDAP_USER_RDN", "uid")
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user against LDAP"""
        try:
            server = ldap3.Server(self.server, get_info=ldap3.ALL)
            user_dn = f"{self.user_rdn}={username},{self.base_dn}"
            
            conn = ldap3.Connection(server, user_dn, password, auto_bind=True)
            
            # Get user attributes
            conn.search(
                search_base=self.base_dn,
                search_filter=f"({self.user_rdn}={username})",
                attributes=['cn', 'mail', 'displayName']
            )
            
            if conn.entries:
                entry = conn.entries[0]
                return {
                    "username": username,
                    "email": str(entry.mail) if hasattr(entry, 'mail') else None,
                    "full_name": str(entry.displayName) if hasattr(entry, 'displayName') else str(entry.cn),
                    "source": "ldap"
                }
            
            conn.unbind()
            return None
            
        except Exception as e:
            print(f"LDAP authentication error: {e}")
            return None

# ============================================================
# SAML Integration
# ============================================================

class SAMLManager:
    """SAML 2.0 authentication for enterprise SSO"""
    
    def __init__(self):
        self.saml_settings = {
            "strict": True,
            "debug": False,
            "sp": {
                "entityId": os.getenv("SAML_SP_ENTITY_ID", "http://localhost:8000/saml/metadata"),
                "assertionConsumerService": {
                    "url": os.getenv("SAML_ACS_URL", "http://localhost:8000/saml/acs"),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                },
                "singleLogoutService": {
                    "url": os.getenv("SAML_SLO_URL", "http://localhost:8000/saml/logout"),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "NameIDFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
            },
            "idp": {
                "entityId": os.getenv("SAML_IDP_ENTITY_ID"),
                "singleSignOnService": {
                    "url": os.getenv("SAML_IDP_SSO_URL"),
                    "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                },
                "x509cert": os.getenv("SAML_IDP_CERT", "").replace("\\n", "\n")
            }
        }
    
    async def prepare_request(self, request: Request) -> Dict:
        """Prepare SAML request attributes"""
        return {
            'http_host': request.headers.get('host'),
            'server_port': request.url.port,
            'script_name': request.url.path,
            'get_data': request.query_params,
            'post_data': dict(await request.form()) if request.method == "POST" else {},
            'https': request.url.scheme == 'https'
        }
    
    async def authenticate(self, request: Request) -> Optional[Dict]:
        """Process SAML authentication"""
        auth = OneLogin_Saml2_Auth(await self.prepare_request(request), old_settings=self.saml_settings)
        
        if 'SAMLResponse' in request.query_params:
            auth.process_response()
            errors = auth.get_errors()
            
            if not errors:
                user_attrs = auth.get_attributes()
                return {
                    "email": user_attrs.get('email', [None])[0],
                    "name": user_attrs.get('displayName', [None])[0],
                    "source": "saml"
                }
        
        return None

sso_manager = SSOManager()
ldap_manager = LDAPManager()
saml_manager = SAMLManager()
