from typing import List, Any, Optional
from .events import PostgresEventStore
from schemas.model_artifact import ModelArtifact, AgentLifecycleState

class AgenticRuntime:
    """
    The unified runtime middleware for agent operations.
    Handles persistence, state transitions, and external notifications.
    """
    def __init__(self, observers: List[Any] = None):
        self.event_store = PostgresEventStore(observers=observers)

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
