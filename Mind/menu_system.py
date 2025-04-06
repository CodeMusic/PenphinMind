import os
import asyncio
from typing import Dict, Any, List
import time
import json

from Mind.mind import Mind
from Interaction.chat_interface import interactive_chat
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.GameCortex.game_manager import GameManager
from Mind.OccipitalLobe.visual_layout_manager import VisualLayoutManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

# Create global Mind instance
mind = Mind()

# Create GameManager instance
game_manager = GameManager()

def clear_screen():
    """Clear the terminal screen"""
    if os.name == 'nt':  # Windows
        os.system('cls')
    else:  # Unix/Linux/MacOS
        os.system('clear')

def print_header():
    """Print PenphinMind header"""
    print("=" * 60)
    print("                 🐧 PenphinMind 🐬")
    print("=" * 60)
    print()

async def get_current_model_info():
    """Get information about the currently active model"""
    # Use Mind to get active model
    active_model = await mind.get_model()
    
    if active_model and active_model.get("success"):
        if isinstance(active_model["model"], dict):
            return active_model["model"]
        elif isinstance(active_model["model"], str):
            if "details" in active_model:
                return active_model["details"]
            return {"model": active_model["model"], "type": active_model["model"].split("-")[0] if "-" in active_model["model"] else ""}
    
    # If API call fails, use the locally cached model name
    model_name = mind.get_default_model()
    if model_name:
        return {"model": model_name, "type": model_name.split("-")[0] if "-" in model_name else ""}
    
    return {"model": "No model selected", "type": ""}

async def display_main_menu() -> str:
    """Display main menu and get user choice"""
    print_header()
    
    # First establish connection with ping
    result = await mind.ping_system()
    
    # Then get hardware info
    hw_info_result = await mind.get_hardware_info()
    
    # Display hardware info
    hw_info = mind.format_hardware_info()
    print(hw_info)
    print()
    
    # Display main menu options
    print("=== Main Menu ===")
    print("1) Chat with PenphinMind")
    print("2) Model Information")
    print("3) System Menu")
    print("4) Games Menu")
    print("5) Exit")
    
    print("\nEnter your choice (1-5): ", end="")
    choice = input().strip()
    return choice

async def display_model_list() -> str:
    """Display list of available models and get user choice"""
    print_header()
    
    # Refresh hardware info before displaying
    hw_info_result = await mind.get_hardware_info()
    
    # Display hardware info
    hw_info = mind.format_hardware_info()
    print(hw_info)

    # Show current active model if available
    current_model = mind.get_default_model()
    if current_model:
        print(f"\nCurrent active model: {current_model}")

async def reboot_system(mind_instance=None):
    """Reboot the M5Stack system"""
    print_header()
    
    # Use the global mind instance if not provided
    mind_instance = mind_instance or mind
    
    print("Rebooting system...")
    
    # Send reboot command
    result = await mind_instance.reboot_device()
    
    if result and result.get("status") == "ok":
        print("Reboot command sent successfully.")
        print("Device will restart. The application will lose connection.")
        print("You may need to restart the application after device reboot.")
        
        # Wait a moment to allow device to reboot
        print("\nWaiting for device to reboot...")
        await asyncio.sleep(5)
        
        # Try to reconnect and get hardware info
        try:
            print("Attempting to reconnect...")
            # Re-initialize the connection through Mind
            reconnect_result = await mind_instance.connect(mind_instance._connection_type)
            
            if reconnect_result:
                # Get updated hardware info
                hw_result = await mind_instance.get_hardware_info()
                print("\nDevice reconnected successfully!")
                print(mind_instance.format_hardware_info())
            else:
                print("\nFailed to reconnect")
        except Exception as e:
            journaling_manager.recordError(f"Error reconnecting after reboot: {e}")
            print("\nCould not reconnect to device after reboot.")
            print("You will need to restart the application manually.")
    else:
        error_msg = result.get("message", "Unknown error") if result else "No response"
        print(f"Reboot failed: {error_msg}")
    
    print("\nPress Enter to return to main menu...")
    input()

# Import interactive_chat here to avoid circular imports

