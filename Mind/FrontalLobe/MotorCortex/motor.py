"""
Neurological Function:
    Motor Cortex (M1) handles:
    - Voluntary muscle movements
    - Motor planning
    - Movement execution
    - Fine motor control

Project Function:
    Handles motor control:
    - Movement commands
    - Motor state management
    - Movement coordination
    - Hardware control
"""

import logging
from typing import Dict, Any, Optional
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from config import CONFIG  # Use absolute import
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class Motor:
    """Handles motor control functionality"""
    
    def __init__(self):
        """Initialize the motor controller"""
        journaling_manager.recordScope("Motor.__init__")
        self._initialized = False
        self._processing = False
        self.current_state = {
            "position": {"x": 0, "y": 0},
            "velocity": {"x": 0, "y": 0},
            "acceleration": {"x": 0, "y": 0}
        }
        
    async def initialize(self) -> None:
        """Initialize the motor controller"""
        journaling_manager.recordScope("Motor.initialize")
        if self._initialized:
            journaling_manager.recordDebug("Motor already initialized")
            return
            
        try:
            self._initialized = True
            journaling_manager.recordInfo("Motor controller initialized")
            
        except Exception as e:
            journaling_manager.recordError(f"Failed to initialize motor controller: {e}")
            raise
            
    async def cleanup(self) -> None:
        """Clean up the motor controller"""
        journaling_manager.recordScope("Motor.cleanup")
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Motor not initialized, skipping cleanup")
                return
                
            self._initialized = False
            self._processing = False
            journaling_manager.recordInfo("Motor controller cleaned up")
            
        except Exception as e:
            journaling_manager.recordError(f"Error cleaning up motor controller: {e}")
            raise
            
    async def execute_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a movement command
        
        Args:
            movement_data: Dictionary containing movement parameters
            
        Returns:
            Dict[str, Any]: Movement execution result
        """
        journaling_manager.recordScope("Motor.execute_movement", movement_data=movement_data)
        try:
            if not self._initialized:
                journaling_manager.recordError("Motor controller not initialized")
                raise RuntimeError("Motor controller not initialized")
                
            if self._processing:
                journaling_manager.recordDebug("Movement already in progress")
                return {"status": "busy", "message": "Movement already in progress"}
                
            self._processing = True
            journaling_manager.recordDebug("Starting movement execution")
            
            # Process movement command
            await SynapticPathways.transmit_command({
                "command_type": "motor",
                "operation": "execute",
                "data": movement_data
            })
            
            # Update state
            self.current_state.update(movement_data)
            journaling_manager.recordDebug(f"Updated motor state: {self.current_state}")
            
            self._processing = False
            journaling_manager.recordInfo("Movement executed successfully")
            return {"status": "ok", "message": "Movement executed"}
            
        except Exception as e:
            self._processing = False
            journaling_manager.recordError(f"Error executing movement: {e}")
            return {"status": "error", "message": str(e)}
            
    async def stop_movement(self) -> None:
        """Stop all current movements"""
        journaling_manager.recordScope("Motor.stop_movement")
        try:
            if not self._initialized:
                journaling_manager.recordDebug("Motor not initialized, skipping stop")
                return
                
            if not self._processing:
                journaling_manager.recordDebug("No movement in progress")
                return
                
            # Send stop command
            await SynapticPathways.transmit_command({
                "command_type": "motor",
                "operation": "stop"
            })
            
            # Reset state
            self.current_state = {
                "position": self.current_state["position"],
                "velocity": {"x": 0, "y": 0},
                "acceleration": {"x": 0, "y": 0}
            }
            
            self._processing = False
            journaling_manager.recordInfo("All movements stopped")
            
        except Exception as e:
            journaling_manager.recordError(f"Error stopping movement: {e}")
            raise 