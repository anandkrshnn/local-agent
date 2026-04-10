#!/usr/bin/env python3
"""
COMPLETE CROSS-PLATFORM TEST SUITE
Tests: Backend API, WebSocket, Sync Engine, Mobile Endpoints, Health Checks
"""

import sys
import asyncio
import json
import time
import requests
import websockets
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

class CrossPlatformTester:
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.start_time = time.time()
        self.token = None
        self.session_id = None
    
    def log_test(self, name: str, passed: bool, message: str = "", duration_ms: float = 0):
        status = "✅" if passed else "❌"
        self.results.append((name, passed, message))
        print(f"  {status} {name} ({duration_ms:.0f}ms)" if duration_ms else f"  {status} {name}")
        if message and not passed:
            print(f"     └─ {message[:100]}")
    
    def run_all_tests(self):
        print("=" * 70)
        print("🧪 LOCAL AGENT v4.0 - CROSS-PLATFORM TEST SUITE")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)
        
        # BACKEND API TESTS
        print("\n🖥️ BACKEND API TESTS")
        print("-" * 40)
        self.test_health_endpoint()
        self.test_status_endpoint()
        self.test_auth_login()
        if self.token:
            self.test_auth_me()
            self.test_chat_endpoint()
        
        # WEBSOCKET TESTS
        print("\n🔌 WEBSOCKET TESTS")
        print("-" * 40)
        try:
            asyncio.run(self.test_websocket_chat())
            asyncio.run(self.test_websocket_logs())
            asyncio.run(self.test_websocket_sync())
        except Exception as e:
            print(f"  ⚠️ WebSocket category skip: {e}")
        
        # ENTERPRISE TESTS
        print("\n🏢 ENTERPRISE TESTS")
        print("-" * 40)
        self.test_sso_providers()
        self.test_audit_endpoint()
        self.test_analytics_endpoint()
        
        # MOBILE ENDPOINT TESTS
        print("\n📱 MOBILE ENDPOINT TESTS")
        print("-" * 40)
        self.test_push_registration()
        self.test_sync_endpoint()
        
        # ADVANCED AI TESTS
        print("\n🧠 ADVANCED AI TESTS")
        print("-" * 40)
        self.test_rag_search()
        
        # INFRASTRUCTURE TESTS
        print("\n☁️ INFRASTRUCTURE TESTS")
        print("-" * 40)
        self.test_kubernetes_health()
        
        self.print_summary()
    
    def test_health_endpoint(self):
        start = time.time()
        try:
            resp = requests.get(f"{BASE_URL}/api/enterprise/health", timeout=5)
            passed = resp.status_code == 200
            self.log_test("Health Check", passed, duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Health Check", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_status_endpoint(self):
        start = time.time()
        try:
            resp = requests.get(f"{BASE_URL}/api/status", timeout=5)
            passed = resp.status_code == 200
            self.log_test("Status Endpoint", passed, duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Status Endpoint", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_auth_login(self):
        start = time.time()
        try:
            # Note: Using mock for verification if real auth not setup
            resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "demo@example.com", "password": "demo123"}, timeout=5)
            passed = resp.status_code == 200
            if passed:
                data = resp.json()
                self.token = data.get('access_token')
                self.session_id = data.get('user', {}).get('id')
            self.log_test("Auth Login", passed, duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Auth Login", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_auth_me(self):
        start = time.time()
        try:
            resp = requests.get(f"{BASE_URL}/api/auth/me", headers={"Authorization": f"Bearer {self.token}"}, timeout=5)
            self.log_test("Auth Me", resp.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("Auth Me", False)

    def test_chat_endpoint(self):
        start = time.time()
        try:
            resp = requests.post(f"{BASE_URL}/api/chat", headers={"Authorization": f"Bearer {self.token}"}, json={"message": "ping"}, timeout=10)
            self.log_test("Chat Endpoint", resp.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("Chat Endpoint", False)

    async def test_websocket_chat(self):
        start = time.time()
        try:
            async with websockets.connect(f"{WS_URL}/ws/chat/test_session") as ws:
                self.log_test("WebSocket Chat Connection", True, duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("WebSocket Chat Connection", False, str(e))

    async def test_websocket_logs(self):
        start = time.time()
        try:
            async with websockets.connect(f"{WS_URL}/ws/logs") as ws:
                self.log_test("WebSocket Logs Connection", True, duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("WebSocket Logs Connection", False, str(e))

    async def test_websocket_sync(self):
        start = time.time()
        try:
            async with websockets.connect(f"{WS_URL}/api/mobile/ws/test_user") as ws:
                self.log_test("WebSocket Sync Connection", True, duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("WebSocket Sync Connection", False, str(e))

    def test_sso_providers(self):
        start = time.time()
        try:
            resp = requests.get(f"{BASE_URL}/api/enterprise/sso/providers", timeout=5)
            self.log_test("SSO Providers", resp.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("SSO Providers", False)

    def test_audit_endpoint(self):
        start = time.time()
        try:
            resp = requests.get(f"{BASE_URL}/api/enterprise/compliance/audit?days=1", headers={"Authorization": f"Bearer {self.token}"}, timeout=5)
            self.log_test("Audit Endpoint", resp.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("Audit Endpoint", False)

    def test_analytics_endpoint(self):
        start = time.time()
        try:
            resp = requests.get(f"{BASE_URL}/api/enterprise/analytics/usage?workspace_id=default", headers={"Authorization": f"Bearer {self.token}"}, timeout=5)
            self.log_test("Analytics Endpoint", resp.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("Analytics Endpoint", False)

    def test_push_registration(self):
        start = time.time()
        try:
            resp = requests.post(f"{BASE_URL}/api/mobile/register-push", headers={"Authorization": f"Bearer {self.token}"}, json={"push_token": "test"}, timeout=5)
            self.log_test("Push Registration", resp.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("Push Registration", False)

    def test_sync_endpoint(self):
        start = time.time()
        try:
            resp = requests.post(f"{BASE_URL}/api/mobile/sync", headers={"Authorization": f"Bearer {self.token}"}, json={"messages": []}, timeout=5)
            self.log_test("Sync Endpoint", resp.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("Sync Endpoint", False)

    def test_rag_search(self):
        start = time.time()
        try:
            resp = requests.get(f"{BASE_URL}/api/ai/rag/search?q=test", timeout=5)
            self.log_test("RAG Search", resp.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("RAG Search", False)

    def test_kubernetes_health(self):
        start = time.time()
        try:
            live = requests.get(f"{BASE_URL}/api/enterprise/health", timeout=3)
            ready = requests.get(f"{BASE_URL}/api/enterprise/ready", timeout=3)
            self.log_test("K8s Health Probes", live.status_code == 200 and ready.status_code == 200, duration_ms=(time.time() - start) * 1000)
        except Exception:
            self.log_test("K8s Health Probes", False)

    def print_summary(self):
        print("\n" + "=" * 70)
        print("📊 CROSS-PLATFORM TEST SUMMARY")
        print("=" * 70)
        total = len(self.results)
        passed = sum(1 for _, p, _ in self.results if p)
        pass_rate = (passed/total)*100 if total > 0 else 0
        print(f"Pass Rate: {pass_rate:.1f}% ({passed}/{total})")
        if pass_rate >= 90:
            print("\n🎉 OUTSTANDING! Local Agent v4.0 is FULLY OPERATIONAL!")
        else:
            print("\n⚠️ Issues detected in some areas.")

if __name__ == "__main__":
    tester = CrossPlatformTester()
    tester.run_all_tests()
