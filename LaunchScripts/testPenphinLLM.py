#!/usr/bin/env python3
import asyncio
import logging
import platform
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import sounddevice as sd
import numpy as np
import time
import sys
from mind import Mind
from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import CommandType
from config import CONFIG

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import (
    CommandType,
    LLMCommand,
    TTSCommand,
    BaseCommand,
    ASRCommand
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Default to INFO if config not available
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PenphinOS")

class AIType(Enum):
    """Available AI types"""
    LOCAL = "local"
    CLOUD = "cloud"
    CUSTOM = "custom"

class CortexCategory(Enum):
    """Neural cortex categories matching brain structure"""
    TEMPORAL = "TemporalLobe"
    PARIETAL = "ParietalLobe"
    OCCIPITAL = "OccipitalLobe"
    FRONTAL = "FrontalLobe"
    LIMBIC = "LimbicSystem"
    CEREBELLUM = "Cerebellum"
    THALAMUS = "Thalamus"
    BASAL_GANGLIA = "BasalGanglia"

class TestMode(Enum):
    """Available test modes"""
    TEXT = "text"
    AUDIO = "audio"
    INTEGRATED = "integrated"
    BICAMERAL = "bicameral"

class AgentType(Enum):
    """Types of bicameral agents"""
    LOGICAL = "logical"
    CREATIVE = "creative"
    INTEGRATOR = "integrator"

class BicameralAgent:
    """Represents a bicameral agent with specific personality"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.personality = self._get_personality()
        self.conversation_history: List[Dict[str, str]] = []
        
    def _get_personality(self) -> str:
        """Get personality prompt based on agent type"""
        if self.agent_type == AgentType.LOGICAL:
            return """You are the logical agent of the bicameral mind. Your role is to:
1. Analyze information rationally and systematically
2. Focus on facts, evidence, and logical connections
3. Identify patterns and relationships
4. Question assumptions and verify conclusions
5. Maintain objectivity in your analysis

Respond in a clear, structured, and analytical manner."""
        elif self.agent_type == AgentType.CREATIVE:
            return """You are the creative agent of the bicameral mind. Your role is to:
1. Generate novel ideas and perspectives
2. Make unexpected connections
3. Consider possibilities beyond conventional thinking
4. Express ideas with imagination and flair
5. Embrace ambiguity and multiple interpretations

Respond in an imaginative, exploratory, and innovative manner."""
        else:  # INTEGRATOR
            return """You are the integrator agent of the bicameral mind. Your role is to:
1. Synthesize insights from both logical and creative perspectives
2. Identify patterns of agreement and disagreement
3. Explore potential synergies between different viewpoints
4. Generate new insights from the integration
5. Maintain balance between analysis and creativity

Respond in a balanced, integrative, and insightful manner."""
            
    async def process_input(self, input_text: str) -> str:
        """Process input through the agent's perspective"""
        try:
            command = LLMCommand(
                command_type=CommandType.LLM,
                prompt=f"{self.personality}\n\nInput: {input_text}\n\nProvide your perspective:",
                max_tokens=300,
                temperature=0.7 if self.agent_type == AgentType.CREATIVE else 0.3
            )
            response = await SynapticPathways.transmit_json(command)
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": input_text
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response.get("response", "")
            })
            
            return response.get("response", "")
            
        except Exception as e:
            logger.error(f"Error processing input for {self.agent_type.value} agent: {e}")
            return f"Error: {str(e)}"

