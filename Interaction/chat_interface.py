# PenphinMind/Interaction/chat_interface.py

import asyncio
import time
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.config import CONFIG

# Don't import BasalGanglia here - that's causing the circular import
# Instead we'll receive it as a parameter

journaling = SystemJournelingManager(CONFIG.log_level)

async def interactive_chat(basal_ganglia=None):
    """
    Interactive chat interface for PenphinMind
    
    Args:
        basal_ganglia: Optional BasalGanglia instance. If not provided,
                      a new instance will be created (may cause circular imports).
    """
    journaling.recordDebug("[PrefrontalCortex] PenphinMind is awake and ready for thought.")
    print("Type your message and press Enter. Type 'exit' to return to the main menu.\n")

    # Use provided basal_ganglia instance if available, otherwise create one
    if basal_ganglia is None:
        # Delayed import to avoid circular dependencies
        from Mind.Subcortex.BasalGanglia.task_manager import BasalGanglia
        brain = BasalGanglia()
        brain.start()
    else:
        brain = basal_ganglia

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
            # Delayed import
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            await SynapticPathways.reset_llm()
            print("LLM has been reset.\n")
            continue

        # Delayed import to avoid circular dependency
        from Mind.Subcortex.BasalGanglia.tasks.think_task import ThinkTask
        
        # Create and register thinking task
        task = ThinkTask(prompt=user_input, stream=True)
        brain.register_task(task)

        # Print AI response marker
        print("\n🤖 PenphinMind: ", end="", flush=True)

        # Wait for it to finish, showing streaming results
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

        print("\n")  # Add newline after response
