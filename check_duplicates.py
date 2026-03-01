import json
from collections import Counter

def check_duplicates(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        keys = []
        for line in lines:
            if ':' in line:
                key = line.split(':')[0].strip().strip('"')
                keys.append(key)
        
        counts = Counter(keys)
        duplicates = {k: v for k, v in counts.items() if v > 1 and k}
        if duplicates:
            print(f"Duplicates in {path}: {duplicates}")
        else:
            print(f"No duplicates in {path}")

check_duplicates(r'C:\Users\eqhsp\AppData\Roaming\Code\User\settings.json')
check_duplicates(r'c:\Users\eqhsp\.antigravity\A2A_MCP\A2A_MCP\.vscode\settings.json')
