#!/usr/bin/env python3
# test_llm_visualization.py - Test script for LLM visualization

import asyncio
import argparse
import sys
import os
from typing import Dict, Any

# Add the project root to the Python path if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways

# ANSI escape codes for colored output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

async def setup_connection(connection_type: str) -> bool:
    """Initialize the connection to the LLM system"""
    print(f"{Colors.BLUE}[*] Initializing {connection_type} connection...{Colors.ENDC}")
    success = await SynapticPathways.initialize(connection_type)
    
    if not success:
        print(f"{Colors.RED}[!] Failed to initialize connection{Colors.ENDC}")
        return False
    
    # Get hardware info
    hw_info = await SynapticPathways.get_hardware_info()
    print(f"{Colors.GREEN}[+] Connection established{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Device status: CPU: {hw_info.get('cpu_load', 'N/A')}, "
          f"Memory: {hw_info.get('memory_usage', 'N/A')}, "
          f"Temp: {hw_info.get('temperature', 'N/A')}{Colors.ENDC}")
    
    # Get available models
    models = await SynapticPathways.get_available_models()
    if models:
        print(f"{Colors.GREEN}[+] Available models: {len(models)}{Colors.ENDC}")
        for model in models[:3]:  # Show only a few models
            print(f"    - {model.get('mode', 'Unknown')}: {model.get('type', 'Unknown')}")
        if len(models) > 3:
            print(f"    - ... and {len(models) - 3} more")
    
    return True

async def think_with_visualization(prompt: str, art_style: str, grid_size: tuple) -> Dict[str, Any]:
    """Send a prompt to the LLM with visualization"""
    width, height = grid_size
    print(f"{Colors.BLUE}[*] Thinking with {art_style} visualization ({width}x{height})...{Colors.ENDC}")
    
    # Different entry points depending on art style
    if art_style in ["wave", "matrix", "binary", "emphasis", "gradient"]:
        return await SynapticPathways.think_with_artistic_grid(
            prompt, 
            art_style=art_style,
            color_mode="color",
            width=width,
            height=height
        )
    else:
        return await SynapticPathways.think_with_pixel_grid(
            prompt,
            width=width,
            height=height,
            color_mode="color" if art_style != "grayscale" else "grayscale"
        )

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="LLM Visualization Test")
    parser.add_argument("--connection", "-c", default="tcp", choices=["tcp", "adb", "serial"],
                       help="Connection type to use (default: tcp)")
    parser.add_argument("--art-style", "-a", default="basic",
                       choices=["basic", "grayscale", "wave", "matrix", "binary", "emphasis", "gradient"],
                       help="Art style for visualization (default: basic)")
    parser.add_argument("--width", "-W", type=int, default=64,
                       help="Width of the pixel grid (default: 64)")
    parser.add_argument("--height", "-H", type=int, default=32,
                       help="Height of the pixel grid (default: 32)")
    args = parser.parse_args()
    
    # Setup connection
    if not await setup_connection(args.connection):
        print(f"{Colors.RED}[!] Exiting due to connection failure{Colors.ENDC}")
        return
    
    # Show welcome message
    print(f"\n{Colors.HEADER}{Colors.BOLD}===== LLM Visualization Test =====")
    print(f"Type your prompt and see the LLM output visualized")
    print(f"Use '/style <style>' to change visualization style")
    print(f"Use '/size <width> <height>' to change grid size")
    print(f"Use '/exit' or Ctrl+C to quit{Colors.ENDC}\n")
    
    # Initialize settings
    art_style = args.art_style
    grid_size = (args.width, args.height)
    
    # Main interaction loop
    try:
        while True:
            # Get user prompt
            try:
                user_input = input(f"{Colors.BOLD}> {Colors.ENDC}")
            except EOFError:
                break
                
            # Handle commands
            if user_input.startswith('/'):
                parts = user_input.strip().split()
                command = parts[0].lower()
                
                if command == '/exit':
                    break
                    
                elif command == '/style' and len(parts) > 1:
                    style = parts[1].lower()
                    valid_styles = ["basic", "grayscale", "wave", "matrix", "binary", "emphasis", "gradient"]
                    if style in valid_styles:
                        art_style = style
                        print(f"{Colors.GREEN}[+] Visualization style set to: {art_style}{Colors.ENDC}")
                    else:
                        print(f"{Colors.YELLOW}[!] Invalid style. Valid options: {', '.join(valid_styles)}{Colors.ENDC}")
                        
                elif command == '/size' and len(parts) > 2:
                    try:
                        width = int(parts[1])
                        height = int(parts[2])
                        if width > 0 and height > 0:
                            grid_size = (width, height)
                            print(f"{Colors.GREEN}[+] Grid size set to: {width}x{height}{Colors.ENDC}")
                        else:
                            print(f"{Colors.YELLOW}[!] Width and height must be positive{Colors.ENDC}")
                    except ValueError:
                        print(f"{Colors.YELLOW}[!] Width and height must be numbers{Colors.ENDC}")
                
                elif command == '/help':
                    print(f"{Colors.BLUE}Available commands:{Colors.ENDC}")
                    print(f"  /style <style> - Change visualization style")
                    print(f"  /size <width> <height> - Change grid size")
                    print(f"  /exit - Exit the program")
                    print(f"  /help - Show this help message")
                    
                else:
                    print(f"{Colors.YELLOW}[!] Unknown command. Type /help for available commands{Colors.ENDC}")
                    
                continue
                
            # Skip empty prompts
            if not user_input.strip():
                continue
                
            # Send the prompt to the LLM with visualization
            try:
                result = await think_with_visualization(user_input, art_style, grid_size)
                
                # Print completion message 
                print(f"\n{Colors.GREEN}[+] Thinking complete!{Colors.ENDC}")
                
                # Ask if user wants to see text result
                show_text = input(f"{Colors.BOLD}Show text result? (y/n): {Colors.ENDC}").lower().startswith('y')
                if show_text:
                    print(f"\n{Colors.BLUE}--- Result ---{Colors.ENDC}")
                    if isinstance(result, dict) and "error" in result:
                        print(f"{Colors.RED}Error: {result['error']}{Colors.ENDC}")
                    else:
                        print(result)
                    print(f"{Colors.BLUE}-------------{Colors.ENDC}\n")
                    
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[!] Thinking interrupted{Colors.ENDC}")
                continue
            except Exception as e:
                print(f"\n{Colors.RED}[!] Error: {str(e)}{Colors.ENDC}")
                
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Program interrupted{Colors.ENDC}")
    
    # Clean up
    print(f"\n{Colors.BLUE}[*] Cleaning up...{Colors.ENDC}")
    await SynapticPathways.cleanup()
    print(f"{Colors.GREEN}[+] Done. Goodbye!{Colors.ENDC}")

if __name__ == "__main__":
    asyncio.run(main()) 