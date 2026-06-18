import urllib.request
import urllib.error
import json
import sys
import time
import os
from pathlib import Path

BASE_URL = "http://127.0.0.1:3000"
EMAIL = "i.jain.akshat@gmail.com"
PASSWORD = "AKSHAtJAIN#2685"

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

section("1. API Health & Auth")
code, data = api("POST", "/auth/login", {"email": EMAIL, "password": PASSWORD})
ok("Login succeeds", code == 200, f"HTTP {code}")
if code != 200:
    print("  FATAL: Cannot login. Aborting further tests.")
    sys.exit(1)
token = data.get("token")

section("2. All V2 Agents LLM Inference Test")
sys.path.insert(0, r"c:\Users\ijain\.gemini\antigravity-ide\scratch\AKSHAT_software_engineer")
os.chdir(r"c:\Users\ijain\.gemini\antigravity-ide\scratch\AKSHAT_software_engineer")

env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip().strip('"')

try:
    from backend.services.llm_service import generate_response
    
    agents_to_test = [
        # Original core agents
        ("project_manager", "Create a complex microservices architecture plan"),
        ("architect", "Design a graph database schema for an agent memory system"),
        ("developer", "Write a Python script to scrape a table from a URL"),
        ("tester", "Write Pytest cases for a generic user authentication flow"),
        ("reviewer", "Review some mock code for an API endpoint"),
        ("devops", "Write a GitHub Actions workflow for Python tests"),
        ("security", "Provide a checklist for securing a FastAPI application"),
        ("memory", "Extract entities from this text: 'AKSHAT is an AI framework'"),
        # New V2 Agents
        ("debug", "Debug this error message: 'IndexError: list index out of range'"),
        ("refactor", "Suggest how to refactor a massive monolithic class with 5000 lines"),
        ("documentation", "Generate Sphinx-style docs for a workflow orchestrator"),
        ("dependency", "Resolve conflicts between requests==2.31.0 and urllib3<2"),
        ("browser", "Write a Selenium script to click a button with id 'submit-btn'"),
        ("vision", "Describe a generic UI mockup for an analytics dashboard")
    ]
    
    for role, prompt in agents_to_test:
        try:
            t0 = time.time()
            response = generate_response(role, prompt)
            elapsed = time.time() - t0
            has_response = bool(response and len(response.strip()) > 10)
            ok(f"Agent '{role}'", has_response, f"{elapsed:.1f}s | {len(response)} chars")
        except Exception as e:
            ok(f"Agent '{role}'", False, str(e)[:80])
            
except Exception as e:
    ok("Agent import", False, str(e))

section("3. Complex Multi-Agent Orchestration Task")
task_desc = "Build a dashboard with authentication that handles browser data extraction and visually aligns components. Make sure to refactor the old code and document it."
code, data = api(
    "POST", "/api/chat",
    {"message": task_desc, "workflow_pattern": "A"},
    token=token
)
ok("Task submitted to orchestrator", code in (200, 202), f"HTTP {code}")
if code in (200, 202):
    print(f"    Task Description: {task_desc}")
    print("    Waiting for multi-agent pipeline to process...")
    for i in range(10):
        time.sleep(3)
        code2, status_data = api("GET", "/api/status", token=token)
        if code2 == 200:
            print(f"      Status: {status_data.get('status')} | Agent: {status_data.get('current_agent')}")
            if status_data.get('status') == "idle":
                break