class TestPenphinLLM:
    """Test class for Mind functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mind: Optional[Mind] = None
        self.is_raspberry_pi = platform.system() == "Linux" and "raspberrypi" in platform.platform().lower()
        self.ai_type: Optional[AIType] = None
        self.custom_endpoint: Optional[str] = None
        self.model: str = "gpt-3.5-turbo"
        self.test_mode: TestMode = TestMode.TEXT
        self.available_functions: Dict[str, List[str]] = {}
        self.chat_history: List[Dict[str, str]] = []
        self.audio_automation: Optional[AudioAutomation] = None
        self.detected_port: Optional[str] = None
        self.bicameral_agents: Dict[AgentType, BicameralAgent] = {}
        self._load_available_functions()
        
    def _load_available_functions(self) -> None:
        """Load available functions from neural_commands"""
        # Get all command types
        command_types = [cmd.value for cmd in CommandType]
        
        # Initialize function dictionary by brain region
        self.available_functions = {
            cortex.value: [] for cortex in CortexCategory
        }
        
        # Map commands to their respective brain regions
        for cmd in command_types:
            if cmd.startswith(("AUDIO", "TTS", "ASR", "SPEECH")):
                self.available_functions[CortexCategory.TEMPORAL.value].append(cmd)
            elif cmd.startswith(("TOUCH", "PRESSURE")):
                self.available_functions[CortexCategory.PARIETAL.value].append(cmd)
            elif cmd.startswith(("VISUAL", "IMAGE")):
                self.available_functions[CortexCategory.OCCIPITAL.value].append(cmd)
            # ... add other mappings as needed
            
    async def detect_llm_port(self) -> Optional[str]:
        """Detect AX630 neural processor"""
        try:
            # Initialize neural processor
            if await SynapticPathways.initialize():
                return "AX630"  # Return identifier for successful initialization
            return None
        except Exception as e:
            print(f"\n❌ Error during neural processor detection: {e}")
            if platform.system() == "Darwin":
                print("\nOn macOS, please ensure:")
                print("1. Silicon Labs USB-Serial driver is installed:")
                print("   brew install --cask silicon-labs-vcp-driver")
                print("2. Device has correct permissions:")
                print("   sudo chmod 666 /dev/tty.usbserial*")
            print("\nPlease check your device connections and try again")
            return None
            
    async def initialize(self) -> bool:
        """Initialize test environment"""
        try:
            self.mind = Mind()
            await self.mind.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            return False
            
    async def get_device_functions(self) -> Dict[str, List[str]]:
        """Get available functions from the device"""
        try:
            response = await SynapticPathways.send_system_command("get_functions")
            return response.get("functions", {})
        except Exception as e:
            self.logger.error(f"Error getting device functions: {e}")
            return {}
            
    def display_function_status(self, device_functions: Dict[str, List[str]]) -> None:
        """Display available and pending functions"""
        print("\nFunction Status by Cortex:")
        print("=" * 50)
        
        for cortex, functions in self.available_functions.items(): 
            print(f"\n{cortex}:")
            print("-" * 30)
            
            # Get device functions for this cortex
            device_cortex_functions = device_functions.get(cortex, [])
            
            # Show implemented functions
            print("Implemented:")
            for func in functions:
                if func in device_cortex_functions:
                    print(f"  ✓ {func}")
                else:
                    print(f"  ✗ {func} (Not available on device)")
                    
            # Show device-only functions
            device_only = [f for f in device_cortex_functions if f not in functions]
            if device_only:
                print("\nDevice-only functions:")
                for func in device_only:
                    print(f"  ! {func} (Not integrated in code)")
                    
    async def select_ai_type(self) -> None:
        """Configure neural processor"""
        print("\n=== Neural Processor Configuration ===")
        print("Initializing AX630 Neural Processor...")
        
        # Always use LOCAL type with AX630
        self.ai_type = AIType.LOCAL
        
        # Detect neural processor
        if await self.detect_llm_port():
            print("\n✓ Neural processor ready for operation")
            print("\nProcessor Details:")
            print("- Model: AX630")
            print("- Mode: Neural Processing Unit")
            print("- Status: Connected and Initialized")
        else:
            print("\n❌ Neural processor initialization failed")
            print("Please check hardware connections and try again")
            raise RuntimeError("Neural processor not found")
                
    async def show_model_options(self) -> None:
        """Show and select neural model options"""
        print("\n=== Neural Model Configuration ===")
        print("Querying available models from neural processor...")
        
        try:
            # Get available models from neural processor
            response = await SynapticPathways.send_system_command("list_models")
            models = response.get("models", [])
            
            if not models:
                print("\n❌ No models found on neural processor")
                raise RuntimeError("No models available")
                
            print("\nAvailable Neural Models:")
            for i, model in enumerate(models, 1):
                print(f"{i}. {model}")
                
            while True:
                try:
                    model_choice = int(input("\nSelect model number: "))
                    if 1 <= model_choice <= len(models):
                        self.model = models[model_choice - 1]
                        print(f"\n✓ Neural model loaded: {self.model}")
                        break
                    print("❌ Invalid choice. Please try again.")
                except ValueError:
                    print("❌ Please enter a valid number.")
                    
        except Exception as e:
            print(f"\n❌ Error configuring neural model: {e}")
            raise
                
    async def show_help(self) -> None:
        """Show help information"""
        print("\nPenphinOS Test Interface Help:")
        print("=" * 50)
        print("\nAvailable Commands:")
        print("1. test - Run basic test sequence")
        print("2. model - Change AI model")
        print("3. functions - Show available functions")
        print("4. chat - Enter chat mode with command support")
        print("5. help - Show this help message")
        print("6. exit - Exit the program")
        print("\nChat Mode Commands:")
        print("- Use [command] syntax for instructions")
        print("- Type 'exit' to return to menu")
        print("- Example: [process audio] [convert to text] [generate response]")
        
    async def select_test_mode(self) -> None:
        """Select test mode"""
        print("\nSelect Test Mode:")
        print("1. Text Mode (LLM only)")
        print("2. Audio Mode (Speech-to-Text and Text-to-Speech)")
        print("3. Integrated Mode (Full audio pipeline)")
        print("4. Bicameral Mode (Logical and Creative agents)")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (1-4): "))
                if choice == 1:
                    self.test_mode = TestMode.TEXT
                    break
                elif choice == 2:
                    self.test_mode = TestMode.AUDIO
                    break
                elif choice == 3:
                    self.test_mode = TestMode.INTEGRATED
                    break
                elif choice == 4:
                    self.test_mode = TestMode.BICAMERAL
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
                
    async def test_text_mode(self, prompt: str) -> Dict[str, Any]:
        """Test text-based interaction with the LLM"""
        try:
            self.logger.info("\nStarting text mode conversation...")
            self.logger.info("Type 'exit' to end the conversation")
            self.logger.info("Type 'help' for available commands")
            
            # Initialize conversation history
            conversation_history = []
            
            while True:
                # Get user input
                user_input = input("\nYou: ").strip()
                
                # Check for exit command
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    self.logger.info("Ending conversation...")
                    break
                    
                # Check for help command
                if user_input.lower() == 'help':
                    self.logger.info("\nAvailable commands:")
                    self.logger.info("- exit/quit/bye: End the conversation")
                    self.logger.info("- help: Show this help message")
                    self.logger.info("- clear: Clear conversation history")
                    self.logger.info("- mode: Switch to a different test mode")
                    continue
                    
                # Check for clear command
                if user_input.lower() == 'clear':
                    conversation_history = []
                    self.logger.info("Conversation history cleared")
                    continue
                    
                # Check for mode switch
                if user_input.lower() == 'mode':
                    await self.select_test_mode()
                    break
                
                # Add user input to history
                conversation_history.append({"role": "user", "content": user_input})
                
                # Prepare the prompt with conversation history
                full_prompt = f"{CONFIG.llm_system_prompt}\n\n"
                for msg in conversation_history[-5:]:  # Keep last 5 messages for context
                    full_prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
                
                # Create LLM command
                command = LLMCommand(
                    command_type=CommandType.LLM,
                    prompt=full_prompt,
                    max_tokens=CONFIG.llm_max_tokens,
                    temperature=CONFIG.llm_temperature,
                    model=CONFIG.llm_model
                )
                
                # Show the JSON being sent
                self.logger.info("\nSending to LLM:")
                self.logger.info(json.dumps(command.to_dict(), indent=2))
                
                # Send to LLM
                response = await SynapticPathways.transmit_json(command)
                
                # Show the JSON response
                self.logger.info("\nReceived from LLM:")
                self.logger.info(json.dumps(response, indent=2))
                
                if response.get("status") == "ok":
                    ai_response = response.get("response", "")
                    self.logger.info(f"\nAI: {ai_response}")
                    conversation_history.append({"role": "assistant", "content": ai_response})
                else:
                    self.logger.error(f"Error: {response.get('message', 'Unknown error')}")
                    
            return {"status": "ok", "message": "Text mode test completed"}
            
        except Exception as e:
            self.logger.error(f"Error in text mode: {e}")
            return {"status": "error", "message": str(e)}
            
    async def test_audio_mode(self, duration: float = 5.0) -> Dict[str, Any]:
        """Test audio recording and processing"""
        if not self.audio_automation:
            raise ValueError("Audio automation not initialized")
            
        try:
            # Verify port is still available
            current_port = await self.detect_llm_port()
            if current_port != self.detected_port:
                self.logger.warning(f"Port changed from {self.detected_port} to {current_port}")
                self.detected_port = current_port
                # Reinitialize audio automation with new port
                audio_config = AudioConfig(
                    sample_rate=16000,
                    channels=1,
                    device=self.detected_port
                )
                self.audio_automation = AudioAutomation(audio_config)
            
            # Start recording
            print(f"\nRecording for {duration} seconds...")
            print(f"Using device: {self.detected_port}")
            await self.audio_automation.start_detection()
            await asyncio.sleep(duration)
            self.audio_automation.stop_detection()
            
            # Process recorded audio
            if self.audio_automation.audio_buffer:
                audio_data = np.concatenate(self.audio_automation.audio_buffer)
                command = ASRCommand(
                    command_type=CommandType.ASR,
                    input_audio=audio_data.tolist(),
                    language="en",
                    model_type="whisper"
                )
                response = await SynapticPathways.transmit_json(command)
                self.logger.info(f"ASR Response: {response}")
                return response
                
        except Exception as e:
            self.logger.error(f"Audio mode test error: {e}")
            raise
            
    async def test_integrated_mode(self) -> None:
        """Test full audio pipeline"""
        try:
            print("\nStarting integrated test...")
            print("1. Speak into the microphone")
            print("2. System will process your speech")
            print("3. Wait for the response")
            print("Press Ctrl+C to stop")
            
            # Use Mind's methods instead of direct audio automation
            await self.mind.start_listening()
            
            while True:
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping integrated test...")
            await self.mind.stop_listening()
        except Exception as e:
            self.logger.error(f"Integrated mode test error: {e}")
            raise
            
    async def initialize_bicameral_agents(self) -> None:
        """Initialize bicameral agents"""
        self.bicameral_agents = {
            AgentType.LOGICAL: BicameralAgent(AgentType.LOGICAL),
            AgentType.CREATIVE: BicameralAgent(AgentType.CREATIVE),
            AgentType.INTEGRATOR: BicameralAgent(AgentType.INTEGRATOR)
        }
        
    async def test_bicameral_mode(self, input_text: str) -> None:
        """Test bicameral conversation processing"""
        try:
            print("\nBicameral Conversation Test")
            print("=" * 50)
            print(f"Input: {input_text}")
            print("\nProcessing through agents...")
            
            # Process through logical agent
            print("\nLogical Agent Analysis:")
            logical_response = await self.bicameral_agents[AgentType.LOGICAL].process_input(input_text)
            print(logical_response)
            
            # Process through creative agent
            print("\nCreative Agent Analysis:")
            creative_response = await self.bicameral_agents[AgentType.CREATIVE].process_input(input_text)
            print(creative_response)
            
            # Integrate perspectives
            print("\nIntegrating Perspectives:")
            integration_prompt = f"""Logical Analysis:
{logical_response}

