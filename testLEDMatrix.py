"""
testLEDMatrix script to demonstrate LED Matrix functionality on Raspberry Pi 
and a mock matrix on macOS.
"""

import platform
import time
import asyncio
from PenphinMind.mind import Mind

async def runPsychologyDrivenMatrixTest():
    """
    Run a test of the LED matrix at 50% brightness, provide status output, 
    then clear on interruption or after the delay.
    """
    mind = Mind()
    await mind.initialize()
    
    try:
        print("✅ Running LED Matrix Test at 50% Brightness...")
        # Use the mind's visual cortex to control the matrix
        await mind.occipital_lobe["visual"].set_background(128, 128, 128)  # Grey background
        await asyncio.sleep(5)
        print("✅ Test Complete!")
    except KeyboardInterrupt:
        print("\n🔹 Exiting... Clearing Matrix.")
    finally:
        await mind.occipital_lobe["visual"].clear()

async def main():
    await runPsychologyDrivenMatrixTest()

if __name__ == "__main__":
    asyncio.run(main()) 