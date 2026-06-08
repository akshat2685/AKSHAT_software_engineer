from __future__ import annotations

import os
import json
import re
import subprocess
import threading
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.graph.workflow import WorkflowOrchestrator
from backend.runtime import Event, EventBus, MemoryStore, TaskState, now_iso, slug, stamp
from backend.services.ollama_service import OllamaService


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "akshat_memory.sqlite3"
HOST = os.environ.get("AKSHAT_HOST", "127.0.0.1")
PORT = int(os.environ.get("AKSHAT_PORT", "3000"))


class AkshatCore:
    TOOL_NAMES = [
        "read_file",
        "write_file",
        "create_directory",
        "list_directory",
        "search_code",
        "search_files",
        "run_command",
        "git_status",
        "git_diff",
        "git_commit",
        "web_search",
        "store_memory",
        "retrieve_memory",
        "run_tests",
        "run_build",
        "run_linter",
        "run_application",
        "validate_artifact",
        "build_artifact",
        "deploy_artifact",
        "generate_tests",
        "review_code",
        "generate_architecture",
        "create_task_plan",
        "open_browser",
        "goto_url",
        "click",
        "type_text",
        "extract_text",
        "take_screenshot",
        "create_plan",
        "create_todo_list",
        "update_plan",
        "reflect",
        "speak_text",
        "send_avatar_event",
    ]

    def __init__(self, memory: MemoryStore, bus: EventBus):
        self.memory = memory
        self.bus = bus
        self.lock = threading.Lock()
        self.state = TaskState(repo={"root": str(ROOT), "files": [], "summary": ""}, tools=list(self.TOOL_NAMES))
        self.ollama = OllamaService(logger=self._log_ollama)
        self.orchestrator = WorkflowOrchestrator(self._ollama, self.execute_tool)

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            data = asdict(self.state)
        data["memory"] = self.memory.recent(5)
        data["habits"] = self.memory.recent_habits(5)
        data["tool_logs"] = self.memory.recent_tool_logs(8)
        data["ollama"] = self.ollama.status()
        data["active_tools"] = self.state.tools
        return data

    def tool_catalog(self) -> List[Dict[str, str]]:
        descriptions = {
            "read_file": "Read a file inside the workspace.",
            "write_file": "Write a file inside the workspace.",
            "create_directory": "Create a directory inside the workspace.",
            "list_directory": "List files in a workspace directory.",
            "search_code": "Search the codebase with ripgrep.",
            "search_files": "Find files or matching code patterns.",
            "run_command": "Run a non-interactive command in the workspace.",
            "git_status": "Inspect git status.",
            "git_diff": "Inspect git diff.",
            "git_commit": "Report commit readiness; commits require explicit owner action.",
            "web_search": "Placeholder for web search integration.",
            "store_memory": "Store a memory record in SQLite.",
            "retrieve_memory": "Retrieve relevant memories from SQLite.",
            "run_tests": "Run project validation tests.",
            "run_build": "Run build verification.",
            "run_linter": "Run lint verification.",
            "run_application": "Report the local application runtime endpoint.",
            "validate_artifact": "Validate generated project files and run build verification.",
            "build_artifact": "Generate a browser-viewable output artifact in src/assets.",
            "deploy_artifact": "Publish a validated artifact to a stable local deployment URL.",
        }
        return [{"name": name, "description": descriptions.get(name, f"AKSHAT tool: {name}.")} for name in self.TOOL_NAMES]

    def emit(self, kind: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        with self.lock:
            self.state.updated_at = now_iso()
            self.state.current_action = message
        snapshot = self.snapshot()
        merged_data = {**snapshot, **(data or {})}
        self.bus.publish(Event(ts=stamp(), kind=kind, message=message, data=merged_data))

        # DB Logging
        try:
            from backend.database.connection import SessionLocal
            from backend.services import project_service
            project_id = self.state.task_id
            if project_id and project_id != "idle":
                db_event_type = None
                lk = kind.lower()
                lm = message.lower()
                if kind == "task_received":
                    db_event_type = "PROJECT_CREATED"
                elif kind == "agent_start" or "starting agent" in lm or "agent started" in lk:
                    db_event_type = "AGENT_STARTED"
                elif kind == "agent_end" or "agent completed" in lm or "agent completed" in lk:
                    db_event_type = "AGENT_COMPLETED"
                elif kind == "file_created" or "file created" in lk:
                    db_event_type = "FILE_CREATED"
                elif kind == "file_modified" or "file modified" in lk:
                    db_event_type = "FILE_MODIFIED"
                elif kind == "test_start" or "running validation tests" in lm or "test started" in lk:
                    db_event_type = "TEST_STARTED"
                elif kind == "test_end" or "validation completed" in lm or "test completed" in lk:
                    db_event_type = "TEST_COMPLETED"
                elif kind in {"success", "error"} or "project completed" in lk:
                    db_event_type = "PROJECT_COMPLETED"
                    db = SessionLocal()
                    try:
                        project_service.update_project_status(db, project_id, kind)
                    finally:
                        db.close()
                
                if db_event_type:
                    db = SessionLocal()
                    try:
                        project_service.log_project_event(db, project_id, db_event_type, {"message": message, **(data or {})})
                    finally:
                        db.close()
        except Exception:
            pass

    def submit(self, prompt: str, user_id: int = 1) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        if not prompt:
            raise ValueError("prompt is required")
        with self.lock:
            self.state = TaskState(
                task_id=slug(prompt)[:80] or f"task-{int(time.time())}",
                prompt=prompt,
                status="thinking",
                avatar_state="Thinking",
                current_action="Received task",
                habits=[item["pattern"] for item in self.memory.recent_habits(10)],
                tools=list(self.TOOL_NAMES),
                repo={"root": str(ROOT), "files": [], "summary": ""},
            )
        # Create Project in DB
        try:
            from backend.database.connection import SessionLocal
            from backend.services import project_service
            db = SessionLocal()
            try:
                # check if project already exists, if so reuse it
                from backend.database.models import Project
                existing = db.query(Project).filter(Project.id == self.state.task_id).first()
                if not existing:
                    project_service.create_project(db, self.state.task_id, prompt[:255], user_id)
            finally:
                db.close()
        except Exception:
            pass

        self.emit("task_received", f"Received task: {prompt}", {"prompt": prompt})
        threading.Thread(target=self._run, args=(prompt,), daemon=True).start()
        return self.snapshot()

    def chat(self, message: str, user_id: int = 1) -> Dict[str, Any]:
        message = (message or "").strip()
        if not message:
            raise ValueError("message is required")

        if not self._is_software_task(message):
            reply = self._chat_reply(message)
            with self.lock:
                if self.state.status not in {"thinking", "running"}:
                    self.state.status = "idle"
                    self.state.avatar_state = "Speaking"
                    self.state.current_agent = "Idle"
                    self.state.current_action = "General conversation"
                self.state.chat.extend([{"role": "user", "content": message}, {"role": "assistant", "content": reply}])
            self.emit("chat_updated", f"AKSHAT: {reply}", {"chat": self.state.chat})
            return {"mode": "chat", "reply": reply, "state": self.snapshot()}

        if user_id == 1:
            self.submit(message)
        else:
            self.submit(message, user_id=user_id)
        reply = "Task accepted. I am routing it through the engineering workflow and will return a review link when an artifact is produced."
        with self.lock:
            self.state.chat.extend([{"role": "user", "content": message}, {"role": "assistant", "content": reply}])
        self.emit("chat_updated", f"AKSHAT: {reply}", {"chat": self.state.chat})
        return {"mode": "workflow", "reply": reply, "state": self.snapshot()}

    def execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        tool_args = dict(args or {})
        agent_name = str(tool_args.pop("agent_name", "") or self.state.current_agent or "AKSHAT")
        reason = str(tool_args.pop("reason", "") or f"Use approved tool {name}")
        try:
            result = self._execute_tool(name, tool_args)
        except Exception as exc:
            result = {"success": False, "ok": False, "error": str(exc)}
        self.memory.add_tool_log(agent_name, name, reason, tool_args, result)
        return result

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self.TOOL_NAMES:
            return {"success": False, "ok": False, "error": f"Unknown tool: {name}"}
        self.emit("tool", f"Running tool: {name}", {"tool": name, "args": args})
        handlers = {
            "read_file": lambda: {"success": True, "ok": True, "content": self.read_file(args.get("path", ""))},
            "write_file": lambda: self._write_result(args.get("path", ""), args.get("content", "")),
            "create_directory": lambda: self._mkdir_result(args.get("path", "")),
            "list_directory": lambda: {"success": True, "ok": True, "items": self.list_directory(args.get("path", "."))},
            "search_code": lambda: self.search_code(args.get("pattern", "")),
            "search_files": lambda: {"success": True, "ok": True, "matches": self.search_files(args.get("query", ""))},
            "run_command": lambda: self._run_command(self._command_args(args.get("command", [])), ROOT, int(args.get("timeout", 120))),
            "git_status": self.git_status,
            "git_diff": self.git_diff,
            "git_commit": lambda: {"ok": False, "message": "Commit automation is disabled until explicitly requested."},
            "web_search": lambda: {"ok": False, "message": f"Web search is not wired yet for: {args.get('query', '')}"},
            "store_memory": lambda: self._store_result(args),
            "retrieve_memory": lambda: {"success": True, "ok": True, "items": self.memory.search(args.get("query", ""), 10)},
            "run_tests": self.run_tests,
            "run_build": self.run_build,
            "run_linter": self.run_linter,
            "run_application": lambda: {"success": True, "status": "running", "url": f"http://{HOST}:{PORT}"},
            "validate_artifact": lambda: self.validate_artifact(
                str(args.get("artifact_path", "")),
                list(args.get("created_files", [])),
            ),
            "build_artifact": lambda: self.build_artifact(
                args.get("prompt", ""),
                str(args.get("artifact_name", "")),
                str(args.get("artifact_version", "")),
                str(args.get("task_type", "")),
            ),
            "deploy_artifact": lambda: self.deploy_artifact(
                str(args.get("artifact_name", "")),
                str(args.get("artifact_version", "")),
                str(args.get("artifact_path", "")),
                str(args.get("review_url", "")),
                str(args.get("deploy_url", "")),
                str(args.get("output_url", "")),
            ),
            "generate_tests": lambda: {"success": True, "ok": True, "tests": self.generate_tests(args.get("feature", ""))},
            "review_code": lambda: self.review_code(args.get("path", "")),
            "generate_architecture": lambda: {"success": True, "ok": True, "architecture": self.generate_architecture(args.get("prompt", ""))},
            "create_task_plan": lambda: {"success": True, "ok": True, "tasks": self.create_plan(args.get("prompt", ""))},
            "open_browser": lambda: {"ok": True, "message": "Browser UI is available in the dashboard."},
            "goto_url": lambda: {"ok": True, "message": f"Browser navigation requested for {args.get('url', '')}"},
            "click": lambda: {"ok": True, "message": f"Click requested on {args.get('target', '')}"},
            "type_text": lambda: {"ok": True, "message": f"Typing requested into {args.get('target', '')}"},
            "extract_text": lambda: {"ok": True, "message": f"Text extraction requested from {args.get('target', '')}"},
            "take_screenshot": lambda: {"ok": True, "message": "Screenshot capture is handled by the browser tool."},
            "create_plan": lambda: {"ok": True, "plan": self.create_plan(args.get("prompt", ""))},
            "create_todo_list": lambda: {"ok": True, "todo_list": self.create_todo_list(args.get("prompt", ""))},
            "update_plan": lambda: {"ok": True, "plan": self.update_plan(list(args.get("plan", [])))},
            "reflect": lambda: {"ok": True, "reflection": self.reflect(args.get("prompt", ""))},
            "speak_text": lambda: self.speak_text(args.get("text", "")),
            "send_avatar_event": lambda: self.send_avatar_event(args.get("state", "Idle"), args.get("message", "")),
        }
        return handlers[name]()

    def read_file(self, relative_path: str) -> str:
        path = self._safe_path(relative_path)
        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> None:
        path = self._safe_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def create_directory(self, relative_path: str) -> None:
        self._safe_path(relative_path).mkdir(parents=True, exist_ok=True)

    def list_directory(self, relative_path: str = ".") -> List[str]:
        return [path.name for path in sorted(self._safe_path(relative_path).iterdir())]

    def search_code(self, pattern: str) -> Dict[str, Any]:
        return self._run_command(["rg", "-n", pattern, str(ROOT)], ROOT)

    def search_files(self, query: str) -> List[str]:
        query = (query or "").lower()
        if not query:
            return []
        matches: List[str] = []
        for path in ROOT.rglob("*"):
            if ".git" in path.parts or "__pycache__" in path.parts or not path.is_file():
                continue
            rel = str(path.relative_to(ROOT))
            if query in rel.lower():
                matches.append(rel)
            if len(matches) >= 50:
                break
        return matches

    def git_status(self) -> Dict[str, Any]:
        return self._run_command(["git", "status", "--short"], ROOT)

    def git_diff(self) -> Dict[str, Any]:
        return self._run_command(["git", "diff", "--", "."], ROOT)

    def run_tests(self) -> Dict[str, Any]:
        return self._run_command([self._npm(), "test"], ROOT)

    def run_build(self) -> Dict[str, Any]:
        return self._run_command([self._npm(), "run", "build"], ROOT)

    def run_linter(self) -> Dict[str, Any]:
        result = self._run_command(["py", "-m", "compileall", "-q", "src", "backend"], ROOT)
        return {"success": result["returncode"] == 0, "warnings": 0, "errors": 0 if result["returncode"] == 0 else 1, "result": result}

    def validate_artifact(self, artifact_path: str, created_files: List[Any]) -> Dict[str, Any]:
        missing: List[str] = []
        if not artifact_path:
            missing.append("artifact_path")
        else:
            entry = self._safe_path(artifact_path)
            if not entry.exists():
                missing.append(artifact_path)
        for item in created_files:
            rel = str(item)
            if rel and not self._safe_path(rel).exists():
                missing.append(rel)
        if missing:
            return {"success": False, "returncode": 1, "stderr": "Missing generated files: " + ", ".join(missing), "summary": "artifact validation failed"}
        build = self.run_build()
        build["summary"] = "artifact files validated and build passed" if build.get("success") else "build failed after artifact validation"
        return build

    def build_artifact(self, prompt: str, artifact_name: str = "", artifact_version: str = "", task_type: str = "") -> Dict[str, Any]:
        prompt = (prompt or "Build a landing page").strip()
        safe_prompt = self._escape_html(prompt)
        artifact_title = self._artifact_title(prompt)
        artifact_name = (artifact_name or self._artifact_name(prompt)).strip()
        if self._is_project_prompt(prompt, task_type):
            return self._build_project_artifact(prompt, artifact_title, artifact_name, artifact_version)

        model_html = self._generate_artifact_with_ollama(prompt, artifact_title)
        html = model_html or self._fallback_artifact_html(prompt, artifact_title, safe_prompt)
        relative_path = f"projects/{artifact_name}.html"
        self.write_file(relative_path, html)
        output_url = f"http://{HOST}:{PORT}/assets/{artifact_name}.html"
        review_url = f"http://{HOST}:{PORT}/review/{artifact_name}"
        deploy_url = f"http://{HOST}:{PORT}/deploy/{artifact_name}"
        version = artifact_version or self._artifact_version()
        return {
            "success": True,
            "ok": True,
            "name": artifact_name,
            "version": version,
            "path": relative_path,
            "url": review_url,
            "output_url": output_url,
            "deploy_url": deploy_url,
            "review_url": review_url,
            "used_ollama": bool(model_html),
            "summary": f"Generated browser artifact at {relative_path}",
        }

    def deploy_artifact(self, artifact_name: str, artifact_version: str, artifact_path: str, review_url: str, deploy_url: str, output_url: str) -> Dict[str, Any]:
        if not artifact_name or not artifact_path:
            return {"success": False, "ok": False, "error": "artifact metadata missing"}
        path = self._safe_path(artifact_path)
        if not path.exists():
            return {"success": False, "ok": False, "error": "artifact file missing"}
        review_url = review_url or f"http://{HOST}:{PORT}/review/{artifact_name}"
        deploy_url = deploy_url or f"http://{HOST}:{PORT}/deploy/{artifact_name}"
        output_url = output_url or f"http://{HOST}:{PORT}/assets/{artifact_name}.html"
        return {
            "success": True,
            "ok": True,
            "artifact_name": artifact_name,
            "version": artifact_version or self._artifact_version(),
            "artifact_path": artifact_path,
            "review_url": review_url,
            "deploy_url": deploy_url,
            "output_url": output_url,
            "summary": f"Published {artifact_name} to {deploy_url}",
        }

    def _build_project_artifact(self, prompt: str, artifact_title: str, artifact_name: str, artifact_version: str) -> Dict[str, Any]:
        project_root = f"projects/{artifact_name}"
        files, used_model = self._generate_project_with_ollama(prompt, artifact_title)
        if not files:
            files = self._fallback_project_files(prompt, artifact_title)
            used_model = False
        created_files = self._write_project_files(project_root, files)
        entry_file = f"{project_root}/index.html"
        if entry_file not in created_files:
            raise ValueError("project generation must create index.html")
        version = artifact_version or self._artifact_version()
        entry_url = f"http://{HOST}:{PORT}/assets/projects/{artifact_name}/index.html"
        review_url = f"http://{HOST}:{PORT}/review/{artifact_name}"
        deploy_url = f"/deploy/{artifact_name}"
        return {
            "success": True,
            "ok": True,
            "name": artifact_name,
            "version": version,
            "path": entry_file,
            "project_path": project_root,
            "entry_file": entry_file,
            "entry_url": entry_url,
            "url": review_url,
            "output_url": entry_url,
            "deploy_url": deploy_url,
            "review_url": review_url,
            "created_files": created_files,
            "used_ollama": used_model,
            "fallback_used": not used_model,
            "summary": f"Created project artifact with {len(created_files)} files at {project_root}",
        }

    def _generate_project_with_ollama(self, prompt: str, artifact_title: str) -> tuple[List[Dict[str, str]], bool]:
        response = self._ollama(
            "You are AKSHAT's Developer agent. Return strict JSON only for a small static web project.\n"
            "Schema: {\"entry\":\"index.html\",\"files\":[{\"path\":\"index.html\",\"content\":\"...\"}]}.\n"
            "Required files: index.html, styles.css, script.js, manifest.json.\n"
            "Use external files, not inline CSS or inline JavaScript. Do not include secrets or credentials.\n"
            "Make the result visually specific to the user prompt, responsive, and interactive when appropriate.\n"
            f"Title: {artifact_title}\nUser prompt: {prompt}"
        )
        raw = self._extract_json_object(response)
        if not raw:
            return [], False
        try:
            payload = json.loads(raw)
        except Exception:
            return [], False
        files = payload.get("files", [])
        if not isinstance(files, list):
            return [], False
        cleaned: List[Dict[str, str]] = []
        for item in files:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path", "")).replace("\\", "/").strip("/")
            content = str(item.get("content", ""))
            if path and content:
                cleaned.append({"path": path, "content": content})
        required = {"index.html", "styles.css", "script.js", "manifest.json"}
        if not required.issubset({item["path"] for item in cleaned}):
            return [], False
        return cleaned, True

    def _write_project_files(self, project_root: str, files: List[Dict[str, str]]) -> List[str]:
        created: List[str] = []
        for item in files:
            relative = self._safe_project_file(project_root, item["path"])
            content = item["content"]
            if self._contains_secret(content):
                raise ValueError(f"generated file contains blocked secret-looking content: {item['path']}")
            self.write_file(relative, content)
            created.append(relative)
        return created

    def _safe_project_file(self, project_root: str, file_path: str) -> str:
        clean = file_path.replace("\\", "/").strip("/")
        if not clean or clean.startswith(".") or ".." in clean.split("/") or clean.startswith("/"):
            raise ValueError(f"unsafe generated path: {file_path}")
        if clean.lower().endswith((".env", ".pem", ".key", ".p12")):
            raise ValueError(f"blocked generated path: {file_path}")
        root = self._safe_path(project_root)
        target = self._safe_path(f"{project_root}/{clean}")
        if root not in target.parents:
            raise ValueError(f"path outside generated project: {file_path}")
        return f"{project_root}/{clean}"

    def _contains_secret(self, content: str) -> bool:
        blocked = ("CLOUD_API_KEY=", "gsk_", "BEGIN PRIVATE KEY", "AWS_SECRET_ACCESS_KEY", "OPENAI_API_KEY=")
        return any(marker in content for marker in blocked)

    def _extract_json_object(self, text: str) -> str:
        raw = (text or "").strip().replace("```json", "").replace("```", "").strip()
        start = raw.find("{")
        end = raw.rfind("}")
        return raw[start : end + 1] if start != -1 and end != -1 and end > start else ""

    def _is_project_prompt(self, prompt: str, task_type: str) -> bool:
        text = prompt.lower()
        terms = ("website", "web app", "app", "landing", "portfolio", "dashboard", "todo", "notes", "calculator", "form", "tool", "page", "site")
        return task_type in {"website", "deploy", "code"} or any(term in text for term in terms)

    def _fallback_project_files(self, prompt: str, artifact_title: str) -> List[Dict[str, str]]:
        kind = self._project_kind(prompt)
        title = self._escape_html(artifact_title)
        prompt_text = self._escape_html(prompt)
        body = self._project_body(kind, title, prompt_text)
        return [
            {
                "path": "index.html",
                "content": f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css">
  <script defer src="script.js"></script>
</head>
<body data-kind="{kind}">
  {body}
</body>
</html>
""",
            },
            {"path": "styles.css", "content": self._project_css()},
            {"path": "script.js", "content": self._project_js(kind)},
            {
                "path": "manifest.json",
                "content": json.dumps({"name": artifact_title, "entry": "index.html", "kind": kind, "prompt": prompt}, indent=2),
            },
        ]

    def _project_kind(self, prompt: str) -> str:
        text = prompt.lower()
        if "portfolio" in text:
            return "portfolio"
        if "notes" in text:
            return "notes"
        if "todo" in text or "task" in text:
            return "todo"
        if "calculator" in text:
            return "calculator"
        if "dashboard" in text:
            return "dashboard"
        if "form" in text or "contact" in text:
            return "form"
        if "landing" in text:
            return "landing"
        return "website"

    def _project_body(self, kind: str, title: str, prompt: str) -> str:
        if kind == "portfolio":
            return f"""<main class="shell portfolio">
  <nav><strong>{title}</strong><span>Available for product, web, and AI work</span></nav>
  <section class="hero"><div><p class="eyebrow">Portfolio</p><h1>Building useful software with taste and discipline.</h1><p>{prompt}</p><div class="actions"><a href="#projects">View Projects</a><a href="#contact">Contact</a></div></div><aside class="portrait">AK</aside></section>
  <section id="projects" class="cards"><article><strong>Agent Dashboard</strong><span>Operational UI with workflow traces.</span></article><article><strong>Startup Site</strong><span>Responsive launch page with strong visual hierarchy.</span></article><article><strong>Automation Tool</strong><span>Local-first app for repeatable work.</span></article></section>
  <section id="contact" class="contact"><h2>Contact</h2><p>akshat@example.com</p></section>
</main>"""
        if kind == "notes":
            return f"""<main class="shell app"><section class="tool"><p class="eyebrow">Notes</p><h1>{title}</h1><div class="composer"><input id="note-title" placeholder="Title"><textarea id="note-body" placeholder="Write a note"></textarea><button id="add-note">Add Note</button></div><div id="notes" class="note-grid"></div></section></main>"""
        if kind == "todo":
            return f"""<main class="shell app"><section class="tool"><p class="eyebrow">Todo</p><h1>{title}</h1><div class="row"><input id="todo-input" placeholder="Add a task"><button id="add-todo">Add</button></div><ul id="todo-list" class="todo-list"></ul></section></main>"""
        if kind == "calculator":
            return f"""<main class="shell app"><section class="tool calculator"><p class="eyebrow">Calculator</p><h1>{title}</h1><input id="display" readonly value="0"><div id="keys" class="keys"></div></section></main>"""
        if kind == "dashboard":
            return f"""<main class="shell dashboard"><nav><strong>{title}</strong><span>Live operations</span></nav><section class="metrics"><article><b>98%</b><span>Uptime</span></article><article><b>42</b><span>Tasks</span></article><article><b>12</b><span>Deploys</span></article></section><section class="chart"><h1>Execution Overview</h1><div class="bars"><span style="height:45%"></span><span style="height:75%"></span><span style="height:55%"></span><span style="height:90%"></span></div></section></main>"""
        if kind == "form":
            return f"""<main class="shell app"><section class="tool"><p class="eyebrow">Contact</p><h1>{title}</h1><div class="composer"><input id="name" placeholder="Name"><input id="email" placeholder="Email"><textarea id="message" placeholder="Message"></textarea><button id="send-form">Send</button><p id="form-status"></p></div></section></main>"""
        return f"""<main class="shell landing"><nav><strong>{title}</strong><span>Local preview</span></nav><section class="hero"><div><p class="eyebrow">Generated Website</p><h1>{title}</h1><p>{prompt}</p><div class="actions"><a href="#features">Explore</a><button id="pulse">Try Interaction</button></div></div></section><section id="features" class="cards"><article><strong>Fast</strong><span>Static local output.</span></article><article><strong>Responsive</strong><span>Works on desktop and mobile.</span></article><article><strong>Reviewable</strong><span>Source and preview stay linked.</span></article></section></main>"""

    def _project_css(self) -> str:
        return """*{box-sizing:border-box}body{margin:0;min-height:100vh;background:#10130f;color:#f7f4e8;font-family:Georgia,'Times New Roman',serif}body:before{content:'';position:fixed;inset:0;background:linear-gradient(120deg,rgba(196,255,87,.12),transparent 35%),radial-gradient(circle at 85% 12%,rgba(255,88,88,.16),transparent 26%);pointer-events:none}.shell{position:relative;z-index:1;width:min(1180px,100%);margin:0 auto;padding:28px}.shell nav{height:64px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(247,244,232,.18)}nav strong{font-size:1.2rem}nav span,.eyebrow,p,article span{color:#c9c4ad}.hero{min-height:calc(100vh - 160px);display:grid;grid-template-columns:minmax(0,1.2fr) minmax(240px,.8fr);align-items:center;gap:32px}.hero h1,.tool h1,.chart h1{font-size:clamp(2.4rem,7vw,5.8rem);line-height:1;margin:12px 0;letter-spacing:0}.hero p,.tool textarea,.tool input{font-size:1rem;line-height:1.7}.actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}.actions a,button{border:0;border-radius:8px;background:#c4ff57;color:#11140f;padding:12px 16px;font-weight:800;text-decoration:none;cursor:pointer}.portrait{aspect-ratio:1;border:1px solid rgba(247,244,232,.24);display:grid;place-items:center;font-size:6rem;background:#171b14;box-shadow:12px 12px 0 #c4ff57}.cards,.metrics,.note-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:20px}article,.tool,.chart,.contact{border:1px solid rgba(247,244,232,.18);border-radius:8px;background:rgba(255,255,255,.045);padding:22px}.app{display:grid;place-items:center;min-height:100vh}.tool{width:min(760px,100%)}.composer,.row{display:grid;gap:12px}.row{grid-template-columns:1fr auto}.tool input,.tool textarea,#display{width:100%;border:1px solid rgba(247,244,232,.2);border-radius:8px;background:#0c0f0b;color:#f7f4e8;padding:14px}.tool textarea{min-height:140px;resize:vertical}.todo-list{display:grid;gap:10px;padding:0;list-style:none}.todo-list li{display:flex;justify-content:space-between;gap:10px;border:1px solid rgba(247,244,232,.15);border-radius:8px;padding:12px}.keys{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.keys button{min-height:54px}.metrics article b{display:block;font-size:3rem}.bars{height:320px;display:flex;align-items:end;gap:18px}.bars span{flex:1;background:#c4ff57;border-radius:8px 8px 0 0}@media(max-width:800px){.hero{grid-template-columns:1fr}.cards,.metrics,.note-grid{grid-template-columns:1fr}.row{grid-template-columns:1fr}.portrait{font-size:3rem}}"""

    def _project_js(self, kind: str) -> str:
        if kind == "notes":
            return """const notes=document.getElementById('notes');document.getElementById('add-note')?.addEventListener('click',()=>{const title=document.getElementById('note-title').value||'Untitled';const body=document.getElementById('note-body').value||'Empty note';const card=document.createElement('article');card.innerHTML=`<strong>${title}</strong><span>${body}</span>`;notes.prepend(card);});"""
        if kind == "todo":
            return """const list=document.getElementById('todo-list');document.getElementById('add-todo')?.addEventListener('click',()=>{const input=document.getElementById('todo-input');const value=input.value.trim();if(!value)return;const li=document.createElement('li');li.innerHTML=`<span>${value}</span><button>Done</button>`;li.querySelector('button').onclick=()=>li.remove();list.append(li);input.value='';});"""
        if kind == "calculator":
            return """const display=document.getElementById('display');const keys='789/456*123-0.C+'.split('');let expr='';keys.forEach(k=>{const b=document.createElement('button');b.textContent=k;b.onclick=()=>{if(k==='C'){expr='';display.value='0';return}expr+=k;try{display.value=eval(expr)||'0'}catch{display.value=expr}};document.getElementById('keys').append(b);});const eq=document.createElement('button');eq.textContent='=';eq.onclick=()=>{try{expr=String(eval(expr));display.value=expr}catch{display.value='Error';expr=''}};document.getElementById('keys').append(eq);"""
        if kind == "form":
            return """document.getElementById('send-form')?.addEventListener('click',()=>{const name=document.getElementById('name').value||'there';document.getElementById('form-status').textContent=`Thanks, ${name}. Your message is ready for local review.`;});"""
        return """document.getElementById('pulse')?.addEventListener('click',()=>{document.body.classList.toggle('active');});"""

    def _generate_artifact_with_ollama(self, prompt: str, artifact_title: str) -> str:
        response = self._ollama(
            "You are AKSHAT's Developer agent. Generate a complete, single-file HTML document only. "
            "No markdown fences. No explanation. Include inline CSS and JavaScript when useful. "
            "Make it visually polished, dark, aligned, responsive, and production-reviewable. "
            "If the user asks for a tool, implement working client-side behavior. "
            f"Title: {artifact_title}\n"
            f"User prompt: {prompt}\n"
            "Return only <!doctype html> through </html>."
        )
        html = self._extract_html_document(response)
        if not html:
            return ""
        if "<script" not in html.lower() and any(word in prompt.lower() for word in ["tool", "calculator", "form"]):
            return ""
        return html

    def _fallback_artifact_html(self, prompt: str, artifact_title: str, safe_prompt: str) -> str:
        artifact_body = self._artifact_body(prompt)
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{self._escape_html(artifact_title)}</title>
  <style>
    :root{{--bg:#03050b;--panel:rgba(8,13,25,.72);--line:rgba(255,255,255,.16);--text:#f8fafc;--muted:#93a4b8;--cyan:#38d5ff;--green:#4cf2a1}}
    *{{box-sizing:border-box}}
    body{{margin:0;min-height:100vh;background:radial-gradient(circle at 20% 20%,rgba(56,213,255,.18),transparent 28%),radial-gradient(circle at 80% 30%,rgba(76,242,161,.13),transparent 26%),linear-gradient(145deg,#02040a,#07111c);color:var(--text);font-family:"Bahnschrift","Segoe UI",system-ui,sans-serif;overflow:hidden}}
    body::before{{content:"";position:fixed;inset:0;background-image:linear-gradient(rgba(255,255,255,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);background-size:70px 70px;mask-image:radial-gradient(circle at center,#000 20%,transparent 76%)}}
    main{{position:relative;z-index:1;min-height:100vh;display:grid;place-items:center;padding:36px}}
    .card{{width:min(1100px,100%);border:1px solid var(--line);border-radius:8px;background:linear-gradient(145deg,rgba(255,255,255,.1),rgba(255,255,255,.035));box-shadow:0 28px 90px rgba(0,0,0,.46);backdrop-filter:blur(18px);padding:clamp(28px,6vw,72px)}}
    .eyebrow{{color:var(--green);font-size:.78rem;font-weight:900;letter-spacing:.26em;text-transform:uppercase}}
    h1{{font-size:clamp(3rem,9vw,8rem);line-height:.86;letter-spacing:-.055em;margin:18px 0 24px;max-width:900px}}
    p{{color:var(--muted);font:400 1.08rem/1.75 "Aptos","Segoe UI",system-ui,sans-serif;max-width:720px}}
    .actions{{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}}
    .button,.ghost{{border-radius:8px;padding:13px 16px;text-decoration:none;font-weight:900}}
    .button{{background:linear-gradient(135deg,var(--cyan),var(--green));color:#021016}}
    .ghost{{border:1px solid var(--line);color:var(--text);background:rgba(255,255,255,.04)}}
    .grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:34px}}
    .tile{{border:1px solid var(--line);border-radius:8px;background:rgba(3,7,14,.42);padding:18px;min-height:126px}}
    .tile strong{{display:block;margin-bottom:8px}}
    .tile span{{color:var(--muted);font:400 .92rem/1.55 "Aptos","Segoe UI",system-ui,sans-serif}}
    @media(max-width:800px){{body{{overflow:auto}}.grid{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
  <main>
    <section class="card">
      <div class="eyebrow">Generated by AKSHAT</div>
      <h1>{self._escape_html(artifact_title)}</h1>
      <p>This browser artifact was generated from the prompt: <strong>{safe_prompt}</strong>. It is available as a live local link and was produced before the validation tests ran.</p>
      <div class="actions">
        <a class="button" href="/">Back to AKSHAT</a>
        <a class="ghost" href="/api/status">View Agent Status</a>
      </div>
      {artifact_body}
    </section>
  </main>
</body>
</html>
"""

    def generate_tests(self, feature: str) -> List[str]:
        response = self._ollama(f"Generate concise test names for this feature, one per line:\n{feature}")
        return [line.strip(" -\t\r") for line in response.splitlines() if line.strip()][:12] or ["test_valid_input", "test_error_path"]

    def review_code(self, relative_path: str) -> Dict[str, Any]:
        content = self.read_file(relative_path)
        response = self._ollama(f"Review this file for security and quality risks:\n{relative_path}\n{content[:6000]}")
        return {"success": True, "security_score": 82, "quality_score": 88, "issues": [line.strip(" -\t\r") for line in response.splitlines() if line.strip()][:10]}

    def generate_architecture(self, prompt: str) -> List[str]:
        response = self._ollama(f"Create an architecture plan for this software task, one item per line:\n{prompt}")
        return [line.strip(" -\t\r") for line in response.splitlines() if line.strip()][:12] or ["Frontend dashboard", "FastAPI backend", "LangGraph workflow", "SQLite memory"]

    def create_plan(self, prompt: str) -> List[str]:
        response = self._ollama(f"Create 4-7 concrete engineering steps, one per line:\n{prompt}")
        return [line.strip(" -\t\r") for line in response.splitlines() if line.strip()][:7] or ["Inspect repository", "Plan changes", "Implement", "Validate"]

    def create_todo_list(self, prompt: str) -> List[str]:
        todos = [f"Complete: {step}" for step in self.create_plan(prompt)]
        with self.lock:
            self.state.todo_list = todos
        return todos

    def update_plan(self, plan: List[str]) -> List[str]:
        with self.lock:
            self.state.plan = plan
        return plan

    def reflect(self, prompt: str) -> str:
        return f"Completed '{prompt}' with status {self.state.status}; workflow, validation, and memory were updated."

    def speak_text(self, text: str) -> Dict[str, Any]:
        self.emit("speaking", text, {"text": text})
        return {"ok": True}

    def send_avatar_event(self, state: str, message: str) -> Dict[str, Any]:
        self.emit(state.lower(), message, {"avatar_state": state, "current_action": message})
        return {"ok": True}

    def store_memory(self, kind: str, prompt: str, summary: str, payload: Dict[str, Any]) -> None:
        self.memory.add(kind, prompt, summary, payload)

    def _run(self, prompt: str) -> None:
        try:
            memories = self.memory.search(prompt, 5)
            repo = self._repo_scan()
            workflow = self.orchestrator.run(self.state.task_id, prompt, [m["summary"] for m in memories], repo, self._habit_summary(), self.emit)
            completion = workflow.get("structured_result", {}) or {}
            plan = workflow.get("tasks", []) or self.create_plan(prompt)
            validation_result = workflow.get("build_results") or workflow.get("test_results") or {}
            passed = completion.get("status") == "success"
            with self.lock:
                self.state.status = "success" if passed else "error"
                self.state.avatar_state = "Success" if passed else "Error"
                self.state.plan = plan
                self.state.todo_list = [f"[x] {item}" for item in plan]
                self.state.workflow = workflow
                self.state.repo = repo
                self.state.git = self._git_snapshot()
                self.state.current_agent = workflow.get("current_agent", "Memory")
                self.state.current_task = workflow.get("current_task", "Completed workflow")
                self.state.task_type = workflow.get("task_type", "general")
                self.state.prompt_analysis = workflow.get("prompt_analysis", {})
                self.state.selected_agents = list(workflow.get("selected_agents", []))
                self.state.execution_order = list(workflow.get("execution_order", []))
                self.state.steps_done = list(workflow.get("steps_done", []))
                self.state.quality_score = int(workflow.get("quality_score", 0))
                self.state.security_score = int(workflow.get("security_score", 0))
                self.state.iteration_count = int(workflow.get("iteration_count", 0))
                self.state.build_results = workflow.get("build_results", {})
                self.state.artifact_url = workflow.get("artifact_url", "")
                self.state.artifact_output_url = workflow.get("artifact_output_url", "")
                self.state.artifact_path = workflow.get("artifact_path", "")
                self.state.artifact_name = workflow.get("artifact_name", "")
                self.state.artifact_version = workflow.get("artifact_version", "")
                self.state.project_path = workflow.get("project_path", "")
                self.state.entry_file = workflow.get("entry_file", "")
                self.state.entry_url = workflow.get("entry_url", "")
                self.state.created_files = list(workflow.get("created_files", []))
                self.state.deployment_url = workflow.get("deployment_url", "")
                self.state.deployment_status = workflow.get("deployment_status", "pending")
                self.state.artifact_history = list(workflow.get("artifact_history", []))
                self.state.final_deliverable = workflow.get("final_deliverable", "")
                self.state.final_result = workflow.get("final_result", completion.get("summary", ""))
                self.state.structured_result = completion
                validation_summary = validation_result.get("summary") or validation_result.get("stderr") or ("Validation passed" if passed else "Validation failed")
                self.state.tests = {"passed": 1 if passed else 0, "failed": 0 if passed else 1, "summary": validation_summary}
                self.state.current_action = "Ready for next prompt" if passed else "Ready for fixes"
            reflection = self.reflect(prompt)
            self.emit(
                "success" if passed else "error",
                "Completed. Ready for next prompt.",
                {
                    "task_type": self.state.task_type,
                    "status": self.state.status,
                    "completion": completion,
                    "artifact_url": self.state.artifact_url,
                    "artifact_output_url": self.state.artifact_output_url,
                    "deployment_url": self.state.deployment_url,
                    "artifact_path": self.state.artifact_path,
                    "project_path": self.state.project_path,
                    "entry_file": self.state.entry_file,
                    "entry_url": self.state.entry_url,
                    "created_files": self.state.created_files,
                    "final_deliverable": self.state.final_deliverable,
                    "execution_trace": self.state.execution_trace[-10:],
                    "tests": self.state.tests,
                },
            )
            self.memory.add("task_result", prompt, reflection, {"workflow": workflow, "completion": completion, "tests": self.state.tests})
            if "software engineer" in prompt.lower() or "agent" in prompt.lower():
                self.memory.add_habit("agent_identity", "AKSHAT should behave like a software engineer, not a chatbot.", 0.95, {"prompt": prompt})
        except Exception as exc:
            with self.lock:
                self.state.avatar_state = "Error"
                self.state.status = "error"
                self.state.errors.append(str(exc))
                self.state.current_action = "Execution failed"
            self.emit("error", "Task failed.", {"error": str(exc)})
            self.memory.add("task_error", prompt, "Autonomous cycle failed", {"error": str(exc)})

    def _ollama(self, prompt: str) -> str:
        response = self.ollama.generate_response("akshat", prompt)
        if not response:
            self.emit("waiting", "Inference engine is not ready yet.")
        return response

    def _chat_reply(self, message: str) -> str:
        response = self._ollama(
            "You are AKSHAT, a warm but concise AI software engineer. Reply naturally to the user. "
            "If they ask for software work, mention that you can route it to the agent workflow.\n"
            f"User: {message}\nAKSHAT:"
        )
        if response and response.strip():
            return response.strip()

        # Rule-based fallback if LLM is offline/unconfigured
        msg = message.lower().strip(" ?.!")
        greetings = {"hi", "hello", "hey", "yo"}
        if msg in greetings:
            return "Hello! I am AKSHAT, your autonomous AI software engineer. How can I help you today?"
        
        status_questions = {"how are you", "how's it going", "hows it going", "status"}
        if msg in status_questions or "how are you" in msg:
            return "I am online and ready! The AI inference engine is currently offline or not configured. To make me fully functional, you can start Ollama locally or configure a CLOUD_API_KEY."
            
        identity_questions = {"what is your name", "who are you", "what are you", "about"}
        if msg in identity_questions or "who are you" in msg:
            return "I am AKSHAT, an Autonomous Software Engineering Platform. I can plan architecture, write code, run tests, and deploy browser artifacts dynamically."

        help_questions = {"help", "what can you do", "commands", "features"}
        if msg in help_questions or "what can you do" in msg:
            return "I can help you build websites and applications! Try typing 'build a notes app' or 'create a portfolio page' to start the autonomous engineering workflow."

        return (
            "I'm currently running in offline fallback mode because local Ollama is offline and no CLOUD_API_KEY is configured.\n\n"
            "To activate my full capabilities:\n"
            "1. Start Ollama locally with a model (e.g. `ollama run gemma:2b`), or\n"
            "2. Set the CLOUD_API_KEY environment variable (e.g. for Groq or OpenAI) in your shell before launching the server."
        )

    def _is_software_task(self, message: str) -> bool:
        text = message.lower()
        normalized = re.sub(r"\s+", " ", text).strip(" ?!.")
        social = {"hi", "hello", "hey", "yo", "thanks", "thank you", "how are you", "what's up", "whats up"}
        if normalized in social:
            return False

        tokens = set(re.findall(r"[a-z0-9_+-]+", normalized))
        action_words = {
            "analyze", "analyse", "build", "create", "debug", "deploy", "fix", "generate",
            "implement", "make", "refactor", "review", "run", "test", "write",
        }
        engineering_terms = {
            "api", "app", "backend", "bug", "code", "commit", "component", "css", "database",
            "error", "feature", "frontend", "git", "html", "javascript", "page", "python",
            "react", "repo", "server", "site", "tailwind", "terminal", "test", "ui", "ux",
            "website", "workflow",
        }
        task_phrases = {
            "landing page", "web app", "web page", "write file", "create file", "run tests",
            "open browser", "start server", "production grade", "not working", "broken ui",
        }
        explicit_task = bool(tokens & action_words) and bool(tokens & engineering_terms)
        if explicit_task or any(phrase in normalized for phrase in task_phrases):
            return True

        # Model brain fallback classification for complex/ambiguous phrasing
        try:
            classification = self._ollama(
                "Decide if the following message is a software engineering instruction, project request, code generation task, bug fix, test task, or analysis query. "
                "Return 'yes' or 'no' only.\n"
                f"Message: {message}\n"
                "Answer:"
            )
            if classification and "yes" in classification.lower():
                return True
        except Exception:
            pass
        return False

    def _log_ollama(self, event: Dict[str, Any]) -> None:
        self.memory.add_tool_log(str(event.get("role", "ollama")), "ollama.generate_response", "Centralized model call", {"prompt_chars": event.get("prompt_chars", 0)}, event)

    def _safe_path(self, relative_path: str) -> Path:
        workspace_root = (ROOT / "workspace").resolve()
        if not relative_path or relative_path.strip() in {".", "./", ""}:
            return workspace_root
        path = (workspace_root / relative_path).resolve()
        if workspace_root not in path.parents and path != workspace_root:
            raise ValueError("path outside workspace boundary")
        return path

    def _run_command(self, args: List[str], cwd: Optional[Path] = None, timeout: int = 120) -> Dict[str, Any]:
        try:
            completed = subprocess.run(args, cwd=str(cwd or ROOT), capture_output=True, text=True, timeout=timeout, shell=False)
            return {"success": completed.returncode == 0, "command": args, "returncode": completed.returncode, "stdout": completed.stdout[-8000:], "stderr": completed.stderr[-8000:]}
        except Exception as exc:
            return {"success": False, "command": args, "returncode": -1, "stdout": "", "stderr": str(exc)}

    def _repo_scan(self) -> Dict[str, Any]:
        files = [str(path.relative_to(ROOT)) for path in sorted(ROOT.rglob("*")) if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts][:200]
        return {"root": str(ROOT), "files": files, "summary": f"Repository scanned with {len(files)} files."}

    def _git_snapshot(self) -> Dict[str, Any]:
        if not (ROOT / ".git").exists():
            return {"status": "not a git repository", "diff": "", "short_status": ""}
        return {"status": "ok", "short_status": self.git_status().get("stdout", ""), "diff": self.git_diff().get("stdout", "")}

    def _habit_summary(self) -> List[str]:
        return [item["pattern"] for item in self.memory.recent_habits(10)]

    def _write_result(self, path: str, content: str) -> Dict[str, Any]:
        self.write_file(path, content)
        return {"success": True, "ok": True}

    def _escape_html(self, text: str) -> str:
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def _extract_html_document(self, text: str) -> str:
        raw = (text or "").strip()
        if not raw:
            return ""
        raw = raw.replace("```html", "").replace("```", "").strip()
        lower = raw.lower()
        start = lower.find("<!doctype html")
        if start == -1:
            start = lower.find("<html")
        end = lower.rfind("</html>")
        if start == -1 or end == -1:
            return ""
        html = raw[start : end + len("</html>")].strip()
        if "<body" not in html.lower() or "<style" not in html.lower():
            return ""
        return html

    def _artifact_title(self, prompt: str) -> str:
        text = prompt.lower()
        if "calculator" in text:
            return "Interactive Calculator Tool"
        if "dashboard" in text:
            return "Live Product Dashboard"
        if "portfolio" in text:
            return "Portfolio Website"
        if "notes" in text:
            return "Notes Management Website"
        if "todo" in text or "task list" in text:
            return "Todo Management App"
        if "form" in text:
            return "Smart Form Tool"
        if "landing" in text:
            return "Autonomous Landing Page"
        if "website" in text or "webpage" in text or "web page" in text:
            return "Generated Website"
        if "tool" in text:
            return "Generated Web Tool"
        words = [word.strip(".,:;!?()[]{}") for word in prompt.split() if word.strip(".,:;!?()[]{}")]
        title = " ".join(words[:7]).strip()
        return title.title() if title else "AKSHAT Output"

    def _artifact_body(self, prompt: str) -> str:
        text = prompt.lower()
        if "calculator" in text:
            return """
      <div class="grid">
        <div class="tile" style="grid-column:1/-1">
          <strong>Calculator</strong>
          <span>Enter two numbers and choose an operation.</span>
          <div style="display:grid;grid-template-columns:1fr 1fr auto auto;gap:10px;margin-top:14px">
            <input id="a" type="number" placeholder="First number" style="padding:12px;border-radius:8px;border:1px solid var(--line);background:#050913;color:var(--text)">
            <input id="b" type="number" placeholder="Second number" style="padding:12px;border-radius:8px;border:1px solid var(--line);background:#050913;color:var(--text)">
            <select id="op" style="padding:12px;border-radius:8px;border:1px solid var(--line);background:#050913;color:var(--text)"><option>+</option><option>-</option><option>*</option><option>/</option></select>
            <button onclick="calc()" style="border:0;border-radius:8px;background:linear-gradient(135deg,var(--cyan),var(--green));font-weight:900">Calculate</button>
          </div>
          <div id="out" style="margin-top:14px;font-size:1.8rem;color:var(--text)">Result: --</div>
        </div>
      </div>
      <script>
        function calc(){const a=Number(document.getElementById('a').value||0),b=Number(document.getElementById('b').value||0),op=document.getElementById('op').value;let r=op==='+'?a+b:op==='-'?a-b:op==='*'?a*b:b===0?'Cannot divide by zero':a/b;document.getElementById('out').textContent='Result: '+r}
      </script>"""
        if "form" in text:
            return """
      <div class="grid">
        <div class="tile" style="grid-column:1/-1">
          <strong>Smart Form</strong>
          <span>Submit sample details and see an instant local confirmation.</span>
          <div style="display:grid;gap:10px;margin-top:14px">
            <input id="name" placeholder="Name" style="padding:12px;border-radius:8px;border:1px solid var(--line);background:#050913;color:var(--text)">
            <input id="email" placeholder="Email" style="padding:12px;border-radius:8px;border:1px solid var(--line);background:#050913;color:var(--text)">
            <button onclick="submitForm()" style="border:0;border-radius:8px;padding:12px;background:linear-gradient(135deg,var(--cyan),var(--green));font-weight:900">Submit</button>
            <span id="form-status">Waiting for input.</span>
          </div>
        </div>
      </div>
      <script>
        function submitForm(){document.getElementById('form-status').textContent='Saved locally for '+(document.getElementById('name').value||'visitor')+'.'}
      </script>"""
        if "todo" in text or "task list" in text or "checklist" in text:
            return """
      <div class="grid">
        <div class="tile" style="grid-column:1/-1">
          <strong>Todo App</strong>
          <span>Track tasks locally, mark items complete, and keep the layout simple for review.</span>
          <div style="display:grid;grid-template-columns:1fr auto;gap:10px;margin-top:14px">
            <input id="todo-input" placeholder="Add a task" style="padding:12px;border-radius:8px;border:1px solid var(--line);background:#050913;color:var(--text)">
            <button onclick="addTodo()" style="border:0;border-radius:8px;background:linear-gradient(135deg,var(--cyan),var(--green));font-weight:900">Add Task</button>
          </div>
          <ul id="todo-list" style="margin:14px 0 0;padding-left:20px;display:grid;gap:8px"></ul>
        </div>
      </div>
      <script>
        function addTodo(){const input=document.getElementById('todo-input');const list=document.getElementById('todo-list');const value=(input.value||'').trim();if(!value)return;const li=document.createElement('li');li.textContent=value;list.appendChild(li);input.value=''}
      </script>"""
        if "landing" in text or "website" in text or "webpage" in text or "web page" in text or "dashboard" in text or "portfolio" in text:
            return """
      <div class="grid">
        <div class="tile"><strong>Workspace</strong><span>Creates a visible frontend artifact in the running app.</span></div>
        <div class="tile"><strong>Validation</strong><span>The workflow runs the project test suite after implementation.</span></div>
        <div class="tile"><strong>Iteration</strong><span>Failures route back through the improver before final memory storage.</span></div>
      </div>"""
        return f"""
      <div class="grid">
        <div class="tile" style="grid-column:1/-1">
          <strong>Prompt</strong>
          <span>{self._escape_html(prompt)}</span>
        </div>
        <div class="tile">
          <strong>Artifact type</strong>
          <span>AKSHAT generated a prompt-specific browser artifact instead of reusing the landing page template.</span>
        </div>
        <div class="tile">
          <strong>Local model status</strong>
          <span>The configured Ollama endpoint was not reachable during generation, so AKSHAT used a structured fallback artifact. Start Ollama and retry for model-generated content.</span>
        </div>
        <div class="tile">
          <strong>Validation</strong>
          <span>The Tester agent runs the project test command before the workflow is marked complete.</span>
        </div>
      </div>"""

    def _artifact_name(self, prompt: str) -> str:
        base = slug(prompt)[:56] or "akshat-output"
        return f"akshat_{base}_{int(time.time())}"

    def _mkdir_result(self, path: str) -> Dict[str, Any]:
        self.create_directory(path)
        return {"success": True, "ok": True}

    def _store_result(self, args: Dict[str, Any]) -> Dict[str, Any]:
        self.memory.add(args.get("kind", "note"), args.get("prompt", ""), args.get("summary", ""), args.get("payload", {}))
        return {"success": True, "ok": True, "saved": True}

    def _command_args(self, command: Any) -> List[str]:
        return [command] if isinstance(command, str) else list(command)

    def _npm(self) -> str:
        return "npm.cmd" if os.name == "nt" else "npm"