# Start the interactive chat with the existing BasalGanglia instance
async def start_chat(mind_instance=None):
    """Start chat interface with LLM"""
    try:
        # Use the global mind instance if not provided
        mind_instance = mind_instance or mind
        
        # First establish a basic ping connection
        print("Establishing connection...")
        ping_result = await mind_instance.ping_system()
        if not ping_result or ping_result.get("status") != "ok":
            print("Error connecting to hardware. Press Enter to return to main menu...")
            input()
            return
        
        # Now refresh hardware info before displaying
        hw_info_result = await mind_instance.get_hardware_info()
        
        # Directly use the interactive chat interface with Mind
        # The ChatManager inside interactive_chat will handle model selection and setup
        await interactive_chat(mind_instance)
            
    except Exception as e:
        journaling_manager.recordError(f"Error starting chat: {e}")
        import traceback
        journaling_manager.recordError(f"Stack trace: {traceback.format_exc()}")
        print(f"\nError starting chat: {e}")
        input("\nPress Enter to return to main menu...")

async def manage_tasks():
    """Display and manage active tasks"""
    print_header()
    
    # Display hardware info
    hw_info_data = await mind.get_hardware_info()
    hw_info = mind.format_hardware_info()
    print(hw_info)
    
    print("\n=== Task Management ===")
    
    # Get task information from Mind's high-level API
    task_info = mind.get_task_status()
    
    # Display task information
    print("\nTasks Overview:")
    print(f"Total tasks: {task_info['total_count']}")
    
    # Show active tasks
    print("\nActive tasks:")
    if task_info['active_tasks']:
        for i, task in enumerate(task_info['active_tasks']):
            task_name = task.get("name", f"Task {i+1}")
            task_type = task.get("type", "Unknown")
            created_time = task.get("created_at", 0)
            
            time_str = "unknown time"
            if created_time:
                age = time.time() - created_time
                time_str = f"{age:.1f} seconds ago"
            
            print(f"  {i+1}. {task_name} (Type: {task_type}, Created: {time_str})")
    else:
        print("  No active tasks")
        
    # Show inactive tasks
    print("\nInactive tasks:")
    if task_info['inactive_tasks']:
        for i, task in enumerate(task_info['inactive_tasks']):
            task_name = task.get("name", f"Task {i+1}")
            task_type = task.get("type", "Unknown")
            
            print(f"  {i+1}. {task_name} (Type: {task_type})")
    else:
        print("  No inactive tasks")
    
    # Display device resource usage (indirect way to see task load)
    print("\nDevice Resource Usage:")
    hw_info = await mind.get_hardware_info()
    hw_data = hw_info.get("response", {}) if hw_info and isinstance(hw_info, dict) else {}
    
    cpu_load = hw_data.get("cpu_loadavg", "N/A")
    mem_usage = hw_data.get("mem", "N/A")
    temp = hw_data.get("temperature", "N/A")
    
    print(f"  CPU Load: {cpu_load}%")
    print(f"  Memory Usage: {mem_usage}%")
    if temp and temp != "N/A":
        temp_val = f"{temp:.1f}°C" if isinstance(temp, (int, float)) else temp
        print(f"  Temperature: {temp_val}")
    
    # Options for task management
    print("\nTask Management Options:")
    print("1) Refresh task information")
    print("2) Reset LLM system")
    print("0) Back to System Menu")
    
    option = input("\nEnter option: ").strip()
    
    if option == "1":
        # Just refresh by calling this function again
        await manage_tasks()
    elif option == "2":
        # Reset LLM
        print("\nResetting LLM system...")
        result = await mind.reset_system()
        reset_success = result.get("status") == "ok"
        print(f"Reset {'successful' if reset_success else 'failed'}")
        if not reset_success:
            print(f"Error: {result.get('message', 'Unknown error')}")
        input("\nPress Enter to continue...")
    else:
        # Any other input returns to system menu
        return

async def system_menu():
    """Display system management menu"""
    print_header()
    
    print("\n=== System Menu ===")
    print("1) Task Management")
    print("2) Reboot System")
    print("0) Back to Main Menu")
    
    option = input("\nEnter option: ").strip()
    
    if option == "1":
        await manage_tasks()
    elif option == "2":
        await reboot_system()
    else:
        # Any other input returns to main menu
        return

