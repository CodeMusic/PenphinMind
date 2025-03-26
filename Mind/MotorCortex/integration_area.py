"""
Motor Integration Area - Processes and integrates motor commands
"""

import logging
from typing import Dict, Any, Optional
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...CorpusCallosum.neural_commands import CommandType, SystemCommand
from ...config import CONFIG
from .planning_area import PlanningArea
from .coordination_area import CoordinationArea
from .pin_definitions import PinDefinitions

logger = logging.getLogger(__name__)

class IntegrationArea:
    """Processes and integrates motor commands"""
    
    def __init__(self):
        """Initialize the integration area"""
        self._initialized = False
        self._processing = False
        
        # Register with SynapticPathways
        SynapticPathways.register_integration_area("motor", this)
        
        self.planning = PlanningArea()
        self.coordination = CoordinationArea()
        self.pins = PinDefinitions()
        
    async def initialize(self) -> None:
        """Initialize the integration area"""
        if self._initialized:
            return
            
        try:
            # Initialize motor processing components
            self._initialized = True
            logger.info("Motor integration area initialized")
            
            # Initialize planning and coordination areas
            await self.planning.initialize()
            await self.coordination.initialize()
            
        except Exception as e:
            logger.error(f"Failed to initialize motor integration area: {e}")
            raise
            
    async def process_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a motor command"""
        if not self._initialized:
            raise RuntimeError("Integration area not initialized")
            
        if self._processing:
            raise RuntimeError("Already processing a command")
            
        try:
            self._processing = True
            
            # Process command based on type
            command_type = command.get("type")
            if command_type == "MOTOR":
                return await self._process_motor(command)
            else:
                raise ValueError(f"Unknown command type: {command_type}")
                
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {"status": "error", "message": str(e)}
            
        finally:
            self._processing = False
            
    async def _process_motor(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process motor command"""
        try:
            action = command.get("action")
            if action == "MOVE":
                return {"status": "ok", "message": "Motor movement executed"}
            elif action == "STOP":
                return {"status": "ok", "message": "Motor movement stopped"}
            else:
                raise ValueError(f"Unknown motor action: {action}")
                
        except Exception as e:
            logger.error(f"Error processing motor command: {e}")
            return {"status": "error", "message": str(e)}
            
    async def execute_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a movement command"""
        try:
            # Plan the movement
            movement_plan = await self.planning.plan_movement(movement_data)
            
            # Coordinate the execution
            result = await self.coordination.execute_movement_plan(movement_plan)
            
            return result
        except Exception as e:
            raise Exception(f"Error executing movement: {e}")
            
    async def stop_movement(self) -> None:
        """Stop all current movements"""
        try:
            await self.coordination.stop_all_movements()
        except Exception as e:
            raise Exception(f"Error stopping movement: {e}")
            
    async def process_motor_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Process a motor command"""
        try:
            # Plan the command
            command_plan = await self.planning.plan_command(command)
            
            # Execute the command
            result = await self.coordination.execute_command(command_plan)
            
            return result
        except Exception as e:
            raise Exception(f"Error processing motor command: {e}") 