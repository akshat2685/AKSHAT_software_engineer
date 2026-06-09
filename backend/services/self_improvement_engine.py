import json
import logging
from typing import Any, Dict, List
from backend.database.connection import SessionLocal
from backend.database.models import ProjectMetrics, OrganizationHealth, ImprovementChangelog, AgentPromptOverride
from backend.services.ollama_service import generate_response

logger = logging.getLogger("self_improvement_engine")

class SelfImprovementEngine:
    def __init__(self):
        self.trigger_threshold = 70
        self.interval = 5

    def evaluate_project(self, project_id: str, workflow_state: Dict[str, Any], passed: bool) -> None:
        """Called at the end of every project run to store metrics and conditionally trigger an improvement cycle."""
        db = SessionLocal()
        try:
            iteration_count = workflow_state.get("iteration_count", 0)
            first_pass = iteration_count == 0 and passed
            cost_efficiency = max(0, 100 - (iteration_count * 15))
            
            # Rough proxy for memory hits (assuming context was passed if length > 0)
            memories = workflow_state.get("memory_context", [])
            knowledge_reuse_rate = 100 if len(memories) > 0 else 0

            # Calculate individual project score
            score = int((int(passed) * 100 * 0.30) +
                        (int(first_pass) * 100 * 0.25) +
                        (cost_efficiency * 0.20) +
                        (100 * 0.15) + # User satisfaction default 100
                        (knowledge_reuse_rate * 0.10))

            pm = ProjectMetrics(
                project_id=project_id,
                success=passed,
                first_pass_quality=first_pass,
                cost_efficiency=cost_efficiency,
                user_satisfaction=100,
                knowledge_reuse_rate=knowledge_reuse_rate,
                health_score=score
            )
            db.add(pm)
            db.commit()

            # Check rolling health over last N projects
            last_projects = db.query(ProjectMetrics).order_by(ProjectMetrics.id.desc()).limit(self.interval).all()
            if len(last_projects) >= 1:
                avg_health = sum(p.health_score for p in last_projects) / len(last_projects)
                oh = OrganizationHealth(score=int(avg_health), projects_analyzed=len(last_projects))
                db.add(oh)
                db.commit()

                trigger_cycle = False
                trigger_reason = ""
                
                if avg_health < self.trigger_threshold:
                    trigger_cycle = True
                    trigger_reason = "Health score dropped below threshold."
                elif not passed:
                    trigger_cycle = True
                    trigger_reason = "Catastrophic failure on last project."
                elif len(last_projects) == self.interval and (db.query(ProjectMetrics).count() % self.interval == 0):
                    trigger_cycle = True
                    trigger_reason = f"Periodic review every {self.interval} projects."

                if trigger_cycle:
                    self.run_improvement_cycle(db, last_projects, avg_health, trigger_reason)
        finally:
            db.close()

    def run_improvement_cycle(self, db, recent_projects: List[ProjectMetrics], avg_health: float, reason: str) -> None:
        """The 7-step self improvement protocol"""
        logger.info(f"Triggering self-improvement cycle: {reason} (Score: {avg_health})")
        
        # 1. INGEST & 2. ANALYZE
        failures = [p for p in recent_projects if not p.success or not p.first_pass_quality]
        if not failures:
            logger.info("No actionable failures found to improve upon.")
            return

        # Prepare summary of recent runs for the LLM
        summary = "Recent Project Failures/Inefficiencies:\n"
        for f in failures:
            summary += f"- Project {f.project_id}: Success={f.success}, FirstPass={f.first_pass_quality}, CostScore={f.cost_efficiency}\n"

        # 3. DIAGNOSE & 4. PRESCRIBE
        prompt = (
            "You are the SELF-IMPROVEMENT ENGINE of AKSHAT V2. Your mission is to evolve the agents.\n"
            "Analyze these recent failures/inefficiencies:\n"
            f"{summary}\n"
            "Based on common AI engineering workflows, which agent role is most likely failing? (Options: project_manager, architect, developer, tester, deploy, reviewer, improver, memory)\n"
            "Generate a JSON object with the following schema:\n"
            "{ "
            '  "category": "PROMPT_REFINEMENT", '
            '  "rationale": "Why this change helps", '
            '  "proposed_changes": "A summary of what changed", '
            '  "agent_role": "developer", '
            '  "new_prompt": "The FULL new system prompt for the agent that will prevent these failures" '
            "}\n"
            "Respond ONLY with valid JSON."
        )

        response = generate_response("system", prompt)
        try:
            import re
            match = re.search(r'\{.*\}', response.replace('\n', ' '), re.DOTALL)
            if not match:
                raise ValueError("No JSON found")
            
            data = json.loads(match.group(0))
            category = data.get("category", "UNKNOWN")
            rationale = data.get("rationale", "")
            proposed = data.get("proposed_changes", "")
            role = data.get("agent_role", "")
            new_prompt = data.get("new_prompt", "")

            if not role or not new_prompt:
                raise ValueError("Missing role or new_prompt in JSON")

            # 5. SIMULATE & 6. DECIDE (In a real scenario we'd re-run old workflows here, but for now we deploy automatically)
            
            # 7. DOCUMENT
            changelog = ImprovementChangelog(
                category=category,
                rationale=rationale,
                proposed_changes=proposed,
                status="deployed"
            )
            db.add(changelog)
            
            # Update active prompt override
            override = db.query(AgentPromptOverride).filter(AgentPromptOverride.agent_role == role).first()
            if not override:
                override = AgentPromptOverride(agent_role=role)
                db.add(override)
            override.prompt_content = new_prompt
            
            db.commit()
            logger.info(f"Self-improvement deployed for {role}: {proposed}")

        except Exception as e:
            logger.error(f"Failed to generate or parse improvement: {e}")
            db.rollback()

engine = SelfImprovementEngine()