async def games_menu():
    """Display games menu and launch selected game"""
    while True:
        print_header()
        
        print("\n=== Games Menu ===")
        
        # Display available games
        available_games = game_manager.list_available_games()
        
        if not available_games:
            print("\nNo games found in the GameCortex directory.")
            print("\n0) Back to Main Menu")
            
            option = input("\nEnter option: ").strip()
            return
        
        print("\nAvailable Games:")
        for i, game_name in enumerate(available_games, 1):
            print(f"{i}) {game_name}")
        
        print("\nOptions:")
        print(f"{len(available_games) + 1}) Game Settings")
        print("0) Back to Main Menu")
        
        # Get user choice
        option = input("\nSelect a game to play or option: ").strip()
        
        if option == "0":
            return
        
        try:
            option_num = int(option)
            if 1 <= option_num <= len(available_games):
                selected_game = available_games[option_num - 1]
                
                print(f"\nLaunching {selected_game}...")
                
                # Initialize the visual cortex and layout manager from the brain architecture
                try:
                    # Access the visual cortex through the proper brain regions
                    print("[NeuralNetwork] Activating visual processing regions...")
                    
                    # Import within the function to avoid circular imports
                    from Mind.OccipitalLobe.VisualCortex.primary_area import PrimaryVisualArea
                    from Mind.OccipitalLobe.visual_layout_manager import VisualLayoutManager
                    from rgbmatrix import RGBMatrix, RGBMatrixOptions
                    
                    # Check if mind already has references to these components
                    primary_visualCortex = None
                    
                    # First try to access through Mind's existing channels
                    if hasattr(mind, 'visual_cortex') and hasattr(mind.visual_cortex, 'primary_area'):
                        primary_visualCortex = mind.visual_cortex.primary_area
                        print("[Visual Cortex] Retrieved existing visual processing module.")
                    else:
                        # Create a new instance of PrimaryVisualArea
                        print("[Visual Cortex] Initializing new visual processing module.")
                        primary_visualCortex = PrimaryVisualArea()
                        # Initialize it with the proper async pattern
                        try:
                            print("[Visual Cortex] Initializing matrix...")
                            import asyncio
                            await primary_visualCortex.initialize()
                            # Store it on the mind object for future use
                            if not hasattr(mind, 'visual_cortex'):
                                setattr(mind, 'visual_cortex', type('VisualCortex', (), {}))
                            setattr(mind.visual_cortex, 'primary_area', primary_visualCortex)
                            print("[Visual Cortex] Visual processing initialized successfully.")
                        except Exception as e:
                            journaling_manager.recordError(f"Error initializing visual cortex: {e}")
                            print(f"[Visual Cortex] Error initializing through brain architecture: {e}")
                            print("[Visual Cortex] Falling back to direct matrix initialization.")
                            
                            # FALLBACK - Direct matrix initialization without brain architecture
                            # This ensures games can run even if the Mind connection fails
                            options = RGBMatrixOptions()
                            options.rows = 64
                            options.cols = 64
                            options.chain_length = 1
                            options.parallel = 1
                            options.hardware_mapping = 'regular'
                            
                            # Apply brightness setting if it exists
                            if hasattr(mind, 'preferred_matrix_brightness'):
                                options.brightness = getattr(mind, 'preferred_matrix_brightness')
                            else:
                                options.brightness = 30  # Default
                                
                            options.disable_hardware_pulsing = True
                            options.gpio_slowdown = 2
                            
                            # Create direct matrix
                            try:
                                print("[Visual Cortex] Initializing direct matrix...")
                                direct_matrix = RGBMatrix(options=options)
                                print("[Visual Cortex] Direct matrix initialized successfully.")
                                
                                # Create layout manager that uses direct matrix
                                layout_manager = VisualLayoutManager(matrix=direct_matrix)
                                print("[Visual Organization] Layout manager initialized with direct matrix.")
                                
                                # Launch game with direct matrix
                                print(f"[Game Cortex] Launching {selected_game} with direct matrix.")
                                game_instance = game_manager.launch_game(
                                    selected_game,
                                    direct_matrix,
                                    layout_manager
                                )
                                
                                if game_instance:
                                    print(f"[Game Cortex] {selected_game} initiated successfully via direct matrix.")
                                    print(f"Game is now running. Press CTRL+C to exit the game.")
                                    
                                    # Game loop with direct matrix
                                    try:
                                        last_time = time.time()
                                        while game_instance and game_manager.get_active_game():
                                            # Calculate delta time for smooth animations
                                            current_time = time.time()
                                            dt = current_time - last_time
                                            last_time = current_time
                                            
                                            # Update game logic
                                            game_instance.update(dt)
                                            
                                            # After updating, call draw
                                            game_instance.draw()
                                            
                                            # Update the display through layout manager
                                            layout_manager.update_display(rotate_degrees=270)
                                            
                                            # Sleep to keep CPU usage reasonable
                                            await asyncio.sleep(0.033)  # ~30 FPS
                                    except KeyboardInterrupt:
                                        print("\n[User Input] Game interrupted by user.")
                                    finally:
                                        print("[Game Cortex] Stopping active game...")
                                        game_manager.stop_active_game()
                                        direct_matrix.Clear()
                                        print("[Visual Cortex] Display cleared, game stopped.")
                                
                                # Return to menu after game ends
                                input("\nPress Enter to return to Games Menu...")
                                continue
                            except Exception as e:
                                journaling_manager.recordError(f"Error creating direct matrix: {e}")
                                print(f"[Visual Cortex] Error creating direct matrix: {e}")
                    
                    # Only continue with brain architecture path if visual cortex initialized
                    if primary_visualCortex and hasattr(primary_visualCortex, '_matrix'):
                        # Create a layout manager that uses the primary visual cortex
                        layout_manager = VisualLayoutManager(visual_cortex=primary_visualCortex)
                        print("[Visual Organization] Layout manager initialized using visual cortex.")
                        
                        # Apply brightness setting from settings if it exists
                        if hasattr(mind, 'preferred_matrix_brightness') and hasattr(primary_visualCortex, '_options'):
                            saved_brightness = getattr(mind, 'preferred_matrix_brightness')
                            print(f"[Visual Cortex] Applying saved brightness: {saved_brightness}%")
                            primary_visualCortex._options.brightness = saved_brightness
                        
                        # Launch the game through the game manager
                        print(f"[Game Cortex] Launching {selected_game} through brain architecture.")
                        game_instance = game_manager.launch_game(
                            selected_game, 
                            primary_visualCortex,  # Pass visual cortex instead of raw matrix
                            layout_manager
                        )
                        
                        if game_instance:
                            print(f"[Game Cortex] {selected_game} initiated successfully.")
                            print(f"Game is now running. Press CTRL+C to exit the game.")
                            
                            # Game loop, keeping CPU usage reasonable
                            try:
                                last_time = time.time()
                                while game_instance and game_manager.get_active_game():
                                    # Calculate delta time for smooth animations
                                    current_time = time.time()
                                    dt = current_time - last_time
                                    last_time = current_time
                                    
                                    # Update game logic
                                    game_instance.update(dt)
                                    
                                    # After updating, call draw
                                    game_instance.draw()
                                    
                                    # Update the display through layout manager
                                    layout_manager.update_display(rotate_degrees=270)
                                    
                                    # Sleep to keep CPU usage reasonable
                                    await asyncio.sleep(0.033)  # ~30 FPS
                            except KeyboardInterrupt:
                                print("\n[User Input] Game interrupted by user.")
                            finally:
                                print("[Game Cortex] Stopping active game...")
                                game_manager.stop_active_game()
                                # Clear the matrix through the visual cortex
                                if primary_visualCortex:
                                    try:
                                        await primary_visualCortex.clear()
                                        print("[Visual Cortex] Display cleared.")
                                    except:
                                        print("[Visual Cortex] Failed to clear display.")
                        else:
                            print(f"[Game Cortex] Failed to launch {selected_game}.")
                    else:
                        print("[Error] Could not access or initialize visual processing modules.")
                        print("Games require hardware support to function.")
                except Exception as e:
                    journaling_manager.recordError(f"Error preparing game environment: {e}")
                    import traceback
                    journaling_manager.recordError(f"Stack trace: {traceback.format_exc()}")
                    print(f"\n[Error] Failed to prepare game environment: {e}")
                
                input("\nPress Enter to return to Games Menu...")
            elif option_num == len(available_games) + 1:
                # Game Settings submenu
                await game_settings_menu()
            else:
                print("\nInvalid option. Please try again.")
                await asyncio.sleep(1)
        except ValueError:
            print("\nInvalid input. Please enter a number.")
            await asyncio.sleep(1)

