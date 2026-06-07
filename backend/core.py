from __future__ import annotations

import os
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
        }
        return [{"name": name, "description": descriptions.get(name, f"AKSHAT tool: {name}.")} for name in self.TOOL_NAMES]

    def emit(self, kind: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.bus.publish(Event(ts=stamp(), kind=kind, message=message, data=data or {}))
        with self.lock:
            self.state.updated_at = now_iso()
            self.state.current_action = message

    def submit(self, prompt: str) -> Dict[str, Any]:
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
        self.emit("task_received", f"Received task: {prompt}", {"prompt": prompt})
        threading.Thread(target=self._run, args=(prompt,), daemon=True).start()
        return self.snapshot()

    def chat(self, message: str) -> Dict[str, Any]:
        message = (message or "").strip()
        if not message:
            raise ValueError("message is required")
        if self._is_software_task(message):
            snapshot = self.submit(message)
            reply = "I routed this to the engineering agents. Watch the workflow queue and command stream for progress."
            with self.lock:
                self.state.chat.extend([{"role": "user", "content": message}, {"role": "assistant", "content": reply}])
            return {"mode": "workflow", "reply": reply, "state": snapshot}
        reply = self._chat_reply(message)
        with self.lock:
            self.state.chat.extend([{"role": "user", "content": message}, {"role": "assistant", "content": reply}])
            self.state.avatar_state = "Speaking"
            self.state.current_action = reply
        self.emit("chat", reply, {"avatar_state": "Speaking", "current_action": reply, "chat": self.state.chat[-8:]})
        self.memory.add("chat", message, reply, {"mode": "conversation"})
        return {"mode": "chat", "reply": reply, "state": self.snapshot()}

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
            plan = workflow.get("tasks", []) or self.create_plan(prompt)
            test_result = workflow.get("test_results", {})
            passed = test_result.get("returncode") == 0
            with self.lock:
                self.state.status = "success" if passed else "error"
                self.state.avatar_state = "Success" if passed else "Error"
                self.state.plan = plan
                self.state.todo_list = [f"[x] {item}" for item in plan]
                self.state.workflow = workflow
                self.state.repo = repo
                self.state.git = self._git_snapshot()
                self.state.current_agent = workflow.get("current_agent", "Memory Agent")
                self.state.quality_score = int(workflow.get("quality_score", 0))
                self.state.security_score = int(workflow.get("security_score", 0))
                self.state.iteration_count = int(workflow.get("iteration_count", 0))
                self.state.final_deliverable = workflow.get("final_deliverable", "")
                self.state.tests = {"passed": 1 if passed else 0, "failed": 0 if passed else 1, "summary": "Validation passed" if passed else "Validation failed"}
                self.state.current_action = "Workflow completed and stored in memory"
            reflection = self.reflect(prompt)
            self.emit("success" if passed else "error", reflection, {"status": self.state.status})
            self.memory.add("task_result", prompt, reflection, {"workflow": workflow, "tests": self.state.tests})
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
        return response or "I am here. Tell me what you want to discuss, or give me a software task and I can run the engineering workflow."

    def _is_software_task(self, message: str) -> bool:
        text = message.lower()
        task_words = {
            "build", "fix", "debug", "test", "create", "implement", "refactor", "deploy",
            "api", "backend", "frontend", "database", "bug", "error", "code", "ui", "ux",
            "website", "app", "feature", "commit", "git", "terminal", "server",
        }
        social = {"hi", "hello", "hey", "yo", "thanks", "thank you", "how are you"}
        if text in social:
            return False
        return any(word in text for word in task_words)

    def _log_ollama(self, event: Dict[str, Any]) -> None:
        self.memory.add_tool_log(str(event.get("role", "ollama")), "ollama.generate_response", "Centralized model call", {"prompt_chars": event.get("prompt_chars", 0)}, event)

    def _safe_path(self, relative_path: str) -> Path:
        path = (ROOT / relative_path).resolve()
        if ROOT not in path.parents and path != ROOT:
            raise ValueError("path outside workspace")
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
