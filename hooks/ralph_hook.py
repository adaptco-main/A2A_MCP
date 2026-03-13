#!/usr/bin/env python3
"""
Ralph Loop Hook - Conceptual implementation for Gemini CLI AfterAgent hook.
This script checks for the <promise>DONE</promise> marker in the agent output.
If missing, it instructs the CLI to retry/continue the turn.
"""
import sys
import json

def main():
    try:
        # Read the JSON input from stdin
        input_data = json.load(sys.stdin)
        output = input_data.get("prompt_response", "")
        
        # Check for completion promise
        if "<promise>DONE</promise>" in output:
            print(json.dumps({"decision": "allow", "reason": "Task complete."}))
        else:
            print(json.dumps({
                "decision": "continue",
                "next_prompt": "I'm helping! The task is not finished. Please continue your work. Remember to output <promise>DONE</promise> when you are truly finished."
            }))
    except Exception as e:
        # On error, allow the exit to avoid infinite loops
        print(json.dumps({"decision": "allow", "reason": f"Hook error: {str(e)}"}))

if __name__ == "__main__":
    main()
