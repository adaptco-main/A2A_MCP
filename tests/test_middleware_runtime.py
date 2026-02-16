
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from middleware import AgenticRuntime
from middleware.observers.whatsapp import WhatsAppEventObserver
from schemas.model_artifact import ModelArtifact, AgentLifecycleState

@pytest.mark.asyncio
async def test_agentic_runtime_end_to_end():
    """Verify that AgenticRuntime correctly handles transitions, persistence, and notifications."""
    mock_observer = MagicMock()
    mock_observer.on_state_change = AsyncMock()
    
    mock_db = MagicMock()
    mock_db.save_artifact.side_effect = lambda x: x
    
    with patch("middleware.events._db_manager", mock_db):
        runtime = AgenticRuntime(observers=[mock_observer])
        
        # Initial artifact
        artifact = ModelArtifact(
            artifact_id="test-rt-1",
            model_id="test",
            weights_hash="h1",
            embedding_dim=1,
            state=AgentLifecycleState.INIT,
            content="test"
        )
        
        # 1. Emit INIT (non-terminal)
        await runtime.emit_event(artifact)
        mock_observer.on_state_change.assert_not_called()
        
        # 2. Transition to CONVERGED (terminal)
        # Assuming transition() works and CONVERGED is terminal
        new_artifact = await runtime.transition_and_emit(artifact, AgentLifecycleState.CONVERGED)
        
        assert new_artifact.state == AgentLifecycleState.CONVERGED
        mock_observer.on_state_change.assert_called_once_with(new_artifact)
        mock_db.save_artifact.assert_called()

@pytest.mark.asyncio
async def test_runtime_registration():
    """Verify dynamic observer registration."""
    mock_observer = MagicMock()
    mock_observer.on_state_change = AsyncMock()
    
    mock_db = MagicMock()
    mock_db.save_artifact.side_effect = lambda x: x
    
    with patch("middleware.events._db_manager", mock_db):
        runtime = AgenticRuntime(observers=[])
        runtime.register_observer(mock_observer)
        
        artifact = ModelArtifact(
            artifact_id="test-rt-2",
            model_id="test",
            weights_hash="h1",
            embedding_dim=1,
            state=AgentLifecycleState.CONVERGED,
            content="test"
        )
        
        await runtime.emit_event(artifact)
        mock_observer.on_state_change.assert_called_once()
