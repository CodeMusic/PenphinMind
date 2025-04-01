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
from ...config import CONFIG
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from ...CorpusCallosum.neural_commands import (
    LLMCommand, TTSCommand, ASRCommand, VADCommand, WhisperCommand,
    CommandType, BaseCommand, SystemCommand
)
import time
import traceback

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

def get_synaptic_pathways():
    """Get the SynapticPathways class, avoiding circular imports"""
    from ...CorpusCallosum.synaptic_pathways import SynapticPathways
    return SynapticPathways

class LLM:
    """Handles language model interactions"""
    
    def __init__(self):
        """Initialize the language model"""
        journaling_manager.recordScope("LLM.__init__")
        self._initialized = False
        self._processing = False
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
                "name": CONFIG.llm_model,
                "temperature": CONFIG.llm_temperature,
                "max_tokens": CONFIG.llm_max_tokens
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
            
    async def _generate_response(self, prompt, system_prompt=None, max_tokens=None, temperature=None) -> Dict[str, Any]:
        """Generate a response from the LLM using the current configuration"""
        try:
            # Use provided parameters or fall back to current state
            max_tokens = max_tokens if max_tokens is not None else self.current_state["model"]["max_tokens"]
            temperature = temperature if temperature is not None else self.current_state["model"]["temperature"]
            
            # Create unique request ID for this generation
            request_id = f"generate_{int(time.time())}"
            
            # Structure the command in M5Stack API format
            command = {
                "type": "LLM",
                "command": "generate",
                "data": {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "request_id": request_id
                }
            }
            
            journaling_manager.recordInfo(f"Sending LLM inference command: {command}")
            
            # Send command through synaptic pathways
            SynapticPathways = get_synaptic_pathways()
            response = await SynapticPathways.send_command(command)
            
            journaling_manager.recordDebug(f"LLM response: {response}")
            
            # Check for errors
            if not response or isinstance(response, dict) and response.get("error"):
                error_code = response.get("error", {}).get("code", "unknown")
                error_message = response.get("error", {}).get("message", "Unknown error")
                journaling_manager.recordError(f"LLM generation error: {error_code} - {error_message}")
                return {
                    "text": f"Error: {error_message}",
                    "error": True,
                    "request_id": request_id,
                    "finished": True
                }
            
            # Parse the response based on M5Stack API format
            if isinstance(response, dict):
                # Check if it's an error response
                if "error" in response:
                    error_code = response.get("error", {}).get("code", "unknown")
                    error_message = response.get("error", {}).get("message", "Unknown error")
                    journaling_manager.recordError(f"LLM generation error: {error_code} - {error_message}")
                    return {
                        "text": f"Error: {error_message}",
                        "error": True,
                        "request_id": request_id,
                        "finished": True
                    }
                
                # Check if the response has data field
                if "data" in response:
                    data = response["data"]
                    # Data could be a string or a dictionary
                    if isinstance(data, str):
                        return {
                            "text": data,
                            "request_id": request_id,
                            "finished": True
                        }
                    elif isinstance(data, dict):
                        return {
                            "text": data.get("generated_text", ""),
                            "request_id": request_id,
                            "finished": data.get("finished", True)
                        }
            
            # Fallback for other response formats
            journaling_manager.recordWarning(f"Unknown response format: {response}")
            return {
                "text": str(response) if response else "",
                "request_id": request_id,
                "finished": True
            }
            
        except Exception as e:
            journaling_manager.recordError(f"Error in LLM response generation: {e}")
            journaling_manager.recordError(traceback.format_exc())
            return {
                "text": f"Error: {str(e)}",
                "error": True,
                "finished": True
            }
            
    async def send_tts(self, text: str, voice_id: str = "default", speed: float = 1.0, pitch: float = 1.0) -> Dict[str, Any]:
        """Send a TTS command"""
        try:
            command = TTSCommand(
                command_type=CommandType.TTS,
                text=text,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch
            )
            SynapticPathways = get_synaptic_pathways()
            return await SynapticPathways.send_command(command.to_dict())
        except Exception as e:
            journaling_manager.recordError(f"Error sending TTS command: {e}")
            raise
            
    async def send_asr(self, audio_data: bytes, language: str = "en", model_type: str = "base") -> Dict[str, Any]:
        """Send an ASR command"""
        try:
            command = ASRCommand(
                command_type=CommandType.ASR,
                input_audio=audio_data,
                language=language,
                model_type=model_type
            )
            SynapticPathways = get_synaptic_pathways()
            return await SynapticPathways.send_command(command.to_dict())
        except Exception as e:
            journaling_manager.recordError(f"Error sending ASR command: {e}")
            raise
            
    async def send_vad(self, audio_chunk: bytes, threshold: float = 0.5, frame_duration: int = 30) -> Dict[str, Any]:
        """Send a VAD command"""
        try:
            command = VADCommand(
                command_type=CommandType.VAD,
                audio_chunk=audio_chunk,
                threshold=threshold,
                frame_duration=frame_duration
            )
            SynapticPathways = get_synaptic_pathways()
            return await SynapticPathways.send_command(command.to_dict())
        except Exception as e:
            journaling_manager.recordError(f"Error sending VAD command: {e}")
            raise
            
    async def send_whisper(self, audio_data: bytes, language: str = "en", model_type: str = "base") -> Dict[str, Any]:
        """Send a Whisper command"""
        try:
            command = WhisperCommand(
                command_type=CommandType.WHISPER,
                audio_data=audio_data,
                language=language,
                model_type=model_type
            )
            SynapticPathways = get_synaptic_pathways()
            return await SynapticPathways.send_command(command.to_dict())
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