from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

from backend.agents.architect import ArchitectAgent
from backend.agents.developer import DeveloperAgent
from backend.agents.devops import DevOpsAgent
from backend.agents.improver import ImproverAgent
from backend.agents.memory import MemoryAgent
from backend.agents.project_manager import ProjectManagerAgent
from backend.agents.reviewer import ReviewerAgent
from backend.agents.tester import TesterAgent
from backend.agents.tools_integration import ToolsIntegrationAgent
from backend.agents.research import ResearchAgent
from backend.agents.ux_frontend import UXFrontendAgent
from backend.agents.data_engineer import DataEngineerAgent
from backend.agents.security import SecurityAgent
from backend.agents.performance import PerformanceAgent
from backend.agents.compliance import ComplianceAgent
from backend.agents.technical_writer import TechnicalWriterAgent
from backend.agents.cost import CostAgent
from backend.agents.debug import DebugAgent
from backend.agents.refactor import RefactorAgent
from backend.agents.documentation import DocumentationAgent
from backend.agents.dependency import DependencyAgent
from backend.agents.browser import BrowserAgent
from backend.agents.vision import VisionAgent

from backend.services.event_coordinator import event_bus
from backend.services.observability_engine import observability_engine
from backend.services.recovery_engine import recovery_engine
from backend.services.reflection_engine import reflection_engine
from backend.services.knowledge_engine import knowledge_engine

