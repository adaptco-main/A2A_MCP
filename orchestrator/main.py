import asyncio
from orchestrator.storage import DBManager
from orchestrator.llm_util import LLMService
from orchestrator.event_store import PostgresEventStore
from orchestrator.whatsapp import WhatsAppEventObserver
from schemas.model_artifact import AgentLifecycleState
from agents.coder import CoderAgent
from agents.tester import TesterAgent

class MCPHub:
    def __init__(self):
        self.db = DBManager()
        self.coder = CoderAgent()
        self.tester = TesterAgent()
        
        # MLOps Ticker: Event Store & Observer
        self.whatsapp = WhatsAppEventObserver()
        self.event_store = PostgresEventStore(observers=[self.whatsapp])

    async def run_healing_loop(self, task_description: str, max_retries=3):
        """
        Phase 2 Logic: Orchestrates the Research -> Code -> Test flow 
        with automatic self-correction loops.
        """
        iteration = 0
        current_parent_id = "initial_research"
        
        # Initial Generation
        artifact = await self.coder.generate_solution(current_parent_id, task_description)
        # Notify event store
        await self.event_store.append_event(artifact)
        
        while iteration < max_retries:
            print(f"--- Iteration {iteration + 1}: Testing Artifact {artifact.artifact_id} ---")
            
            # Tester evaluates the artifact
            report = await self.tester.validate(artifact.artifact_id)
            
            if report.status == "PASS":
                # State Transition: CONVERGED
                if hasattr(artifact, 'transition'):
                    try:
                        artifact = artifact.transition(AgentLifecycleState.CONVERGED)
                        await self.event_store.append_event(artifact)
                        print(f"✓ System Healthy: Solution Verified. Transitioned to {AgentLifecycleState.CONVERGED.value}")
                    except Exception as e:
                        print(f"Warning: Failed to transition artifact: {e}")
                else:
                    print("✓ System Healthy: Solution Verified.")
                
                return artifact

            # Phase 2 Self-Healing: Route feedback back to Coder
            print(f"✗ Failure Detected: {report.critique}")
            
            # State Transition: HEALING
            if hasattr(artifact, 'transition'):
                try:
                    artifact = artifact.transition(AgentLifecycleState.HEALING)
                    await self.event_store.append_event(artifact)
                except Exception:
                    pass

            artifact = await self.coder.generate_solution(
                parent_id=artifact.artifact_id, 
                feedback=report.critique
            )
            # Notify event store of new artifact
            await self.event_store.append_event(artifact)
            
            iteration += 1

        print("!! Max retries reached. Human intervention required.")
        # State Transition: FAILED
        if hasattr(artifact, 'transition'):
            try:
                artifact = artifact.transition(AgentLifecycleState.FAILED)
                await self.event_store.append_event(artifact)
            except Exception:
                pass
                
        return None

if __name__ == "__main__":
    hub = MCPHub()
    # Mock run won't work without actual agents/LLM keys, but structure is correct.
    # asyncio.run(hub.run_healing_loop("Fix connection string in storage.py"))
