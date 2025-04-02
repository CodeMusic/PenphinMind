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

    # Get or create BasalGanglia instance
    if basal_ganglia is None:
        # Delayed import to avoid circular dependencies
        from Mind.Subcortex.BasalGanglia.task_manager import BasalGanglia
        brain = BasalGanglia()
        brain.start()
    else:
        brain = basal_ganglia
    
    # Display task statistics if available
    if hasattr(brain, 'get_task_stats'):
        stats = brain.get_task_stats()
        journaling.recordInfo(f"[PrefrontalCortex] Current task stats: {stats}")
        if stats["active"] > 0:
            print(f"System currently has {stats['active']} active tasks.\n")
    elif hasattr(brain, 'get_task_count'):
        count = brain.get_task_count()
        journaling.recordInfo(f"[PrefrontalCortex] Current task count: {count}")
        if count > 0:
            print(f"System currently has {count} active tasks.\n")
    
    # Make sure to clean up when exiting the function
    try:
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
                from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
                await SynapticPathways.reset_llm()
                print("LLM has been reset.\n")
                continue
                
            # Handle stats command to show current tasks
            if user_input.lower() in ("stats", "tasks"):
                print("\nCurrent Task Status:")
                if hasattr(brain, 'get_task_stats'):
                    stats = brain.get_task_stats()
                    print(f"- Active tasks: {stats['active']}")
                    print(f"- Inactive tasks: {stats['inactive']}")
                    print(f"- Total tasks: {stats['total']}")
                    print(f"- Historical tasks: {stats['history']}")
                    last_cleanup = time.strftime("%H:%M:%S", time.localtime(stats['last_cleanup']))
                    print(f"- Last cleanup: {last_cleanup}")
                elif hasattr(brain, 'get_task_count'):
                    count = brain.get_task_count()
                    print(f"- Active tasks: {count}")
                else:
                    print("Task statistics not available.")
                print()
                continue

            # Delayed import to avoid circular dependency
            from Mind.Subcortex.BasalGanglia.tasks.think_task import ThinkTask
            
            # Create thinking task
            task = None
            
            # Use different methods depending on brain type
            if hasattr(brain, 'think'):
                # BasalGangliaIntegration has think method
                task = brain.think(user_input, stream=True)
                if task is None:
                    print("\n🤖 PenphinMind: Sorry, the system is currently busy with too many tasks.")
                    print("Please try the 'reset' command or wait a moment and try again.\n")
                    continue
            else:
                # Original BasalGanglia doesn't have think, use register_task
                task = ThinkTask(prompt=user_input, stream=True)
                if hasattr(brain, 'register_task'):
                    success = brain.register_task(task)
                    if not success:
                        print("\n🤖 PenphinMind: Sorry, the system is currently busy with too many tasks.")
                        print("Please try the 'reset' command or wait a moment and try again.\n")
                        continue
                else:
                    print("\n🤖 PenphinMind: Sorry, I don't know how to process that request.")
                    continue

            # Print AI response marker
            print("\n🤖 PenphinMind: ", end="", flush=True)

            # Wait for it to finish, showing streaming results
            last_result = ""
            timeout_counter = 0
            max_timeout = 300  # 30 seconds
            
            while task.active:
                if hasattr(task, 'result') and task.result and task.result != last_result:
                    # Only print the new part of the response
                    new_part = task.result[len(last_result):]
                    print(new_part, end="", flush=True)
                    last_result = task.result
                    timeout_counter = 0  # Reset timeout counter when we get new content
                else:
                    timeout_counter += 1
                    # Force-stop task if it's been inactive for too long
                    if timeout_counter > max_timeout:
                        journaling.recordWarning("Task timed out, forcing stop")
                        if hasattr(task, 'stop') and callable(task.stop):
                            task.stop()
                        break
                
                await asyncio.sleep(0.1)

            # Print any final result not yet displayed
            if hasattr(task, 'result') and task.result and task.result != last_result:
                new_part = task.result[len(last_result):]
                print(new_part, end="", flush=True)

            print("\n")  # Add newline after response
            
            # Make sure task properly stops
            if task.active and hasattr(task, 'stop') and callable(task.stop):
                task.stop()
                
    finally:
        # Log final task statistics
        if hasattr(brain, 'get_task_stats'):
            stats = brain.get_task_stats()
            journaling.recordInfo(f"[PrefrontalCortex] Final task stats: {stats}")
        elif hasattr(brain, 'get_task_count'):
            count = brain.get_task_count()
            journaling.recordInfo(f"[PrefrontalCortex] Final task count: {count}")