async def game_settings_menu():
    """Display and manage game settings"""
    # Get current brightness from PrimaryVisualArea if available
    # This follows the brain region architecture of PenphinMind
    brightness_perceptualValue = 30  # Default fallback value
    
    try:
        # Access through Mind's neurological pathways
        from Mind.OccipitalLobe.VisualCortex.primary_area import PrimaryVisualArea
        
        # Check if there's an existing instance through Mind
        primary_visualCortex = None
        
        # Try to access through Mind's existing channels
        if hasattr(mind, 'visual_cortex') and hasattr(mind.visual_cortex, 'primary_area'):
            primary_visualCortex = mind.visual_cortex.primary_area
            if hasattr(primary_visualCortex, '_options') and hasattr(primary_visualCortex._options, 'brightness'):
                brightness_perceptualValue = primary_visualCortex._options.brightness
                print(f"[Visual Cortex] Retrieved current brightness: {brightness_perceptualValue}%")
        else:
            print("[Visual Cortex] No existing primary visual cortex found in Mind.")
    except ImportError:
        journaling_manager.recordWarning("Could not import PrimaryVisualArea class")
        print("[Visual Cortex] Could not access visual processing modules.")
    except Exception as e:
        journaling_manager.recordError(f"Error accessing visual cortex: {e}")
        print(f"[Visual Cortex] Error: {e}")
    
    while True:
        print_header()
        print("\n=== Visual Cortex Settings ===")
        
        print(f"\nCurrent Visual Parameters:")
        print(f"1) Matrix Brightness Perception: {brightness_perceptualValue}%")
        print("\n0) Back to Games Menu")
        
        option = input("\nSelect parameter to adjust (0-1): ").strip()
        
        if option == "0":
            return
        elif option == "1":
            # Brightness adjustment through proper brain regions
            print(f"\nCurrent brightness perception: {brightness_perceptualValue}%")
            print("Enter new brightness level (1-100):")
            
            try:
                new_perceptualValue = int(input().strip())
                if 1 <= new_perceptualValue <= 100:
                    brightness_perceptualValue = new_perceptualValue
                    
                    # Properly update through brain architecture
                    success = False
                    
                    try:
                        # First way: update through primary_visualCortex if available
                        if primary_visualCortex:
                            print("[Visual Cortex] Updating matrix brightness through primary visual cortex...")
                            primary_visualCortex._options.brightness = brightness_perceptualValue
                            
                            # If matrix is initialized, we need to reinitialize with new options
                            if hasattr(primary_visualCortex, '_matrix') and primary_visualCortex._matrix:
                                # In a complete implementation, we would need to:
                                # 1. Properly clean up the existing matrix
                                # 2. Reinitialize with the new options
                                # However, this might require deeper integration
                                print("[Visual Cortex] Note: Matrix needs reinitialization to apply brightness change")
                                print("[Visual Cortex] Changes will apply on next system restart")
                            
                            success = True
                            
                        # Second way: directly update options in tests/vision/777Test.py approach
                        # This would require accessing the matrix options from that module
                        if not success:
                            print("[Visual Cortex] Updating through global matrix settings...")
                            
                            # Access global options if available
                            import sys
                            if 'rgbmatrix' in sys.modules:
                                rgb_module = sys.modules['rgbmatrix']
                                if hasattr(rgb_module, 'RGBMatrixOptions'):
                                    # Save to a config file that other modules can read
                                    config_file = "matrix_settings.conf"
                                    with open(config_file, "w") as f:
                                        f.write(f"brightness={brightness_perceptualValue}\n")
                                    
                                    print(f"[Visual Cortex] Brightness preference saved to {config_file}")
                                    print("[Visual Cortex] Changes will apply on next system restart")
                                    success = True
                    except Exception as e:
                        journaling_manager.recordError(f"Error updating brightness: {e}")
                        print(f"[Visual Cortex] Error setting brightness: {e}")
                    
                    if success:
                        print(f"\nVisual brightness perception set to {brightness_perceptualValue}%")
                        print("(Note: Some changes may require restart to take effect)")
                    else:
                        print("\nCould not directly update hardware. Saving preference only.")
                        print("Brightness will be set on next system initialization.")
                        
                        # Store in a variable that can be checked when initializing games
                        # This is a temporary storage, in a real system this would be persisted
                        if not hasattr(mind, 'preferred_matrix_brightness'):
                            setattr(mind, 'preferred_matrix_brightness', brightness_perceptualValue)
                else:
                    print("\nInvalid brightness value. Must be between 1 and 100.")
            except ValueError:
                print("\nInvalid input. Please enter a number.")
            
            input("\nPress Enter to continue...")
        else:
            print("\nInvalid option. Please try again.")
            await asyncio.sleep(1)

async def run_menu_system(mind_instance=None):
    """Run the interactive menu system"""
    try:
        # Use global mind instance if not provided
        mind_instance = mind_instance or mind
        
        # Display the main menu and handle user choices
        while True:
            # Remove clear_screen() call here to preserve logs
            
            # Get main menu choice
            choice = await display_main_menu()
            
            if choice == "1":  # Chat
                await start_chat(mind_instance)
            elif choice == "2":  # Information
                await display_model_list()
            elif choice == "3":  # System
                await system_menu()
            elif choice == "4":  # Games
                await games_menu()
            elif choice == "5":  # Exit
                print("\nExiting PenphinMind menu system...")
                break
            else:
                print("\nInvalid choice. Please try again.")
                await asyncio.sleep(1)
    except Exception as e:
        journaling_manager.recordError(f"Error running menu system: {e}")
        import traceback
        journaling_manager.recordError(f"Stack trace: {traceback.format_exc()}")
        print(f"\nError running menu system: {e}")
        input("\nPress Enter to return to main menu...") 