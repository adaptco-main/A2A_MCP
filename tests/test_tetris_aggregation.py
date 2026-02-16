import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime
from orchestrator.observers.tetris_observer import TetrisScoreAggregator
from schemas.database import EventModel

@pytest.mark.asyncio
async def test_tetris_aggregator_buffers_and_flushes():
    # Setup
    mock_wa_observer = AsyncMock()
    # Mock _send_whatsapp_message since it's an internal method we call
    mock_wa_observer._send_whatsapp_message = AsyncMock()
    
    # Use small flush interval for testing
    aggregator = TetrisScoreAggregator(mock_wa_observer, flush_interval_seconds=1)
    
    events = [
        EventModel(pipeline="tetris-node", state="SCORE_FINALIZED", category="gaming", details={"score": 100}, timestamp=datetime.utcnow()),
        EventModel(pipeline="tetris-node", state="SCORE_FINALIZED", category="gaming", details={"score": 200}, timestamp=datetime.utcnow()),
        EventModel(pipeline="tetris-node", state="SCORE_FINALIZED", category="gaming", details={"score": 300}, timestamp=datetime.utcnow()),
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
    mock_wa_observer = AsyncMock()
    aggregator = TetrisScoreAggregator(mock_wa_observer, flush_interval_seconds=1)
    
    mlops_event = EventModel(pipeline="mlops", state="DEPLOYED", category="mlops", details={}, timestamp=datetime.utcnow())
    
    await aggregator.on_state_change(mlops_event)
    
    async with aggregator._lock:
        assert len(aggregator.buffer) == 0
    
    await asyncio.sleep(1.2)
    mock_wa_observer._send_whatsapp_message.assert_not_called()
