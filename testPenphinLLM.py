"""
Test script for PenphinMind LLM functionality
"""

import os
import sys
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import platform

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger = logging.getLogger(__name__)
    logger.info(f"Added project root to Python path: {project_root}")

from Mind.mind import Mind
from Mind.config import CONFIG

logger = logging.getLogger(__name__)

async def test_llm():
    """Test LLM functionality"""
    mind = Mind()
    
    try:
        # Initialize mind
        await mind.initialize()
        
        # Check if we're on macOS
        is_macos = platform.system() == "Darwin"
        
        if is_macos:
            # Interactive chat mode for macOS
            print("\nWelcome to PenphinMind Chat!")
            print("Type 'exit' to quit")
            print("-" * 50)
            
            while True:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == 'exit':
                    break
                    
                # Process input through mind
                response = await mind.process_input(user_input)
                
                # Print response
                if response.get("status") == "ok":
                    print("\nPenphinMind:", response.get("response", ""))
                else:
                    print("\nError:", response.get("message", "Unknown error"))
                    
        else:
            # Basic test for other platforms
            test_input = "Hello, how are you?"
            result = await mind.process_input(test_input)
            logger.info(f"LLM test result: {result}")
            
    finally:
        # Clean up
        await mind.cleanup()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    asyncio.run(test_llm()) 