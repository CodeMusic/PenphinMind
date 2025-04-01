#!/usr/bin/env python3
import asyncio
import argparse
from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways

async def main():
    parser = argparse.ArgumentParser(description="Test UI Modes")
    parser.add_argument("--mode", "-m", choices=["full", "fc", "headless"], 
                       default="fc", help="UI mode")
    parser.add_argument("--prompt", "-p", default="What is the capital of France?",
                      help="Test prompt")
    args = parser.parse_args()
    
    # Set UI mode
    print(f"Setting UI mode to: {args.mode}")
    SynapticPathways.set_ui_mode(args.mode)
    
    # Initialize connection
    print("Initializing connection...")
    await SynapticPathways.initialize("tcp")
    
    # Perform thinking with visualization
    print(f"\nThinking with prompt: '{args.prompt}'")
    print(f"This should use {'pixel grid' if args.mode == 'full' else 'text stream' if args.mode == 'fc' else 'basic'} visualization.")
    
    result = await SynapticPathways.think_with_visualization(args.prompt)
    
    # Print result
    print("\nResult:")
    print(result)
    
    # Cleanup
    print("\nCleaning up...")
    await SynapticPathways.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
