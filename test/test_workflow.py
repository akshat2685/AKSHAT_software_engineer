from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.core import AkshatCore
from backend.graph.workflow import PromptAnalyzer, WorkflowOrchestrator
from backend.runtime import EventBus, MemoryStore
from backend.services.ollama_service import OllamaService


class FakeToolRunner:
    def __init__(self, fail_first_test: bool = False) -> None:
        self.fail_first_test = fail_first_test
        self.test_runs = 0
        self.calls: list[tuple[str, dict[str, object]]] = []

    def __call__(self, name: str, args: dict[str, object]) -> dict[str, object]:
        self.calls.append((name, dict(args)))
        if name == "build_artifact":
            artifact_name = str(args.get("artifact_name", "akshat-output"))
            return {
                "success": True,
                "ok": True,
                "name": artifact_name,
                "version": str(args.get("artifact_version", "20260101010101")),
                "path": f"src/assets/projects/{artifact_name}/index.html",
                "project_path": f"src/assets/projects/{artifact_name}",
                "entry_file": f"src/assets/projects/{artifact_name}/index.html",
                "entry_url": f"http://127.0.0.1:3000/assets/projects/{artifact_name}/index.html",
                "created_files": [
                    f"src/assets/projects/{artifact_name}/index.html",
                    f"src/assets/projects/{artifact_name}/styles.css",
                    f"src/assets/projects/{artifact_name}/script.js",
                    f"src/assets/projects/{artifact_name}/manifest.json",
                ],
                "url": f"http://127.0.0.1:3000/review/{artifact_name}",
                "output_url": f"http://127.0.0.1:3000/assets/projects/{artifact_name}/index.html",
                "deploy_url": f"http://127.0.0.1:3000/deploy/{artifact_name}",
                "review_url": f"http://127.0.0.1:3000/review/{artifact_name}",
            }
        if name in {"run_build", "validate_artifact"}:
            return {"success": True, "returncode": 0, "stdout": "ok", "stderr": "", "summary": "build ok"}
        if name == "run_tests":
            self.test_runs += 1
            if self.fail_first_test and self.test_runs == 1:
                return {"success": False, "returncode": 1, "stdout": "", "stderr": "first test failed", "summary": "failed"}
            return {"success": True, "returncode": 0, "stdout": "ok", "stderr": "", "summary": "tests ok"}
        if name == "deploy_artifact":
            artifact_name = str(args.get("artifact_name", "akshat-output"))
            return {
                "success": True,
                "ok": True,
                "artifact_name": artifact_name,
                "artifact_path": str(args.get("artifact_path", "")),
                "review_url": f"http://127.0.0.1:3000/review/{artifact_name}",
                "deploy_url": f"http://127.0.0.1:3000/deploy/{artifact_name}",
                "output_url": f"http://127.0.0.1:3000/assets/projects/{artifact_name}/index.html",
                "version": str(args.get("artifact_version", "20260101010101")),
                "summary": "deployed",
            }
        return {"success": True, "ok": True, "summary": name}


class WorkflowTests(unittest.TestCase):
    def test_prompt_analyzer_classifies_prompt_types(self) -> None:
        analyzer = PromptAnalyzer()

        self.assertEqual(analyzer.analyze("build a dashboard website").task_type, "website")
        self.assertEqual(analyzer.analyze("please deploy this release").task_type, "deploy")
        self.assertEqual(analyzer.analyze("fix the login bug").task_type, "bug_fix")
        self.assertEqual(analyzer.analyze("research the API behavior").task_type, "research")
        self.assertEqual(analyzer.analyze("implement a calculator tool").task_type, "code")

    @patch("backend.agents.base.generate_response", return_value="")
    def test_website_prompt_routes_through_deploy(self, _mock_generate_response: object) -> None:
        runner = FakeToolRunner()
        orchestrator = WorkflowOrchestrator(lambda _: "", runner)
        events: list[tuple[str, str]] = []

        def emit(kind: str, message: str, data: dict[str, object]) -> None:
            events.append((kind, message))

        state = orchestrator.run("task-1", "Build a website dashboard", [], {"summary": "repo"}, [], emit)

        self.assertEqual(state["task_type"], "website")
        self.assertIn("Deploy", state["selected_agents"])
        self.assertIn("Deploy", state["execution_order"])
        self.assertEqual(state["deployment_status"], "published")
        self.assertTrue(state["deployment_url"].endswith("/deploy/" + state["artifact_name"]))
        self.assertTrue(state["artifact_history"])
        self.assertIn("index.html", "\n".join(state["created_files"]))
        self.assertEqual(state["structured_result"]["status"], "success")
        self.assertTrue(any(kind == "workflow" for kind, _ in events))

    @patch("backend.agents.base.generate_response", return_value="")
    def test_bug_fix_prompt_retries_through_improver(self, _mock_generate_response: object) -> None:
        runner = FakeToolRunner(fail_first_test=True)
        orchestrator = WorkflowOrchestrator(lambda _: "", runner)
        events: list[tuple[str, str]] = []

        def emit(kind: str, message: str, data: dict[str, object]) -> None:
            events.append((kind, message))

        state = orchestrator.run("task-2", "Fix the checkout bug", [], {"summary": "repo"}, [], emit)

        self.assertEqual(state["task_type"], "bug_fix")
        self.assertTrue(state["tests_passed"])
        self.assertGreaterEqual(state["execution_order"].count("Tester"), 2)
        self.assertIn("Improver", state["execution_order"])
        self.assertEqual(state["test_results"]["returncode"], 0)
        self.assertEqual(state["structured_result"]["status"], "success")


