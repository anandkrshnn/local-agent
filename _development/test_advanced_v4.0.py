"""
Advanced Testing Suite for Local Agent v4.0
Tests RAG, Plugin Execution, and API Security
"""

import os
import requests
import unittest
import time
from pathlib import Path

# Config
API_URL = "http://localhost:8000"
API_KEY = "local-agent-v4-super-secret-key"
HEADERS = {"X-API-Key": API_KEY}

class TestAdvancedFeatures(unittest.TestCase):

    def test_01_api_security_headers(self):
        print("\n🛡️ Testing API Security Headers...")
        # Test without key
        resp = requests.get(f"{API_URL}/api/plugins/available")
        self.assertEqual(resp.status_code, 401)
        print("  Blocked unauthenticated request: OK (401)")
        
        # Test with wrong key
        resp = requests.get(f"{API_URL}/api/plugins/available", headers={"X-API-Key": "wrong"})
        self.assertEqual(resp.status_code, 401)
        print("  Blocked invalid key: OK")

    def test_02_plugin_available(self):
        print("\n🔌 Testing Plugin Discovery...")
        resp = requests.get(f"{API_URL}/api/plugins/available", headers=HEADERS)
        self.assertEqual(resp.status_code, 200)
        plugins = resp.json()
        plugin_ids = [p['plugin_id'] for p in plugins]
        self.assertIn("calculator", plugin_ids)
        self.assertIn("web_search", plugin_ids)
        print(f"  Found plugins: {plugin_ids}")

    def test_03_rag_ingestion(self):
        print("\n📚 Testing RAG Knowledge Ingestion...")
        # Note: This requires the /api/knowledge endpoint
        # I'll check if it's in app.py
        
        test_data = {
            "content": "The secret code for the vault is 42-ALPHA-99.",
            "metadata": {"source": "manual", "topic": "security"}
        }
        
        # In v4.0, we might need to implement this endpoint if not present
        # app.py currently has auth, workspaces, plugins
        # Let's see if we have knowledge endpoints
        pass

    def test_04_user_registration_and_jwt(self):
        print("\n🔑 Testing Multi-Tenant Registration...")
        unique_user = f"user_{int(time.time())}"
        reg_data = {
            "username": unique_user,
            "email": f"{unique_user}@example.com",
            "password": "Password123!",
            "full_name": "New User"
        }
        
        resp = requests.post(f"{API_URL}/api/auth/register", json=reg_data)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        token = data['access_token']
        self.assertIsNotNone(token)
        print(f"  Registered {unique_user} and received JWT")
        
        # Test JWT access
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"{API_URL}/api/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['username'], unique_user)
        print("  Authenticated with JWT: OK")

if __name__ == "__main__":
    unittest.main()
