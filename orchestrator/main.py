import asyncio
from orchestrator.storage import DBManager
from orchestrator.llm_util import LLMService
from middleware import AgenticRuntime, WhatsAppEventObserver
from schemas.model_artifact import AgentLifecycleState
from agents.coder import CoderAgent
from agents.tester import TesterAgent

class MCPHub:
    def __init__(self):
        self.db = DBManager()
        self.coder = CoderAgent()
        self.tester = TesterAgent()
        
        # Initialize Agentic Runtime Middleware
        self.runtime = AgenticRuntime(observers=[WhatsAppEventObserver()])

    async def run_healing_loop(self, task_description: str, max_retries=3):
        """
        Phase 2 Logic: Orchestrates the Research -> Code -> Test flow 
        with automatic self-correction loops managed by the middleware.
        """
        iteration = 0
        current_parent_id = "initial_research"
        
        # Initial Generation
        artifact = await self.coder.generate_solution(current_parent_id, task_description)
        # Middleware handle event persistence and notification
        await self.runtime.emit_event(artifact)
        
        while iteration < max_retries:
            print(f"--- Iteration {iteration + 1}: Testing Artifact {artifact.artifact_id} ---")
            
            # Tester evaluates the artifact
            report = await self.tester.validate(artifact.artifact_id)
            
            if report.status == "PASS":
                # Middleware handle transition and persistence
                try:
                    artifact = await self.runtime.transition_and_emit(artifact, AgentLifecycleState.CONVERGED)
                    print(f"✓ System Healthy: Solution Verified. Transitioned to {AgentLifecycleState.CONVERGED.value}")
                except Exception as e:
                    print(f"✓ System Healthy: Solution Verified. (Transition Warning: {e})")
                
                return artifact

            # Phase 2 Self-Healing
            print(f"✗ Failure Detected: {report.critique}")
            
            # Transition to HEALING state via Middleware
            try:
                artifact = await self.runtime.transition_and_emit(artifact, AgentLifecycleState.HEALING)
            except Exception:
                pass

            artifact = await self.coder.generate_solution(
                parent_id=artifact.artifact_id, 
                feedback=report.critique
            )
            # Notify runtime of new artifact version
            await self.runtime.emit_event(artifact)
            
            iteration += 1

        print("!! Max retries reached. Human intervention required.")
        # Final terminal state: FAILED
        try:
            artifact = await self.runtime.transition_and_emit(artifact, AgentLifecycleState.FAILED)
        except Exception:
            pass
                
        return None

if __name__ == "__main__":
    hub = MCPHub()
    # Mock run won't work without actual agents/LLM keys, but structure is correct.
    # asyncio.run(hub.run_healing_loop("Fix connection string in storage.py"))
