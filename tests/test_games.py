#!/usr/bin/env python3
"""
Test script to launch the menu system with our games.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project root to sys.path to allow imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    """Main function to run the menu system."""
    try:
        # Display a simple header
        print("\n" + "=" * 60)
        print("PenphinMind Games Test")
        print("=" * 60 + "\n")
        
        print("Initializing menu system...")
        
        # Import menu_system from the correct location
        from Mind.menu_system import run_menu_system
        
        # Run the menu system
        await run_menu_system()
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logging.error(f"Error in test_games: {e}")
        import traceback
        logging.error(f"Stack trace: {traceback.format_exc()}")
        
    print("\nTest complete.")

if __name__ == "__main__":
    # Run the async event loop
    asyncio.run(main()) 