"""
DockingShell - The Hub controller for Agentic Field Games.

Implements the core cycle: Observe → Normalize → Unify → Act
"""
import numpy as np
from typing import Dict, List, Any, Optional
from .tensor_field import TensorField
from .spoke_adapter import SpokeAdapter


class DockingShell:
    """Central controller for the Agency Hub."""
    
    def __init__(self, embedding_dim: int = 64):
        """
        Initialize the Docking Shell.
        
        Args:
            embedding_dim: Dimensionality of the cognitive manifold
        """
        self.tensor_field = TensorField(embedding_dim=embedding_dim)
        self.spoke: Optional[SpokeAdapter] = None
        self.cycle_count = 0
        
    def dock(self, spoke: SpokeAdapter) -> bool:
        """
        Connect to a Field Game (Spoke).
        
        Args:
            spoke: SpokeAdapter implementation
            
        Returns:
            True if docking successful
        """
        self.spoke = spoke
        print(f"[DOCK] Connected to: {spoke.get_name()}")
        print(f"[DOCK] State schema: {spoke.get_state_schema()}")
        return True
    
    def inject_knowledge(self, concepts: List[np.ndarray]):
        """
        Prime the RAG system with knowledge vectors.
        
        Args:
            concepts: List of embedding vectors
        """
        self.tensor_field.inject_knowledge(concepts)
        print(f"[KNOWLEDGE] Injected {len(concepts)} concepts")
        
    def cycle(self) -> Dict[str, Any]:
        """
        Execute one cycle: Observe → Normalize → Unify → Act.
        
        Returns:
            Dictionary with cycle results
        """
        if not self.spoke:
            raise RuntimeError("No spoke docked. Call dock() first.")
            
        self.cycle_count += 1
        
        # 1. OBSERVE: Get raw state from environment
        raw_state = self.spoke.observe()
        
        # 2. NORMALIZE: Voxelize and compute eigenstate
        voxel_tensor = self.tensor_field.voxelize_state(raw_state)
        eigenstate = self.tensor_field.compute_eigenstate(voxel_tensor)
        
        # 3. UNIFY: Map to knowledge via RAG
        unified_state = self.tensor_field.rag_unify(eigenstate)
        
        # 4. ACT: Synthesize and execute action token
        token = self._synthesize_token(unified_state, raw_state)
        success = self.spoke.act(token)
        
        # Log cycle
        print(f"[CYCLE {self.cycle_count}] Eigenstate: {eigenstate[:5]}...")
        print(f"[CYCLE {self.cycle_count}] Token: {token}")
        print(f"[CYCLE {self.cycle_count}] Action success: {success}")
        
        return {
            "cycle": self.cycle_count,
            "eigenstate": eigenstate.tolist(),
            "unified_state": unified_state,
            "token": token,
            "success": success
        }
    
    def _synthesize_token(self, unified_state: Dict, raw_state: Dict) -> Dict[str, Any]:
        """
        Generate action token from unified state.
        
        NOTE: This is a heuristic placeholder. In production, this would
        call an LLM (Gemini/GPT) with the unified state as context.
        
        Args:
            unified_state: Knowledge-grounded state
            raw_state: Original environmental state
            
        Returns:
            Action token dictionary
        """
        # Simple heuristic: Use knowledge similarity to decide action
        scores = unified_state.get("similarity_scores", [])
        
        if not scores or max(scores) < 0.3:
            # Low knowledge match → explore
            return {
                "action": "explore",
                "params": {"direction": "random"}
            }
        else:
            # High knowledge match → exploit
            knowledge_idx = unified_state["knowledge_retrieved"][0]
            return {
                "action": "spawn_structure",
                "params": {
                    "type": "platform",
                    "knowledge_ref": knowledge_idx
                }
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about the docking session."""
        return {
            "cycles_executed": self.cycle_count,
            "spoke_connected": self.spoke.get_name() if self.spoke else None,
            "embedding_dim": self.tensor_field.get_embedding_dim(),
            "knowledge_count": len(self.tensor_field.knowledge_vectors)
        }
