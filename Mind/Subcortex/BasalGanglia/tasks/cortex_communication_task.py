from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import asyncio
from typing import Dict, Any

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class CortexCommunicationTask(NeuralTask):
    """Task to manage communication between cortices"""
    
    def __init__(self, source_cortex: str, target_cortex: str, 
                data: Dict[str, Any], priority: int = 2):
        """
        Initialize a cortex communication task
        
        Args:
            source_cortex: Source cortex name
            target_cortex: Target cortex name
            data: Data to communicate
            priority: Task priority (lower = higher priority)
        """
        super().__init__(name="CortexCommunicationTask", priority=priority)
        self.task_type = TaskType.CORTEX_COMMUNICATION
        self.source_cortex = source_cortex
        self.target_cortex = target_cortex
        self.data = data
        self.active = True
        self.log = logging.getLogger("CortexCommunicationTask")
        journaling_manager.recordInfo(f"[BasalGanglia] Created CortexCommunicationTask: {source_cortex} → {target_cortex}")
        
    def run(self):
        """Execute the cortex communication task"""
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running CortexCommunicationTask", 
                                    source=self.source_cortex, target=self.target_cortex)
        
        try:
            self.log.info(f"Relaying data from {self.source_cortex} to {self.target_cortex}")
            
            # Create event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Import here to avoid circular imports
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            
            # Use SynapticPathways to relay between cortices
            self.result = loop.run_until_complete(
                SynapticPathways.relay_between_cortices(
                    self.source_cortex,
                    self.target_cortex,
                    self.data
                )
            )
            
            journaling_manager.recordInfo(f"[BasalGanglia] Data relay complete: {self.source_cortex} → {self.target_cortex}")
            
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Error in cortex communication: {e}")
            self.result = {"error": str(e)}
            
        self.stop()  # Communication task completes after one relay 