import argparse
import sys
import time
import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path

# Add project root to sys.path to allow imports from orchestrator
sys.path.append(str(Path(__file__).parent.parent))

from middleware import AgenticRuntime, WhatsAppEventObserver
from schemas.model_artifact import ModelArtifact, AgentLifecycleState

async def train(episodes: int, export: bool):
    print(f"Starting training for {episodes} episodes...")
    # Simulate RL training loop
    for i in range(episodes):
        print(f"Episode {i+1}/{episodes}: Reward={(i+1)*10}")
        time.sleep(0.1) # Simulate computation

    if export:
        print("Exporting model to 'parker_model.zip'...")
        # Simulate export
        with open("parker_model.zip", "w") as f:
            f.write("mock_model_data")
        
        # Notify MLOps Ticker
        print("📢 Notifying MLOps Ticker...")
        try:
            # Initialize Observer with Env Vars (graceful fallback if not set)
            api_token = os.getenv("WHATSAPP_API_TOKEN")
            phone_id = os.getenv("WHATSAPP_PHONE_ID")
            channel_id = os.getenv("WHATSAPP_CHANNEL_ID")
            
            observers = []
            if api_token and phone_id and channel_id:
                observers.append(WhatsAppEventObserver(api_token, phone_id, channel_id))
            else:
                print("⚠️ WhatsApp credentials not found. Skipping notification.")

            if observers:
                runtime = AgenticRuntime(observers=observers)
                
                # Use ModelArtifact for better schema alignment
                artifact = ModelArtifact(
                    artifact_id=f"parker-rl-{str(uuid.uuid4())[:8]}",
                    model_id="parker-rl-v1",
                    weights_hash=str(uuid.uuid4()),
                    embedding_dim=128,
                    state=AgentLifecycleState.CONVERGED, # Assuming training completion is convergence
                    content="RL training completed",
                    metadata={
                        "pipeline": "parker-rl-training",
                        "episodes": episodes,
                        "reward_mean": episodes*10
                    }
                )
                
                await runtime.emit_event(artifact)
                print("✅ detailed CONVERGED event emitted to ticker via AgenticRuntime.")
        except Exception as e:
            print(f"❌ Failed to notify ticker: {e}")

import websockets
import json
import random

async def agent_loop():
    uri = "ws://server:8080"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        print("Connected to Game Server")
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                # print(f"Received observation: {data}")
                
                # Simple Logic: Randomly move
                action = {
                    "type": "move",
                    "direction": random.choice(["left", "right", "jump", "idle"])
                }
                await websocket.send(json.dumps(action))
                
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

def interactive():
    try:
        asyncio.run(agent_loop())
    except KeyboardInterrupt:
        print("Agent stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Parker RL Agent")
    parser.add_argument("--episodes", type=int, default=10, help="Number of training episodes")
    parser.add_argument("--export", action="store_true", help="Export the trained model")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()

    if args.interactive:
        interactive()
    else:
        asyncio.run(train(args.episodes, args.export))