Creative Analysis:
{creative_response}

Please integrate these perspectives and provide:
1. Common themes and agreements
2. Key differences and tensions
3. Potential synergies
4. New insights that emerge
5. What might have been missed
"""
            integrated_response = await self.bicameral_agents[AgentType.INTEGRATOR].process_input(integration_prompt)
            print(integrated_response)
            
        except Exception as e:
            self.logger.error(f"Bicameral test error: {e}")
            raise
            
    async def run_tests(self):
        """Run all tests based on selected mode"""
        try:
            if self.test_mode == TestMode.TEXT:
                # Test LLM with various prompts
                prompts = [
                    "What is the meaning of life?",
                    "Explain quantum computing in simple terms",
                    "Write a haiku about artificial intelligence"
                ]
                
                for prompt in prompts:
                    print(f"\nTesting prompt: {prompt}")
                    await self.test_text_mode(prompt)
                    
            elif self.test_mode == TestMode.AUDIO:
                # Test audio recording and processing
                await self.test_audio_mode()
                
            elif self.test_mode == TestMode.INTEGRATED:
                # Test full audio pipeline
                await self.test_integrated_mode()
                
            elif self.test_mode == TestMode.BICAMERAL:
                # Initialize bicameral agents
                await self.initialize_bicameral_agents()
                
                # Test prompts for bicameral processing
                prompts = [
                    "What is consciousness?",
                    "How can we solve climate change?",
                    "What makes art beautiful?"
                ]
                
                for prompt in prompts:
                    await self.test_bicameral_mode(prompt)
                    
        except Exception as e:
            self.logger.error(f"Test error: {e}")
            raise
            
    async def cleanup(self):
        """Clean up resources"""
        if self.audio_automation:
            self.audio_automation.stop_detection()
        await SynapticPathways.close_connections()

    def _parse_command_instructions(self, text: str) -> List[str]:
        """Extract command instructions from square brackets"""
        pattern = r'\[(.*?)\]'
        return re.findall(pattern, text)

    async def _process_command_instructions(self, instructions: List[str]) -> str:
        """Process command instructions and return action plan"""
        try:
            # Create a prompt that includes available functions and instructions
            prompt = f"""You are PenphinOS, an AI assistant with access to various neural functions.
