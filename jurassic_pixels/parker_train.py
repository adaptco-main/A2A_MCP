import argparse
import sys
import time
import asyncio
import os
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Add project root to sys.path to allow imports from orchestrator
sys.path.append(str(Path(__file__).parent.parent))

from middleware import AgenticRuntime, WhatsAppEventObserver
from schemas.model_artifact import ModelArtifact, AgentLifecycleState

import websockets

logger = logging.getLogger("ParkerAgent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

# ---------------------------------------------------------------------------
# Action schema
# ---------------------------------------------------------------------------

ALLOWED_DIRECTIONS = {"left", "right", "jump", "idle"}
FAIL_CLOSED_ACTION = {"type": "move", "direction": "idle"}

PARKER_PROMPT_TEMPLATE = (
    "You are Parker, an autonomous game agent.\n"
    "Choose exactly ONE action for the next tick.\n"
    "Allowed directions: left, right, jump, idle.\n"
    "Reply with JSON ONLY — no explanation, no markdown, no extra text.\n"
    "Schema: {{\"type\":\"move\",\"direction\":\"<direction>\"}}\n\n"
    "Current observation:\n{observation}"
)


def validate_action(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Strict allowlist validation. Raises ValueError with a reason code on failure."""
    if not isinstance(raw, dict):
        raise ValueError("E_ACTION_NOT_OBJECT")
    if raw.get("type") != "move":
        raise ValueError("E_ACTION_TYPE_INVALID")
    direction = raw.get("direction")
    if direction not in ALLOWED_DIRECTIONS:
        raise ValueError(f"E_ACTION_DIRECTION_INVALID: {direction!r}")
    return {"type": "move", "direction": direction}


def decide_action(model: Any, observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Gemini to produce the next Parker action.
    Fail-closed to idle on any error (invalid JSON, schema violation, API failure).
    """
    prompt = PARKER_PROMPT_TEMPLATE.format(
        observation=json.dumps(observation, sort_keys=True, separators=(",", ":"))
    )
    try:
        response = model.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        raw_text = response.text.strip()

        # Strip markdown fences if model wraps in ```json ... ```
        if raw_text.startswith("```"):
            lines = raw_text.splitlines()
            raw_text = "\n".join(
                line for line in lines
                if not line.startswith("```")
            ).strip()

        action = json.loads(raw_text)
        validated = validate_action(action)
        logger.debug("Parker action: %s", validated)
        return validated

    except json.JSONDecodeError as e:
        logger.warning("E_ACTION_JSON_DECODE: %s | raw=%r", e, locals().get("raw_text", ""))
    except ValueError as e:
        logger.warning("E_ACTION_VALIDATION: %s", e)
    except Exception as e:
        logger.warning("E_MODEL_CALL_FAILED: %s", e)

    logger.info("Fail-closed: returning idle action")
    return FAIL_CLOSED_ACTION.copy()


# ---------------------------------------------------------------------------
# Gemini client initialisation
# ---------------------------------------------------------------------------

def init_gemini() -> Optional[Any]:
    """
    Initialise the Gemini client from GEMINI_API_KEY env var.
    Returns None if credentials are unavailable — agent will not run in intelligent mode.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error(
            "E_MISSING_MODEL_CREDENTIALS: GEMINI_API_KEY not set. "
            "Parker will not run in intelligent mode."
        )
        return None
    try:
        from google import genai  # type: ignore[import]
        client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialised (gemini-2.0-flash)")
        return client
    except ImportError:
        logger.error("E_MISSING_DEPENDENCY: google-genai not installed. Run: pip install google-genai")
        return None


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

async def agent_loop():
    client = init_gemini()
    if client is None:
        logger.error("Intelligent mode unavailable. Exiting agent loop.")
        return

    uri = "ws://server:8080"
    logger.info("Connecting to %s...", uri)
    async with websockets.connect(uri) as websocket:
        logger.info("Connected to Game Server")
        while True:
            try:
                message = await websocket.recv()
                observation = json.loads(message)

                # Gemini decides the action
                action = decide_action(client, observation)
                await websocket.send(json.dumps(action))

            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection closed")
                break
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                break


# ---------------------------------------------------------------------------
# Training loop (RL stub — separate from intelligent agent loop)
# ---------------------------------------------------------------------------

async def train(episodes: int, export: bool):
    print(f"Starting training for {episodes} episodes...")
    for i in range(episodes):
        print(f"Episode {i+1}/{episodes}: Reward={(i+1)*10}")
        time.sleep(0.1)  # Simulate computation

    if export:
        print("Exporting model to 'parker_model.zip'...")
        with open("parker_model.zip", "w") as f:
            f.write("mock_model_data")

        print("📢 Notifying MLOps Ticker...")
        try:
            api_token = os.getenv("WHATSAPP_API_TOKEN")
            phone_id = os.getenv("WHATSAPP_PHONE_ID")
            channel_id = os.getenv("WHATSAPP_CHANNEL_ID")

            observers = []
            if api_token and phone_id and channel_id:
                observers.append(WhatsAppEventObserver(api_token, phone_id, channel_id))
            else:
                print("⚠️  WhatsApp credentials not found. Skipping notification.")

            if observers:
                runtime = AgenticRuntime(observers=observers)
                artifact = ModelArtifact(
                    artifact_id=f"parker-rl-{str(uuid.uuid4())[:8]}",
                    model_id="parker-rl-v1",
                    weights_hash=str(uuid.uuid4()),
                    embedding_dim=128,
                    state=AgentLifecycleState.CONVERGED,
                    content="RL training completed",
                    metadata={
                        "pipeline": "parker-rl-training",
                        "episodes": episodes,
                        "reward_mean": episodes * 10,
                    },
                )
                await runtime.emit_event(artifact)
                print("✅ CONVERGED event emitted via AgenticRuntime.")
        except Exception as e:
            print(f"❌ Failed to notify ticker: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def interactive():
    try:
        asyncio.run(agent_loop())
    except KeyboardInterrupt:
        print("Agent stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train / Run Parker Agent")
    parser.add_argument("--episodes", type=int, default=10, help="Number of training episodes")
    parser.add_argument("--export", action="store_true", help="Export the trained model")
    parser.add_argument("--interactive", action="store_true", help="Run in intelligent agent mode (Gemini)")

    args = parser.parse_args()

    if args.interactive:
        interactive()
    else:
        asyncio.run(train(args.episodes, args.export))
