from typing import List, Any, Optional, Dict
from .events import PostgresEventStore
from schemas.model_artifact import ModelArtifact, AgentLifecycleState

class AgenticRuntime:
    """
    The unified runtime middleware for agent operations.
    Handles persistence, state transitions, and external notifications.
    """
    def __init__(self, observers: List[Any] = None):
        self.event_store = PostgresEventStore(observers=observers)

    async def initiate_handshake(self, model_id: str, weights_hash: str, embedding_dim: int, metadata: Dict = None) -> ModelArtifact:
        """
        Create a ModelArtifact in the HANDSHAKE state and emit it.
        This provides a trace for the initial model onboarding on the MCP.
        """
        artifact = ModelArtifact(
            model_id=model_id,
            weights_hash=weights_hash,
            embedding_dim=embedding_dim,
            state=AgentLifecycleState.HANDSHAKE,
            content=f"Handshake initiated for model {model_id}",
            metadata=metadata or {}
        )
        return await self.emit_event(artifact)

    async def emit_event(self, artifact: ModelArtifact) -> Any:
        """
        Record an event (artifact) in the persistent store.
        """
        return await self.event_store.append_event(artifact)

    async def transition_and_emit(self, artifact: ModelArtifact, target_state: AgentLifecycleState) -> ModelArtifact:
        """
        Transition an artifact to a new state and record the event.
        Returns the new artifact instance.
        """
        if not hasattr(artifact, 'transition'):
            raise TypeError("Artifact must be a ModelArtifact instance with transition logic.")
        
        new_artifact = artifact.transition(target_state)
        await self.emit_event(new_artifact)
        return new_artifact

    def register_observer(self, observer: Any):
        """
        Dynamically register a new observer for event notifications.
        """
        self.event_store.observers.append(observer)
