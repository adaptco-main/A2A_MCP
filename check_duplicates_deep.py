import json
from collections import Counter

def check_duplicates_deep(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        keys = []
        for line in lines:
            stripped = line.strip()
            if ':' in stripped and stripped.startswith('"'):
                key = stripped.split(':')[0].strip().strip('"')
                keys.append(key)
        
        counts = Counter(keys)
        duplicates = {k: v for k, v in counts.items() if v > 1 and k}
        if duplicates:
            print(f"DUPLICATES: {duplicates}")
        else:
            print("NO_DUPLICATES")

check_duplicates_deep(r'C:\Users\eqhsp\AppData\Roaming\Code\User\settings.json')
