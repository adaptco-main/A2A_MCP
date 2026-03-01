import json
import os

path = r'C:\Users\eqhsp\AppData\Roaming\Code\User\settings.json'
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("REFORMAT_SUCCESS")
except Exception as e:
    print(f"REFORMAT_ERROR: {e}")
