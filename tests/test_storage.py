import pytest
from orchestrator.storage import DBManager
from schemas.agent_artifacts import MCPArtifact
import uuid
import json

def test_artifact_persistence_lifecycle():
    """
    Validates the 'Schematic Rigor' directive by testing 
    the full Save -> Retrieve cycle.
    """
    db = DBManager()
    test_id = str(uuid.uuid4())
    
    # 1. Setup Mock Artifact
    artifact_content = {"status": "verified"}
    artifact = MCPArtifact(
        artifact_id=test_id,
        type="unit_test_artifact",
        content=json.dumps(artifact_content),
        metadata={
            "parent_artifact_id": "root-node",
            "agent_name": "TestAgent",
            "version": "1.0.0",
        }
    )

    # 2. Test Save (Persistence Directive)
    db.save_artifact(artifact)

    # 3. Test Retrieval (Traceability Directive)
    retrieved = db.get_artifact(test_id)
    
    assert retrieved is not None
    assert retrieved.agent_name == "TestAgent"
    retrieved_content = json.loads(retrieved.content)
    assert retrieved_content["status"] == "verified"
    print(f"✓ Persistence Lifecycle Verified for ID: {test_id}")

if __name__ == "__main__":
    test_artifact_persistence_lifecycle()