Available functions by cortex:
{json.dumps(self.available_functions, indent=2)}

The following command instructions were received:
{json.dumps(instructions, indent=2)}

Please analyze these instructions and provide a detailed action plan that:
1. Identifies which functions should be used
2. Specifies the order of operations
3. Notes any potential issues or requirements
4. Suggests any additional functions that might be needed

Format your response in a clear, structured way."""

            command = LLMCommand(
                command_type=CommandType.LLM,
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )
            response = await SynapticPathways.transmit_json(command)
            return response.get("response", "Failed to generate action plan")
        except Exception as e:
            self.logger.error(f"Error processing command instructions: {e}")
            return f"Error processing command instructions: {str(e)}"

    async def chat(self) -> None:
        """Enter chat mode with command instruction support"""
        print("\nEntering Chat Mode")
        print("Commands:")
        print("- [command] - Use square brackets for instructions")
        print("- ? or help - Show help information")
        print("- menu or exit - Return to main menu")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['menu', 'exit']:
                    break
                elif user_input.lower() in ['?', 'help']:
                    print("\nChat Mode Help:")
                    print("=" * 50)
                    print("Regular Chat:")
                    print("- Just type your message for a conversation")
                    print("\nCommand Instructions:")
                    print("- Use [command] syntax for instructions")
                    print("- Example: [process audio] [convert to text]")
                    print("\nSpecial Commands:")
                    print("- ? or help - Show this help message")
                    print("- menu or exit - Return to main menu")
                    print("\nAvailable Functions:")
                    for cortex, functions in self.available_functions.items():
                        if functions:
                            print(f"\n{cortex}:")
                            for func in functions:
                                print(f"  - {func}")
                    continue
                    
                # Check for command instructions
                instructions = self._parse_command_instructions(user_input)
                
                if instructions:
                    print("\nProcessing command instructions...")
                    action_plan = await self._process_command_instructions(instructions)
                    print("\nAction Plan:")
                    print(action_plan)
                    
                    # Add to chat history
                    self.chat_history.append({
                        "role": "user",
                        "content": user_input
                    })
                    self.chat_history.append({
                        "role": "assistant",
                        "content": action_plan
                    })
                else:
                    # Regular chat interaction
                    command = LLMCommand(
                        command_type=CommandType.LLM,
                        prompt=user_input,
                        max_tokens=150,
                        temperature=0.7
                    )
                    response = await SynapticPathways.transmit_json(command)
                    assistant_response = response.get("response", "")
                    
                    print(f"\nAssistant: {assistant_response}")
                    
                    # Add to chat history
                    self.chat_history.append({
                        "role": "user",
                        "content": user_input
                    })
                    self.chat_history.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                    
            except Exception as e:
                self.logger.error(f"Chat error: {e}")
                print(f"\nError: {str(e)}")
                
    async def run_menu(self):
        """Run the main menu system"""
        try:
            # Select AI type
            await self.select_ai_type()
            
            # Select test mode
            await self.select_test_mode()
            
            while True:
                print("\nPenphinOS Test Interface")
                print("=" * 50)
                print(f"AI Type: {self.ai_type.value}")
                print(f"Model: {self.model}")
                print(f"Test Mode: {self.test_mode.value}")
                print("\nOptions:")
                print("1. Run Tests")
                print("2. Change Model")
                print("3. Show Functions")
                print("4. Chat Mode")
                print("5. Help")
                print("6. Exit")
                
                try:
                    choice = int(input("\nEnter your choice: "))
                    
                    if choice == 1:
                        await self.run_tests()
                    elif choice == 2:
                        await self.show_model_options()
                    elif choice == 3:
                        if self.ai_type == AIType.LOCAL:
                            device_functions = await self.get_device_functions()
                            self.display_function_status(device_functions)
                        else:
                            print("\nFunction status only available for Local AI")
                    elif choice == 4:
                        await self.chat()
                    elif choice == 5:
                        await self.show_help()
                    elif choice == 6:
                        break
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")
                    
        except Exception as e:
            self.logger.error(f"Menu error: {e}")
            raise
        finally:
            await self.cleanup()

    async def test_auditory_processing(self, audio_data: bytes) -> bool:
        """Test complete auditory processing pathway"""
        try:
            # Use Mind interface instead of accessing internal components
            result = await self.mind.process_audio(audio_data)
            self.logger.info(f"Auditory processing result: {result}")
            
            # Use Mind's speech understanding method
            text = await self.mind.understand_speech(audio_data)
            self.logger.info(f"Language comprehension result: {text}")
            
            # Use Mind's speech generation method
            if text:
                response = await self.mind.generate_speech(f"Understood: {text}")
                self.logger.info("Speech generation successful")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            return False

async def main():
    """Main entry point for PenphinOS testing"""
    try:
        # Create and run test interface
        test_interface = TestPenphinLLM()
        await test_interface.initialize()
        await test_interface.run_menu()
        
    except Exception as e:
        logger.error(f"Runtime error: {e}")
    finally:
        if 'test_interface' in locals():
            await test_interface.cleanup()
        await SynapticPathways.close_connections()
            
if __name__ == "__main__":
    asyncio.run(main()) 