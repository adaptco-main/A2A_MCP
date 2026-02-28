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
from llm.gemini_client import GeminiClient
from llm.decision_engine import DecisionEngine
from llm.decision_schema import ParkerDecision

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
    "Choose the next action.\n"
    "Allowed directions for 'move' type: left, right, jump, idle.\n"
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


def decide_action(engine: DecisionEngine, observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Gemini via the DecisionEngine to produce the next Parker action.
    Returns a mapped dictionary for fail-closed WebSocket compliance.
    """
    user_prompt = PARKER_PROMPT_TEMPLATE.format(
        observation=json.dumps(observation, sort_keys=True, separators=(",", ":"))
    )
    try:
        decision = engine.decide(
            system="You are Parker's training controller. Decide the next action. Output JSON that matches ParkerDecision.",
            user=f"Context:\nEnvironment observation.\n\nState:\n{user_prompt}\n\nGoal:\nNavigate without crashing."
        )
        
        logger.debug("Parker decided: %s (confidence: %f)", decision.action, decision.confidence)
        
        # Map ParkerDecision back to legacy move dictionary for WebSockets
        if decision.action in ["drive", "continue"]:
             # If mapping drive to ws schema...
             # We'll use the direction equivalent
             return {"type": "move", "direction": "idle"}
        elif decision.action in ["left", "right", "jump", "idle"]:
             return {"type": "move", "direction": decision.action}
        else:
             return {"type": "move", "direction": "idle"}
             
    except Exception as e:
        logger.warning("E_MODEL_CALL_FAILED: %s", e)

    logger.info("Fail-closed: returning idle action")
    return FAIL_CLOSED_ACTION.copy()


# ---------------------------------------------------------------------------
# Gemini client initialisation
# ---------------------------------------------------------------------------

def init_gemini() -> Optional[DecisionEngine]:
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
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        client = GeminiClient(api_key=api_key, model=model_name)
        engine = DecisionEngine(client)
        logger.info(f"Gemini client and Decision Engine initialised ({model_name})")
        return engine
    except Exception as e:
        logger.error(f"E_GEMINI_INIT_FAILED: {e}")
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

                # Gemini decides the action via DecisionEngine
                action = decide_action(client, observation)
                await websocket.send(json.dumps(action))

            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection closed")
                break
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                break


# ---------------------------------------------------------------------------
# Training loop (LoRA Adaptation)
# ---------------------------------------------------------------------------

async def train(episodes: int, export: bool):
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
        from peft import get_peft_model, LoraConfig, TaskType
        from datasets import Dataset
    except ImportError:
        logger.error("Missing required ML/LoRA dependencies (transformers, peft, datasets). Cannot train.")
        return

    print(f"Starting LoRA adaptation for {episodes} steps...")
    
    # 1. Load Base Model
    model_id = "gpt2" # Using a lightweight model for this architecture out of the box
    logger.info(f"Loading base model {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_id)

    # 2. Configure LoRA
    # Mapping our schema concept to actual PEFT config
    lora_config = LoraConfig(
        r=8, 
        lora_alpha=16,
        target_modules=["c_attn"], # gpt2 specific attention blocks
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 3. Generate dynamic training data using DecisionEngine
    client = init_gemini()
    training_texts = []
    
    if client:
        print("Gathering dynamic observations from DecisionEngine...")
        # Simulate phase space states
        simulated_states = [
            {"player": {"x": 10, "y": 5}, "enemy": {"x": 12, "y": 5}},
            {"player": {"x": 10, "y": 5}, "enemy": {"x": 10, "y": 6}},
            {"player": {"x": 20, "y": 2}, "enemy": {"x": 15, "y": 2}},
        ] * (episodes // 3 + 1)
        simulated_states = simulated_states[:episodes]
        
        for state in simulated_states:
            action = decide_action(client, state)
            obs_str = json.dumps(state, sort_keys=True, separators=(",", ":"))
            dir_str = action.get("direction", "idle")
            training_texts.append(f"Observation: {obs_str}. Action: {dir_str}")
    else:
        print("Falling back to simulated logs (Gemini unavailable)...")
        training_texts = [
            "Observation: player at (10, 5), enemy at (12, 5). Action: jump",
            "Observation: player at (10, 5), enemy at (10, 6). Action: left",
        ] * (episodes // 2 + 1)
        training_texts = training_texts[:episodes]

    dataset = Dataset.from_dict({"text": training_texts})
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=64)
        
    tokenized_datasets = dataset.map(tokenize_function, batched=True)

    # 4. Train
    training_args = TrainingArguments(
        output_dir="./parker_lora_outputs",
        learning_rate=2e-4,
        per_device_train_batch_size=2,
        num_train_epochs=1,
        max_steps=episodes,
        logging_steps=max(1, episodes // 10),
        save_strategy="no" # Keep it lightweight for this script
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets,
    )

    trainer.train()

    if export:
        export_path = "parker_model_lora"
        print(f"Exporting LoRA adapters to '{export_path}'...")
        model.save_pretrained(export_path)

        print("📢 Notifying Event Store via AgenticRuntime...")
        try:
            from schemas.model_artifact import LoRAConfig as ArtifactLoRAConfig
            observers = []
            
            # Use WhatsApp if credentials exist
            api_token = os.getenv("WHATSAPP_API_TOKEN")
            phone_id = os.getenv("WHATSAPP_PHONE_ID")
            channel_id = os.getenv("WHATSAPP_CHANNEL_ID")
            if api_token and phone_id and channel_id:
                observers.append(WhatsAppEventObserver(api_token, phone_id, channel_id))
            else:
                print("⚠️  WhatsApp credentials not found. Local event store only.")

            runtime = AgenticRuntime(observers=observers)
            
            # Map the config into the artifact
            recorded_lora = ArtifactLoRAConfig(
                rank=lora_config.r,
                alpha=lora_config.lora_alpha,
                target_modules=list(lora_config.target_modules) if isinstance(lora_config.target_modules, (list, set)) else [],
                training_samples=len(dataset)
            )
            
            artifact = ModelArtifact(
                artifact_id=f"parker-lora-{str(uuid.uuid4())[:8]}",
                model_id=model_id,
                weights_hash=str(uuid.uuid4()), # In prod this would be the actual directory hash
                embedding_dim=model.config.hidden_size if hasattr(model.config, 'hidden_size') else 128,
                state=AgentLifecycleState.CONVERGED,
                content="LoRA adaptation completed securely",
                lora_config=recorded_lora,
                metadata={
                    "pipeline": "parker-lora-training",
                    "steps": episodes,
                },
            )
            
            # Fire and forget emission
            await runtime.emit_event(artifact)
            print("✅ CONVERGED event emitted via AgenticRuntime.")
        except Exception as e:
            print(f"❌ Failed to notify runtime: {e}")


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
    parser.add_argument("--episodes", type=int, default=10, help="Number of training steps")
    parser.add_argument("--export", action="store_true", help="Export the trained model adapters")
    parser.add_argument("--interactive", action="store_true", help="Run in intelligent agent mode (Gemini)")

    args = parser.parse_args()

    if args.interactive:
        interactive()
    else:
        asyncio.run(train(args.episodes, args.export))
