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
        self.hardware_info = {
            "cpu_loadavg": "N/A",
            "mem": "N/A",
            "temperature": "N/A",
            "timestamp": 0
        }
        self.last_refresh_time = 0
        self.refresh_interval = 60.0  # Refresh once per minute
        self.active = True  # Make sure it's active by default
        self.first_run = True  # Flag to indicate first run
        
        # Schedule immediate initial refresh
        asyncio.create_task(self._initial_refresh())
        
    async def _initial_refresh(self):
        """Perform immediate initial refresh after a slight delay to ensure connections are ready."""
        await asyncio.sleep(1.0)  # Short delay to let system initialize
        journaling_manager.recordInfo("[HardwareInfoTask] 🔄 Performing initial hardware info refresh")
        
        try:
            # First refresh might fail if connections aren't ready, so try a few times
            for attempt in range(3):
                try:
                    await self._refresh_hardware_info()
                    self.last_refresh_time = time.time()
                    journaling_manager.recordInfo(f"[HardwareInfoTask] ✅ Initial hardware info obtained: {self.hardware_info}")
                    break
                except Exception as e:
                    if attempt < 2:  # Try again if not last attempt
                        journaling_manager.recordWarning(f"[HardwareInfoTask] Initial refresh attempt {attempt+1} failed: {e}")
                        await asyncio.sleep(1.0)  # Wait before retrying
                    else:
                        journaling_manager.recordError(f"[HardwareInfoTask] All initial refresh attempts failed: {e}")
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] Error in initial refresh: {e}")
        
    async def execute(self):
        """Execute the hardware info task."""
        try:
            current_time = time.time()
            
            # Check if it's time to refresh or if it's the first run
            if self.first_run or (current_time - self.last_refresh_time >= self.refresh_interval):
                journaling_manager.recordInfo("[HardwareInfoTask] 🔄 Refreshing hardware info")
                
                # Refresh the hardware info
                await self._refresh_hardware_info()
                self.last_refresh_time = current_time
                self.first_run = False
                
                # Log updated values
                journaling_manager.recordInfo(f"[HardwareInfoTask] ✅ Hardware info updated: {self.hardware_info}")
            
            # Always return the current info (cached or freshly fetched)
            return self.hardware_info
            
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] ❌ Error in execute: {e}")
            import traceback
            journaling_manager.recordError(f"[HardwareInfoTask] Stack trace: {traceback.format_exc()}")
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
            
            # Process response with proper field mapping
            if response and "data" in response:
                api_data = response["data"]
                
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
            else:
                journaling_manager.recordError(f"[HardwareInfoTask] ❌ Invalid API response: {response}")
                
        except Exception as e:
            journaling_manager.recordError(f"[HardwareInfoTask] ❌ Error refreshing hardware info: {e}")
            raise

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