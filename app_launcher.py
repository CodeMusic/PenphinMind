from PreFrontalCortex.system_journeling_manager import (
    SystemJournelingManager,
    SystemJournelingLevel
)
from PenphinMind.mind import Mind

async def launch_penphin_os():
    """Launch the main PenphinOS system"""
    mind = Mind()
    await mind.initialize()
    # Add any additional initialization or startup logic here
    return mind

async def launch_test_llm():
    """Launch the LLM test environment"""
    mind = Mind()
    await mind.initialize()
    # Add LLM-specific test logic here
    return mind

async def launch_test_led():
    """Launch the LED matrix test environment"""
    mind = Mind()
    await mind.initialize()
    # Add LED matrix-specific test logic here
    return mind

async def main():
    # Initialize the journaling manager
    journaling_manager = SystemJournelingManager(SystemJournelingLevel.INFO)
    journaling_manager.record_info("Initializing PenphinMind system")
    
    # Launch the appropriate component based on command line arguments
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-llm":
            await launch_test_llm()
        elif sys.argv[1] == "--test-led":
            await launch_test_led()
        else:
            await launch_penphin_os()
    else:
        await launch_penphin_os()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())