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
        
        # System Operations
        "ping": (CommandType.SYSTEM, "ping"),
        "hardware_info": (CommandType.SYSTEM, "hwinfo"),
        "reboot": (CommandType.SYSTEM, "reboot"),
        "debug_transport": (CommandType.SYSTEM, "debug_transport"),
        "set_model": (CommandType.SYSTEM, "set_model"),
        "get_model": (CommandType.SYSTEM, "get_model"),
        "list_models": (CommandType.SYSTEM, "lsmode"),
        "reset_llm": (CommandType.SYSTEM, "reset_llm"),
        "reset_system": (CommandType.SYSTEM, "reset_system"),
        
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
    async def execute_operation(cls, operation: str, data: Dict[str, Any] = None, use_task: bool = None, stream: bool = False):
        try:
            # Special debug for set_model operation
            if operation == "set_model":
                print("\n==================================")
                print("🔍 SET MODEL OPERATION DEBUG")
                print("==================================")
                print(f"• Model: {data.get('model', 'not specified')}")
                print(f"• Connection: {cls._connection_type}")
                print(f"• Initialized: {cls._initialized}")
                if data and 'persona' in data:
                    persona = data.get('persona', '')
                    # Truncate persona for display
                    if len(persona) > 100:
                        persona_display = f"{persona[:50]}...{persona[-50:]}"
                    else:
                        persona_display = persona
                    print(f"• Persona: {persona_display}")
                print(f"• Use task: {use_task}")
                print(f"• Stream: {stream}")
                print("==================================")
            
            # Special debug for hardware_info operation
            if operation == "hardware_info":
                print("\n==================================")
                print("🔍 HARDWARE INFO OPERATION DEBUG")
                print("==================================")
                print(f"• Connection: {cls._connection_type}")
                print(f"• Initialized: {cls._initialized}")
                print(f"• Transport exists: {cls._transport is not None}")
                print("==================================")
                
            # Start debug log for operation execution
            journaling_manager.recordInfo("==================================")
            journaling_manager.recordInfo(f"🛠️ EXECUTING OPERATION: {operation}")
            journaling_manager.recordInfo("==================================")
            journaling_manager.recordInfo(f"• Connection type: {cls._connection_type}")
            journaling_manager.recordInfo(f"• Initialized: {cls._initialized}")
            journaling_manager.recordInfo(f"• Transport exists: {cls._transport is not None}")
            
            # Log data details if present
            if data:
                journaling_manager.recordInfo("• Data parameters:")
                for k, v in data.items():
                    # Truncate long values
                    if isinstance(v, str) and len(v) > 100:
                        v = f"{v[:50]}...{v[-50:]}"
                    journaling_manager.recordInfo(f"  - {k}: {v}")
            
            # Special handling for debug_transport
            if operation == "debug_transport":
                journaling_manager.recordInfo("🔍 Running debug_transport diagnostic...")
                return await cls.debug_transport()
            
            # First ensure transport layer is initialized
            if not cls._initialized:
                journaling_manager.recordInfo("⚠️ Transport not initialized, initializing now...")
                success = await cls._initialize_transport(cls._connection_type or "tcp")
                if not success:
                    journaling_manager.recordError("❌ Failed to initialize transport layer")
                    return {"status": "error", "message": "Failed to initialize transport layer"}
            
            if operation not in cls.OPERATION_MAP:
                journaling_manager.recordError(f"❌ Unknown operation: {operation}")
                return {"status": "error", "message": f"Unknown operation: {operation}"}

            command_type, action = cls.OPERATION_MAP[operation]
            journaling_manager.recordInfo(f"• Command type: {command_type}, Action: {action}")
            
            # Create command using create_command
            # The create_command function now handles CommandType enum conversion
            journaling_manager.recordInfo("🔄 Creating command...")
            command = create_command(
                unit_type=command_type,
                command_name=action,
                data=data or {}
            )
            journaling_manager.recordInfo(f"✅ Command created: {command.get('request_id', 'unknown')}")

            # Special debug for operations - print out the command
            if operation in ["set_model", "hardware_info"]:
                print(f"📦 {operation.upper()} COMMAND: {json.dumps(command, indent=2)}")

            # Determine execution path
            if use_task:
                journaling_manager.recordInfo("🔄 Executing via task system...")
                result = await cls._execute_task(command)
            elif stream:
                journaling_manager.recordInfo("🔄 Executing via stream handler...")
                result = await cls._handle_stream(command)
            else:
                journaling_manager.recordInfo("🔄 Executing via direct execution...")
                result = await cls.execute(command)
            
            # Special post-processing for hardware_info operation
            if operation == "hardware_info" and result and isinstance(result, dict):
                # Check if this is a successful API response with error code 0
                if "error" in result and isinstance(result["error"], dict) and result["error"].get("code") == 0:
                    # Extract data field
                    if "data" in result:
                        # Return in a standardized format
                        return {
                            "status": "ok",
                            "data": result["data"]
                        }
            
            # Special post-processing for list_models operation
            if operation == "list_models" and result and isinstance(result, dict):
                # Check if this is a successful API response with error code 0
                if "error" in result and isinstance(result["error"], dict) and result["error"].get("code") == 0:
                    # Extract data field which contains the model list
                    if "data" in result and isinstance(result["data"], list):
                        # Return in standardized format
                        return {
                            "status": "ok",
                            "response": result["data"]
                        }
                    else:
                        # Data missing or not a list
                        return {
                            "status": "error",
                            "message": "Invalid model list response"
                        }
            
            # Log execution result
            status = result.get("status", "unknown") 
            journaling_manager.recordInfo(f"📋 Operation result: {status}")
            if status != "ok":
                journaling_manager.recordError(f"❌ Error message: {result.get('message', 'No message')}")
            
            # Special debug for operations - print out the result
            if operation in ["set_model", "hardware_info"]:
                print(f"📋 {operation.upper()} RESULT: {json.dumps(result, indent=2)}")
                print("==================================")
            
            journaling_manager.recordInfo("==================================")
            return result

        except Exception as e:
            journaling_manager.recordError(f"❌ Operation execution error: {e}")
            journaling_manager.recordError(f"❌ Stack trace: {traceback.format_exc()}")
            journaling_manager.recordInfo("==================================")
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
    async def _handle_llm_stream(cls, command: Union[LLMCommand, Dict[str, Any]]) -> Dict[str, Any]:
        """Handle LLM streaming operations"""
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Convert LLMCommand to dict if needed
            command_dict = command.to_dict() if isinstance(command, LLMCommand) else command
            
            # Setup streaming
            setup_response = await cls.execute("setup_llm", {
                "response_format": "llm.utf-8.stream",
                "input": "llm.utf-8.stream",
                "enoutput": True,
                "stream": True
            })
            
            if setup_response["status"] != "ok":
                return setup_response
            
            # Send command directly to hardware
            response = await cls._send_to_hardware(command_dict)
            
            # Get work_id from command
            work_id = command_dict.get("work_id", "llm")
            
            # Cleanup after streaming
            await cls.execute("exit_llm", {"work_id": work_id})
            
            return response
            
        except Exception as e:
            journaling_manager.recordError(f"LLM stream error: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def _execute_task(cls, command: BaseCommand) -> Dict[str, Any]:
        """Execute command through task system"""
        try:
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            bg = SynapticPathways.get_basal_ganglia()
            task = bg.get_task(command.work_id)
            
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
            journaling_manager.recordInfo("==================================")
            journaling_manager.recordInfo("📋 COMMAND EXECUTION:")
            journaling_manager.recordInfo("==================================")
            
            # First ensure transport layer is initialized
            if not cls._initialized:
                journaling_manager.recordInfo("⚠️ Transport not initialized in execute method")
                journaling_manager.recordInfo(f"• Connection type: {cls._connection_type}")
                
                if cls._connection_type:
                    journaling_manager.recordInfo(f"🔄 Initializing transport with existing connection type: {cls._connection_type}")
                    success = await cls._initialize_transport(cls._connection_type)
                    if not success:
                        journaling_manager.recordError("❌ Failed to initialize transport")
                        return {"status": "error", "message": f"Failed to initialize transport with {cls._connection_type}"}
                else:
                    journaling_manager.recordWarning("⚠️ No connection type specified, defaulting to TCP")
                    success = await cls._initialize_transport("tcp")
                    if not success:
                        journaling_manager.recordError("❌ Failed to initialize transport with default TCP")
                        return {"status": "error", "message": "Failed to initialize transport with default TCP"}
            
            # Log command type
            if isinstance(command, dict):
                command_type = f"Dict with work_id: {command.get('work_id', 'unknown')}"
                action = command.get('action', 'unknown')
            elif isinstance(command, BaseCommand):
                command_type = command.__class__.__name__
                action = getattr(command, 'action', 'unknown')
            else:
                command_type = type(command).__name__
                action = 'unknown'
            
            journaling_manager.recordInfo(f"• Command type: {command_type}")
            journaling_manager.recordInfo(f"• Action: {action}")
            
            # If command is a dict, process based on its type
            journaling_manager.recordInfo("🔄 Determining execution path...")
            if isinstance(command, dict):
                # Determine command type from command dict
                if "work_id" in command:
                    if command.get("work_id") == "llm":
                        journaling_manager.recordInfo("🧠 Using LLM handler")
                        result = await cls._handle_llm_dict(command)
                    elif command.get("work_id") == "sys":
                        journaling_manager.recordInfo("⚙️ Using System handler")
                        result = await cls._handle_system_dict(command)
                    elif command.get("work_id") in ["audio", "tts", "asr", "vad", "whisper", "kws"]:
                        journaling_manager.recordInfo("🔊 Using Audio handler")
                        result = await cls._handle_audio_dict(command)
                    else:
                        journaling_manager.recordInfo("⚡ Using direct execution")
                        result = await cls._execute_direct(command)
                else:
                    journaling_manager.recordInfo("⚡ Using direct execution (no work_id)")
                    result = await cls._execute_direct(command)
            # Execute through appropriate handler based on command type
            elif isinstance(command, LLMCommand):
                journaling_manager.recordInfo("🧠 Using LLM handler")
                result = await cls._handle_llm_command(command)
            elif isinstance(command, SystemCommand):
                journaling_manager.recordInfo("⚙️ Using System handler")
                result = await cls._handle_system_command(command)
            elif isinstance(command, AudioCommand):
                journaling_manager.recordInfo("🔊 Using Audio handler")
                result = await cls._handle_audio_command(command)
            else:
                journaling_manager.recordError(f"❌ Unknown command type: {type(command)}")
                result = {"status": "error", "message": f"Unknown command type: {type(command)}"}
            
            # Log execution result
            status = result.get("status", "unknown") 
            journaling_manager.recordInfo(f"📋 Command result: {status}")
            if status != "ok":
                journaling_manager.recordError(f"❌ Error: {result.get('message', 'No message')}")
            
            journaling_manager.recordInfo("==================================")
            return result
                
        except Exception as e:
            journaling_manager.recordError(f"❌ Command execution error: {e}")
            journaling_manager.recordError(f"❌ Stack trace: {traceback.format_exc()}")
            journaling_manager.recordInfo("==================================")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _execute_direct(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command directly"""
        try:
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Get BasalGanglia instance
            bg = SynapticPathways.get_basal_ganglia()
            
            # Execute command directly
            comm_task = bg.get_communication_task()
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
            result = await cls._send_to_hardware(command.to_dict())
            
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
            result = await cls._send_to_hardware(command.to_dict())
            
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
            result = await cls._send_to_hardware(command.to_dict())
            
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
            result = await cls._send_to_hardware(command.to_dict())
            
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Whisper error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _handle_kws(cls, command: AudioCommand) -> Dict[str, Any]:
        """Handle keyword spotting command execution"""
        try:
            # Extract parameters from command
            audio_data = command.data.get("audio_data")
            wake_word = command.data.get("wake_word", "hey penphin")
            
            if not audio_data:
                return {"status": "error", "message": "No audio data provided for KWS"}
                
            # Send command directly to hardware
            journaling_manager.recordInfo(f"[NeurocorticalBridge] Processing KWS request for wake word: {wake_word}")
            result = await cls._send_to_hardware(command.to_dict())
            
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] KWS error: {e}")
            return {"status": "error", "message": str(e)}
    
    @classmethod
    async def _direct_get_model(cls) -> Dict[str, Any]:
        """Get current active model directly without using task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Get communication task
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                return {"success": False, "error": "Communication task not available"}
                
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
                return {"success": True, "model": response.get("data", "")}
            else:
                return {"success": False, "error": "Invalid response format"}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error getting model: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _direct_list_models(cls) -> List[Dict[str, Any]]:
        """Direct model listing without using the task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Create list models request
            list_models_command = {
                "request_id": f"lsmode_{int(time.time())}",
                "work_id": "sys",
                "action": "lsmode"
            }
            
            # Special handling for lsmode to avoid recursion
            # We'll use a direct low-level communication here
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[NeurocorticalBridge] Communication task not available")
                return SynapticPathways.available_models
            
            # Send the command directly via communication task to avoid the recursion loop
            journaling_manager.recordInfo("[NeurocorticalBridge] Using direct communication for lsmode command")
            response = await comm_task.send_command(list_models_command)
            
            if response and isinstance(response, dict) and "data" in response:
                models_data = response["data"]
                if isinstance(models_data, list):
                    # Update shared cache
                    SynapticPathways.available_models = models_data
                    
                    return models_data
                else:
                    journaling_manager.recordError(f"[NeurocorticalBridge] Invalid models data format: {type(models_data)}")
            else:
                journaling_manager.recordError(f"[NeurocorticalBridge] Invalid models response: {response}")
            
            # Return cached models if available
            return SynapticPathways.available_models
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error listing models: {e}")
            return SynapticPathways.available_models
    
    @classmethod
    async def _direct_set_model(cls, model_name: str) -> Dict[str, Any]:
        """Direct model selection without using the task system"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        
        try:
            # Get communication task directly from BasalGanglia
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                journaling_manager.recordError("[NeurocorticalBridge] Communication task not available for set model")
                return {"success": False, "error": "Communication task not available"}
            
            # Create setup command with the selected model
            setup_command = {
                "request_id": f"setup_{int(time.time())}",
                "work_id": "sys",
                "action": "setup",
                "object": "llm.setup",
                "data": {
                    "model": model_name,
                    "response_format": "llm.utf-8.stream", 
                    "input": "llm.utf-8.stream", 
                    "enoutput": True,
                    "enkws": True,
                    "max_token_len": 127,
                    "unit": "llm"
                }
            }
            
            # Send command directly through communication task
            journaling_manager.recordInfo("[NeurocorticalBridge] Sending set model request directly through communication task")
            response = await comm_task.send_command(setup_command)
            
            if response and response.get("error", {}).get("code", 1) == 0:
                # Update default model
                SynapticPathways.default_llm_model = model_name
                return {"success": True, "model": model_name}
            else:
                error_msg = response.get("error", {}).get("message", "Unknown error")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error setting model: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _direct_reset_llm(cls) -> Dict[str, Any]:
        try:
            reset_command = SystemCommand.create_reset_command(
                target="llm",
                request_id=f"reset_{int(time.time())}"
            )
            
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                return {"success": False, "error": "Communication task not available"}
                
            return await comm_task.send_command(reset_command)
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error resetting LLM: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    async def _direct_ping(cls) -> Dict[str, Any]:
        """Direct ping without using the task system"""
        try:
            ping_command = SystemCommand.create_ping_command()
            bg = cls.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                return {"success": False, "error": "Communication task not available"}
            
            return await comm_task.send_command(ping_command)
            
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Ping error: {e}")
            return {"success": False, "error": str(e)}

    @classmethod
    def get_basal_ganglia(cls):
        """Get BasalGanglia instance, avoiding circular imports"""
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        return SynapticPathways.get_basal_ganglia()

    @classmethod
    async def _direct_reset_system(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Handle reset system command directly"""
        try:
            journaling_manager.recordInfo("[NeurocorticalBridge] Handling reset system command")
            
            # Get SystemCommandTask from BasalGanglia
            bg = cls.get_basal_ganglia()
            system_task = bg.get_task("SystemCommandTask")
            
            if not system_task:
                journaling_manager.recordInfo("[NeurocorticalBridge] Creating new SystemCommandTask for reset")
                from Mind.Subcortex.BasalGanglia.tasks.system_command_task import SystemCommandTask
                system_task = SystemCommandTask(command_type="reset")
                bg.register_task(system_task)
            else:
                # Configure existing task
                system_task.command = "reset"
                system_task.data = None
            
            # Execute the task
            journaling_manager.recordInfo("[NeurocorticalBridge] Executing reset command via SystemCommandTask")
            system_task.active = True
            result = await system_task.execute()
            return result
        except Exception as e:
            journaling_manager.recordError(f"[NeurocorticalBridge] Error in reset_system: {e}")
            import traceback
            journaling_manager.recordError(f"[NeurocorticalBridge] Stack trace: {traceback.format_exc()}")
            return {"success": False, "error": str(e)}

    @classmethod
    async def get_hardware_info(cls) -> Dict[str, Any]:
        """Get hardware information from the device"""
        try:
            return await cls.execute("hardware_info")
        except Exception as e:
            journaling_manager.recordError(f"Error getting hardware info: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    async def initialize_system(cls, connection_type: str = None) -> bool:
        """Initialize the entire system, including transport layer
        
        This replaces functionality previously in SynapticPathways
        
        Args:
            connection_type: Type of connection to use (serial, adb, tcp)
            
        Returns:
            bool: Success status
        """
        try:
            journaling_manager.recordInfo(f"[NeurocorticalBridge] initialize_system called with connection_type: {connection_type}")
            
            # Store the connection type even if None
            old_type = cls._connection_type
            cls._connection_type = connection_type
            journaling_manager.recordInfo(f"[NeurocorticalBridge] Connection type changed: {old_type} -> {connection_type}")
            
            # Initialize transport layer if a connection type was provided
            if connection_type:
                journaling_manager.recordInfo(f"[NeurocorticalBridge] Initializing transport with {connection_type}")
                success = await cls._initialize_transport(connection_type)
                if not success:
                    journaling_manager.recordError(f"Failed to initialize transport with {connection_type}")
                    return False
                
                cls._initialized = True
                journaling_manager.recordInfo(f"System initialized with {connection_type} connection")
            else:
                journaling_manager.recordInfo("[NeurocorticalBridge] No connection type provided, deferring transport initialization")
                # We'll initialize on first command
            
            # Initialize other components or settings here if needed
            
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"System initialization error: {e}")
            import traceback
            journaling_manager.recordError(f"Initialization stack trace: {traceback.format_exc()}")
            return False

    @classmethod
    async def _initialize_transport(cls, connection_type: str) -> bool:
        """Initialize transport layer
        
        Args:
            connection_type: Type of connection to use
        
        Returns:
            bool: Success status
        """
        try:
            from Mind.Subcortex.transport_layer import get_transport
            from Mind.config import CONFIG
            
            # Log all connection variables for debugging
            journaling_manager.recordInfo("==================================")
            journaling_manager.recordInfo("🔍 TRANSPORT INITIALIZATION DEBUG:")
            journaling_manager.recordInfo("==================================")
            journaling_manager.recordInfo(f"• Connection Type: {connection_type}")
            journaling_manager.recordInfo(f"• Previously initialized: {cls._initialized}")
            journaling_manager.recordInfo(f"• Previous transport exists: {cls._transport is not None}")
            
            # Log config values
            journaling_manager.recordInfo(f"• Config llm_service.ip: {CONFIG.llm_service.get('ip', 'not set')}")
            journaling_manager.recordInfo(f"• Config llm_service.port: {CONFIG.llm_service.get('port', 'not set')}")
            journaling_manager.recordInfo(f"• Config adb_path: {getattr(CONFIG, 'adb_path', 'not set')}")
            
            # Save connection type
            old_connection_type = cls._connection_type
            cls._connection_type = connection_type
            journaling_manager.recordInfo(f"• Connection type changed: {old_connection_type} → {connection_type}")
            
            # Log connection attempt
            journaling_manager.recordInfo(f"🔌 Initializing {connection_type} transport...")
            
            # Get transport instance
            cls._transport = get_transport(connection_type)
            if not cls._transport:
                journaling_manager.recordError(f"❌ Failed to get transport for {connection_type}")
                return False
            
            journaling_manager.recordInfo(f"✅ Transport object created: {cls._transport.__class__.__name__}")
            journaling_manager.recordInfo(f"🧪 Testing if transport is available...")
            is_available = cls._transport.is_available()
            journaling_manager.recordInfo(f"🔍 Transport available: {is_available}")
            
            # Connect transport
            journaling_manager.recordInfo(f"🔌 Connecting to transport...")
            success = await cls._transport.connect()
            
            if not success:
                journaling_manager.recordError(f"❌ Failed to connect {connection_type} transport")
                return False
            
            # Log connection details
            if hasattr(cls._transport, "endpoint"):
                journaling_manager.recordInfo(f"✅ Connected to endpoint: {cls._transport.endpoint}")
            
            # Set initialized flag
            cls._initialized = True    
            journaling_manager.recordInfo(f"✅ Successfully initialized {connection_type} transport")
            journaling_manager.recordInfo("==================================")
            return True
            
        except Exception as e:
            journaling_manager.recordError(f"❌ Transport initialization error: {e}")
            import traceback
            journaling_manager.recordError(f"❌ Stack trace: {traceback.format_exc()}")
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
    async def _send_to_hardware(cls, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send command directly to hardware through transport layer
        
        This method handles the direct hardware communication.
        SynapticPathways should NOT do this - it should only relay to the bridge.
        
        Args:
            command: Command dictionary to send
            
        Returns:
            Dict[str, Any]: Response from hardware
        """
        try:
            # Import here to avoid circular imports
            from .transport_layer import get_transport
            
            # Log detailed command execution information - always print this regardless of log level
            print("\n==================================")
            print("🚀 HARDWARE COMMAND EXECUTION:")
            print("==================================")
            
            # Check if we have an initialized transport
            print(f"• Transport state: initialized={cls._initialized}, type={cls._connection_type}")
            print(f"• Transport object exists: {cls._transport is not None}")
            print(f"• Command: {command.get('action', 'unknown')} (work_id: {command.get('work_id', 'unknown')})")
            
            # Get transport if needed (we'll store it on first use)
            if not cls._transport or not cls._initialized:
                # If connection_type is None, default to "tcp"
                if cls._connection_type is None:
                    print("⚠️ No connection type specified, defaulting to TCP")
                    cls._connection_type = "tcp"
                
                print(f"🔄 Creating new transport for {cls._connection_type}")
                cls._transport = get_transport(cls._connection_type)
                
                # Initialize transport if not already connected
                if not cls._initialized or not cls._transport:
                    print(f"🔌 Initializing transport: {cls._connection_type}")
                    success = await cls._initialize_transport(cls._connection_type)
                    if not success:
                        print(f"❌ Failed to initialize transport with {cls._connection_type}")
                        return {"status": "error", "message": f"Failed to initialize transport with {cls._connection_type}"}
                
            if not cls._transport:
                print("❌ Transport not initialized - unable to create transport instance")
                return {"status": "error", "message": "Transport not initialized - unable to create transport instance"}
            
            # Log the command in full detail
            print("📦 COMMAND DETAILS:")
            print(f"• Request ID: {command.get('request_id', 'not set')}")
            print(f"• Work ID: {command.get('work_id', 'not set')}")
            print(f"• Action: {command.get('action', 'not set')}")
            print(f"• Object: {command.get('object', 'not set')}")
            
            if 'data' in command and command['data'] and isinstance(command['data'], dict):
                print("• Data:")
                for k, v in command['data'].items():
                    # Truncate long values
                    if isinstance(v, str) and len(v) > 100:
                        v = f"{v[:50]}...{v[-50:]}"
                    print(f"  - {k}: {v}")
            
            # Log the full raw JSON that will be sent - always print regardless of log level
            raw_json = json.dumps(command, indent=2)
            print("📤 RAW JSON REQUEST:")
            print(raw_json)
            
            # Use the transport's transmit method (correct method name)
            try:
                print("🔄 Transmitting command via transport...")
                start_time = time.time()
                
                # The transport expects a Dict[str, Any] or already formatted JSON string
                if isinstance(command, str):
                    print("⚠️ Command is string, converting to JSON...")
                    response = await cls._transport.transmit(json.loads(command))
                else:
                    print("✅ Sending command as dictionary...")
                    response = await cls._transport.transmit(command)
                
                # Log timing and detailed response
                elapsed = time.time() - start_time
                print(f"⏱️ Command completed in {elapsed:.2f} seconds")
                
                # Log the full raw JSON that was received - always print regardless of log level
                if response:
                    raw_response = json.dumps(response, indent=2)
                    print("🐧 RAW JSON RESPONSE 🐬:")
                    print(raw_response)
                else:
                    print("⚠️ Empty or null response received")
                
                # Log response details
                print("📦 RESPONSE DETAILS:")
                if response:
                    if isinstance(response, dict):
                        error = response.get('error', {})
                        if isinstance(error, dict):
                            print(f"• Status: {error.get('code', 'not found')}")
                            print(f"• Message: {error.get('message', 'not found')}")
                        else:
                            print(f"• Error: {error}")
                        
                        # Log data if present but truncate if too large
                        if 'data' in response:
                            data_str = str(response['data'])
                            if len(data_str) > 200:
                                data_str = f"{data_str[:100]}...{data_str[-100:]}"
                            print(f"• Data: {data_str}")
                    else:
                        print(f"• Non-dictionary response: {type(response)}")
                        print(f"• Content: {response}")
                else:
                    print("⚠️ Empty response received")
                
                print("==================================")
                
                # Still use journaling manager to record the information in case it's needed
                journaling_manager.recordInfo("Command transmission completed")
                
                return response
                
            except Exception as e:
                print(f"❌ Transport transmit error: {e}")
                print(f"❌ Stack trace: {traceback.format_exc()}")
                print("==================================")
                return {"status": "error", "message": f"Transport transmit error: {e}"}
            
        except Exception as e:
            print(f"❌ Hardware communication error: {e}")
            print(f"❌ Stack trace: {traceback.format_exc()}")
            print("==================================")
            return {"status": "error", "message": str(e)}

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