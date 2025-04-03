#!/usr/bin/env python3
"""
Fix Bridge Indentation
---------------------
A script to fix the indentation errors in neurocortical_bridge.py
"""

import os
import re
import sys
from pathlib import Path

def fix_indentation():
    """Fix indentation in the neurocortical_bridge.py file"""
    # Path to the file
    file_path = Path(__file__).parent.parent / "Mind" / "Subcortex" / "neurocortical_bridge.py"
    
    print(f"Fixing indentation in {file_path}")
    
    if not file_path.exists():
        print(f"Error: {file_path} not found")
        return False
    
    # Read the file
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Fix the indentation in the set_model method
    pattern1 = r"else:\s+# API returned an error\s+error_message = error.get\(\"message\", \"Unknown error\"\)\s+return \{\s+\"status\": \"error\",\s+\"message\": f\"API Error: \{error_message\}\",\s+\"response\": setup_result\s+\}\s+# Fallback response\s+return \{"
    replacement1 = r"else:\n                # API returned an error\n                error_message = error.get(\"message\", \"Unknown error\")\n                return {\n                    \"status\": \"error\",\n                    \"message\": f\"API Error: {error_message}\",\n                    \"response\": setup_result\n                }\n            \n            # Fallback response\n            return {"
    
    # Fix the indentation in the execute method
    pattern2 = r"if work_id == \"llm\" and action == \"inference\":\s+# Get the prompt based on the command format\s+if isinstance\(command, dict\):"
    replacement2 = r"if work_id == \"llm\" and action == \"inference\":\n                # Get the prompt based on the command format\n                if isinstance(command, dict):"
    
    # Make the replacements
    content = re.sub(pattern1, replacement1, content)
    content = re.sub(pattern2, replacement2, content)
    
    # Write the file back
    with open(file_path, 'w') as file:
        file.write(content)
    
    print("Successfully fixed indentation")
    return True

if __name__ == "__main__":
    # Create directory if it doesn't exist
    os.makedirs(Path(__file__).parent, exist_ok=True)
    
    # Run the fix
    fix_indentation() 