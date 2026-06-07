from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List

from backend.agents.architect import ArchitectAgent
from backend.agents.developer import DeveloperAgent
from backend.agents.improver import ImproverAgent
from backend.agents.memory import MemoryAgent
from backend.agents.project_manager import ProjectManagerAgent
from backend.agents.reviewer import ReviewerAgent
from backend.agents.tester import TesterAgent

try:
    from langgraph.graph import END, StateGraph
except Exception:
    END = "__end__"  # type: ignore
    StateGraph = None  # type: ignore


AGENT_ORDER = ["ProjectManager", "Architect", "Developer", "Tester", "Reviewer", "Improver", "Memory"]


@dataclass
class WorkflowState:
    project_id: str
    user_request: str
    current_agent: str = "ProjectManager"
    current_task: str = "Understanding request"
    requirements: List[str] = field(default_factory=list)
    architecture: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    generated_code: str = ""
    test_results: Dict[str, Any] = field(default_factory=dict)
    tests_passed: bool = False
    review_reports: List[str] = field(default_factory=list)
    fix_history: List[str] = field(default_factory=list)
    quality_score: int = 0
    security_score: int = 0
    iteration_count: int = 0
    memory_context: List[str] = field(default_factory=list)
    agent_outputs: Dict[str, str] = field(default_factory=dict)
    agent_runs: List[Dict[str, Any]] = field(default_factory=list)
    replay_events: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, str]] = field(default_factory=list)
    final_deliverable: str = ""
    final_result: str = ""
    workflow_engine: str = "custom"

    def record(self, agent: str, task: str, output: str) -> None:
        self.current_agent = agent
        self.current_task = task
        self.agent_outputs[agent] = output
        self.events.append({"agent": agent, "task": task, "output": output})

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
        self.uses_langgraph = StateGraph is not None
        self.agents = {
            "project_manager": ProjectManagerAgent(tool_runner),
            "architect": ArchitectAgent(tool_runner),
            "developer": DeveloperAgent(tool_runner),
            "tester": TesterAgent(tool_runner),
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
            workflow_engine="langgraph" if self.uses_langgraph else "custom_branching_loop",
        )
        if self.uses_langgraph:
            try:
                return self._run_langgraph(state, emit)
            except Exception as exc:
                state.workflow_engine = "custom_branching_loop_langgraph_fallback"
                state.record("Workflow", "LangGraph fallback", f"LangGraph execution failed: {exc}")
                emit("workflow", "LangGraph fallback activated.", {"error": str(exc)})
        return self._run_sequence(state, emit)

    def _run_sequence(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> Dict[str, Any]:
        self.agents["project_manager"].run(state, emit)
        self.agents["architect"].run(state, emit)
        self.agents["developer"].run(state, emit)
        self.agents["tester"].run(state, emit)
        retries = 0
        while not state.tests_passed and retries < 2:
            self.agents["improver"].run(state, emit)
            self.agents["tester"].run(state, emit)
            retries += 1
        if state.tests_passed:
            self.agents["reviewer"].run(state, emit)
        else:
            state.quality_score = 45
            state.security_score = 50
        self.agents["memory"].run(state, emit)
        return state.to_dict()

    def _run_langgraph(self, state: WorkflowState, emit: Callable[[str, str, Dict[str, Any]], None]) -> Dict[str, Any]:
        assert StateGraph is not None

        def node(name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
            def run_node(data: Dict[str, Any]) -> Dict[str, Any]:
                self.agents[name].run(data["state"], emit)
                return data
            return run_node

        def route_after_tests(data: Dict[str, Any]) -> str:
            return "reviewer" if data["state"].tests_passed else "improver"

        def route_after_improver(data: Dict[str, Any]) -> str:
            return "memory" if data["state"].iteration_count >= 3 and not data["state"].tests_passed else "tester"

        graph = StateGraph(dict)
        graph.add_node("project_manager", node("project_manager"))
        graph.add_node("architect", node("architect"))
        graph.add_node("developer", node("developer"))
        graph.add_node("tester", node("tester"))
        graph.add_node("reviewer", node("reviewer"))
        graph.add_node("improver", node("improver"))
        graph.add_node("memory", node("memory"))
        graph.set_entry_point("project_manager")
        graph.add_edge("project_manager", "architect")
        graph.add_edge("architect", "developer")
        graph.add_edge("developer", "tester")
        graph.add_conditional_edges("tester", route_after_tests, {"reviewer": "reviewer", "improver": "improver"})
        graph.add_edge("reviewer", "memory")
        graph.add_conditional_edges("improver", route_after_improver, {"tester": "tester", "memory": "memory"})
        graph.add_edge("memory", END)
        result = graph.compile().invoke({"state": state})
        return result["state"].to_dict()
