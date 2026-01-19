import json

import jsonschema

SCHEMA_PATH = "schemas/ArcState.v1.schema.json"


def validate_arc_state(data):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
        schema = json.load(schema_file)

    try:
        jsonschema.validate(instance=data, schema=schema)
        print("✅ [VALID] ArcState matches the Hyperbolic-Cubic contract.")
        return True
    except jsonschema.exceptions.ValidationError as exc:
        print(f"❌ [FAIL] Deterministic Drift Detected: {exc.message}")
        return False


if __name__ == "__main__":
    test_artifact = {
        "fossil_id": "0x702447D5",
        "geodesic_manifold": {
            "curvature": -1.0,
            "step_vector": [0.33, 0.66, 0.99],
            "propagator_type": "Poincare_Disk",
        },
        "lattice_state": {
            "voxel_coords": [1, 2, 0],
            "rotation_kernel": [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
        },
        "invariant_status": "VALIDATED",
    }

    validate_arc_state(test_artifact)
