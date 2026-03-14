import asyncio
import logging
from orchestrator.intent_engine import IntentEngine

async def test_run():
    logging.basicConfig(level=logging.INFO)
    try:
        engine = IntentEngine()
        print("IntentEngine initialized successfully.")
        # Try a simple categorization
        plan = await engine.manager.categorize_project("Build a simple hello world app")
        print(f"ManagingAgent categorized project: {plan.project_name}")
        for action in plan.actions:
            print(f" - Task: {action.title}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_run())