AGENT_ORDER = [
    "ProjectManager",
    "Architect",
    "Developer",
    "Tester",
    "DevOps",
    "Reviewer",
    "Improver",
    "ToolsEngine",
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
    workflow_pattern: str = "A"
    parallel_tracks: int = 1
    max_loops: int = 1
    gates: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WorkflowPatternsEngine:
    def analyze(self, prompt: str, explicit_pattern: str = "Auto") -> PromptAnalysis:
        text = (prompt or "").strip().lower()
        if not text:
            text = "build a reviewable output"

        task_type = self._task_type(text)
        needs_tests = task_type in {"code", "website", "deploy", "bug_fix"}
        needs_deploy = task_type in {"website", "deploy"}
        needs_review = True
        artifact_kind = "report" if task_type == "research" else "artifact"

        pattern = "A"
        max_loops = 1
        parallel_tracks = 1
        gates = []
        
        if explicit_pattern and explicit_pattern != "Auto":
            pattern = explicit_pattern
            if pattern == "B":
                parallel_tracks = 2
                gates.append("INTEGRATION_GATE")
            elif pattern == "C":
                max_loops = 3
        else:
            if "critical" in text or "hotfix" in text or "incident" in text:
                pattern = "E"
            elif "bug" in text and "secure" in text:
                pattern = "C"
                max_loops = 3
            elif "massive" in text or "large" in text or "swarm" in text or "parallel" in text:
                pattern = "B"
                parallel_tracks = 2
                gates.append("INTEGRATION_GATE")
            elif "research" in text or "spike" in text or "unknown" in text:
                pattern = "D"
            
        pipeline = []
        if pattern == "A" or pattern == "D":
            pipeline = ["ProjectManager", "Architect", "Developer", "Tester", "DevOps", "Reviewer"]
        elif pattern == "B":
            pipeline = ["ProjectManager", "Architect", "Developer", "Tester", "DevOps", "Reviewer"]
        elif pattern == "C":
            pipeline = ["ProjectManager", "Architect", "Developer", "Tester", "Reviewer", "Improver"]
        elif pattern == "E":
            pipeline = ["Memory", "Improver", "Reviewer", "DevOps"]
            
        if not needs_tests and "Tester" in pipeline: pipeline.remove("Tester")
        if not needs_deploy and "DevOps" in pipeline: pipeline.remove("DevOps")
        
        # Dynamic phase 1 injections based on context
        if task_type == "research" or "research" in text or "spike" in text:
            if "Research" not in pipeline:
                pipeline.insert(1, "Research") # Run right after PM
        
        if task_type == "website" or "ui" in text or "frontend" in text or "design" in text:
            if "UXFrontend" not in pipeline:
                if "Architect" in pipeline:
                    pipeline.insert(pipeline.index("Architect") + 1, "UXFrontend")
                else:
                    pipeline.insert(1, "UXFrontend")
                    
        if "data" in text or "database" in text or "schema" in text or "sql" in text:
            if "DataEngineer" not in pipeline:
                if "Developer" in pipeline:
                    pipeline.insert(pipeline.index("Developer"), "DataEngineer")
                else:
                    pipeline.insert(1, "DataEngineer")
                    
        # Dynamic phase 2 injections based on context
        if "Developer" in pipeline or "security" in text or "auth" in text:
            if "Security" not in pipeline:
                if "Developer" in pipeline:
                    pipeline.insert(pipeline.index("Developer") + 1, "Security")
                else:
                    pipeline.append("Security")
                    
        if "performance" in text or "scale" in text or "optimize" in text or "load" in text:
            if "Performance" not in pipeline:
                if "Tester" in pipeline:
                    pipeline.insert(pipeline.index("Tester") + 1, "Performance")
                else:
                    pipeline.append("Performance")
                    
        if "DevOps" in pipeline or "compliance" in text or "gdpr" in text or "legal" in text:
            if "Compliance" not in pipeline:
                if "DevOps" in pipeline:
                    pipeline.insert(pipeline.index("DevOps"), "Compliance")
                else:
                    pipeline.append("Compliance")
                    
        # Dynamic phase 3 injections
        if "Reviewer" in pipeline or "docs" in text or "documentation" in text or "readme" in text:
            if "TechnicalWriter" not in pipeline:
                if "Reviewer" in pipeline:
                    pipeline.insert(pipeline.index("Reviewer"), "TechnicalWriter")
                else:
                    pipeline.append("TechnicalWriter")
            if "Documentation" not in pipeline:
                pipeline.append("Documentation")

        if "bug" in text or "fix" in text or "debug" in text or "refactor" in text:
            if "Debug" not in pipeline:
                pipeline.append("Debug")
            if "Refactor" not in pipeline:
                pipeline.append("Refactor")

        if "dependency" in text or "package" in text or "pip" in text or "npm" in text:
            if "Dependency" not in pipeline:
                pipeline.append("Dependency")

        if "browser" in text or "ui" in text or "playwright" in text or "vision" in text or "see" in text:
            if "Browser" not in pipeline:
                pipeline.append("Browser")
            if "Vision" not in pipeline:
                pipeline.append("Vision")
        
        if "ToolsEngine" not in pipeline: pipeline.append("ToolsEngine")
        if "Memory" not in pipeline: pipeline.append("Memory")
        if "Cost" not in pipeline: pipeline.append("Cost")

        notes = [f"Classified as {task_type}.", f"Selected Workflow Pattern {pattern}."]
        print(f"[WORKFLOW ENGINE] — Pattern Selected\\n├─ Pattern: {pattern}\\n├─ Parallel Tracks: {parallel_tracks}\\n├─ Max Loops: {max_loops}\\n└─ Agents Scheduled: {pipeline}")

        return PromptAnalysis(
            task_type=task_type,
            confidence=0.88 if task_type != "general" else 0.5,
            selected_agents=list(dict.fromkeys(pipeline)),
            execution_order=list(dict.fromkeys(pipeline)),
            needs_tests=needs_tests,
            needs_deploy=needs_deploy,
            needs_review=needs_review,
            artifact_kind=artifact_kind,
            workflow_pattern=pattern,
            parallel_tracks=parallel_tracks,
            max_loops=max_loops,
            gates=gates,
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
        self.analyzer = WorkflowPatternsEngine()
        self.agents = {
            "project_manager": ProjectManagerAgent(tool_runner),
            "architect": ArchitectAgent(tool_runner),
            "developer": DeveloperAgent(tool_runner),
            "tester": TesterAgent(tool_runner),
            "devops": DevOpsAgent(tool_runner),
            "reviewer": ReviewerAgent(tool_runner),
            "improver": ImproverAgent(tool_runner),
            "tools_engine": ToolsIntegrationAgent(tool_runner),
            "memory": MemoryAgent(tool_runner),
            "research": ResearchAgent(tool_runner),
            "ux_frontend": UXFrontendAgent(tool_runner),
            "data_engineer": DataEngineerAgent(tool_runner),
            "security": SecurityAgent(tool_runner),
            "performance": PerformanceAgent(tool_runner),
            "compliance": ComplianceAgent(tool_runner),
            "technical_writer": TechnicalWriterAgent(tool_runner),
            "cost": CostAgent(tool_runner),
            "debug": DebugAgent(tool_runner),
            "refactor": RefactorAgent(tool_runner),
            "documentation": DocumentationAgent(tool_runner),
            "dependency": DependencyAgent(tool_runner),
            "browser": BrowserAgent(tool_runner),
            "vision": VisionAgent(tool_runner),
        }

    def run(
        self,
        project_id: str,
        prompt: str,
        memory_context: List[str],
        repo: Dict[str, Any],
        habits: List[str],
        emit: Callable[[str, str, Dict[str, Any]], None],
        workflow_pattern: str = "Auto",
    ) -> Dict[str, Any]:
        state = WorkflowState(
            project_id=project_id,
            user_request=prompt,
            memory_context=memory_context + habits,
        )
        analysis = self.analyzer.analyze(prompt, workflow_pattern)
        state.task_type = analysis.task_type
        state.prompt_analysis = analysis.to_dict()
        state.selected_agents = list(analysis.selected_agents)
        state.execution_order = []
        state.workflow_engine = analysis.workflow_pattern
        state.artifact_name = self._artifact_name(prompt)
        state.artifact_version = self._artifact_version()
        state.agent_context = self._build_agent_context(state, analysis, repo)
        emit("workflow", f"Pattern {analysis.workflow_pattern} selected for {state.task_type}", {"analysis": state.prompt_analysis})
        
        if analysis.workflow_pattern == "B":
            self._run_pattern_b_parallel_swarm(state, emit)
        elif analysis.workflow_pattern == "C":
            self._run_pattern_c_adversarial(state, emit, analysis.max_loops)
        elif analysis.workflow_pattern == "E":
            self._run_pattern_e_hotfix(state, emit)
        else:
            self._run_pattern_a_sequential(state, emit)
        state.structured_result = self._build_completion(state)
        state.final_result = state.structured_result.get("summary", "")
        try:
            reflection_engine.trigger_reflection(prompt, state.to_dict())
        except Exception:
            pass
        return state.to_dict()

    def _run_pattern_a_sequential(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> None:
        self._run_sequence(state, emit)

    def _run_pattern_b_parallel_swarm(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> None:
        if "ProjectManager" in state.selected_agents: self._run_agent("project_manager", state, emit)
        if "Architect" in state.selected_agents: self._run_agent("architect", state, emit)
        
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(self._run_agent, "developer", state, emit)
            f2 = executor.submit(self._run_agent, "tools_engine", state, emit)
            concurrent.futures.wait([f1, f2])
            
        print("[WORKFLOW ENGINE] — INTEGRATION GATE reached.")
            
        if "Tester" in state.selected_agents: self._run_validation_loop(state, emit)
        if "DevOps" in state.selected_agents and state.artifact_path: self._run_agent("devops", state, emit)
        if "TechnicalWriter" in state.selected_agents: self._run_agent("technical_writer", state, emit)
        if "Reviewer" in state.selected_agents: self._run_agent("reviewer", state, emit)
        self._run_agent("memory", state, emit)
        self._run_agent("cost", state, emit)

    def _run_pattern_c_adversarial(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None], max_loops: int) -> None:
        if "ProjectManager" in state.selected_agents: self._run_agent("project_manager", state, emit)
        if "Architect" in state.selected_agents: self._run_agent("architect", state, emit)
        self._run_agent("developer", state, emit)
        
        retries = 0
        while not state.tests_passed and retries < max_loops:
            self._run_agent("tester", state, emit)
            if state.tests_passed:
                break
            print(f"[WORKFLOW ENGINE] — Routing Event\\n├─ Trigger: Tester Failed\\n├─ New Path: Improver (Loop {retries+1}/{max_loops})")
            if "Improver" not in state.selected_agents: state.selected_agents.append("Improver")
            self._run_agent("improver", state, emit)
            self._run_agent("developer", state, emit)
            retries += 1
            
        if "DevOps" in state.selected_agents and state.artifact_path: self._run_agent("devops", state, emit)
        if "Reviewer" in state.selected_agents: self._run_agent("reviewer", state, emit)
        self._run_agent("tools_engine", state, emit)
        self._run_agent("memory", state, emit)

    def _run_pattern_e_hotfix(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> None:
        self._run_agent("memory", state, emit)
        self._run_agent("improver", state, emit)
        self._run_agent("technical_writer", state, emit)
        self._run_agent("reviewer", state, emit)
        self._run_agent("devops", state, emit)
        self._run_agent("cost", state, emit)
        print("[WORKFLOW ENGINE] — Routing Event\\n├─ Trigger: Hotfix Express deployed\\n├─ Old Path: Full Pipeline\\n├─ New Path: Expedited Deploy")

    def _run_sequence(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> None:
        if "ProjectManager" in state.selected_agents: self._run_agent("project_manager", state, emit)
        if "Research" in state.selected_agents: self._run_agent("research", state, emit)
        if "Architect" in state.selected_agents: self._run_agent("architect", state, emit)
        if "UXFrontend" in state.selected_agents: self._run_agent("ux_frontend", state, emit)
        if "DataEngineer" in state.selected_agents: self._run_agent("data_engineer", state, emit)
        if "Dependency" in state.selected_agents: self._run_agent("dependency", state, emit)
        if "Developer" in state.selected_agents: self._run_agent("developer", state, emit)
        if "Security" in state.selected_agents: self._run_agent("security", state, emit)
        if "Tester" in state.selected_agents: self._run_validation_loop(state, emit)
        if "Debug" in state.selected_agents and not state.tests_passed: self._run_agent("debug", state, emit)
        if "Refactor" in state.selected_agents: self._run_agent("refactor", state, emit)
        if "Performance" in state.selected_agents: self._run_agent("performance", state, emit)
        if "Compliance" in state.selected_agents: self._run_agent("compliance", state, emit)
        if "DevOps" in state.selected_agents and state.artifact_path: self._run_agent("devops", state, emit)
        if "Browser" in state.selected_agents: self._run_agent("browser", state, emit)
        if "Vision" in state.selected_agents: self._run_agent("vision", state, emit)
        if "TechnicalWriter" in state.selected_agents: self._run_agent("technical_writer", state, emit)
        if "Documentation" in state.selected_agents: self._run_agent("documentation", state, emit)
        if "Reviewer" in state.selected_agents:
            if state.tests_passed or state.task_type in {"research", "general"} or state.deployment_status == "published":
                self._run_agent("reviewer", state, emit)
        if "ToolsEngine" in state.selected_agents: self._run_agent("tools_engine", state, emit)
        if "Memory" in state.selected_agents: self._run_agent("memory", state, emit)
        if "Cost" in state.selected_agents: self._run_agent("cost", state, emit)

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
        
        from backend.services.memory_engine import memory_engine
        from backend.services.governance_engine import GovernanceEngine
        try:
            mem_result = memory_engine.retrieve(
                query=f"{label} task for {state.task_type}: {state.user_request}",
                agent_role=label,
                context=str(context)
            )
            context["memory_engine_context"] = mem_result
        except Exception:
            pass

        try:
            org_context = knowledge_engine.retrieve(f"{label} task for {state.task_type}: {state.user_request}")
            context["knowledge_engine_context"] = org_context
        except Exception:
            pass
            
        state.agent_context[label] = context
        
        gov_engine = GovernanceEngine(self.llm)
        max_retries = 2
        attempt = 0
        
        import asyncio
        def _pub(event_type, payload):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(event_bus.publish(event_type, payload))
                else:
                    loop.run_until_complete(event_bus.publish(event_type, payload))
            except Exception:
                try:
                    asyncio.run(event_bus.publish(event_type, payload))
                except Exception:
                    pass

        _pub("TaskCreated" if name == "project_manager" else f"Agent{label}Started", {"project_id": state.project_id})
        
        while attempt <= max_retries:
            import time
            start_time = time.time()
            try:
                self.agents[name].run(state, emit)
                success = True
            except Exception as e:
                success = False
                _pub("BuildFailed", {"project_id": state.project_id, "error": str(e)})
                raise e
                
            duration_ms = (time.time() - start_time) * 1000
            try:
                observability_engine.record_agent_execution(label, duration_ms, tokens_used=0, success=success)
            except Exception:
                pass
            
            output = state.agent_outputs.get(label, "")
            
            # Skip governance for Improver itself to avoid infinite recursion loops, and Memory
            if name in ["improver", "memory"]:
                break
                
            try:
                eval_data = gov_engine.evaluate_gate(name, output, state.user_request)
                log_str = gov_engine.format_log(eval_data, label)
                print(log_str)
                emit("governance", f"Governance: {eval_data['verdict']} (Q:{eval_data['scores'].get('quality')} S:{eval_data['scores'].get('security')} P:{eval_data['scores'].get('performance')} E:{eval_data['scores'].get('ethics')})", {"evaluation": eval_data})
                
                if eval_data.get("adr_required"):
                    memory_engine.ingest({
                        "content": f"ADR Topic: {eval_data.get('adr_topic')}\\nFindings: {eval_data.get('findings')}",
                        "type": "ADR",
                        "source_agent": "Governance",
                        "project_id": state.project_id,
                        "outcome": "success"
                    })
                
                if eval_data["min_score"] >= 7:
                    break  # PASS
                    
                if attempt == max_retries:
                    if eval_data["min_score"] >= 5:
                        print(f"[GOVERNANCE ENGINE] — CONDITIONAL Proceeding after {max_retries} loops.")
                        break
                    else:
                        print(f"[GOVERNANCE ENGINE] — HALT! Governance failed permanently.")
                        state.status = "error"
                        emit("error", "Workflow halted by Governance Engine (score < 5).", {})
                        raise RuntimeError(f"Governance Gate Failed for {name}")
                
                print(f"[GOVERNANCE ENGINE] — Remediation loop triggered. Score: {eval_data['min_score']}")
                emit("governance_failed", f"Score < 7. Triggering Improver... (Loop {attempt+1})", {"remediation": eval_data["remediation"]})
                
                if "Improver" not in state.agent_context:
                    state.agent_context["Improver"] = {}
                state.agent_context["Improver"]["remediation"] = eval_data["remediation"]
                self.agents["improver"].run(state, emit)
                attempt += 1
            except Exception as e:
                print(f"[GOVERNANCE ENGINE] Error: {e}")
                break
        
        try:
            recovery_engine.save_checkpoint(state.project_id, state.to_dict())
        except Exception:
            pass

        output = state.agent_outputs.get(label, "")
        if name in ["developer", "data_engineer", "ux_frontend"]:
            _pub("CodeGenerated", {"project_id": state.project_id, "output": output})
        elif name == "reviewer":
            _pub("ReviewCompleted", {"project_id": state.project_id, "output": output})
        elif name == "devops":
            _pub("DeployFinished", {"project_id": state.project_id, "output": output})
            
        try:
            output = state.agent_outputs.get(label, "")
            if output:
                memory_engine.ingest({
                    "content": f"Task: {state.user_request}\\nOutput: {output}",
                    "type": "IMPLEMENTATION" if name == "developer" else ("REQUIREMENT" if name == "project_manager" else "WORKFLOW"),
                    "source_agent": label,
                    "project_id": state.project_id,
                    "outcome": "success" if state.tests_passed else "pending"
                })
        except Exception:
            pass

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
            "DevOps": {
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
            "ToolsEngine": {
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
        if name == "tools_engine":
            return "ToolsEngine"
        return "".join(part.title() for part in name.split("_"))

    def _artifact_name(self, prompt: str) -> str:
        base = "".join(ch.lower() if ch.isalnum() else "-" for ch in prompt).strip("-")[:56] or "akshat-output"
        return f"akshat_{base}_{int(datetime.now(timezone.utc).timestamp())}"

    def _artifact_version(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
