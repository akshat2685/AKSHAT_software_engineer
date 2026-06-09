import json
import re
from typing import Any, Callable, Dict, List, Optional

class GovernanceEngine:
    def __init__(self, llm: Callable[[str], str]):
        self.llm = llm

    def evaluate_gate(self, agent_name: str, agent_output: str, task_context: str) -> Dict[str, Any]:
        """
        Evaluates the output of an agent against the Quality & Governance criteria.
        Returns a dictionary with the evaluation results.
        """
        gate_map = {
            "project_manager": "Requirements Gate",
            "architect": "Architecture Gate",
            "developer": "Implementation Gate",
            "tester": "Test Gate",
            "reviewer": "Review Gate",
            "tools_engine": "Compliance Gate",
            "devops": "Deploy Gate",
            "memory": "Data Governance Gate",
            "improver": "Implementation Gate",
            "research": "Architecture Gate",
            "ux_frontend": "Implementation Gate",
            "data_engineer": "Architecture Gate",
            "security": "Security Gate",
            "performance": "Performance Gate",
            "compliance": "Compliance Gate",
            "technical_writer": "Review Gate",
            "cost": "Performance Gate",
        }
        gate_name = gate_map.get(agent_name.lower(), "General Gate")
        
        prompt = f"""You are the QUALITY & GOVERNANCE ENGINE of AKSHAT V2. You are the conscience and the referee.
Every artifact passes through your judgment. You do not build. You protect. You validate.

---

### GATE: {gate_name}
Evaluate the following output from the '{agent_name}' agent.
Task Context: {task_context}

Agent Output:
{agent_output[:4000]}  # Truncated to avoid context limits

---

Provide your evaluation strictly as a JSON object (no markdown, no extra text).
Schema:
{{
  "gate": "{gate_name}",
  "scores": {{
    "quality": <int 1-10>,
    "security": <int 1-10>,
    "performance": <int 1-10>,
    "ethics": <int 1-10>
  }},
  "findings": ["finding 1", "finding 2"],
  "remediation": "what needs to be fixed if score is low",
  "adr_required": false,
  "adr_topic": ""
}}

Rules for scoring:
- If output lacks basic structure, score < 5.
- If output is acceptable but missing some polish, score 5-6.
- If output is good and secure, score 7-10.
"""
        response = self.llm(prompt)
        
        # Parse JSON
        parsed = self._extract_json(response)
        
        # Calculate verdict
        scores = parsed.get("scores", {})
        min_score = min([scores.get(k, 10) for k in ["quality", "security", "performance", "ethics"] if isinstance(scores.get(k), int)])
        
        if min_score >= 7:
            verdict = "PASS"
        elif min_score >= 5:
            verdict = "CONDITIONAL"
        else:
            verdict = "FAIL"
            
        parsed["verdict"] = verdict
        parsed["min_score"] = min_score
        
        return parsed

    def _extract_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                pass
        return {
            "gate": "Unknown",
            "scores": {"quality": 10, "security": 10, "performance": 10, "ethics": 10},
            "findings": ["Failed to parse governance output."],
            "remediation": "",
            "adr_required": False
        }

    def format_log(self, eval_data: Dict[str, Any], agent_role: str) -> str:
        scores = eval_data.get("scores", {})
        findings = "\\n├─ ".join(eval_data.get("findings", ["None"]))
        adr = eval_data.get("adr_topic", "") if eval_data.get("adr_required") else "no"
        
        return f"""[GOVERNANCE ENGINE] — Gate Evaluation
├─ Gate: {eval_data.get('gate')}
├─ Evaluator: {agent_role}
├─ Scores: Q:{scores.get('quality', '-')} S:{scores.get('security', '-')} P:{scores.get('performance', '-')} E:{scores.get('ethics', '-')}
├─ Verdict: {eval_data.get('verdict')}
├─ Findings: {findings}
├─ Remediation: {eval_data.get('remediation', 'None')}
└─ ADR Required: {adr}
"""
