import subprocess
from typing import Dict, Any

class SandboxEngine:
    def execute_in_sandbox(self, command: str, image: str = "python:3.12-slim") -> Dict[str, Any]:
        """
        Executes a command safely inside an isolated Docker container.
        """
        try:
            result = subprocess.run(
                ["docker", "run", "--rm", "--network", "none", image, "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except Exception as e:
            return {"success": False, "stdout": "", "stderr": str(e)}

sandbox_engine = SandboxEngine()
