import os
import shutil
from pathlib import Path

def cleanup_project():
    """
    Cleans all files and directories in the current directory
    """
    current_dir = Path.cwd()
    
    # First, remove all __pycache__ directories and .pyc files
    for item in current_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(item)
            print(f"Removed: {item}")
        except Exception as e:
            print(f"Error removing {item}: {e}")
            
    for item in current_dir.rglob("*.pyc"):
        try:
            os.remove(item)
            print(f"Removed: {item}")
        except Exception as e:
            print(f"Error removing {item}: {e}")
    
    # Now remove all other files and directories
    for item in current_dir.iterdir():
        try:
            if item.is_file():
                os.remove(item)
                print(f"Removed file: {item}")
            elif item.is_dir():
                shutil.rmtree(item)
                print(f"Removed directory: {item}")
        except Exception as e:
            print(f"Error removing {item}: {e}")

if __name__ == "__main__":
    cleanup_project() 