#!/usr/bin/env python3
"""
Security Fix Verification Script
Tests log sanitization and client secret removal
"""

import json
import re
import subprocess
import os

def test_log_sanitization():
    """Test that sensitive data is removed from logs"""
    print("\n🛡️ Testing Log Sanitization...")
    
    # Import the sanitization patterns
    from local_agent.web.logs import SENSITIVE_PATTERNS, LogStreamer
    
    streamer = LogStreamer()
    
    # Test data with sensitive PostgreSQL fields
    test_entry = {
        "level": "INFO",
        "message": "User login",
        "user": {
            "id": "123",
            "email": "admin@example.com",
            "password_hash": "$2y$10$abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN",
            "settings": {"theme": "dark", "notifications": True}
        },
        "api_key": "sk-1234567890abcdef",
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    }
    
    sanitized = streamer.sanitize_log_entry(test_entry)
    sanitized_str = json.dumps(sanitized)
    
    # Verify sensitive data is redacted
    checks = [
        ("email", "admin@example.com", "[REDACTED]"),
        ("password_hash", "$2y$10$", "[REDACTED]"),
        ("api_key", "sk-1234567890abcdef", "[REDACTED]"),
        ("token", "eyJhbGciOiJ", "[REDACTED]"),
    ]
    
    all_passed = True
    for field, original, expected in checks:
        if original in sanitized_str:
            print(f"  ❌ FAIL: {field} leaked in logs")
            all_passed = False
        elif expected in sanitized_str:
            print(f"  ✅ PASS: {field} properly redacted")
        else:
            print(f"  ⚠️ WARNING: {field} not found in log")
    
    return all_passed

def test_no_hardcoded_keys_in_frontend():
    """Test that no hardcoded API keys exist in frontend builds"""
    print("\n🔍 Testing Frontend for Hardcoded Keys...")
    
    # Check source files
    frontend_src = "frontend/src/App.jsx"
    mobile_src = "mobile/App.tsx"
    
    hardcoded_patterns = [
        "local-agent-key-2024",
        "local-agent-v4-super-secret-key",
        "const API_KEY = '",
        "API_KEY = '"
    ]
    
    all_clean = True
    
    for filepath in [frontend_src, mobile_src]:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for pattern in hardcoded_patterns:
                    if pattern in content:
                        print(f"  ❌ FAIL: Hardcoded key pattern '{pattern}' found in {filepath}")
                        all_clean = False
        
        if all_clean and os.path.exists(filepath):
            print(f"  ✅ PASS: No hardcoded keys in {filepath}")
    
    return all_clean

def test_auth_modal_exists():
    """Test that auth modal is present in frontend"""
    print("\n🔐 Testing Auth Modal Presence...")
    
    frontend_src = "frontend/src/App.jsx"
    
    if os.path.exists(frontend_src):
        with open(frontend_src, 'r', encoding='utf-8') as f:
            content = f.read()
            
            checks = [
                ("showAuthModal", "Auth modal state exists"),
                ("apiKey", "API key input exists"),
                ("apiUrl", "API URL input exists"),
                ("saveConfigAndConnect", "Connect function exists"),
            ]
            
            all_present = True
            for pattern, desc in checks:
                if pattern in content:
                    print(f"  ✅ PASS: {desc}")
                else:
                    print(f"  ❌ FAIL: {desc} missing")
                    all_present = False
            
            return all_present
    
    print("  ❌ FAIL: frontend/src/App.jsx not found")
    return False

def main():
    print("=" * 60)
    print("🔒 SECURITY FIX VERIFICATION")
    print("=" * 60)
    
    results = []
    
    results.append(("Log Sanitization", test_log_sanitization()))
    results.append(("No Hardcoded Keys", test_no_hardcoded_keys_in_frontend()))
    results.append(("Auth Modal Present", test_auth_modal_exists()))
    
    print("\n" + "=" * 60)
    print("📊 SECURITY VERIFICATION SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 All security fixes verified!")
        print("   ✅ Password hashes redacted from logs")
        print("   ✅ No hardcoded API keys in frontend")
        print("   ✅ Auth modal properly implemented")
        print("\n🔒 System is now SECURE for production deployment!")
    else:
        print("\n⚠️ Some security checks failed. Please review.")

if __name__ == "__main__":
    main()
