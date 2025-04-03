#!/usr/bin/env python3
"""
Script to fix configuration imports across the PenphinMind codebase.
This replaces various incorrect config imports with proper absolute imports.
"""

import os
import re
from pathlib import Path

def fix_imports(directory):
    """
    Fix incorrect config imports in all Python files in the given directory
    and its subdirectories.
    """
    total_files = 0
    fixed_files = 0
    
    # Import patterns to search for and their replacements
    import_patterns = [
        # Direct Mind.config imports
        ('from Mind.config import CONFIG', 'from config import CONFIG  # Use absolute import'),
        # Relative imports from Mind modules
        ('from ...config import CONFIG', 'from config import CONFIG  # Use absolute import'),
        ('from ....config import CONFIG', 'from config import CONFIG  # Use absolute import'),
        ('from .....config import CONFIG', 'from config import CONFIG  # Use absolute import'),
        # Relative imports with AudioOutputType
        ('from ...config import CONFIG, AudioOutputType', 'from config import CONFIG, AudioOutputType  # Use absolute import'),
        ('from ....config import CONFIG, AudioOutputType', 'from config import CONFIG, AudioOutputType  # Use absolute import'),
        ('from .....config import CONFIG, AudioOutputType', 'from config import CONFIG, AudioOutputType  # Use absolute import'),
    ]
    
    # Walk through all Python files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Skip this script itself
                if file == 'fix_config_imports.py':
                    continue
                    
                total_files += 1
                file_fixed = False
                
                # Read the file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for each pattern and apply replacements
                new_content = content
                for pattern, replacement in import_patterns:
                    if pattern in new_content:
                        new_content = new_content.replace(pattern, replacement)
                        file_fixed = True
                
                # Only write if changes were made
                if file_fixed:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    print(f"Fixed imports in: {file_path}")
                    fixed_files += 1
    
    return total_files, fixed_files

if __name__ == "__main__":
    # Fix imports in the PenphinMind directory
    project_root = Path(__file__).parent
    
    print(f"Scanning files in {project_root}...")
    total, fixed = fix_imports(project_root)
    
    print(f"\nSummary:")
    print(f"Total Python files scanned: {total}")
    print(f"Files with fixed imports: {fixed}")
    
    print("\nDone! All problematic config imports have been fixed.") 