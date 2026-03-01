import json

def dict_raise_on_duplicates(ordered_pairs):
    d = {}
    for k, v in ordered_pairs:
        if k in d:
            raise ValueError(f"Duplicate key: {k}")
        d[k] = v
    return d

try:
    with open(r'C:\Users\eqhsp\AppData\Roaming\Code\User\settings.json', 'r', encoding='utf-8') as f:
        json.load(f, object_pairs_hook=dict_raise_on_duplicates)
    print("GLOBAL: VALID")
except ValueError as e:
    print(f"GLOBAL: {e}")
except Exception as e:
    print(f"GLOBAL ERROR: {e}")

try:
    with open(r'c:\Users\eqhsp\.antigravity\A2A_MCP\A2A_MCP\.vscode\settings.json', 'r', encoding='utf-8') as f:
        json.load(f, object_pairs_hook=dict_raise_on_duplicates)
    print("WORKSPACE: VALID")
except ValueError as e:
    print(f"WORKSPACE: {e}")
