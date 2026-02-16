import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from middleware.observers.tetris import TetrisScoreAggregator
from schemas.model_artifact import ModelArtifact, AgentLifecycleState

@pytest.mark.asyncio
async def test_tetris_aggregator_buffers_and_flushes():
    # Setup
    mock_wa_observer = MagicMock()
    mock_wa_observer._send_whatsapp_message = AsyncMock()
    
    # Use small flush interval for testing
    aggregator = TetrisScoreAggregator(mock_wa_observer, flush_interval_seconds=1)
    
    # We use ModelArtifact as our proxy for events in the new system
    events = [
        ModelArtifact(model_id="t1", weights_hash="h1", embedding_dim=1, category="gaming", state="SCORE_FINALIZED", metadata={"score": 100}),
        ModelArtifact(model_id="t2", weights_hash="h2", embedding_dim=1, category="gaming", state="SCORE_FINALIZED", metadata={"score": 200}),
        ModelArtifact(model_id="t3", weights_hash="h3", embedding_dim=1, category="gaming", state="SCORE_FINALIZED", metadata={"score": 300}),
    ]
    
    # 1. Dispatch events to aggregator
    for event in events:
        await aggregator.on_state_change(event)
    
    # 2. Verify buffer state (should have 3 items)
    async with aggregator._lock:
        assert len(aggregator.buffer) == 3

    # 3. Wait for flush interval + small buffer
    await asyncio.sleep(1.5)
    
    # 4. Verify WhatsApp observer was called ONCE with aggregated stats
    mock_wa_observer._send_whatsapp_message.assert_called_once()
    call_args = mock_wa_observer._send_whatsapp_message.call_args[0][0]
    
    assert "[GAMING TICKER AGGREGATED]" in call_args
    assert "count: 3 matches" in call_args
    assert "avg_score: 200.00" in call_args
    assert "high_score: 300" in call_args
    
    # 5. Verify buffer is cleared
    async with aggregator._lock:
        assert len(aggregator.buffer) == 0

@pytest.mark.asyncio
async def test_tetris_aggregator_ignores_mlops_events():
    mock_wa_observer = MagicMock()
    mock_wa_observer._send_whatsapp_message = AsyncMock()
    aggregator = TetrisScoreAggregator(mock_wa_observer, flush_interval_seconds=1)
    
    mlops_event = ModelArtifact(model_id="m1", weights_hash="h", embedding_dim=1, category="mlops", state=AgentLifecycleState.INIT)
    
    await aggregator.on_state_change(mlops_event)
    
    async with aggregator._lock:
        assert len(aggregator.buffer) == 0
    
    await asyncio.sleep(1.2)
    mock_wa_observer._send_whatsapp_message.assert_not_called()

