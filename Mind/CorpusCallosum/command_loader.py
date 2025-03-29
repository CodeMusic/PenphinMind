"""
Command loader for neural command system
"""

import json
from pathlib import Path
from typing import Dict, Any, Type
from dataclasses import dataclass, field
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
from .command_types import BaseCommand, CommandType

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class CommandLoader:
    """Loader for neural command definitions"""
    
    def __init__(self):
        """Initialize the command loader"""
        journaling_manager.recordScope("CommandLoader.__init__")
        self.command_definitions = self._load_command_definitions()
        
    def _load_command_definitions(self) -> Dict[str, Any]:
        """Load command definitions from JSON file"""
        journaling_manager.recordScope("CommandLoader._load_command_definitions")
        try:
            # Get the path to raw_commands.json
            current_dir = Path(__file__).parent
            json_path = current_dir / "raw_commands.json"
            
            if not json_path.exists():
                journaling_manager.recordError(f"Command definitions file not found: {json_path}")
                raise FileNotFoundError(f"Command definitions file not found: {json_path}")
                
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            # Get command definitions from command_types key
            definitions = data.get("command_types", {})
            journaling_manager.recordDebug(f"Loaded {len(definitions)} command definitions")
            return definitions
            
        except Exception as e:
            journaling_manager.recordError(f"Error loading command definitions: {e}")
            raise
            
    def _create_command_class(self, command_type: str, definition: Dict[str, Any]) -> Type[BaseCommand]:
        """Create a command class from its definition"""
        journaling_manager.recordScope("CommandLoader._create_command_class", command_type=command_type)
        try:
            # Create class attributes
            class_attrs = {
                "__doc__": definition.get("description", f"Command for {command_type}")
            }
            
            # Add parameters from definition
            for param_name, param_def in definition.get("parameters", {}).items():
                param_type = param_def.get("type", "str")
                param_default = param_def.get("default")
                param_description = param_def.get("description", "")
                
                # Map JSON types to Python types
                type_mapping = {
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict
                }
                
                python_type = type_mapping.get(param_type, str)
                
                # Add field with default if specified
                if param_default is not None:
                    class_attrs[param_name] = field(default=param_default, metadata={"description": param_description})
                else:
                    class_attrs[param_name] = field(metadata={"description": param_description})
                    
            # Create the class
            command_class = dataclass(type(f"{command_type.title()}Command", (BaseCommand,), class_attrs))
            journaling_manager.recordDebug(f"Created command class: {command_class.__name__}")
            return command_class
            
        except Exception as e:
            journaling_manager.recordError(f"Error creating command class: {e}")
            raise
            
    def load_commands(self) -> Dict[str, Type[BaseCommand]]:
        """Load all command classes"""
        journaling_manager.recordScope("CommandLoader.load_commands")
        try:
            command_classes = {}
            for command_type, definition in self.command_definitions.items():
                if command_type in CommandType.__members__:
                    command_classes[command_type] = self._create_command_class(command_type, definition)
                else:
                    journaling_manager.recordError(f"Invalid command type in definitions: {command_type}")
                    
            journaling_manager.recordDebug(f"Loaded {len(command_classes)} command classes")
            return command_classes
            
        except Exception as e:
            journaling_manager.recordError(f"Error loading command classes: {e}")
            raise
            
    def get_command_class(self, command_type: str) -> Type[BaseCommand]:
        """Get a command class by type"""
        journaling_manager.recordScope("CommandLoader.get_command_class", command_type=command_type)
        try:
            if command_type not in self.command_definitions:
                journaling_manager.recordError(f"Unknown command type: {command_type}")
                raise ValueError(f"Unknown command type: {command_type}")
                
            if command_type not in CommandType.__members__:
                journaling_manager.recordError(f"Invalid command type: {command_type}")
                raise ValueError(f"Invalid command type: {command_type}")
                
            return self._create_command_class(command_type, self.command_definitions[command_type])
            
        except Exception as e:
            journaling_manager.recordError(f"Error getting command class: {e}")
            raise
            
    def validate_command(self, command_type: str, data: Dict[str, Any]) -> None:
        """Validate command data against its definition"""
        journaling_manager.recordScope("CommandLoader.validate_command", command_type=command_type)
        try:
            if command_type not in self.command_definitions:
                journaling_manager.recordError(f"Unknown command type: {command_type}")
                raise ValueError(f"Unknown command type: {command_type}")
                
            if command_type not in CommandType.__members__:
                journaling_manager.recordError(f"Invalid command type: {command_type}")
                raise ValueError(f"Invalid command type: {command_type}")
                
            definition = self.command_definitions[command_type]
            required_params = {
                name for name, param in definition.get("parameters", {}).items()
                if not param.get("optional", False)
            }
            
            missing_params = required_params - set(data.keys())
            if missing_params:
                journaling_manager.recordError(f"Missing required parameters: {missing_params}")
                raise ValueError(f"Missing required parameters: {missing_params}")
                
            journaling_manager.recordDebug("Command data validated successfully")
            
        except Exception as e:
            journaling_manager.recordError(f"Command validation failed: {e}")
            raise 