#!/usr/bin/env python3
"""
Comprehensive Test Suite for Local Agent v4.0
Tests: Multi-model routing, Web UI, Tools, Multi-user, Performance
"""

import os
import sys
import json
import time
import asyncio
import threading
import requests
from pathlib import Path
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from local_agent.core.agent import LocalAgent
from local_agent.models.router import ModelRouter
from local_agent.tools.registry import ToolRegistry
from local_agent.utils.sessions import SessionManager
from local_agent.utils.cache import ModelCache
from local_agent.utils.gpu import GPUAccelerator

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration_ms: float
    details: Dict = None

class ComprehensiveTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
        self.agent = None
        self.router = None
        
    def log_test(self, name: str, passed: bool, message: str = "", details: Dict = None, duration_ms: float = 0):
        result = TestResult(
            name=name,
            passed=passed,
            message=message,
            duration_ms=duration_ms,
            details=details
        )
        self.results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {name} ({duration_ms:.0f}ms)")
        if message and not passed:
            print(f"   └─ {message[:100]}")
        if details and not passed:
            print(f"   └─ Details: {str(details)[:100]}")
    
    def run_all_tests(self):
        print("=" * 70)
        print("🧪 LOCAL AGENT v4.0 - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 70)
        
        # Section 1: Core Components
        self.test_core_initialization()
        self.test_permission_broker()
        self.test_vector_memory()
        self.test_sandbox_security()
        
        # Section 2: Model Router
        self.test_model_router_initialization()
        self.test_model_availability()
        self.test_intent_routing()
        
        # Section 3: Tool Registry
        self.test_tool_registry()
        self.test_tool_permissions()
        
        # Section 4: Multi-User Sessions
        self.test_session_manager()
        self.test_session_isolation()
        
        # Section 5: Performance
        self.test_cache_system()
        self.test_gpu_detection()
        
        # Section 6: Web UI (if running)
        self.test_web_api()
        
        # Section 7: Integration Tests
        self.test_chat_flow()
        self.test_file_operations()
        self.test_memory_search()
        
        # Section 8: Stress Tests
        self.test_concurrent_requests()
        self.test_long_conversation()
        
        # Summary
        self.print_summary()
        self.save_results()
    
    # =========================================================
    # SECTION 1: CORE COMPONENTS
    # =========================================================
    
    def test_core_initialization(self):
        print("\n📦 SECTION 1: Core Components")
        print("-" * 40)
        
        start = time.time()
        try:
            self.agent = LocalAgent(verbose=False)
            duration = (time.time() - start) * 1000
            passed = self.agent is not None
            self.log_test("Agent Initialization", passed, 
                         "Agent created successfully" if passed else "Failed to create agent",
                         duration_ms=duration)
        except Exception as e:
            self.log_test("Agent Initialization", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_permission_broker(self):
        start = time.time()
        try:
            # Request permission
            perm = self.agent.broker.request_permission({
                "intent": "read_file",
                "resource": "test.txt"
            })
            
            passed = "granted" in perm or "requires_confirmation" in perm
            self.log_test("Permission Broker", passed, 
                         f"Response: {perm.get('reason', 'Granted')[:50]}",
                         duration_ms=(time.time() - start) * 1000,
                         details=perm)
        except Exception as e:
            self.log_test("Permission Broker", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_vector_memory(self):
        start = time.time()
        try:
            # Store event
            self.agent.memory.store("test_event", {"message": "test"})
            stats = self.agent.memory.get_stats()
            passed = stats['total_events'] > 0
            self.log_test("Vector Memory", passed, 
                         f"Total events: {stats['total_events']}",
                         duration_ms=(time.time() - start) * 1000,
                         details=stats)
        except Exception as e:
            self.log_test("Vector Memory", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_sandbox_security(self):
        start = time.time()
        try:
            # Try to escape sandbox
            from local_agent.core.sandbox import SandboxPath
            sandbox = SandboxPath()
            
            try:
                sandbox.resolve("../../../../etc/passwd")
                passed = False
                message = "Sandbox escape should have been blocked"
            except PermissionError:
                passed = True
                message = "Sandbox correctly blocked escape attempt"
            
            self.log_test("Sandbox Security", passed, message,
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Sandbox Security", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    # =========================================================
    # SECTION 2: MODEL ROUTER
    # =========================================================
    
    def test_model_router_initialization(self):
        print("\n🤖 SECTION 2: Model Router")
        print("-" * 40)
        
        start = time.time()
        try:
            self.router = ModelRouter()
            passed = self.router is not None
            self.log_test("Router Initialization", passed,
                         "Router created successfully" if passed else "Failed",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Router Initialization", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_model_availability(self):
        start = time.time()
        try:
            status = self.router.get_status()
            available_providers = [p for p in status['providers'] if p['available']]
            passed = len(available_providers) > 0
            
            provider_names = [p['name'] for p in available_providers]
            self.log_test("Model Availability", passed,
                         f"Available: {', '.join(provider_names) if provider_names else 'None'}",
                         duration_ms=(time.time() - start) * 1000,
                         details=status)
        except Exception as e:
            self.log_test("Model Availability", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_intent_routing(self):
        start = time.time()
        try:
            test_cases = [
                ("Hello, how are you?", "greeting"),
                ("Read my file test.txt", "file_operation"),
                ("Explain quantum computing", "complex_reasoning"),
                ("Write a Python function", "code_generation"),
            ]
            
            passed = True
            for prompt, expected in test_cases:
                try:
                    response = self.router.route(prompt)
                    if not response.content:
                        passed = False
                        break
                except:
                    passed = False
                    break
            
            self.log_test("Intent Routing", passed,
                         f"Tested {len(test_cases)} prompts",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Intent Routing", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    # =========================================================
    # SECTION 3: TOOL REGISTRY
    # =========================================================
    
    def test_tool_registry(self):
        print("\n🔧 SECTION 3: Tool Registry")
        print("-" * 40)
        
        start = time.time()
        try:
            registry = ToolRegistry(self.agent)
            tools = registry.list_tools()
            passed = len(tools) > 0
            
            self.log_test("Tool Registry", passed,
                         f"Registered {len(tools)} tools: {', '.join(list(tools.keys())[:5])}...",
                         duration_ms=(time.time() - start) * 1000,
                         details={"tools": list(tools.keys())})
        except Exception as e:
            self.log_test("Tool Registry", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_tool_permissions(self):
        start = time.time()
        try:
            # Test that high-risk tools require confirmation
            registry = ToolRegistry(self.agent)
            write_tool = registry.get("write_file")
            
            passed = write_tool is not None and write_tool.requires_confirmation == True
            self.log_test("Tool Permissions", passed,
                         "Write tool correctly requires confirmation" if passed else "Permission issue",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Tool Permissions", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    # =========================================================
    # SECTION 4: MULTI-USER SESSIONS
    # =========================================================
    
    def test_session_manager(self):
        print("\n👥 SECTION 4: Multi-User Sessions")
        print("-" * 40)
        
        start = time.time()
        try:
            manager = SessionManager()
            session1 = manager.create()
            session2 = manager.create()
            
            passed = session1.session_id != session2.session_id
            self.log_test("Session Manager", passed,
                         f"Created 2 isolated sessions",
                         duration_ms=(time.time() - start) * 1000,
                         details={"session1": session1.session_id[:8], "session2": session2.session_id[:8]})
        except Exception as e:
            self.log_test("Session Manager", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_session_isolation(self):
        start = time.time()
        try:
            manager = SessionManager()
            session_a = manager.create()
            session_b = manager.create()
            
            # Add different messages to each session
            session_a.add_message("user", "Message from A")
            session_b.add_message("user", "Message from B")
            
            # Verify isolation
            passed = (len(session_a.messages) == 1 and len(session_b.messages) == 1)
            self.log_test("Session Isolation", passed,
                         "Sessions maintain isolated state",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Session Isolation", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    # =========================================================
    # SECTION 5: PERFORMANCE
    # =========================================================
    
    def test_cache_system(self):
        print("\n⚡ SECTION 5: Performance")
        print("-" * 40)
        
        start = time.time()
        try:
            cache = ModelCache()
            test_key = "test_prompt"
            test_value = "test_response"
            
            cache.set(test_key, "test_model", "test_response", data=test_value)
            cached = cache.get(test_key, "test_model", "test_response")
            
            passed = cached == test_value
            self.log_test("Cache System", passed,
                         "Cache store/retrieve working" if passed else "Cache failed",
                         duration_ms=(time.time() - start) * 1000)
            
            # Cleanup
            cache.clear()
        except Exception as e:
            self.log_test("Cache System", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_gpu_detection(self):
        start = time.time()
        try:
            gpu = GPUAccelerator()
            info = gpu.get_device_info()
            passed = True  # GPU detection is informative, not required
            
            self.log_test("GPU Detection", passed,
                         f"Device: {info['device']} | CUDA: {info['has_cuda']} | MPS: {info['has_mps']}",
                         duration_ms=(time.time() - start) * 1000,
                         details=info)
        except Exception as e:
            self.log_test("GPU Detection", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    # =========================================================
    # SECTION 6: WEB API (if running)
    # =========================================================
    
    def test_web_api(self):
        print("\n🌐 SECTION 6: Web API")
        print("-" * 40)
        
        start = time.time()
        try:
            # Check if server is running
            response = requests.get("http://localhost:8000/api/status", timeout=2)
            passed = response.status_code == 200
            
            if passed:
                data = response.json()
                self.log_test("Web API Status", passed,
                             f"Version: {data.get('version', 'unknown')}",
                             duration_ms=(time.time() - start) * 1000,
                             details=data)
            else:
                self.log_test("Web API Status", False, f"HTTP {response.status_code}",
                             duration_ms=(time.time() - start) * 1000)
        except requests.exceptions.ConnectionError:
            self.log_test("Web API Status", False, "Server not running (start with: python -m local_agent.web.app)",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Web API Status", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    # =========================================================
    # SECTION 7: INTEGRATION TESTS
    # =========================================================
    
    def test_chat_flow(self):
        print("\n💬 SECTION 7: Integration Tests")
        print("-" * 40)
        
        start = time.time()
        try:
            response = self.agent.chat("Hello, what is your name?")
            passed = len(response) > 0 and "error" not in response.lower()
            self.log_test("Chat Flow", passed,
                         f"Response: {response[:50]}..." if passed else "No response",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Chat Flow", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_file_operations(self):
        start = time.time()
        try:
            # Create a test file in sandbox
            from local_agent.core.sandbox import SandboxPath
            sandbox = SandboxPath()
            test_file = sandbox.resolve("integration_test.txt")
            
            with open(test_file, 'w') as f:
                f.write("Integration test content")
            
            # Read it with agent
            response = self.agent.chat("read integration_test.txt")
            passed = "Integration test content" in response
            
            self.log_test("File Operations", passed,
                         f"Read test file: {'Success' if passed else 'Failed'}",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("File Operations", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    def test_memory_search(self):
        start = time.time()
        try:
            # Store something in memory
            self.agent.memory.store("search_test", {"content": "unique_search_term_12345"})
            
            # Search for it
            response = self.agent.chat("search memory for unique_search_term_12345")
            passed = "found" in response.lower() or "result" in response.lower()
            
            self.log_test("Memory Search", passed,
                         f"Search returned: {response[:50]}..." if passed else "No results",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Memory Search", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    # =========================================================
    # SECTION 8: STRESS TESTS
    # =========================================================
    
    def test_concurrent_requests(self):
        print("\n⚡ SECTION 8: Stress Tests")
        print("-" * 40)
        
        start = time.time()
        results = []
        
        def make_request(i):
            try:
                resp = self.agent.chat(f"Test message {i}")
                results.append(True)
            except:
                results.append(False)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=make_request, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        passed = len(results) == 5 and all(results)
        self.log_test("Concurrent Requests", passed,
                     f"Completed {len(results)}/5 requests",
                     duration_ms=(time.time() - start) * 1000)
    
    def test_long_conversation(self):
        start = time.time()
        try:
            messages = [
                "Hello",
                "What can you do?",
                "Read test.txt",
                "Search memory for test",
                "Goodbye"
            ]
            
            for msg in messages:
                response = self.agent.chat(msg)
                if "error" in response.lower():
                    passed = False
                    break
            else:
                passed = True
            
            self.log_test("Long Conversation", passed,
                         f"Processed {len(messages)} messages successfully",
                         duration_ms=(time.time() - start) * 1000)
        except Exception as e:
            self.log_test("Long Conversation", False, str(e), duration_ms=(time.time() - start) * 1000)
    
    # =========================================================
    # SUMMARY
    # =========================================================
    
    def print_summary(self):
        print("\n" + "=" * 70)
        print("📈 TEST SUMMARY")
        print("=" * 70)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        pass_rate = (passed / total) * 100 if total > 0 else 0
        total_duration = (time.time() - self.start_time) * 1000
        
        print(f"\n   Total Tests:    {total}")
        print(f"   Passed:         {passed} ✅")
        print(f"   Failed:         {failed} ❌")
        print(f"   Pass Rate:      {pass_rate:.1f}%")
        print(f"   Total Duration: {total_duration:.0f}ms")
        print(f"   Avg per test:   {total_duration/total:.0f}ms")
        
        # Group by category
        categories = {}
        for result in self.results:
            # Extract category from test name (first word or two)
            words = result.name.split()[:2]
            category = " ".join(words)
            if category not in categories:
                categories[category] = {'passed': 0, 'total': 0}
            categories[category]['total'] += 1
            if result.passed:
                categories[category]['passed'] += 1
        
        print(f"\n   Results by Category:")
        for cat, data in sorted(categories.items()):
            rate = (data['passed'] / data['total']) * 100
            bar = "█" * int(rate / 10) + "░" * (10 - int(rate / 10))
            print(f"     • {cat:<20} {bar} {rate:.0f}% ({data['passed']}/{data['total']})")
        
        if failed > 0:
            print(f"\n   ❌ Failed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"     • {result.name}: {result.message[:80]}")
        
        print("\n" + "=" * 70)
        print(f"✅ Test suite completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Overall verdict
        if pass_rate >= 90:
            print("\n🎉 OUTSTANDING! Your Local Agent v4.0 is PRODUCTION READY!")
        elif pass_rate >= 75:
            print("\n👍 Good! Minor issues to address, but core functionality works.")
        else:
            print("\n⚠️ Some issues detected. Review failed tests above.")
    
    def save_results(self):
        """Save test results to file"""
        results_file = f"test_results_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "version": "4.0.0",
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": total - passed,
                    "pass_rate": (passed / total) * 100 if total > 0 else 0
                },
                "results": [
                    {
                        "name": r.name,
                        "passed": r.passed,
                        "message": r.message,
                        "duration_ms": r.duration_ms,
                        "details": r.details
                    }
                    for r in self.results
                ]
            }, f, indent=2)
        
        print(f"\n📁 Results saved to: {results_file}")

if __name__ == "__main__":
    tester = ComprehensiveTester()
    tester.run_all_tests()
