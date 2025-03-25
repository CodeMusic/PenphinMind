"""
Integration area for the Motor Cortex, handling motor control and movement
"""

from typing import Dict, Any
from CorpusCallosum.synaptic_pathways import SynapticPathways
from CorpusCallosum.neural_commands import CommandType, SystemCommand
from config import CONFIG
from .planning_area import PlanningArea
from .coordination_area import CoordinationArea
from .pin_definitions import PinDefinitions

class IntegrationArea:
    """Integration area for motor control"""
    
    def __init__(self):
        self.planning = PlanningArea()
        self.coordination = CoordinationArea()
        self.pins = PinDefinitions()
        
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
            
    async def initialize(self) -> None:
        """Initialize motor components"""
        # Initialize planning and coordination areas
        await self.planning.initialize()
        await self.coordination.initialize() 