"""
Neurological Function:
    Language Model System:
    - Natural language processing
    - Text generation
    - Context understanding
    - Semantic analysis
    - Response generation
    - Language comprehension
    - Cognitive processing

Project Function:
    Handles language processing:
    - Text input processing
    - Response generation
    - Context management
    - Model interaction
"""

import logging
from typing import Dict, Any, Optional
from config import CONFIG  # Use absolute import
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.Subcortex.api_commands import create_command, parse_response
import time
import traceback
from Mind.Subcortex.neurocortical_bridge import NeurocorticalBridge
from Mind.Subcortex.api_commands import (
    CommandType,
    LLMCommand,
    AudioCommand,
    parse_response
)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

def get_synaptic_pathways():
    """Get the SynapticPathways class, avoiding circular imports"""
    from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
    return SynapticPathways

class LLM:
    """Handles language model interactions"""
    
    def __init__(self):
        """Initialize the language model"""
        journaling_manager.recordScope("LLM.__init__")
        self._initialized = False
        self._processing = False
        self._config = CONFIG  # Use the imported CONFIG
        self.current_state = {
            "model": None,
            "status": "idle",
            "error": None
        }
        
    async def initialize(self) -> None:
        """Initialize the language model"""
        journaling_manager.recordScope("LLM.initialize")
        if self._initialized:
            journaling_manager.recordDebug("LLM already initialized")
            return
            
        try:
            # Initialize model with configuration
            self.current_state["model"] = {
                "name": self._config["llm"]["default_model"],
                "temperature": self._config["llm"]["temperature"],
                "max_tokens": self._config["llm"]["max_tokens"],
                "persona": self._config["llm"]["persona"]
            }
            journaling_manager.recordDebug(f"LLM model configured: {self.current_state['model']}")
            
            # Initialize synaptic pathways for hardware communication
            SynapticPathways = get_synaptic_pathways()
            await SynapticPathways.initialize()
            
            # Register as an integration area for command handling
            SynapticPathways.register_integration_area("llm", self)
            journaling_manager.recordInfo("LLM registered as integration area")
            
            self._initialized = True
            journaling_manager.recordInfo("Language model initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize language model: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the language model"""
        journaling_manager.recordScope("LLM.cleanup")
        try:
            self._initialized = False
            self.current_state["model"] = None
            journaling_manager.recordInfo("Language model cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up language model: {e}")
            raise
            
    async def process_input(self, input_text: str) -> Dict[str, Any]:
        """Process text input through the language model"""
        journaling_manager.recordScope("LLM.process_input", input_text=input_text)
        try:
            if not self._initialized:
                journaling_manager.recordError("Language model not initialized")
                raise RuntimeError("Language model not initialized")
                
            if self._processing:
                journaling_manager.recordError("Already processing input")
                raise RuntimeError("Already processing input")
                
            self._processing = True
            self.current_state["status"] = "processing"
            
            # Process input through model
            response = await self._generate_response(input_text)
            journaling_manager.recordDebug(f"Generated response: {response}")
            
            self._processing = False
            self.current_state["status"] = "completed"
            journaling_manager.recordInfo("Input processed successfully")
            
            return response
            
        except Exception as e:
            self._processing = False
            self.current_state["status"] = "error"
            self.current_state["error"] = str(e)
            journaling_manager.recordError(f"Error processing input: {e}")
            raise
            
    async def _generate_response(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Generate a response from the LLM"""
        try:
            think_command = LLMCommand.create_think_command(
                prompt=prompt,
                system_message=system_prompt
            )
            return await NeurocorticalBridge.execute(think_command)
        except Exception as e:
            journaling_manager.recordError(f"Error generating response: {e}")
            return {"status": "error", "message": str(e)}
            
    async def send_tts(self, text: str, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0):
        """Send a TTS command"""
        try:
            command = AudioCommand.create_tts_command(
                text=text,
                voice=voice_id,
                speed=speed,
                pitch=pitch
            )
            return await NeurocorticalBridge.execute(command)
        except Exception as e:
            journaling_manager.recordError(f"Error sending TTS command: {e}")
            raise
            
    async def send_asr(self, audio_data: bytes, language: str = "en"):
        """Send an ASR command"""
        try:
            command = AudioCommand.create_asr_command(
                audio_data=audio_data,
                language=language
            )
            return await NeurocorticalBridge.execute(command)
        except Exception as e:
            journaling_manager.recordError(f"Error sending ASR command: {e}")
            raise
            
    async def send_vad(self, audio_chunk: bytes, threshold: float = 0.5, frame_duration: int = 30):
        """Send a VAD command"""
        try:
            command = AudioCommand.create_vad_command(
                audio_chunk=audio_chunk,
                threshold=threshold,
                frame_duration=frame_duration
            )
            return await NeurocorticalBridge.execute(command)
        except Exception as e:
            journaling_manager.recordError(f"Error sending VAD command: {e}")
            raise
            
    async def send_whisper(self, audio_data: bytes, language: str = "en", model_type: str = "base"):
        """Send a Whisper command"""
        try:
            command = AudioCommand.create_whisper_command(
                audio_data=audio_data,
                language=language,
                model_type=model_type
            )
            return await NeurocorticalBridge.execute(command)
        except Exception as e:
            journaling_manager.recordError(f"Error sending Whisper command: {e}")
            raise
            
    async def process_assistant_interaction(self, audio_data: bytes = None, text_input: str = None) -> Dict[str, Any]:
        """High-level method to process a complete assistant interaction"""
        try:
            # Process audio input if provided
            if audio_data and not text_input:
                asr_response = await self.send_asr(audio_data)
                text_input = asr_response.get("text", "")
                if not text_input:
                    return {"status": "error", "message": "Failed to transcribe audio"}

            # Process text through LLM
            llm_response = await self.process_input(text_input)
            assistant_response = llm_response.get("text", "")

            # Generate audio response
            audio_path = None
            if assistant_response:
                tts_response = await self.send_tts(assistant_response)
                audio_path = tts_response.get("audio_path")

            return {
                "status": "ok",
                "input_text": text_input,
                "assistant_response": assistant_response,
                "audio_path": audio_path
            }

        except Exception as e:
            journaling_manager.recordError(f"Assistant interaction failed: {e}")
            return {"status": "error", "message": str(e)}

    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process an LLM command"""
        try:
            command_type = command.get("command_type")
            if command_type != CommandType.LLM.value:
                raise ValueError(f"Invalid command type for LLM: {command_type}")
                
            # Extract command parameters
            action = command.get("action")
            parameters = command.get("parameters", {})
            
            if action == "generate" or action == "inference":
                # Handle text generation
                prompt = None
                
                # Extract prompt from different possible locations
                if "prompt" in parameters:
                    prompt = parameters["prompt"]
                elif "data" in command and isinstance(command["data"], dict) and "prompt" in command["data"]:
                    prompt = command["data"]["prompt"]
                elif "data" in command and isinstance(command["data"], str):
                    prompt = command["data"]
                else:
                    journaling_manager.recordWarning(f"No prompt found in command: {command}")
                    prompt = ""
                
                # Get other parameters
                max_tokens = parameters.get("max_tokens", 100)
                if "data" in command and isinstance(command["data"], dict) and "max_tokens" in command["data"]:
                    max_tokens = command["data"]["max_tokens"]
                    
                temperature = parameters.get("temperature", 0.7)
                if "data" in command and isinstance(command["data"], dict) and "temperature" in command["data"]:
                    temperature = command["data"]["temperature"]
                
                # Generate response
                response = await self._generate_response(prompt, max_tokens=max_tokens, temperature=temperature)
                
                # Format response according to M5Stack API
                return {
                    "request_id": command.get("request_id", response.get("request_id", f"resp_{int(time.time())}")),
                    "work_id": "llm",
                    "data": {
                        "text": response.get("text", "")
                    },
                    "error": {"code": 0, "message": ""} if not response.get("error") else {"code": -1, "message": response.get("text", "Error")},
                    "object": "llm.utf-8.stream",
                    "created": int(time.time())
                }
                
            elif action == "analyze":
                # Handle text analysis
                text = parameters.get("text", "")
                analysis_type = parameters.get("analysis_type", "sentiment")
                
                if analysis_type == "sentiment":
                    result = await self.analyze_sentiment(text)
                elif analysis_type == "entities":
                    result = await self.extract_entities(text)
                else:
                    raise ValueError(f"Unsupported analysis type: {analysis_type}")
                    
                # Format response according to M5Stack API
                return {
                    "request_id": command.get("request_id", f"analyze_{int(time.time())}"),
                    "work_id": "llm",
                    "data": result,
                    "error": {"code": 0, "message": ""},
                    "object": "llm.utf-8",
                    "created": int(time.time())
                }
                
            else:
                raise ValueError(f"Unsupported action: {action}")
                
        except Exception as e:
            journaling_manager.recordError(f"Error processing LLM command: {e}")
            journaling_manager.recordError(traceback.format_exc())
            
            # Return error in M5Stack API format
            return {
                "request_id": command.get("request_id", f"error_{int(time.time())}"),
                "work_id": "llm",
                "data": None,
                "error": {"code": -1, "message": str(e)},
                "object": "llm",
                "created": int(time.time())
            } 

    async def generate_response(self, prompt: str, stream: bool = False):
        try:
            return await NeurocorticalBridge.execute("think", {
                "prompt": prompt,
                "stream": stream
            }) 
        except Exception as e:
            journaling_manager.recordError(f"Error generating response: {e}")
            return {"status": "error", "message": str(e)}

    #TO DO: Add sentiment analysis
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of a text"""
        try:
            return await NeurocorticalBridge.execute("analyze_sentiment", {
                "text": text
            })
        except Exception as e:
            journaling_manager.recordError(f"Error analyzing sentiment: {e}")
            return {"status": "error", "message": str(e)}


