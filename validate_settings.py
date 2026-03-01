import json
try:
    with open(r'C:\Users\eqhsp\AppData\Roaming\Code\User\settings.json', 'r', encoding='utf-8') as f:
        json.load(f)
    print("GLOBAL_SETTINGS_VALID")
except Exception as e:
    print(f"GLOBAL_SETTINGS_ERROR: {e}")

try:
    with open(r'c:\Users\eqhsp\.antigravity\A2A_MCP\A2A_MCP\.vscode\settings.json', 'r', encoding='utf-8') as f:
        json.load(f)
    print("WORKSPACE_SETTINGS_VALID")
except Exception as e:
    print(f"WORKSPACE_SETTINGS_ERROR: {e}")
