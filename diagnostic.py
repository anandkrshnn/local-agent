# diagnostic.py
import requests
import os
import socket

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

print("=" * 60)
print("--- LOCAL AGENT DIAGNOSTIC ---")
print("=" * 60)

# 1. Check Ollama
print("\n1. OLLAMA STATUS:")
try:
    resp = requests.get("http://localhost:11434/api/tags", timeout=5)
    if resp.status_code == 200:
        print("   [OK] Ollama is running")
    else:
        print(f"   [FAIL] Ollama error: {resp.status_code}")
except:
    print("   [FAIL] Ollama is NOT running")

# 2. Check Server
print("\n2. SERVER STATUS:")
try:
    resp = requests.get("http://localhost:8000/api/status", timeout=5)
    if resp.status_code == 200:
        print(f"   [OK] Server is running: {resp.json()}")
    else:
        print(f"   [FAIL] Server error: {resp.status_code}")
except:
    print("   [FAIL] Server is NOT running")

# 3. Check Files
print("\n3. FILE STATUS:")
if os.path.exists('.env.example'):
    print("   [OK] .env.example file found")
else:
    print("   [WARN] .env.example file NOT found")

# 4. Check Ports
print("\n4. PORT CHECK:")
print(f"   - Port 8000 (Backend): {'UP' if check_port(8000) else 'DOWN'}")
print(f"   - Port 5173 (Frontend): {'UP' if check_port(5173) else 'DOWN'}")
print(f"   - Port 5174 (Frontend): {'UP' if check_port(5174) else 'DOWN'}")

print("\n" + "=" * 60)
