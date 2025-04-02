from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging
import time
import asyncio
from typing import Dict, Any
import psutil
import json

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class HardwareInfoTask(NeuralTask):
    """Task to fetch and monitor hardware information"""
    
    def __init__(self, priority=5):
        """Initialize hardware info task with default values."""
        super().__init__("HardwareInfoTask", priority)
        # Initialize with shared cache values if available
        from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
        self.hardware_info = SynapticPathways.current_hw_info.copy() if hasattr(SynapticPathways, 'current_hw_info') else {
            "cpu_loadavg": "N/A",
            "mem": "N/A",
            "temperature": "N/A",
            "timestamp": 0
        }
        self.last_refresh_time = 0  # Initialize to 0 to force immediate refresh
        self.refresh_interval = 60.0  # Refresh once per minute
        self.active = True
        
        # Schedule immediate initial refresh
        self._schedule_immediate_refresh()
        
        journaling_manager.recordInfo("[HardwareInfoTask] Initialized, scheduled immediate refresh")
        
    def _schedule_immediate_refresh(self):
        """Schedule immediate refresh"""
        asyncio.create_task(self._initial_refresh())
        
    async def _initial_refresh(self):
        """Perform immediate hardware info refresh"""
        try:
            # Small delay to ensure other systems are ready
            await asyncio.sleep(0.5)
            
            # Refresh hardware info
            journaling_manager.recordInfo("[HardwareInfoTask] Performing initial refresh")
            await self._refresh_hardware_info()
            self.last_refresh_time = time.time()
            
            # Update SynapticPathways shared cache
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            SynapticPathways.current_hw_info = self.hardware_info.copy()
            
            journaling_manager.recordInfo(f"[HardwareInfoTask] Initial refresh completed: {self.hardware_info}")
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] Error in initial refresh: {e}")
        
    async def execute(self):
        """Background task to update hardware info every minute."""
        current_time = time.time()
        
        # Check if it's time for a refresh
        if current_time - self.last_refresh_time >= self.refresh_interval:
            journaling_manager.recordInfo("[HardwareInfoTask] 🔄 Performing background refresh")
            
            try:
                await self._refresh_hardware_info()
                self.last_refresh_time = current_time
                journaling_manager.recordInfo(f"[HardwareInfoTask] ✅ Background refresh completed: {self.hardware_info}")
                
                # Make sure to update the shared cache 
                from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
                SynapticPathways.current_hw_info = self.hardware_info.copy()
            except Exception as e:
                journaling_manager.recordError(f"[HardwareInfoTask] ❌ Background refresh error: {e}")
        
        # Return current info without logging every time
        return self.hardware_info
            
    async def _refresh_hardware_info(self):
        """Refresh hardware information from API."""
        try:
            # Get communication task
            from Mind.CorpusCallosum.synaptic_pathways import SynapticPathways
            bg = SynapticPathways.get_basal_ganglia()
            comm_task = bg.get_communication_task()
            
            if not comm_task:
                raise Exception("Communication task not found")
            
            # Create request with exact API format
            hwinfo_command = {
                "request_id": "001",
                "work_id": "sys",
                "action": "hwinfo"
            }
            
            # Send command
            journaling_manager.recordInfo("[HardwareInfoTask] 📤 Requesting hardware info")
            response = await comm_task.send_command(hwinfo_command)
            
            # Fix: Handle the case where response might be a string
            if isinstance(response, str):
                journaling_manager.recordWarning(f"[HardwareInfoTask] Received string response: {response}")
                # Try to parse JSON if possible
                try:
                    import json
                    response = json.loads(response)
                except json.JSONDecodeError:
                    journaling_manager.recordError(f"[HardwareInfoTask] Failed to parse string response as JSON")
                    return False
            
            # Process response with proper field mapping
            if response and isinstance(response, dict) and "data" in response:
                api_data = response["data"]
                
                # Check if api_data is a dictionary
                if not isinstance(api_data, dict):
                    journaling_manager.recordError(f"[HardwareInfoTask] API data is not a dictionary: {type(api_data)}")
                    return False
                
                # Update hardware info with exact field names from API
                self.hardware_info = {
                    "cpu_loadavg": api_data.get("cpu_loadavg", 0),
                    "mem": api_data.get("mem", 0),
                    "temperature": api_data.get("temperature", 0),
                    "timestamp": time.time()
                }
                
                # Update shared cache in SynapticPathways
                SynapticPathways.current_hw_info = self.hardware_info
                
                journaling_manager.recordInfo(f"[HardwareInfoTask] ✅ Hardware info refreshed: {self.hardware_info}")
                return True
            else:
                journaling_manager.recordError(f"[HardwareInfoTask] ❌ Invalid API response: {response}")
                return False
                
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] ❌ Error refreshing hardware info: {e}")
            import traceback
            journaling_manager.recordError(f"[HardwareInfoTask] Stack trace: {traceback.format_exc()}")
            return False

    def run(self):
        """Implementation of abstract method from Task base class."""
        # This synchronous method is required but we'll use async execute instead
        # You can make this a proxy to the async method if needed
        journaling_manager.recordDebug("[BasalGanglia] HardwareInfoTask.run called (using async execute instead)")
        return self.hardware_info

    def _refresh_local_hardware_info(self):
        """Fallback to local hardware info when API fails."""
        try:
            import psutil
            
            # Get CPU, memory, and temperature info locally
            self.hardware_info = {
                "cpu_loadavg": psutil.cpu_percent(),
                "mem": psutil.virtual_memory().percent,
                "temperature": 0,  # No good way to get temperature cross-platform
                "timestamp": time.time(),
                "ip_address": self._get_ip_address() if hasattr(self, "_get_ip_address") else "N/A"
            }
            
            journaling_manager.recordInfo(f"[HardwareInfoTask] Using local hardware info: {self.hardware_info}")
            
        except ImportError:
            journaling_manager.recordWarning("[HardwareInfoTask] psutil not installed - using dummy values")
            self.hardware_info = {
                "cpu_loadavg": 0,
                "mem": 0,
                "temperature": 0,
                "timestamp": time.time(),
                "ip_address": "N/A"
            }

    def _get_ip_address(self):
        """Get the system IP address."""
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] Error getting IP: {e}")
            return "N/A"
    
    def get_hardware_info(self):
        """Return cached hardware info without forcing a refresh"""
        return self.hardware_info
    
    def format_hw_info(self) -> str:
        """Format hardware info for display"""
        hw = self.hardware_info
        
        # Format timestamp as readable time
        timestamp = hw.get("timestamp", 0)
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp)) if timestamp else "N/A"
        
        # Format the hardware info in the requested format
        info_str = f"""~
CPU: {hw.get('cpu_loadavg', 'N/A')} | Memory: {hw.get('mem', 'N/A')} | Updated: {time_str}
~"""
        
        return info_str 