class ChatRoutingTests(unittest.TestCase):
    def make_core(self) -> AkshatCore:
        db_file = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        db_file.close()
        return AkshatCore(MemoryStore(Path(db_file.name)), EventBus())

    @patch("backend.core.OllamaService.generate_response", return_value="Hello. Give me a software task when you want agents.")
    def test_general_chat_does_not_start_agent_workflow(self, _mock_generate_response: object) -> None:
        core = self.make_core()

        response = core.chat("hi")

        self.assertEqual(response["mode"], "chat")
        self.assertEqual(response["state"]["status"], "idle")
        self.assertEqual(response["state"]["selected_agents"], [])
        self.assertEqual(response["state"]["workflow"], {})

    @patch("backend.core.OllamaService.generate_response", return_value="")
    def test_software_task_routes_to_agent_workflow(self, _mock_generate_response: object) -> None:
        core = self.make_core()

        with patch.object(core, "submit", return_value=core.snapshot()) as submit:
            response = core.chat("build a portfolio website")

        self.assertEqual(response["mode"], "workflow")
        submit.assert_called_once_with("build a portfolio website")

    @patch("backend.core.OllamaService.generate_response", return_value="")
    def test_website_artifact_creates_project_files(self, _mock_generate_response: object) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("backend.core.ROOT", Path(tmp)):
                core = self.make_core()
                result = core.build_artifact("build a notes app", "akshat_notes_test", "20260101010101", "website")

        self.assertTrue(result["success"])
        self.assertEqual(Path(result["path"]).name, "index.html")
        self.assertIn("projects/akshat_notes_test/index.html", result["created_files"])
        self.assertIn("projects/akshat_notes_test/styles.css", result["created_files"])
        self.assertIn("projects/akshat_notes_test/script.js", result["created_files"])
        self.assertTrue(result["fallback_used"])

    def test_generated_project_rejects_unsafe_paths(self) -> None:
        payload = json.dumps(
            {
                "entry": "index.html",
                "files": [
                    {"path": "index.html", "content": "<!doctype html><html><head></head><body></body></html>"},
                    {"path": "styles.css", "content": "body{}"},
                    {"path": "script.js", "content": "console.log('ok')"},
                    {"path": "manifest.json", "content": "{}"},
                    {"path": "../../.env", "content": "nope"},
                ],
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            with patch("backend.core.ROOT", Path(tmp)):
                with patch("backend.core.OllamaService.generate_response", return_value=payload):
                    core = self.make_core()
                    with self.assertRaises(ValueError):
                        core.build_artifact("build a website", "akshat_unsafe_test", "20260101010101", "website")


class CloudFallbackTests(unittest.TestCase):
    def test_cloud_provider_disables_without_key_and_masks_status(self) -> None:
        with patch.dict(os.environ, {"CLOUD_API_KEY": ""}, clear=False):
            service = OllamaService(
                url="http://localhost:11434/api/generate",
                model="free01/gemma4:e4b",
                cloud_api_key="",
                cloud_api_url="",
                cloud_api_model="",
            )

        status = service.status()
        payload = json.dumps(status)

        self.assertFalse(status["cloud"]["ready"])
        self.assertFalse(status["cloud"]["api_key_present"])
        self.assertIn("disabled", status["cloud"]["message"].lower())
        self.assertNotIn("gsk_", payload)

    def test_cloud_fallback_is_used_when_ollama_fails(self) -> None:
        service = OllamaService(
            url="http://localhost:11434/api/generate",
            model="free01/gemma4:e4b",
            cloud_api_key="gsk_example_key",
            cloud_api_url="https://example.com/v1/chat/completions",
            cloud_api_model="cloud-model",
        )

        with patch.object(service, "_generate_with_ollama", return_value=("", "timeout")):
            with patch.object(service.cloud, "generate_response", return_value="cloud answer") as cloud_generate:
                response = service.generate_response("developer", "Explain the fallback chain")

        self.assertEqual(response, "cloud answer")
        cloud_generate.assert_called_once()
        self.assertTrue(service.cloud.ready)


if __name__ == "__main__":
    unittest.main()
