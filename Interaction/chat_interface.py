# PenphinMind/Interaction/chat_interface.py

import asyncio
import time
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.config import CONFIG
# Import SynapticPathways at the top level so it's properly in scope
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge

# Initialize journaling
journaling = SystemJournelingManager(CONFIG.log_level)

async def interactive_chat(basal_ganglia=None):
    """
    Interactive chat interface for PenphinMind
    
    Args:
        basal_ganglia: BasalGanglia instance from the menu system
    """
    journaling.recordDebug("[PrefrontalCortex] PenphinMind is awake and ready for thought.")
    print("Type your message and press Enter. Type 'exit' to return to the main menu.\n")

    # Use provided basal_ganglia instance
    brain = basal_ganglia
    
    # SynapticPathways is now imported at the top level
    
    while True:
        user_input = input("🧠 You: ").strip()

        if user_input.lower() in ("exit", "quit", "menu"):
            journaling.recordDebug("[PrefrontalCortex] Ending chat session.")
            print("Returning to main menu...")
            break

        if not user_input:
            continue

        # Handle reset command
        if user_input.lower() == "reset":
            print("\nResetting LLM...")
            await NeurocorticalBridge.execute("reset_llm", use_task=False)
            print("LLM has been reset.\n")
            continue

        # Process thinking using the bridge
        print("\n🐧🐬 PenphinMind: ", end="", flush=True)
        
        try:
            # Use the bridge with task=True for interactive streaming
            task = await NeurocorticalBridge.execute(
                "think", 
                {"prompt": user_input}, 
                use_task=True,
                stream=True
            )
            
            if task:
                # Wait for the task to complete, showing streaming results
                last_result = ""
                while task.active:
                    if hasattr(task, 'result') and task.result and task.result != last_result:
                        # Only print the new part of the response
                        new_part = task.result[len(last_result):]
                        print(new_part, end="", flush=True)
                        last_result = task.result
                    await asyncio.sleep(0.1)
                
                # Print any final result not yet displayed
                if hasattr(task, 'result') and task.result and task.result != last_result:
                    new_part = task.result[len(last_result):]
                    print(new_part, end="", flush=True)
                    
                # Make sure task properly stops
                if task.active and hasattr(task, 'stop') and callable(task.stop):
                    task.stop()
            else:
                print("Error: Could not create thinking task.")
                    
        except Exception as e:
            journaling.recordError(f"Error in thinking task: {e}")
            import traceback
            journaling.recordError(f"Stack trace: {traceback.format_exc()}")
            print(f"Error processing your request: {e}")
            
        print()  # Add newline after response
