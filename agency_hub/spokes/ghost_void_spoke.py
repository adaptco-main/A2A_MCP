"""
Ghost Void Spoke
Wraps the World Model (Base44) and Drift Logic for Agentic Interaction.
"""

from typing import Dict, Any, Tuple
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agency_hub.spoke_adapter import SpokeAdapter
from phase_space_tick import PhaseSpaceTick

class GhostVoidSpoke(SpokeAdapter):
    """
    Connects the Agency Docking Shell to the Ghost Void Engine via PhaseSpaceTick simulation.
    """
    
    def __init__(self):
        self.world = PhaseSpaceTick()
        self.current_state = {
            "energy": 0.0,
            "drift_mode": "GRIP",
            "grid_pos": (5, 5),
            "similarity": 0.0
        }
        print("GhostVoidSpoke: Initialized. Connected to PhaseSpaceTick.")

    def observe(self) -> Dict[str, Any]:
        """
        Return current state of the Phase Space.
        """
        return self.current_state

    def act(self, token: Dict[str, Any]) -> bool:
        """
        Execute action token.
        Token Expected: {"action": "drive", "params": {"velocity": float, "steering": float, "prompt": str}}
        """
        action_type = token.get("action")
        params = token.get("params", {})
        
        if action_type == "drive":
            vel = params.get("velocity", 0.0)
            steer = params.get("steering", 0.0)
            prompt = params.get("prompt", "Agent Drive")
            
            result = self.world.run_tick(prompt, vel, steer, verbose=False)
            
            # Map result back to state schema
            drift_state = result["drift"]
            mode = drift_state.mode if drift_state else "STATIC"
            
            self.current_state = {
                "energy": result["energy"],
                "drift_mode": mode,
                "grid_pos": result["grid_pos"],
                "similarity": result["similarity"]
            }
            return True
            
        elif action_type == "reset":
            self.world.reset()
            self.current_state["grid_pos"] = (5, 5)
            self.current_state["drift_mode"] = "GRIP"
            return True
            
        print(f"GhostVoidSpoke: Unknown action '{action_type}'")
        return False

    def get_state_schema(self) -> Dict[str, str]:
        return {
            "energy": "float",
            "drift_mode": "string",
            "grid_pos": "tuple(int, int)",
            "similarity": "float"
        }
