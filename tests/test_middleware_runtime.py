import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from middleware import AgenticRuntime, WhatsAppEventObserver
from schemas.model_artifact import ModelArtifact, AgentLifecycleState

@pytest.mark.asyncio
class TestMiddlewareRuntime:
    async def test_runtime_emit_event(self):
        """Verify that runtime correctly emits events through the event store."""
        mock_db = MagicMock()
        mock_db.save_artifact.side_effect = lambda x: x
        
        with patch("middleware.events._db_manager", mock_db):
            runtime = AgenticRuntime()
            artifact = ModelArtifact(
                artifact_id="test-1",
                model_id="test",
                weights_hash="h1",
                embedding_dim=1,
                state=AgentLifecycleState.INIT,
                content="test"
            )
            
            saved = await runtime.emit_event(artifact)
            assert saved.artifact_id == "test-1"
            mock_db.save_artifact.assert_called_once()

    async def test_runtime_transition_and_emit(self):
        """Verify integrated state transition and emission."""
        mock_db = MagicMock()
        mock_db.save_artifact.side_effect = lambda x: x
        mock_observer = MagicMock()
        mock_observer.on_state_change = AsyncMock()
        
        with patch("middleware.events._db_manager", mock_db):
            runtime = AgenticRuntime(observers=[mock_observer])
            artifact = ModelArtifact(
                artifact_id="trans-1",
                model_id="test",
                weights_hash="h1",
                embedding_dim=1,
                state=AgentLifecycleState.INIT,
                content="test"
            )
            
            # Transition to EMBEDDING (Non-terminal)
            next_art = await runtime.transition_and_emit(artifact, AgentLifecycleState.EMBEDDING)
            assert next_art.state == AgentLifecycleState.EMBEDDING
            mock_observer.on_state_change.assert_not_called()
            
            # For terminal test, we bypass strict machine validation to test Middleware logic
            # by directly setting state on a mock-like copy
            terminal_art = next_art.model_copy(update={"state": AgentLifecycleState.CONVERGED})
            await runtime.emit_event(terminal_art)
            mock_observer.on_state_change.assert_called_once()

    def test_register_observer(self):
        """Verify dynamic observer registration."""
        runtime = AgenticRuntime()
        assert len(runtime.event_store.observers) == 0
        
        runtime.register_observer(MagicMock())
        assert len(runtime.event_store.observers) == 1
