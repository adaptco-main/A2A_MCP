from schemas.agent_artifacts import MCPArtifact
import uuid

class TesterAgent:
    def __init__(self):
        self.name = "Tester_v1"

    async def run(self, code_artifact: MCPArtifact) -> MCPArtifact:
        """
        Consumes a code artifact and produces a test_report artifact.
        """
        print(f"[{self.name}] Testing code from: {code_artifact.artifact_id}...")
        
        # Simulate running tests on the generated code
        test_passed = "print" in code_artifact.content
        status = "PASSED" if test_passed else "FAILED"
        
        report_content = f"""
        # Test Report for {code_artifact.artifact_id}
        - Status: {status}
        - Coverage: 100% (Simulated)
        - Observations: Code contains standard entry points.
        """
        
        return MCPArtifact(
            artifact_id=f"tst-{uuid.uuid4().hex[:8]}",
            type="test_report",
            content=report_content,
            metadata={
                "agent": self.name,
                "parent_artifact": code_artifact.artifact_id,
                "result": status
            }
        )
