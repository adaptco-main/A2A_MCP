import json
import os

path = r'c:\Users\eqhsp\.antigravity\A2A_MCP\A2A_MCP\.vscode\settings.json'
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("REFORMAT_WORKSPACE_SUCCESS")
except Exception as e:
    print(f"REFORMAT_WORKSPACE_ERROR: {e}")
