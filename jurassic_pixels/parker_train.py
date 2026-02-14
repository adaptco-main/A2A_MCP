import argparse
import sys
import time

def train(episodes: int, export: bool):
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

import asyncio
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
        train(args.episodes, args.export)
