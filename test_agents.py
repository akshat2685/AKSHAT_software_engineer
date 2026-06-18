"""
AKSHAT Agent Ecosystem Test
Tests all agents, LLM service, and API endpoints
"""
import urllib.request
import urllib.error
import json
import sys
import time
import os

BASE_URL = "http://127.0.0.1:3000"
EMAIL = "i.jain.akshat@gmail.com"
PASSWORD = "AKSHAtJAIN#2685"

# ------------------------------------------------------------------ #
def api(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode("utf-8") if data else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())
    except Exception as e:
        return 0, {"error": str(e)}

def ok(label, cond, detail=""):
    status = "[PASS]" if cond else "[FAIL]"
    print(f"  {status}  {label}", f"({detail})" if detail else "")
    return cond

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

# ------------------------------------------------------------------ #
section("1. API Health Check")
code, data = api("GET", "/docs")
ok("Swagger docs reachable", code == 200, f"HTTP {code}")

# ------------------------------------------------------------------ #
section("2. Authentication")
code, data = api("POST", "/auth/login", {"email": EMAIL, "password": PASSWORD})
ok("Login succeeds", code == 200, f"HTTP {code}")
if code != 200:
    print("  FATAL: Cannot login. Aborting further tests.")
    sys.exit(1)

token = data.get("token")
user_id = data.get("user_id")
ok("JWT token received", bool(token), token[:30] + "..." if token else "none")
ok("User ID assigned", bool(user_id), str(user_id))

# ------------------------------------------------------------------ #
section("3. Authenticated API Endpoints")

code, data = api("GET", "/api/status", token=token)
ok("/api/status accessible", code == 200, f"HTTP {code}")
if code == 200:
    print(f"    status={data.get('status')}  agent={data.get('current_agent')}")

code, data = api("GET", "/api/projects", token=token)
ok("/api/projects accessible", code == 200, f"HTTP {code}")
if code == 200:
    print(f"    Projects in DB: {len(data)}")
    for p in data[:3]:
        print(f"      - [{p['status']}] {p['name']} ({p['id'][:8]}...)")

code, data = api("GET", "/api/settings", token=token)
ok("/api/settings accessible", code == 200, f"HTTP {code}")
if code == 200:
    cloud_model = data.get('cloud_model') or '(not set)'
    print(f"    cloud_model={cloud_model}")
    print(f"    has_key={data.get('has_key')}  masked={data.get('masked_key')}")

# ------------------------------------------------------------------ #
section("4. LLM Service Health")
sys.path.insert(0, r"c:\Users\ijain\.gemini\antigravity-ide\scratch\AKSHAT_software_engineer")
os.chdir(r"c:\Users\ijain\.gemini\antigravity-ide\scratch\AKSHAT_software_engineer")

# Load .env
from pathlib import Path
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip('"')

try:
    from backend.services.llm_service import _default_service
    status = _default_service.status()
    ok("LLM service instantiated", True)
    ok("Ollama local connected", status.get("connected", False), status.get("message", ""))
    ok("Cloud provider configured", status.get("cloud", {}).get("ready", False), 
       f"url={status.get('cloud_configured_url') or 'none'}  model={status.get('cloud_configured_model') or 'none'}")
    ok("At least one provider ready", status.get("ready", False), status.get("message", ""))
    print(f"    Active message: {status.get('message')}")
except Exception as e:
    ok("LLM service import", False, str(e))

# ------------------------------------------------------------------ #
section("5. Individual Agent Tests")
try:
    from backend.services.llm_service import generate_response
    
    agents_to_test = [
        ("project_manager", "Create a simple to-do app"),
        ("architect", "Design a REST API for task management"),
        ("developer", "Write a Python function that reverses a string"),
        ("tester", "Write a unit test for a function that reverses a string"),
        ("reviewer", "Review this code: def reverse(s): return s[::-1]"),
        ("devops", "How would you deploy a FastAPI app to production?"),
        ("security", "What are OWASP top 3 vulnerabilities to check for?"),
        ("memory", "Summarize what was discussed so far"),
    ]
    
    for role, prompt in agents_to_test:
        try:
            t0 = time.time()
            response = generate_response(role, prompt)
            elapsed = time.time() - t0
            has_response = bool(response and len(response.strip()) > 10)
            ok(f"Agent '{role}'", has_response, 
               f"{elapsed:.1f}s | {len(response)} chars" if has_response else "empty response")
            if has_response:
                # Print first 120 chars of response
                preview = response.strip()[:120].replace("\n", " ")
                print(f"    Preview: {preview}...")
        except Exception as e:
            ok(f"Agent '{role}'", False, str(e)[:80])
            
except Exception as e:
    ok("Agent import", False, str(e))

# ------------------------------------------------------------------ #
section("6. Orchestration Test (Submit a Task via API)")
code, data = api(
    "POST", "/api/chat",
    {"message": "Build a minimal hello world HTML page", "workflow_pattern": "A"},
    token=token
)
ok("Task submitted to orchestrator", code in (200, 202), f"HTTP {code}")
if code in (200, 202):
    print(f"    Response: {str(data)[:200]}")
    
    # Wait a moment then check status
    time.sleep(3)
    code2, status_data = api("GET", "/api/status", token=token)
    if code2 == 200:
        print(f"    Status after submit: {status_data.get('status')} | Agent: {status_data.get('current_agent')}")
        ok("System is processing or complete", 
           status_data.get("status") in ("thinking", "running", "success", "idle"), 
           status_data.get("status"))

# ------------------------------------------------------------------ #
section("7. WebSocket Endpoint")
import socket
# Just check the WS port is open
try:
    s = socket.create_connection(("127.0.0.1", 3000), timeout=3)
    s.close()
    ok("WebSocket port (3000) reachable", True)
except Exception as e:
    ok("WebSocket port (3000) reachable", False, str(e))

# ------------------------------------------------------------------ #
section("Summary")
print("\n  Backend URL:    http://127.0.0.1:3000")
print("  Frontend URL:   http://127.0.0.1:3000  (built SPA)")
print("  API Docs:       http://127.0.0.1:3000/docs")
print("  Logged in as:   i.jain.akshat@gmail.com\n")
