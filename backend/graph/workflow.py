from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from backend.agents.architect import ArchitectAgent
from backend.agents.developer import DeveloperAgent
from backend.agents.deploy import DeployAgent
from backend.agents.improver import ImproverAgent
from backend.agents.memory import MemoryAgent
from backend.agents.project_manager import ProjectManagerAgent
from backend.agents.reviewer import ReviewerAgent
from backend.agents.tester import TesterAgent

AGENT_ORDER = [
    "ProjectManager",
    "Architect",
    "Developer",
    "Tester",
    "Deploy",
    "Reviewer",
    "Improver",
    "Memory",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PromptAnalysis:
    task_type: str
    confidence: float
    selected_agents: List[str]
    execution_order: List[str]
    needs_tests: bool
    needs_deploy: bool
    needs_review: bool
    artifact_kind: str
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PromptAnalyzer:
    def analyze(self, prompt: str) -> PromptAnalysis:
        text = (prompt or "").strip().lower()
        if not text:
            text = "build a reviewable output"

        task_type = self._task_type(text)
        needs_tests = task_type in {"code", "website", "deploy", "bug_fix"}
        needs_deploy = task_type in {"website", "deploy"}
        needs_review = True
        artifact_kind = "report" if task_type == "research" else "artifact"

        pipeline = ["ProjectManager"]
        if task_type != "general":
            pipeline.append("Architect")
        pipeline.append("Developer")
        if needs_tests:
            pipeline.append("Tester")
        if needs_deploy:
            pipeline.append("Deploy")
        if needs_review:
            pipeline.append("Reviewer")
        pipeline.append("Memory")

        notes = [f"Classified as {task_type}."]
        if needs_deploy:
            notes.append("Deployment URL should point to a stable local review surface.")
        if task_type == "bug_fix":
            notes.append("Include improver retry if validation fails.")

        return PromptAnalysis(
            task_type=task_type,
            confidence=0.88 if task_type != "general" else 0.5,
            selected_agents=list(dict.fromkeys(pipeline)),
            execution_order=list(dict.fromkeys(pipeline)),
            needs_tests=needs_tests,
            needs_deploy=needs_deploy,
            needs_review=needs_review,
            artifact_kind=artifact_kind,
            notes=notes,
        )

    def _task_type(self, text: str) -> str:
        deploy_terms = ("deploy", "publish", "release", "ship", "launch")
        website_terms = ("website", "web page", "webpage", "landing page", "dashboard", "portfolio", "site")
        bug_terms = ("bug", "fix", "error", "broken", "regression", "crash", "fails", "failure")
        research_terms = ("research", "explain", "compare", "analyze", "analyse", "summary", "investigate", "why", "how")
        code_terms = ("build", "implement", "create", "write", "code", "feature", "app", "tool", "form", "calculator")

        if any(term in text for term in deploy_terms):
            return "deploy" if "website" not in text else "website"
        if any(term in text for term in website_terms):
            return "website"
        if any(term in text for term in bug_terms):
            return "bug_fix"
        if any(term in text for term in research_terms):
            return "research"
        if any(term in text for term in code_terms):
            return "code"
        return "general"


@dataclass
class WorkflowState:
    project_id: str
    user_request: str
    current_agent: str = "ProjectManager"
    current_task: str = "Understanding request"
    task_type: str = "general"
    prompt_analysis: Dict[str, Any] = field(default_factory=dict)
    selected_agents: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    steps_done: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    architecture: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    generated_code: str = ""
    test_results: Dict[str, Any] = field(default_factory=dict)
    build_results: Dict[str, Any] = field(default_factory=dict)
    tests_passed: bool = False
    review_reports: List[str] = field(default_factory=list)
    fix_history: List[str] = field(default_factory=list)
    quality_score: int = 0
    security_score: int = 0
    iteration_count: int = 0
    artifact_name: str = ""
    artifact_version: str = ""
    artifact_url: str = ""
    artifact_output_url: str = ""
    artifact_path: str = ""
    project_path: str = ""
    entry_file: str = ""
    entry_url: str = ""
    created_files: List[str] = field(default_factory=list)
    deployment_url: str = ""
    deployment_status: str = "pending"
    artifact_history: List[Dict[str, Any]] = field(default_factory=list)
    memory_context: List[str] = field(default_factory=list)
    agent_context: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    agent_commands: Dict[str, str] = field(default_factory=dict)
    agent_outputs: Dict[str, str] = field(default_factory=dict)
    agent_runs: List[Dict[str, Any]] = field(default_factory=list)
    execution_trace: List[Dict[str, Any]] = field(default_factory=list)
    replay_events: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, str]] = field(default_factory=list)
    final_deliverable: str = ""
    final_result: str = ""
    structured_result: Dict[str, Any] = field(default_factory=dict)
    workflow_engine: str = "prompt_routed_sequence"

    def record(self, agent: str, task: str, output: str, payload: Dict[str, Any] | None = None) -> None:
        entry = payload or {}
        self.current_agent = agent
        self.current_task = task
        self.agent_outputs[agent] = output
        self.events.append({"agent": agent, "task": task, "output": output})
        self.execution_trace.append(
            {
                "timestamp": _utc_now(),
                "agent": agent,
                "task": task,
                "output": output,
                "payload": entry,
            }
        )
        self.agent_runs.append(
            {
                "timestamp": _utc_now(),
                "agent_name": agent,
                "action": task,
                "result": output,
                "payload": entry,
            }
        )
        self.execution_order.append(agent)
        self.steps_done.append(f"{agent}: {task}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WorkflowOrchestrator:
    def __init__(
        self,
        llm: Callable[[str], str],
        tool_runner: Callable[[str, Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        self.llm = llm
        self.tool_runner = tool_runner
        self.analyzer = PromptAnalyzer()
        self.agents = {
            "project_manager": ProjectManagerAgent(tool_runner),
            "architect": ArchitectAgent(tool_runner),
            "developer": DeveloperAgent(tool_runner),
            "tester": TesterAgent(tool_runner),
            "deploy": DeployAgent(tool_runner),
            "reviewer": ReviewerAgent(tool_runner),
            "improver": ImproverAgent(tool_runner),
            "memory": MemoryAgent(tool_runner),
        }

    def run(
        self,
        project_id: str,
        prompt: str,
        memory_context: List[str],
        repo: Dict[str, Any],
        habits: List[str],
        emit: Callable[[str, str, Dict[str, Any]], None],
    ) -> Dict[str, Any]:
        state = WorkflowState(
            project_id=project_id,
            user_request=prompt,
            memory_context=memory_context + habits,
        )
        analysis = self.analyzer.analyze(prompt)
        state.task_type = analysis.task_type
        state.prompt_analysis = analysis.to_dict()
        state.selected_agents = list(analysis.selected_agents)
        state.execution_order = []
        state.workflow_engine = "prompt_routed_sequence"
        state.artifact_name = self._artifact_name(prompt)
        state.artifact_version = self._artifact_version()
        state.agent_context = self._build_agent_context(state, analysis, repo)
        emit("workflow", f"Prompt classified as {state.task_type}", {"analysis": state.prompt_analysis})
        self._run_sequence(state, emit)
        state.structured_result = self._build_completion(state)
        state.final_result = state.structured_result.get("summary", "")
        return state.to_dict()

    def _run_sequence(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> None:
        self._run_agent("project_manager", state, emit)
        if "Architect" in state.selected_agents:
            self._run_agent("architect", state, emit)
        if "Developer" in state.selected_agents:
            self._run_agent("developer", state, emit)
        if "Tester" in state.selected_agents:
            self._run_validation_loop(state, emit)
        if "Deploy" in state.selected_agents and state.artifact_path:
            self._run_agent("deploy", state, emit)
        if "Reviewer" in state.selected_agents:
            if state.tests_passed or state.task_type in {"research", "general"} or state.deployment_status == "published":
                self._run_agent("reviewer", state, emit)
        self._run_agent("memory", state, emit)

    def _run_validation_loop(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> None:
        self._run_agent("tester", state, emit)
        retries = 0
        while not state.tests_passed and retries < 2:
            if "Improver" not in state.selected_agents:
                state.selected_agents.append("Improver")
            self._run_agent("improver", state, emit)
            self._run_agent("tester", state, emit)
            retries += 1

    def _run_agent(self, name: str, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> None:
        label = self._agent_label(name)
        context = state.agent_context.get(label, {})
        state.agent_context[label] = context
        self.agents[name].run(state, emit)

    def _build_agent_context(self, state: WorkflowState, analysis: PromptAnalysis, repo: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        review_url = f"/review/{state.artifact_name}"
        deploy_url = f"/deploy/{state.artifact_name}"
        output_url = f"/assets/{state.artifact_name}.html"
        project_url = f"/assets/projects/{state.artifact_name}/index.html"
        base = {
            "ProjectManager": {
                "task_type": analysis.task_type,
                "prompt": state.user_request,
                "memory_context": state.memory_context,
            },
            "Architect": {
                "task_type": analysis.task_type,
                "repo_summary": repo.get("summary", ""),
                "artifact_kind": analysis.artifact_kind,
            },
            "Developer": {
                "prompt": state.user_request,
                "artifact_name": state.artifact_name,
                "artifact_version": state.artifact_version,
                "review_url": review_url,
                "output_url": output_url,
                "entry_url": project_url,
                "task_type": analysis.task_type,
            },
            "Tester": {
                "task_type": analysis.task_type,
                "validation": "build" if analysis.task_type in {"website", "deploy"} else "tests",
                "artifact_path": state.artifact_path,
            },
            "Deploy": {
                "artifact_name": state.artifact_name,
                "review_url": review_url,
                "deploy_url": deploy_url,
                "output_url": project_url,
            },
            "Reviewer": {
                "artifact_url": review_url,
                "deployment_url": deploy_url,
                "task_type": analysis.task_type,
            },
            "Improver": {
                "task_type": analysis.task_type,
            },
            "Memory": {
                "task_type": analysis.task_type,
            },
        }
        return base

    def _build_completion(self, state: WorkflowState) -> Dict[str, Any]:
        execution_agents = [entry["agent_name"] for entry in state.agent_runs]
        artifacts = [item for item in state.artifact_history if item]
        summary = state.final_deliverable or state.structured_result.get("summary", "") or f"Completed {state.task_type} task."
        return {
            "task_id": state.project_id,
            "task_type": state.task_type,
            "summary": summary,
            "executed_plan": state.tasks,
            "agents_used": execution_agents,
            "execution_order": state.execution_order,
            "artifacts": artifacts,
            "deployment_url": state.deployment_url,
            "build_results": state.build_results,
            "test_results": state.test_results,
            "review_reports": state.review_reports,
            "execution_trace": state.execution_trace,
            "selected_agents": state.selected_agents,
            "prompt_analysis": state.prompt_analysis,
            "artifact_name": state.artifact_name,
            "artifact_version": state.artifact_version,
            "artifact_url": state.artifact_url,
            "artifact_output_url": state.artifact_output_url,
            "artifact_path": state.artifact_path,
            "project_path": state.project_path,
            "entry_file": state.entry_file,
            "entry_url": state.entry_url,
            "created_files": state.created_files,
            "status": "success" if state.tests_passed or state.task_type == "research" or state.deployment_status == "published" else "needs_attention",
        }

    def _agent_label(self, name: str) -> str:
        if name == "project_manager":
            return "ProjectManager"
        return "".join(part.title() for part in name.split("_"))

    def _artifact_name(self, prompt: str) -> str:
        base = "".join(ch.lower() if ch.isalnum() else "-" for ch in prompt).strip("-")[:56] or "akshat-output"
        return f"akshat_{base}_{int(datetime.now(timezone.utc).timestamp())}"

    def _artifact_version(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
