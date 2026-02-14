import json
import os

class SystemsArchitect:
    """
    Architect agent responsible for policy schema definition and governance.
    """
    def __init__(self):
        self.policy_dir = "agency_hub/architect"
        self.policy_path = os.path.join(self.policy_dir, "gate_policy.json")
        self.schema_path = os.path.join(self.policy_dir, "gate_policy.schema.json")

    def initialize_policies(self):
        """
        Creates the initial gate policy and local-resolvable schema.
        """
        print("SystemsArchitect: Initializing policies...")
        
        # 1. Create Schema
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "identity": {"type": "string"},
                "permissions": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "proof_config": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "method": {"type": "string"}
                    }
                }
            },
            "required": ["identity", "permissions"]
        }
        
        os.makedirs(self.policy_dir, exist_ok=True)
        with open(self.schema_path, 'w') as f:
            json.dump(schema, f, indent=2)
        print(f"SystemsArchitect: Local schema created at {self.schema_path}")

        # 2. Create Policy with relative $schema URI
        policy = {
            "$schema": "./gate_policy.schema.json",
            "identity": "ghost-void-core",
            "permissions": ["read", "execute", "test"],
            "proof_config": {
                "enabled": True,
                "method": "sha256-anchored"
            }
        }
        
        with open(self.policy_path, 'w') as f:
            json.dump(policy, f, indent=2)
        print(f"SystemsArchitect: Policy created with local schema reference at {self.policy_path}")

if __name__ == "__main__":
    architect = SystemsArchitect()
    architect.initialize_policies()
