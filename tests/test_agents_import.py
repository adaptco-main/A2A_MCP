
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents import TesterAgent, GatingAgent, ActionModelingAgent
    print("Successfully imported TesterAgent, GatingAgent, and ActionModelingAgent.")
    
    tester = TesterAgent()
    gater = GatingAgent()
    modeler = ActionModelingAgent()
    
    print("Successfully instantiated all agents.")
    
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error during instantiation: {e}")
    sys.exit(1)
