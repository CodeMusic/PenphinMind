"""
NeurocorticalBridge: A bridge between direct API calls and the task system

This module provides a unified interface for operations that can be executed
either directly or through the BasalGanglia task system, depending on their nature.
"""

import asyncio
import time
import json
import traceback
from typing import Dict, Any, Optional, Callable, List, Union

from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from Mind.Subcortex.api_commands import (
    create_command, 
    parse_response, 
    BaseCommand, 
    SystemCommand, 
    LLMCommand, 
    CommandType,
    AudioCommand,
    CommandFactory
)

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class NeurocorticalBridge:
    """Bridge between direct API calls and the task system"""
    
    OPERATION_MAP = {
        # LLM Operations
        "think": (CommandType.LLM, "inference"),
        "setup_llm": (CommandType.LLM, "setup"),
        "exit_llm": (CommandType.LLM, "exit"),
        
        # System Operations - match exact API commands
        "ping": (CommandType.SYSTEM, "ping"),
        "hardware_info": (CommandType.SYSTEM, "hwinfo"),
        "reboot": (CommandType.SYSTEM, "reboot"),
        "reset_system": (CommandType.SYSTEM, "reset"),
        "list_models": (CommandType.SYSTEM, "lsmode"),
        
        # Set model is handled through LLM setup
        "set_model": (CommandType.LLM, "setup"),
        
        # Audio Operations
        "setup_audio": (CommandType.AUDIO, "setup"),
        "asr": (CommandType.AUDIO, "asr"),
        "tts": (CommandType.AUDIO, "tts"),
        "vad": (CommandType.AUDIO, "vad"),
        "whisper": (CommandType.AUDIO, "whisper"),
        "kws": (CommandType.AUDIO, "kws")
    }
    
    # Class variables for hardware transport management
    _transport = None
    _connection_type = None
    _initialized = False
    
    @classmethod
    async def create_llm_pixel_grid(cls, width: int = 64, height: int = 64, color_mode: str = "rgb") -> Dict[str, Any]:
        """
        Create a pixel grid for drawing
        
        Args:
            width: Width of the grid in pixels
            height: Height of the grid in pixels
            color_mode: Color mode ('rgb', 'grayscale')
            
        Returns:
            Dict with grid information
        """
        journaling_manager.recordInfo(f"[NeurocorticalBridge] Creating pixel grid: {width}x{height} ({color_mode})")
        
        try:
            # Import needed modules
            import numpy as np
            from PIL import Image, ImageDraw
            
            # Create a blank grid
            if color_mode == "rgb":
                grid = np.zeros((height, width, 3), dtype=np.uint8)
            else:  # grayscale
                grid = np.zeros((height, width), dtype=np.uint8)
                
            # Create a PIL image from the grid for drawing
            if color_mode == "rgb":
                image = Image.fromarray(grid, mode="RGB")
            else:
                image = Image.fromarray(grid, mode="L")
                
            # Return grid information
            return {
                "status": "success",
                "grid": {
                    "width": width,
                    "height": height,
                    "color_mode": color_mode,
                    "image": image
                }
            }
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error creating pixel grid: {e}")
            import traceback
            journaling_manager.recordError(f"[NeurocorticalBridge] Error trace: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Error creating pixel grid: {str(e)}"
            }
            
    @classmethod
    def _to_dict_safely(cls, command):
        """
        Safely convert a command to a dictionary
        
        Args:
            command: Command to convert (could be dict, BaseCommand, or str)
            
        Returns:
            dict: Command as a dictionary, or the original if it's a string
            
        Raises:
            TypeError: If command is not a dict, doesn't have to_dict, and is not a string
        """
        if isinstance(command, dict):
            return command
        
        if hasattr(command, 'to_dict') and callable(getattr(command, 'to_dict')):
            return command.to_dict()
        
        if isinstance(command, str):
            # For string commands, return as is
            journaling_manager.recordWarning(f"Command is a string, not converting to dict: {command[:50]}...")
            return command
            
        # If we get here, we don't know how to handle this type
        error_msg = f"Unsupported command type: {type(command)}"
        journaling_manager.recordError(error_msg)
        raise TypeError(error_msg)
    
    @classmethod
    async def execute_operation(cls, operation: str, data: Dict[str, Any] = None, use_task: bool = None, stream: bool = False):
        """
        Execute a cognitive operation
        
        This is the main entry point for executing operations through the bridge.
        It will determine whether to use task system or direct execution.
        
        Args:
            operation: The operation to execute (mapped through OPERATION_MAP)
            data: Optional data for the operation
            use_task: Force task system usage (None = decide automatically)
            stream: Whether to stream results
            
        Returns:
            Dict[str, Any]: Operation result
        """
        try:
            journaling_manager.recordInfo(f"Execute operation: {operation}")
            
            # Special handling for pixel_grid operation
            if operation == "pixel_grid":
                width = data.get("width", 64)
                height = data.get("height", 64)
                color_mode = data.get("color_mode", "rgb")
                return await cls.create_llm_pixel_grid(width, height, color_mode)
            
            # If this is a special command, show debug info
            if operation in ["set_model", "hardware_info", "reset_system", "list_models", "ping", "reboot"]:
                print(f"📦 {operation.upper()} COMMAND: {json.dumps(data, indent=2) if data else '{}'}")
            
            # Special handling for critical system operations - always use direct transport
            if operation == "ping":
                return await cls._direct_ping()
                
            elif operation == "hardware_info":
                # Create direct hwinfo command
                hw_command = cls.create_sys_command("hwinfo")
                hw_result = await cls._send_to_hardware(hw_command)
                
                # Special post-processing for hardware_info operation
                if isinstance(hw_result, dict) and "error" in hw_result:
                    if isinstance(hw_result["error"], dict) and hw_result["error"].get("code") == 0:
                        # Extract data field
                        if "data" in hw_result:
                            return {
                                "status": "ok",
                                "response": hw_result["data"]
                            }
                
                # If we got here, there was an error
                return {
                    "status": "error",
                    "message": f"Hardware info failed: {hw_result.get('error', hw_result)}"
                }
                
            elif operation == "list_models":
                # Create direct lsmode command
                ls_command = cls.create_sys_command("lsmode")
                ls_result = await cls._send_to_hardware(ls_command)
                
                # Special post-processing for list_models operation
                if isinstance(ls_result, dict) and "error" in ls_result:
                    if isinstance(ls_result["error"], dict) and ls_result["error"].get("code") == 0:
                        # Extract data field (list of models)
                        if "data" in ls_result and isinstance(ls_result["data"], list):
                            return {
                                "status": "ok",
                                "response": ls_result["data"]
                            }
                
                # If we got here, there was an error
                return {
                    "status": "error",
                    "message": f"List models failed: {ls_result.get('error', ls_result)}"
                }
                
            elif operation == "reset_system":
                # Use our new direct method
                return await cls._direct_reset_system()
                
            elif operation == "reboot":
                # Use our new direct method
                return await cls._direct_reboot()
            
            # For other operations, follow normal procedure
            
            # Look up the command type and unit in the mapping
            if operation not in cls.OPERATION_MAP:
                journaling_manager.recordError(f"Unknown operation: {operation}")
                return {"status": "error", "message": f"Unknown operation: {operation}"}

            command_type, command_name = cls.OPERATION_MAP[operation]
            
            # For set_model, we need to create a proper llm setup command
            if operation == "set_model" and data:
                from Mind.Subcortex.api_commands import CommandFactory
                
                # Extract model name and persona
                model_name = data.get("model", "")
                persona = data.get("prompt", "")
                
                # Create setup command
                setup_command = CommandFactory.create_llm_setup_command(
                    model_name=model_name,
                    persona=persona
                )
                
                # Send directly through hardware transport
                setup_result = await cls._send_to_hardware(setup_command)
                
                # Process result
                if isinstance(setup_result, dict) and "error" in setup_result:
                    error = setup_result.get("error", {})
                    if isinstance(error, dict) and error.get("code") == 0:
                        # Success according to API
                        return {
                            "status": "ok",
                            "message": "Model set successfully",
                            "response": setup_result
                        }
                    else:
                        # API returned an error
                        error_message = error.get("message", "Unknown error")
                        return {
                            "status": "error",
                            "message": f"API Error: {error_message}",
                            "response": setup_result
                        }
            
            # Fallback response
            return {
                    "status": "error",
                    "message": "Failed to set model, unexpected response format"
                }
            
            # Create a command dict with the right format using helper function
            command = create_command(command_type, command_name, data)
            
            # Decide between task system and direct execution
            # Force direct execution for system operations regardless of use_task
            if command_type == CommandType.SYSTEM:
                journaling_manager.recordInfo(f"Using direct execution for system operation: {operation}")
                return await cls._execute_direct(command)
            
            # For other operations, use the task flag
            if use_task is True:
                journaling_manager.recordInfo(f"Using task system for operation: {operation} per explicit flag")
                # Special handling for streaming in task system
                if stream and operation == "think":
                    return await cls._handle_stream(command)
                return await cls._execute_task(command)
            elif use_task is False:
                journaling_manager.recordInfo(f"Using direct execution for operation: {operation} per explicit flag")
                # Special handling for streaming in direct execution
                if stream and operation == "think":
                    return await cls._handle_llm_stream(command)
                return await cls._execute_direct(command)
            
            # For streaming think operations, always use direct mode
            if stream and operation == "think":
                journaling_manager.recordInfo(f"Using direct execution for streaming think operation")
                return await cls._handle_llm_stream(command)
            
            # Decide between direct and task based on operation
            if command_type == CommandType.LLM:
                # Direct execution for LLM operations
                journaling_manager.recordInfo(f"Using direct execution for LLM operation: {operation}")
                return await cls._execute_direct(command)
            else:
                # Task system for other operations (like audio)
                journaling_manager.recordInfo(f"Using task system for operation: {operation}")
                return await cls._execute_task(command)

        except Exception as e:
            journaling_manager.recordError(f"Execute operation error: {e}")
            import traceback
            journaling_manager.recordError(f"Operation error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def _handle_stream(cls, command: Union[BaseCommand, Dict[str, Any]]) -> Dict[str, Any]:
        """Handle streaming operations"""
        try:
            if isinstance(command, LLMCommand) or (isinstance(command, dict) and command.get("work_id") == "llm"):
                return await cls._handle_llm_stream(command)
            else:
                return {"status": "error", "message": "Streaming not supported for this operation"}
        except Exception as e:
            journaling_manager.recordError(f"Stream handling error: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def _handle_llm_stream(cls, command: Union[Dict[str, Any], BaseCommand], callback=None) -> Dict[str, Any]:
        """
        Handle streaming LLM inference
        
        Args:
            command: The command to execute
            callback: Optional external callback to receive streaming chunks directly
            
        Returns:
            Dict with status and collected response
        """
        try:
            # Get the prompt from the command
            prompt = ""
            if isinstance(command, dict):
                # If data is a string, it's the prompt (non-streaming format)
                if isinstance(command.get("data"), str):
                    prompt = command.get("data", "")
                # If data is a dict, look for prompt or delta
                elif isinstance(command.get("data"), dict):
                    prompt = command.get("data", {}).get("prompt", 
                            command.get("data", {}).get("delta", ""))
            else:
                # Command object
                data = getattr(command, "data", None)
                if isinstance(data, str):
                    prompt = data
                elif isinstance(data, dict):
                    prompt = data.get("prompt", data.get("delta", ""))
                
            journaling_manager.recordDebug("=== LLM STREAM REQUEST ===")
            journaling_manager.recordDebug(f"Prompt (first 100 chars): {prompt[:100]}...")
            
            # First, create a proper stream command
            stream_command = cls.create_llm_inference_command(prompt, stream=True)
            
            # Log the structured stream command
            journaling_manager.recordDebug("=== STREAM COMMAND JSON ===")
            journaling_manager.recordDebug(json.dumps(stream_command, indent=2))
            
            # Initialize response stream
            responses = []
            response_text = ""
            
            # Get an asyncio queue for collecting streaming responses
            stream_queue = asyncio.Queue()
            
            # Create a callback to handle streaming responses
            async def handle_stream_chunk(chunk):
                try:
                    # Log the chunk with truncation for large responses
                    chunk_log = json.dumps(chunk)
                    if len(chunk_log) > 500:
                        journaling_manager.recordDebug(f"Stream chunk received (truncated): {chunk_log[:500]}...")
                    else:
                        journaling_manager.recordDebug(f"Stream chunk received: {chunk_log}")
                    
                    # Extract text from the chunk
                    chunk_text = ""
                    
                    # For API that returns proper objects with data field
                    if isinstance(chunk, dict) and "data" in chunk:
                        data = chunk["data"]
                        
                        # Handle both string and object data formats
                        if isinstance(data, str):
                            chunk_text = data
                            await stream_queue.put(data)
                        elif isinstance(data, dict) and "delta" in data:
                            # Newer API with delta field
                            delta = data.get("delta", "")
                            if delta:
                                chunk_text = delta
                                await stream_queue.put(delta)
                                
                            # Check for finish flag
                            if data.get("finish", False):
                                # Signal completion
                                await stream_queue.put(None)
                    else:
                        # For simple API that just returns text
                        if isinstance(chunk, str):
                            chunk_text = chunk
                            await stream_queue.put(chunk)
                    
                    # If an external callback was provided, call it with the chunk text
                    if callback and chunk_text:
                        try:
                            # Call the external callback with the text
                            if asyncio.iscoroutinefunction(callback):
                                await callback(chunk_text)
                            else:
                                callback(chunk_text)
                        except Exception as e:
                            journaling_manager.recordError(f"Error in external callback: {e}")
                except Exception as e:
                    journaling_manager.recordError(f"Error processing stream chunk: {e}")
            
            # Setup transport streaming - the callback will add chunks to the queue
            stream_result = await cls._send_to_hardware(stream_command, stream_callback=handle_stream_chunk)
            
            # Process all streaming chunks until complete
            while True:
                try:
                    # Wait for a chunk, but with timeout to prevent hanging indefinitely
                    chunk = await asyncio.wait_for(stream_queue.get(), timeout=15.0)
                    
                    # None signals end of stream
                    if chunk is None:
                        journaling_manager.recordDebug("Stream complete (received None chunk)")
                        break
                        
                    # Add chunk to response text
                    response_text += chunk
                    responses.append(chunk)
                    
                    # Log length for debug
                    journaling_manager.recordDebug(f"Current response length: {len(response_text)} chars, {len(responses)} chunks")
                    
                except asyncio.TimeoutError:
                    journaling_manager.recordWarning("Stream timeout waiting for data")
                    break
                except Exception as e:
                    journaling_manager.recordError(f"Error processing stream chunk: {e}")
                    break
            
            # Log the final response
            journaling_manager.recordDebug(f"Final response length: {len(response_text)} chars")
            journaling_manager.recordDebug(f"Response (first 500 chars): {response_text[:500]}...")
            
            # Return the complete response
            return {
                "status": "ok",
                "response": response_text,
                "chunks": responses
            }
        except Exception as e:
            journaling_manager.recordError(f"Streaming error: {e}")
            import traceback
            journaling_manager.recordError(f"Streaming error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def _execute_task(cls, command: BaseCommand) -> Dict[str, Any]:
        """Execute command through task system"""
        try:
            # Use our own get_basal_ganglia method 
            bg = cls.get_basal_ganglia()
            if not bg:
                return {"status": "error", "message": "BasalGanglia not available"}
            
            task = bg.get_task(command.work_id) if hasattr(bg, 'get_task') else None
            
            if task:
                task.command = command.action
                task.data = command.data
                task.active = True
                await task.execute()
                return {"status": "ok", "response": "Task started", "task": task}
            else:
                return {"status": "error", "message": "Task not found"}
                
        except Exception as e:
            journaling_manager.recordError(f"Task execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def execute(cls, command: Union[BaseCommand, Dict[str, Any]]) -> Dict[str, Any]:
        """Execute a command through appropriate pathway"""
        try:
            # Log command execution
            journaling_manager.recordInfo("=================================")
            journaling_manager.recordInfo("📋 COMMAND EXECUTION:")
            journaling_manager.recordInfo("=================================")
            
            # Get command details
            if isinstance(command, dict):
                work_id = command.get("work_id", "unknown")
                action = command.get("action", "unknown")
            else:
                work_id = getattr(command, "work_id", "unknown")
                action = getattr(command, "action", "unknown")
            
            journaling_manager.recordInfo(f"Work ID: {work_id}, Action: {action}")
            
            # Special case for LLM inference (thinking)
            if work_id == "llm" and action == "inference":
                # Get the prompt based on the command format
                if isinstance(command, dict):
                    # Check if data is string (non-streaming) or dict (streaming)
                    data = command.get("data", {})
                    
                    if isinstance(data, str):
                        # Non-streaming format where data is the prompt string directly
                        prompt = data
                        stream = False
                        journaling_manager.recordDebug("Using non-streaming format (data is string)")
                    elif isinstance(data, dict):
                        # Streaming format where prompt is in data.delta
                        prompt = data.get("delta", "")
                        stream = True  # It's streaming if data is a dict with delta
                        journaling_manager.recordDebug("Using streaming format (data is dict with delta)")
                    else:
                        # Unknown format
                        prompt = ""
                        stream = False
                        journaling_manager.recordError(f"Unknown data format: {type(data)}")
                else:
                    # For BaseCommand objects
                    data = getattr(command, "data", {})
                    
                    if isinstance(data, str):
                        prompt = data
                        stream = False
                    elif isinstance(data, dict):
                        prompt = data.get("delta", "")
                        stream = True
                    else:
                        prompt = ""
                        stream = False
                
                # Debug logging for inference request
                journaling_manager.recordDebug("=== LLM INFERENCE REQUEST ===")
                journaling_manager.recordDebug(f"Prompt (first 100 chars): {prompt[:100]}...")
                journaling_manager.recordDebug(f"Stream mode: {stream}")
                
                # For streaming mode, use a specialized method
                if stream:
                    journaling_manager.recordInfo(f"Using streaming mode for inference")
                    return await cls._handle_llm_stream(command)
                
                # For normal mode, use direct hardware transport
                journaling_manager.recordInfo(f"Using direct hardware transport for inference")
                
                # Use the safe conversion method
                safe_command = cls._to_dict_safely(command)
                
                # Log the inference command payload
                journaling_manager.recordDebug("=== INFERENCE COMMAND JSON ===")
                journaling_manager.recordDebug(json.dumps(safe_command, indent=2))
                
                # Execute directly through transport
                result = await cls._send_to_hardware(safe_command)
                
                # Log the inference result
                journaling_manager.recordDebug("=== INFERENCE RESULT JSON ===")
                journaling_manager.recordDebug(json.dumps(result, indent=2))
                
                # Process result
                if result and isinstance(result, dict):
                    # If we have a standard API response format
                    if "error" in result and isinstance(result["error"], dict):
                        error_code = result["error"].get("code", -1)
                        if error_code == 0:
                            # Success
                            response = result.get("data", "")
                            return {
                                "status": "ok",
                                "response": response,
                                "raw": result
                            }
                        else:
                            # API error
                            error_msg = result["error"].get("message", "Unknown error")
                            return {
                                "status": "error",
                                "message": error_msg,
                                "raw": result
                            }
                
                # If we get here, format wasn't recognized
                return {
                    "status": "error",
                    "message": "Unexpected response format",
                    "raw": result
                }
            
            # For other operations, try direct execution first
            journaling_manager.recordInfo(f"Using direct transport for command")
            
            # Initialize transport if needed
            if not cls._initialized:
                success = await cls._initialize_transport(cls._connection_type or "tcp")
                if not success:
                    return {
                        "status": "error", 
                        "message": "Failed to initialize transport"
                    }
            
            # Send directly through transport using our safe conversion method
            safe_command = cls._to_dict_safely(command)
            result = await cls._send_to_hardware(safe_command)
            
            # Check for API response format
            if isinstance(result, dict) and "error" in result:
                error = result.get("error", {})
                if isinstance(error, dict):
                    error_code = error.get("code", -1)
                    if error_code == 0:
                        # Success
                        return {
                            "status": "ok",
                            "response": result.get("data", ""),
                            "raw": result
                        }
                    else:
                        # API error
                        error_msg = error.get("message", "Unknown error")
                        return {
                            "status": "error",
                            "message": error_msg,
                            "raw": result
                        }
            
            # Fallback if response format wasn't recognized
            return {
                "status": "error",
                "message": "Failed to execute command - Unexpected response format",
                "raw": result
            }
                
        except Exception as e:
            journaling_manager.recordError(f"❌ Command execution error: {e}")
            import traceback
            journaling_manager.recordError(f"❌ Stack trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _execute_direct(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command directly"""
        try:
            # Get BasalGanglia instance from our own method instead of SynapticPathways
            bg = cls.get_basal_ganglia()
            if not bg:
                return {"status": "error", "message": "BasalGanglia not available"}
            
            # Execute command directly
            comm_task = bg.get_communication_task() if hasattr(bg, 'get_communication_task') else None
            if comm_task:
                response = await comm_task.send_command(command)
                if response:
                    return {"status": "ok", "response": response}
                else:
                    return {"status": "error", "message": "No response"}
            else:
                return {"status": "error", "message": "Communication task not available"}
                
        except Exception as e:
            journaling_manager.recordError(f"Direct execution error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_llm_command(cls, command: LLMCommand, stream: bool = False):
        """Handle LLM commands with proper routing"""
        action = command.action
        bg = cls.get_basal_ganglia()
        
        # For basic configuration commands, use communication task
        if action in ["setup", "reset"]:
            comm_task = bg.get_communication_task()
            return await comm_task.send_command(command)
            
        # For inference, use ThinkTask if possible
        elif action == "inference":
            prompt = command.data.get("delta", "")
            if prompt:
                stream_mode = command.stream if hasattr(command, "stream") else stream
                return bg.think(prompt=prompt, stream=stream_mode)
            
            comm_task = bg.get_communication_task()
            return await comm_task.send_command(command)
            
    @classmethod
    async def _handle_system_command(cls, command: SystemCommand):
        """Handle system commands by creating and executing appropriate tasks"""
        command_type = command.command_type
        data = command.data
        
        # Get SystemCommandTask from BasalGanglia
        bg = cls.get_basal_ganglia()
        system_task = bg.system_command(command_type, data)
        
        # Wait for task to complete (this is a blocking operation)
        while system_task.active or not system_task.has_completed():
            await asyncio.sleep(0.1)
        
        # Return task result
        return system_task.result if system_task.result is not None else {"error": "Task completed with no result"}
    
    @classmethod
    async def _handle_audio_command(cls, command: AudioCommand) -> Dict[str, Any]:
        """Handle audio commands based on their action"""
        try:
            if command.action == "tts":
                return await cls._handle_tts(command)
            elif command.action == "asr":
                return await cls._handle_asr(command)
            elif command.action == "vad":
                return await cls._handle_vad(command)
            elif command.action == "whisper":
                return await cls._handle_whisper(command)
            elif command.action == "kws":
                return await cls._handle_kws(command)
            else:
                return {"status": "error", "message": f"Unknown audio action: {command.action}"}
        except Exception as e:
            journaling_manager.recordError(f"Audio command error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_tts(cls, command: AudioCommand) -> Dict[str, Any]:
        """Handle text-to-speech command execution"""
        try:
            # Extract parameters from command
            text = command.data.get("text", "")
            voice = command.data.get("voice", "default")
            speed = command.data.get("speed", 1.0)
            pitch = command.data.get("pitch", 1.0)
            
            if not text:
                return {"status": "error", "message": "No text provided for TTS"}
                
            # Send command directly to hardware
            journaling_manager.recordInfo(f"[NeurocorticalBridge] Processing TTS: {text[:50]}...")
            
            # Use the safe conversion method
            safe_command = cls._to_dict_safely(command)
            result = await cls._send_to_hardware(safe_command)
            
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] TTS error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_asr(cls, command: AudioCommand) -> Dict[str, Any]:
        """Handle automatic speech recognition command execution"""
        try:
            # Extract parameters from command
            audio_data = command.data.get("audio_data")
            language = command.data.get("language", "en")
            
            if not audio_data:
                return {"status": "error", "message": "No audio data provided for ASR"}
                
            # Send command directly to hardware
            journaling_manager.recordInfo("[NeurocorticalBridge] Processing ASR request")
            # Use the safe conversion method
            safe_command = cls._to_dict_safely(command)
            result = await cls._send_to_hardware(safe_command)
            
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] ASR error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_vad(cls, command: AudioCommand) -> Dict[str, Any]:
        """Handle voice activity detection command execution"""
        try:
            # Extract parameters from command
            audio_chunk = command.data.get("audio_chunk", b'')
            threshold = command.data.get("threshold", 0.5)
            frame_duration = command.data.get("frame_duration", 30)
                
            # Send command directly to hardware
            journaling_manager.recordInfo("[NeurocorticalBridge] Processing VAD request")
            # Use the safe conversion method
            safe_command = cls._to_dict_safely(command)
            result = await cls._send_to_hardware(safe_command)
            
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] VAD error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_whisper(cls, command: AudioCommand) -> Dict[str, Any]:
        """Handle whisper (ASR) command execution"""
        try:
            # Extract parameters from command
            audio_data = command.data.get("audio_data")
            language = command.data.get("language", "en")
            model_type = command.data.get("model_type", "base")
            
            if not audio_data:
                return {"status": "error", "message": "No audio data provided for Whisper"}
                
            # Send command directly to hardware
            journaling_manager.recordInfo("[NeurocorticalBridge] Processing Whisper request")
            # Use the safe conversion method
            safe_command = cls._to_dict_safely(command)
            result = await cls._send_to_hardware(safe_command)
            
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Whisper error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_kws(cls, command: AudioCommand) -> Dict[str, Any]:
        """Handle keyword spotting command execution"""
        try:
            # Extract parameters from command
            audio_data = command.data.get("audio_data", b'')
            keywords = command.data.get("keywords", [])
            
            if not audio_data:
                return {"status": "error", "message": "No audio data provided for KWS"}
                
            # Send command directly to hardware
            journaling_manager.recordInfo("[NeurocorticalBridge] Processing KWS request")
            # Use the safe conversion method
            safe_command = cls._to_dict_safely(command)
            result = await cls._send_to_hardware(safe_command)
            
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] KWS error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _direct_get_model(cls) -> Dict[str, Any]:
        """Get current active model directly without using task system"""
        try:
            # Get communication task from our own method
            bg = cls.get_basal_ganglia()
            if not bg:
                return {"status": "error", "message": "BasalGanglia not available"}
                
            comm_task = bg.get_communication_task() if hasattr(bg, 'get_communication_task') else None
            
            if not comm_task:
                return {"status": "error", "message": "Communication task not available"}
                
            # Create get model command
            get_model_command = {
                "request_id": f"get_model_{int(time.time())}",
                "work_id": "sys",
                "action": "get_model"
            }
            
            # Send command directly through comm task
            response = await comm_task.send_command(get_model_command)
            
            # Process response
            if response and isinstance(response, dict):
                return {"status": "ok", "model": response.get("data", "")}
            else:
                return {"status": "error", "message": "Invalid response format"}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error getting model: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _direct_list_models(cls) -> List[Dict[str, Any]]:
        """Direct model listing without using the task system"""
        try:
            # Import SynapticPathways only for caching model data
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            cached_models = getattr(SynapticPathways, "available_models", [])
            
            # Create list models request using our system command format method
            list_models_command = cls.create_sys_command("lsmode")
            
            # Use our own get_basal_ganglia method
            bg = cls.get_basal_ganglia()
            if not bg:
                journaling_manager.recordError("[NeurocorticalBridge] BasalGanglia not available")
                return cached_models  # Fall back to cached models
                
            comm_task = bg.get_communication_task() if hasattr(bg, 'get_communication_task') else None
            
            if not comm_task:
                journaling_manager.recordError("[NeurocorticalBridge] Communication task not available")
                return cached_models  # Fall back to cached models
            
            # Send the command directly via communication task
            journaling_manager.recordInfo("[NeurocorticalBridge] Using direct communication for lsmode command")
            response = await comm_task.send_command(list_models_command)
            
            if response and isinstance(response, dict) and "data" in response:
                models_data = response["data"]
                if isinstance(models_data, list):
                    # Update shared cache if we have access to SynapticPathways
                    if 'SynapticPathways' in locals():
                        SynapticPathways.available_models = models_data
                    
                    return models_data
                else:
                    journaling_manager.recordError(f"[NeurocorticalBridge] Invalid models data format: {type(models_data)}")
            else:
                journaling_manager.recordError(f"[NeurocorticalBridge] Invalid models response: {response}")
            
            # Return cached models if available
            return cached_models
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error listing models: {e}")
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            return getattr(SynapticPathways, "available_models", [])
    
    @classmethod
    async def _direct_set_model(cls, model_name: str) -> Dict[str, Any]:
        """Set model directly without using the task system"""
        try:
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_set_model] Setting model to {model_name}")
            
            # Get local reference to BasalGanglia
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Create setup command using our system command format method
            setup_command = cls.create_setup_command(model_name)
            
            # Log the setup command for debugging
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_set_model] Setup command: {json.dumps(setup_command)}")
            
            # Get communication task directly from BasalGanglia
            bg = cls.get_basal_ganglia()
            if not bg:
                journaling_manager.recordDebug("[NeurocorticalBridge._direct_set_model] ❌ BasalGanglia not available")
                return {"status": "error", "message": "BasalGanglia not available"}
                
            comm_task = bg.get_communication_task() if hasattr(bg, 'get_communication_task') else None
            
            if not comm_task:
                journaling_manager.recordDebug("[NeurocorticalBridge._direct_set_model] ❌ Communication task not available")
                return {"status": "error", "message": "Communication task not available"}
            
            # Send command directly through communication task
            journaling_manager.recordDebug("[NeurocorticalBridge._direct_set_model] Sending command through communication task")
            response = await comm_task.send_command(setup_command)
            
            # Process response
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_set_model] Response: {json.dumps(response)}")
            
            # Handle API response format
            if isinstance(response, dict) and "error" in response:
                error = response["error"]
                if isinstance(error, dict) and error.get("code") == 0:
                    journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_set_model] ✅ Model set successfully to {model_name}")
                    
                    # Update default model if we have access to SynapticPathways
                    if 'SynapticPathways' in locals():
                        SynapticPathways.default_llm_model = model_name
                        journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_set_model] ✅ Updated default model to {model_name}")
                    
                    return {"status": "ok", "model": model_name}
                else:
                    error_msg = error.get("message", "Unknown error")
                    journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_set_model] ❌ Error: {error_msg}")
                    return {"status": "error", "message": error_msg}
            else:
                journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_set_model] ❌ Unexpected response format")
                return {"status": "error", "message": "Unexpected response format"}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge._direct_set_model] Error: {e}")
            import traceback
            journaling_manager.recordError(f"[NeurocorticalBridge._direct_set_model] Error trace: {traceback.format_exc()}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _direct_reset_system(cls) -> Dict[str, Any]:
        """
        Reset the system directly using API format
        
        API format:
        Request: {"request_id": "001", "work_id": "sys", "action": "reset"}
        Response: {"created": timestamp, "error": {"code": 0, "message": "llm server restarting ..."}, "request_id": "001", "work_id": "sys"}
        
        Returns:
            Dict with status and response
        """
        journaling_manager.recordDebug("[NeurocorticalBridge._direct_reset_system] ⚡ Creating reset command...")
        
        try:
            # Create properly formatted reset command per API spec
            reset_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "reset"
            }
            
            # Log the command
            journaling_manager.recordInfo(f"📡 Sending system reset command: {json.dumps(reset_command)}")
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_reset_system] 📦 Command: {json.dumps(reset_command, indent=2)}")
            
            # Send command
            response = await cls._send_to_hardware(reset_command)
            
            # Log the response
            journaling_manager.recordInfo(f"📡 Received reset response: {json.dumps(response)}")
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_reset_system] 📊 Response: {json.dumps(response, indent=2)}")
            
            # Process API response
            if isinstance(response, dict) and "error" in response:
                error = response.get("error", {})
                if isinstance(error, dict) and error.get("code") == 0:
                    # API success format
                    success_message = error.get("message", "System reset initiated")
                    
                    journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_reset_system] ✅ Reset successful: {success_message}")
                    
                    # For reset, we can get a second completion message, but we won't wait for it
                    return {
                        "status": "ok",
                        "message": success_message,
                        "response": response
                    }
                else:
                    # API error format
                    error_message = error.get("message", "Unknown error")
                    
                    journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_reset_system] ❌ Reset error: {error_message}")
                    
                    return {
                        "status": "error",
                        "message": f"Reset failed: {error_message}",
                        "response": response
                    }
            else:
                # Invalid response format
                journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_reset_system] ❌ Invalid reset response format")
                
                return {
                    "status": "error",
                    "message": "Invalid reset response format",
                    "response": response
                }
                
        except Exception as e:
            journaling_manager.recordError(f"Reset system error: {e}")
            import traceback
            journaling_manager.recordError(f"Reset error trace: {traceback.format_exc()}")
            
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_reset_system] ❌ Error: {e}")
                
            return {
                "status": "error",
                "message": f"Reset error: {str(e)}"
            }
    
    @classmethod
    async def _direct_ping(cls) -> Dict[str, Any]:
        """Send a ping command to verify system connectivity using direct transport"""
        journaling_manager.recordDebug("[NeurocorticalBridge._direct_ping] ⚡ Creating ping command...")
        
        try:
            # Create a properly formatted ping command per API spec
            ping_command = CommandFactory.create_ping_command("001")  # Use fixed request ID for stability
            
            # Log the command we're sending
            journaling_manager.recordInfo(f"📡 Sending direct ping command: {json.dumps(ping_command)}")
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_ping] 📦 Command: {json.dumps(ping_command, indent=2)}")
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_ping] 🔌 Connection type: {cls._connection_type}")
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_ping] 🔄 Initialized: {cls._initialized}")
            
            # Use direct hardware transport
            response = await cls._send_to_hardware(ping_command)
            
            # Log the raw response
            journaling_manager.recordInfo(f"📡 Received ping response: {json.dumps(response)}")
            journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_ping] 📊 Response: {json.dumps(response, indent=2) if response else 'None'}")
            
            # Check for properly formatted API response
            if isinstance(response, dict) and "error" in response:
                error_code = response.get("error", {}).get("code", -1)
                
                if error_code == 0:
                    # API success code is 0
                    journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_ping] ✅ Ping successful (error code 0)")
                    
                    return {
                        "status": "ok",
                        "message": "Ping successful",
                        "response": response,
                        "timestamp": time.time()
                    }
                else:
                    # Got an error response from the API
                    error_msg = response.get("error", {}).get("message", "Unknown error")
                    journaling_manager.recordError(f"Ping API error: Code {error_code}, Message: {error_msg}")
                    journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_ping] ❌ Ping failed with error code {error_code}: {error_msg}")
                    
                    return {
                        "status": "error",
                        "message": f"Ping failed with error code {error_code}: {error_msg}",
                        "response": response
                    }
            else:
                # Unexpected response format
                journaling_manager.recordError(f"Unexpected ping response format: {json.dumps(response)}")
                journaling_manager.recordDebug(f"[NeurocorticalBridge._direct_ping] ❌ Unexpected response format")
                
                return {
                    "status": "error",
                    "message": "Unexpected ping response format",
                    "response": response
                }
            
        except Exception as e:
            journaling_manager.recordError(f"Direct ping error: {e}")
            import traceback
            journaling_manager.recordError(f"Ping error trace: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Ping error: {str(e)}"
            }

    @classmethod
    def get_basal_ganglia(cls):
        """
        Get BasalGanglia instance or create a minimal one if unable to import

        This is used to maintain compatibility when BasalGanglia is not available
        """
        try:
            # Import here to avoid circular imports
            from Mind.Subcortex.BasalGanglia.basal_ganglia_integration import BasalGangliaIntegration
            # Create instance if needed
            bg_integration = BasalGangliaIntegration()
            journaling_manager.recordInfo("Using actual BasalGanglia")
            return bg_integration
        except ImportError:
            # Create a minimal implementation with only essential functionality
            class MinimalBasalGanglia:
                def __init__(self):
                    journaling_manager.recordInfo("Created MinimalBasalGanglia")
                
                def get_task(self, task_type):
                    # Return None to indicate task not found
                    return None
                
                def register_task(self, task):
                    # Do nothing in minimal implementation
                    journaling_manager.recordInfo(f"MinimalBasalGanglia: Task registration not supported")
                    return False
                
                async def think(self, prompt, stream=False):
                    """
                    Minimal implementation of think function
                    """
                    journaling_manager.recordError(f"MinimalBasalGanglia: Think not fully implemented")
                    return {
                        "status": "error",
                        "message": "BasalGanglia not available - Think operation not supported"
                    }
                
                def get_communication_task(self):
                    # Return None to indicate communication task not available
                    journaling_manager.recordInfo("MinimalBasalGanglia: Communication task not available")
                    return None
            
            # Return an instance of the minimal implementation
            journaling_manager.recordInfo("Using MinimalBasalGanglia (limited functionality)")
            return MinimalBasalGanglia()

    @classmethod
    async def get_hardware_info(cls) -> Dict[str, Any]:
        """Get hardware information from the device"""
        try:
            # Create a proper hardware info command
            hw_command = cls.create_sys_command("hwinfo")
            
            # Send command directly through transport
            result = await cls._send_to_hardware(hw_command)
            
            # Process the result in standard format
            if isinstance(result, dict) and "error" in result:
                error = result.get("error", {})
                if isinstance(error, dict) and error.get("code") == 0:
                    # Success - extract data field
                    return {
                        "status": "ok",
                        "data": result.get("data", {})
                    }
            
            # If we get here, there was an error
            return {
                "status": "error", 
                "message": "Failed to get hardware info",
                "raw_response": result
            }
        except Exception as e:
            journaling_manager.recordError(f"Error getting hardware info: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def initialize_system(cls, connection_type: str = None) -> bool:
        """
        Initialize the system with the specified connection type
        
        Args:
            connection_type: Type of connection to use (serial, tcp, adb)
            
        Returns:
            bool: True if initialization was successful
        """
        try:
            # Use default connection type if not specified
            if connection_type is None:
                connection_type = "tcp"  # Default to TCP
            
            journaling_manager.recordInfo(f"🔍 Setting connection mode to {connection_type}...")
            
            # Use _initialize_transport, which will get connection details from the mind configuration
            # This method is now updated to work with mind-specific configuration
            result = await cls._initialize_transport(connection_type)
            
            if result:
                # If successful, get hardware info
                hw_info = await cls.get_hardware_info()
                cls._initialized = True
                return True
            else:
                journaling_manager.recordError(f"Failed to establish {connection_type} connection")
                print(f"Failed to establish {connection_type} connection")
                cls._initialized = False
                return False
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Initialization error: {e}")
            import traceback
            journaling_manager.recordError(f"[NeurocorticalBridge] Initialization trace: {traceback.format_exc()}")
            cls._initialized = False
            return False

    @classmethod
    async def _initialize_transport(cls, transport_type: str = None) -> bool:
        """Initialize transport layer for hardware communication
        
        Args:
            transport_type: Type of transport to use (serial, tcp, adb)
        
        Returns:
            bool: True if initialization was successful
        """
        try:
            # Import here to avoid circular imports
            from .transport_layer import get_transport
            from Mind.mind_config import get_mind_by_id, get_default_mind_id
            
            # Use the provided transport type or default to TCP
            if transport_type is None:
                transport_type = "tcp"  # Default to TCP
            
            # Store connection type for future use
            cls._connection_type = transport_type
            journaling_manager.recordInfo(f"Initializing {transport_type} transport...")
            print(f"\n🚀 Initializing {transport_type.upper()} transport...")
            
            # Get connection details from mind configuration
            try:
                # Try to get the default mind first
                mind_id = get_default_mind_id()
                mind_config = get_mind_by_id(mind_id)
                
                # Get connection settings
                connection_details = mind_config.get("connection", {})
                
                journaling_manager.recordInfo(f"Using connection settings from mind: {mind_id}")
                journaling_manager.recordInfo(f"Connection details: {connection_details}")
                print(f"🔍 Using connection settings from mind: {mind_id}")
                
                # Log if using "auto" settings
                if connection_details.get("ip") == "auto" or connection_details.get("port") == "auto":
                    journaling_manager.recordInfo("Using 'auto' connection settings - will attempt to discover values")
                    print("📡 Using 'auto' connection settings - will attempt to discover values")
                    print("This may take a moment as we search for the device...")
                else:
                    print(f"📡 Connecting to {connection_details.get('ip')}:{connection_details.get('port')}")
                
                # Create transport instance with connection details
                cls._transport = get_transport(transport_type, connection_details)
                
            except Exception as e:
                journaling_manager.recordWarning(f"Failed to get mind connection settings: {e}")
                journaling_manager.recordWarning("Falling back to transport without explicit connection details")
                print("⚠️ Failed to get connection settings, using defaults")
                
                # Create transport instance without connection details
                cls._transport = get_transport(transport_type)
            
            if not cls._transport:
                journaling_manager.recordError(f"Failed to create {transport_type} transport")
                print(f"❌ Failed to create {transport_type} transport")
                return False
            
            # Connect transport
            journaling_manager.recordInfo(f"Connecting {transport_type} transport...")
            print("🔌 Connecting to device...")
            connect_result = await cls._transport.connect()
            
            if connect_result:
                journaling_manager.recordInfo(f"✅ {transport_type.upper()} transport connected successfully")
                print(f"✅ {transport_type.upper()} transport connected successfully")
                cls._initialized = True    
                
                # Get firmware/hardware info
                print("📊 Getting device information...")
                hw_info = await cls.get_hardware_info()
                if hw_info and hw_info.get("status") == "ok":
                    print(f"📱 Device connected: {hw_info.get('data', {}).get('model', 'Unknown')}")
                    print(f"🔋 Battery: {hw_info.get('data', {}).get('battery', 'Unknown')}%")
                
                return True
            else:
                journaling_manager.recordError(f"❌ Failed to connect {transport_type} transport")
                print(f"❌ Failed to connect {transport_type} transport")
                cls._initialized = False
                return False
            
        except Exception as e:
            journaling_manager.recordError(f"Transport initialization error: {e}")
            import traceback
            journaling_manager.recordError(f"Initialization error trace: {traceback.format_exc()}")
            print(f"❌ Error initializing transport: {e}")
            cls._initialized = False
            return False

    @classmethod
    async def _handle_llm_dict(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LLM commands in dict format"""
        try:
            # Process based on action
            action = command.get("action")
            
            if action in ["setup", "reset"]:
                # Direct communication for setup/reset
                bg = cls.get_basal_ganglia()
                comm_task = bg.get_communication_task()
                if not comm_task:
                    return {"status": "error", "message": "Communication task not available"}
                return await comm_task.send_command(command)
                
            elif action == "inference":
                # Inference handling
                bg = cls.get_basal_ganglia()
                prompt = command.get("data", {}).get("delta", "")
                if prompt:
                    return await bg.think(prompt=prompt, stream=False)
                
                # Direct transmission to hardware
                return await cls._send_to_hardware(command)
                
            else:
                return {"status": "error", "message": f"Unknown LLM action: {action}"}
                
        except Exception as e:
            journaling_manager.recordError(f"LLM dict handler error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_system_dict(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system commands in dict format"""
        try:
            # Direct transmission to hardware
            return await cls._send_to_hardware(command)
                
        except Exception as e:
            journaling_manager.recordError(f"System dict handler error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_audio_dict(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle audio commands in dict format"""
        try:
            # Direct transmission to hardware
            return await cls._send_to_hardware(command)
                
        except Exception as e:
            journaling_manager.recordError(f"Audio dict handler error: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    def _get_transport(cls):
        """Get the current transport instance, initializing if needed"""
        if not cls._transport or not cls._initialized:
            journaling_manager = SystemJournelingManager()
            journaling_manager.recordDebug("Transport not initialized or missing, initializing now...")
            # Import here to avoid circular imports
            from .transport_layer import get_transport
            
            # Create a new transport with the current connection type (or default to tcp)
            connection_type = cls._connection_type or "tcp"
            cls._transport = get_transport(connection_type)
            
        return cls._transport
        
    @classmethod
    async def _send_to_hardware(cls, command: Union[Dict[str, Any], str], stream_callback=None) -> Dict[str, Any]:
        """Send a command directly to hardware transport layer"""
        try:
            # Basic validation
            if command is None:
                journaling_manager.recordError("Cannot send None command to hardware")
                return {"error": {"code": -1, "message": "Invalid command (None)"}}
                
            # Make sure we have a transport
            transport = cls._get_transport()
            if not transport:
                journaling_manager.recordError("Hardware transport not available")
                return {"error": {"code": -1, "message": "Hardware transport not available"}}
                
            # Check for proper connection
            if not transport.connected:
                # Try to initialize and connect if needed
                journaling_manager.recordInfo("Transport not connected, trying to connect...")
                
                # Initialize transport if not already done
                if not cls._initialized or not cls._transport:
                    journaling_manager.recordInfo("Transport not initialized, initializing now...")
                    
                    # Make sure we have a connection type
                    if cls._connection_type is None:
                        journaling_manager.recordError("No connection type specified")
                        return {"error": {"code": -1, "message": "No connection type specified"}}
                        
                    # Try to initialize
                    init_result = await cls.initialize(cls._connection_type)
                    if not init_result:
                        journaling_manager.recordError("Failed to initialize transport")
                        return {"error": {"code": -1, "message": "Failed to initialize transport"}}
                        
                    # Refresh transport reference
                    transport = cls._get_transport()
                    
                # Connect if we have a transport but it's not connected
                if transport and not transport.connected:
                    connect_result = await transport.connect()
                    if not connect_result:
                        journaling_manager.recordError("Failed to connect transport")
                        return {"error": {"code": -1, "message": "Failed to connect transport"}}
            
            # Convert BaseCommand to dict if needed
            safe_command = cls._to_dict_safely(command)
            
            # Log the command (truncated for large commands)
            log_cmd = json.dumps(safe_command)
            if len(log_cmd) > 500:
                journaling_manager.recordDebug(f"Sending command (truncated): {log_cmd[:500]}...")
            else:
                journaling_manager.recordDebug(f"Sending command: {log_cmd}")
            
            # Transmit command through transport
            try:
                # Check if we're in streaming mode
                if stream_callback:
                    # Use the transport's stream method if available
                    if hasattr(transport, 'stream') and callable(getattr(transport, 'stream')):
                        journaling_manager.recordInfo("Using transport's streaming capability")
                        response = await transport.stream(safe_command, stream_callback)
                    else:
                        # Fallback to regular transmit if streaming not available
                        journaling_manager.recordWarning("Transport doesn't support streaming, falling back to regular transmit")
                        response = await transport.transmit(safe_command)
                else:
                    # Standard non-streaming command
                    response = await transport.transmit(safe_command)
                
                # Special verbose logging for LLM inference responses
                if isinstance(command, dict) and command.get("work_id") == "llm" and command.get("action") == "inference":
                    print("\n=== LLM INFERENCE RESPONSE ===")
                    print(json.dumps(response, indent=2))
                    print("===============================\n")
                
                # Log response (truncate if too large)
                if not stream_callback:  # Don't log the response for streaming commands as it's handled by the callback
                    resp_str = json.dumps(response) if response else "None"
                    log_resp = resp_str[:200] + "..." if len(resp_str) > 200 else resp_str
                    journaling_manager.recordInfo(f"Received from hardware: {log_resp}")
                
                return response or {"error": {"code": -1, "message": "Empty response from hardware"}}
            except Exception as e:
                    journaling_manager.recordError(f"Transport transmission error: {e}")
                    return {
                        "error": {
                            "code": -1,
                            "message": f"Transport error: {str(e)}"
                        }
                    }
        except Exception as e:
            journaling_manager.recordError(f"Error sending to hardware: {e}")
            import traceback
            journaling_manager.recordError(f"Hardware send error trace: {traceback.format_exc()}")
            return {
                "error": {
                    "code": -1,
                    "message": f"Hardware communication error: {str(e)}"
                }
            }

    @classmethod
    async def cleanup(cls) -> None:
        """Clean up resources before shutdown
        
        This replaces functionality previously in SynapticPathways
        """
        try:
            # Clean up transport
            if cls._transport:
                journaling_manager.recordInfo(f"Cleaning up {cls._connection_type} transport...")
                try:
                    await cls._transport.disconnect()
                except Exception as e:
                    journaling_manager.recordError(f"Error during transport cleanup: {e}")
            
            # Reset state
            cls._transport = None
            cls._initialized = False
            cls._connection_type = None
            
            journaling_manager.recordInfo("Bridge resources cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error during bridge cleanup: {e}")
            import traceback
            journaling_manager.recordError(f"Cleanup error trace: {traceback.format_exc()}")

    @classmethod
    async def debug_transport(cls) -> Dict[str, Any]:
        """Debug transport setup and configuration
        
        This method is used to diagnose transport initialization issues
        """
        try:
            from .transport_layer import get_transport
            
            # Log the current state
            journaling_manager.recordInfo("===== TRANSPORT LAYER DEBUG =====")
            journaling_manager.recordInfo(f"Connection type: {cls._connection_type}")
            journaling_manager.recordInfo(f"Initialized: {cls._initialized}")
            journaling_manager.recordInfo(f"Transport object exists: {cls._transport is not None}")
            
            # Test creation of each transport type
            for transport_type in ["tcp", "serial", "adb"]:
                try:
                    journaling_manager.recordInfo(f"Testing creation of {transport_type} transport...")
                    transport = get_transport(transport_type)
                    journaling_manager.recordInfo(f"✅ Successfully created {transport_type} transport: {transport}")
                    
                    # Test available method
                    is_available = transport.is_available()
                    journaling_manager.recordInfo(f"{transport_type} is_available(): {is_available}")
                    
                except Exception as e:
                    journaling_manager.recordError(f"❌ Failed to create {transport_type} transport: {e}")
            
            # Try to initialize the specified transport type
            if cls._connection_type:
                try:
                    journaling_manager.recordInfo(f"Testing initialization of {cls._connection_type} transport...")
                    test_transport = get_transport(cls._connection_type)
                    connect_result = await test_transport.connect()
                    journaling_manager.recordInfo(f"Connect result: {connect_result}")
                    
                    if connect_result:
                        # Try a simple ping
                        journaling_manager.recordInfo("Testing ping command...")
                        ping_cmd = {
                            "request_id": f"ping_{int(time.time())}",
                            "work_id": "sys",
                            "action": "ping"
                        }
                        try:
                            # Use transmit method (the correct method name)
                            ping_result = await test_transport.transmit(ping_cmd)
                            journaling_manager.recordInfo(f"Ping result: {ping_result}")
                        except Exception as e:
                            journaling_manager.recordError(f"Ping error: {e}")
                        
                        # Clean up
                        await test_transport.disconnect()
                        
                except Exception as e:
                    journaling_manager.recordError(f"Test initialization error: {e}")
            
            journaling_manager.recordInfo("===== END TRANSPORT DEBUG =====")
            return {"status": "ok", "message": "Transport debug complete. Check logs for details."}
            
        except Exception as e:
            journaling_manager.recordError(f"Transport debug error: {e}")
            import traceback
            journaling_manager.recordError(f"Debug error trace: {traceback.format_exc()}")
            return {"status": "error", "message": f"Transport debug failed: {e}"} 

    @classmethod
    def create_sys_command(cls, action, request_id=None):
        """
        Create a system command in exact API format
        
        Args:
            action: The system action (ping, hwinfo, lsmode, reset, reboot)
            request_id: Optional request ID
            
        Returns:
            dict: Command dictionary formatted per API spec
        """
        if not request_id:
            request_id = f"{int(time.time())}"
            
        return {
            "request_id": request_id,
            "work_id": "sys",
            "action": action
        }
    
    @classmethod
    def create_llm_setup_command(cls, model_name, persona=None, request_id=None):
        """
        Create a command for LLM setup following the exact API format
        
        Args:
            model_name: The model to set up
            persona: Optional system prompt/persona
            request_id: Optional request ID (generated if None)
            
        Returns:
            dict: Properly formatted command
        """
        if request_id is None:
            request_id = str(int(time.time()))
        
        # Get a journaling manager for logging
        journaling_manager = SystemJournelingManager()
        journaling_manager.recordInfo(f"Creating LLM setup command for model: {model_name}")
        
        # Set default persona if not provided
        if persona is None:
            persona = "You are a helpful assistant."
            
        # Create setup command as per API
        setup_command = {
            "request_id": request_id,
            "work_id": "llm",
            "action": "setup",
            "model": model_name,
            "response_format": "llm.utf-8",  # Standard output
            "input": "llm.utf-8",           # UART input
            "enoutput": True,               # Enable UART output
            "enkws": False,                 # No KWS interruption
            "max_token_len": 127,           # Default max token
            "prompt": persona               # System message/persona
        }
        
        # Log the command for debugging
        journaling_manager.recordDebug(f"LLM setup command created: {json.dumps(setup_command)}")
        
        return setup_command
    
    @classmethod
    def create_llm_inference_command(cls, prompt, request_id=None, stream=False, work_id=None):
        """
        Create a command for LLM inference following the exact API format.
        
        For non-streaming, data is a string.
        For streaming, data is an object with delta, index, and finish.
        
        Args:
            prompt: The prompt text
            request_id: Optional request ID (generated if None)
            stream: Whether to use streaming mode
            work_id: Optional specific work_id from setup (e.g., "llm.1003") - if None, uses generic "llm"
            
        Returns:
            dict: Properly formatted command
        """
        # Log the streaming mode being used
        journaling_manager = SystemJournelingManager()
        mode_str = "STREAMING" if stream else "NON-STREAMING"
        journaling_manager.recordInfo(f"🔍 Creating LLM inference command in {mode_str} mode")
        
        if request_id is None:
            request_id = str(int(time.time()))
        
        # Use the provided work_id if available, otherwise default to "llm"
        if work_id is None:
            work_id = "llm"
        
        # Log the work_id being used
        journaling_manager.recordInfo(f"Using work_id: {work_id}")
        
        # Create base command structure
        base_command = {
            "request_id": request_id,
            "work_id": work_id,
            "action": "inference"
        }
        
        if stream:
            # Streaming format
            journaling_manager.recordDebug(f"Using streaming format with data as object (delta, index, finish)")
            # Add streaming-specific fields
            base_command["object"] = "llm.utf-8.stream"
            base_command["data"] = {
                "delta": prompt,
                "index": 0,
                "finish": True
            }
        else:
            # Non-streaming format
            journaling_manager.recordDebug(f"Using non-streaming format with data as string")
            # Add non-streaming specific fields
            base_command["object"] = "llm.utf-8"
            base_command["data"] = prompt
        
        # Log the final command structure for debugging
        journaling_manager.recordDebug(f"Created command: {json.dumps(base_command)}")
        
        return base_command
    
    @classmethod
    async def _direct_reboot(cls) -> Dict[str, Any]:
        """
        Reboot the entire system directly using API format
        
        API format:
        Request: {"request_id": "001", "work_id": "sys", "action": "reboot"}
        Response: {"created": timestamp, "error": {"code": 0, "message": "rebooting ..."}, "request_id": "001", "work_id": "sys"}
        
        Returns:
            Dict with status and response
        """
        from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingLevel
        should_print_debug = journaling_manager.currentLevel == SystemJournelingLevel.DEBUG or journaling_manager.currentLevel == SystemJournelingLevel.SCOPE
        
        if should_print_debug:
            print(f"\n[NeurocorticalBridge._direct_reboot] ⚡ Creating reboot command...")
        
        try:
            # Create properly formatted reboot command per API spec
            reboot_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "reboot"
            }
            
            # Log the command
            journaling_manager.recordInfo(f"📡 Sending system reboot command: {json.dumps(reboot_command)}")
            
            if should_print_debug:
                print(f"[NeurocorticalBridge._direct_reboot] 📦 Command: {json.dumps(reboot_command, indent=2)}")
            
            # Send command
            response = await cls._send_to_hardware(reboot_command)
            
            # Log the response
            journaling_manager.recordInfo(f"📡 Received reboot response: {json.dumps(response)}")
            
            if should_print_debug:
                print(f"[NeurocorticalBridge._direct_reboot] 📊 Response: {json.dumps(response, indent=2)}")
            
            # Process API response
            if isinstance(response, dict) and "error" in response:
                error = response.get("error", {})
                if isinstance(error, dict) and error.get("code") == 0:
                    # API success format
                    success_message = error.get("message", "System reboot initiated")
                    
                    if should_print_debug:
                        print(f"[NeurocorticalBridge._direct_reboot] ✅ Reboot successful: {success_message}")
                    
                    # Note: After reboot, system will disconnect
                    return {
                        "status": "ok",
                        "message": success_message,
                        "response": response
                    }
                else:
                    # API error format
                    error_message = error.get("message", "Unknown error")
                    
                    if should_print_debug:
                        print(f"[NeurocorticalBridge._direct_reboot] ❌ Reboot error: {error_message}")
                    
                    return {
                        "status": "error",
                        "message": f"Reboot failed: {error_message}",
                        "response": response
                    }
            else:
                # Invalid response format
                if should_print_debug:
                    print(f"[NeurocorticalBridge._direct_reboot] ❌ Invalid reboot response format")
                
                return {
                    "status": "error",
                    "message": "Invalid reboot response format",
                    "response": response
                }
                
        except Exception as e:
            journaling_manager.recordError(f"Reboot system error: {e}")
            import traceback
            journaling_manager.recordError(f"Reboot error trace: {traceback.format_exc()}")
            
            if should_print_debug:
                print(f"[NeurocorticalBridge._direct_reboot] ❌ Error: {e}")
                
            return {
                "status": "error",
                "message": f"Reboot error: {str(e)}"
            }

    @classmethod
    def _to_json_string(cls, command):
        """
        Convert a command object to a JSON string
        
        Args:
            command: Command to convert (dict, BaseCommand, or string)
            
        Returns:
            str: JSON string representation of the command
        """
        if isinstance(command, str):
            # Already a string, just return it
            return command
            
        # Convert dict or BaseCommand to a JSON string
        try:
            if hasattr(command, 'to_dict'):
                # BaseCommand objects have to_dict method
                command_dict = command.to_dict()
            elif isinstance(command, dict):
                # Already a dict
                command_dict = command
            else:
                # Try to convert to a dict (may fail)
                command_dict = dict(command)
                
            # Convert to JSON string
            return json.dumps(command_dict)
        except Exception as e:
            journaling_manager = SystemJournelingManager()
            journaling_manager.recordError(f"Error converting command to JSON: {e}")
            # Return an empty JSON object as fallback
            return "{}"

    @classmethod
    async def get_active_llm_tasks(cls) -> Dict[str, Any]:
        """
        Get information about active LLM tasks on the device
        This helps debug when LLM commands aren't working properly
        
        Returns:
            Dict with status and task information
        """
        try:
            # Create a properly formatted command to query LLM tasks
            task_command = {
                "request_id": str(int(time.time())),
                "work_id": "sys",
                "action": "lstasks"
            }
            
            # Log the command being sent
            journaling_manager.recordInfo("🔍 Sending lstasks command to query active LLM tasks")
            print("\n=== ACTIVE LLM TASKS CHECK ===")
            print("Sending task query command:")
            print(json.dumps(task_command, indent=2))
            
            # Send command directly through transport
            task_result = await cls._send_to_hardware(task_command)
            
            # Log the raw response for debugging
            print("\n=== TASK RESPONSE ===")
            print(json.dumps(task_result, indent=2))
            print("=======================\n")
            
            # Process the result
            llm_tasks = []
            active_tasks = []
            
            if isinstance(task_result, dict):
                if "data" in task_result and isinstance(task_result["data"], list):
                    # Filter for LLM related tasks
                    for task in task_result["data"]:
                        if isinstance(task, dict):
                            # Extract task info
                            task_info = {
                                "id": task.get("id", "unknown"),
                                "name": task.get("name", "unknown"),
                                "type": task.get("type", "unknown"),
                                "status": task.get("status", "unknown"),
                                "created": task.get("created", 0)
                            }
                            
                            # Add to the appropriate list
                            active_tasks.append(task_info)
                            
                            # Check if it's LLM related
                            task_name = task.get("name", "").lower()
                            task_type = task.get("type", "").lower()
                            if "llm" in task_name or "llm" in task_type:
                                llm_tasks.append(task_info)
                
                return {
                    "status": "ok",
                    "llm_tasks": llm_tasks,
                    "active_tasks": active_tasks,
                    "raw_response": task_result
                }
            
            return {
                "status": "error",
                "message": "Failed to get task information",
                "raw_response": task_result
            }
            
        except Exception as e:
            journaling_manager.recordError(f"Error getting active LLM tasks: {e}")
            import traceback
            journaling_manager.recordError(f"Task query error trace: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Task query error: {str(e)}"
            }

    @classmethod
    async def test_llm_setup(cls, model_name="qwen2.5-0.5b") -> Dict[str, Any]:
        """
        Test LLM setup with extensive debug logging
        This helps diagnose setup issues by showing all requests and responses
        
        Args:
            model_name: Name of the model to test setup with
            
        Returns:
            Dict with setup test results
        """
        try:
            print("\n====== LLM SETUP DEBUG TEST ======")
            print(f"Testing LLM setup with model: {model_name}")
            
            # 1. Create proper setup command
            setup_command = cls.create_llm_setup_command(
                model_name=model_name,
                persona="You are a helpful assistant."
            )
            
            # Log the setup command
            print("\n--- SETUP COMMAND ---")
            print(json.dumps(setup_command, indent=2))
            
            # 2. Send setup command
            print("\nSending setup command...")
            setup_result = await cls._send_to_hardware(setup_command)
            
            # Log the setup response
            print("\n--- SETUP RESPONSE ---")
            print(json.dumps(setup_result, indent=2))
            
            # 3. Check for active LLM tasks
            print("\nChecking for active LLM tasks...")
            task_result = await cls.get_active_llm_tasks()
            
            # Log task information
            if task_result.get("status") == "ok":
                llm_tasks = task_result.get("llm_tasks", [])
                print(f"\nFound {len(llm_tasks)} LLM-related tasks:")
                for task in llm_tasks:
                    print(f"  - Task {task['id']}: {task['name']} ({task['status']})")
            
            # 4. Try a simple inference test
            print("\nTesting simple inference command...")
            test_prompt = "Hello, this is a test."
            
            # Create inference command
            inference_command = cls.create_llm_inference_command(
                prompt=test_prompt,
                stream=False
            )
            
            # Log the inference command
            print("\n--- TEST INFERENCE COMMAND ---")
            print(json.dumps(inference_command, indent=2))
            
            # Send inference command
            print("\nSending inference command...")
            inference_result = await cls._send_to_hardware(inference_command)
            
            # Log the inference response
            print("\n--- TEST INFERENCE RESPONSE ---")
            print(json.dumps(inference_result, indent=2))
            
            # 5. Summarize test results
            print("\n====== LLM SETUP TEST SUMMARY ======")
            
            # Check setup result
            setup_success = False
            if isinstance(setup_result, dict) and "error" in setup_result:
                error = setup_result.get("error", {})
                if isinstance(error, dict) and error.get("code") == 0:
                    setup_success = True
                    print("✅ LLM Setup: SUCCESS")
                else:
                    error_msg = error.get("message", "Unknown error")
                    print(f"❌ LLM Setup: FAILED - {error_msg}")
            else:
                print("❌ LLM Setup: FAILED - Unexpected response format")
            
            # Check inference result
            inference_success = False
            if isinstance(inference_result, dict) and "error" in inference_result:
                error = inference_result.get("error", {})
                if isinstance(error, dict) and error.get("code") == 0:
                    inference_success = True
                    print("✅ LLM Inference: SUCCESS")
                    if "data" in inference_result:
                        data = inference_result.get("data", "")
                        print(f"   Response: {data[:100]}..." if len(data) > 100 else f"   Response: {data}")
                else:
                    error_msg = error.get("message", "Unknown error")
                    print(f"❌ LLM Inference: FAILED - {error_msg}")
            else:
                print("❌ LLM Inference: FAILED - Unexpected response format")
            
            print("\n====================================")
            
            return {
                "status": "ok" if setup_success and inference_success else "error",
                "setup_success": setup_success,
                "inference_success": inference_success,
                "setup_result": setup_result,
                "inference_result": inference_result,
                "active_tasks": task_result
            }
            
        except Exception as e:
            journaling_manager.recordError(f"LLM setup test error: {e}")
            import traceback
            journaling_manager.recordError(f"Setup test error trace: {traceback.format_exc()}")
            print(f"\n❌ ERROR: {e}")
            print("\n====================================")
            return {
                "status": "error",
                "message": str(e)
            } 

    @classmethod
    async def initialize(cls, connection_type: str) -> bool:
        """Initialize the transport layer"""
        try:
            journaling_manager.recordInfo(f"Initializing {connection_type} transport")
            print(f"🔄 Initializing {connection_type} transport...")
            
            # Store the connection type
            cls._connection_type = connection_type
            
            # Create the transport based on connection type
            if connection_type == "tcp":
                from Mind.Subcortex.transport_layer import WiFiTransport
                cls._transport = WiFiTransport()
                cls._initialized = False  # Will be set based on connect result
            elif connection_type == "embedded":
                from Mind.Subcortex.transport_layer import EmbeddedTransport
                cls._transport = EmbeddedTransport()
                cls._initialized = True  # Embedded is always connected
            elif connection_type == "ble":
                # Future BLE transport
                journaling_manager.recordError("BLE transport not yet implemented")
                return False
            else:
                journaling_manager.recordError(f"Unknown connection type: {connection_type}")
                return False
                
            # For transports that require connection, establish it
            if hasattr(cls._transport, 'connect'):
                # Attempt to connect
                connect_result = await cls._transport.connect()
                
                # Set initialized based on connection result
                cls._initialized = connect_result
                
                # Get firmware/hardware info
                print("📊 Getting device information...")
                hw_info = await cls.get_hardware_info()
                if hw_info and hw_info.get("status") == "ok":
                    print(f"📱 Device connected: {hw_info.get('data', {}).get('model', 'Unknown')}")
                
                # Return success based on connection result
                if connect_result:
                    journaling_manager.recordInfo(f"✅ Successfully connected {connection_type} transport")
                    print(f"✅ Successfully connected {connection_type} transport")
                    return True
                else:
                    journaling_manager.recordError(f"❌ Failed to connect {connection_type} transport")
                    print(f"❌ Failed to connect {connection_type} transport")
                    cls._initialized = False
                    return False
            else:
                # For transports that don't require connection
                journaling_manager.recordInfo(f"✅ Transport initialized: {connection_type}")
                print(f"✅ Transport initialized: {connection_type}")
                cls._initialized = True
                return True
                
        except Exception as e:
            journaling_manager.recordError(f"Error initializing transport: {e}")
            import traceback
            journaling_manager.recordError(f"Initialization error trace: {traceback.format_exc()}")
            print(f"❌ Error initializing transport: {e}")
            cls._initialized = False
            return False