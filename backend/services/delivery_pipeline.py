from typing import Any, Dict

class DeliveryPipeline:
    def __init__(self):
        self.stages = ["Build", "Test", "Security Scan", "Package", "Deploy", "Monitor"]

    def run_pipeline(self, artifact_path: str) -> Dict[str, Any]:
        results = {}
        for stage in self.stages:
            print(f"[DeliveryPipeline] Running stage: {stage}")
            # Mocking the pipeline stages
            results[stage] = "success"
            
            if results[stage] != "success":
                return self.rollback(artifact_path)
                
        return {"status": "deployed", "details": results}

    def rollback(self, artifact_path: str) -> Dict[str, Any]:
        print(f"[DeliveryPipeline] Rolling back {artifact_path}")
        return {"status": "rollback_completed"}

delivery_pipeline = DeliveryPipeline()
