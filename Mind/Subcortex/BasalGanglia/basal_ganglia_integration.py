import logging
from typing import Optional, Dict, Any
import asyncio
import time
import traceback

from Mind.Subcortex.BasalGanglia.task_manager import BasalGanglia
from Mind.Subcortex.BasalGanglia.tasks.think_task import ThinkTask
from Mind.Subcortex.BasalGanglia.tasks.system_command_task import SystemCommandTask
from Mind.Subcortex.BasalGanglia.tasks.display_visual_task import DisplayVisualTask
from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask
from Mind.Subcortex.BasalGanglia.tasks.hardware_info_task import HardwareInfoTask
from Mind.Subcortex.BasalGanglia.tasks.model_management_task import ModelManagementTask
from Mind.Subcortex.BasalGanglia.tasks.cortex_communication_task import CortexCommunicationTask
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class BasalGangliaIntegration:
    """Integration class for Basal Ganglia task system"""
    
    def __init__(self):
        """Initialize the basal ganglia integration."""
        self._tasks = {}
        self._task_history = []  # Keep track of completed tasks
        self._max_tasks = 10  # Maximum number of active tasks
        self._max_history = 20  # Maximum number of tasks to keep in history
        self._last_cleanup = time.time()  # Track when we last cleaned up
        self._cleanup_interval = 60  # Clean up every minute
        self._running = True
        
        # Log initialization
        journaling_manager.recordInfo("[BasalGanglia] 🚀 Initializing BasalGanglia task system")
        
        # Create core tasks
        self._create_core_tasks()
        
        # Start task loop
        self._task_loop = asyncio.create_task(self.task_loop())
        journaling_manager.recordInfo("[BasalGanglia] 🔄 Task loop started")
        
        # Start cleanup task
        asyncio.create_task(self._background_cleanup())
    
    def _create_core_tasks(self):
        """Create and register core tasks."""
        try:
            # Import task classes directly here to avoid circular imports
            from Mind.Subcortex.BasalGanglia.tasks.communication_task import CommunicationTask
            from Mind.Subcortex.BasalGanglia.tasks.hardware_info_task import HardwareInfoTask
            from Mind.Subcortex.BasalGanglia.tasks.system_command_task import SystemCommandTask
            from Mind.Subcortex.BasalGanglia.tasks.model_management_task import ModelManagementTask
            
            # Create and register tasks
            self.add_task(CommunicationTask(priority=1))
            self.add_task(HardwareInfoTask(priority=5))
            self.add_task(SystemCommandTask(priority=3))
            self.add_task(ModelManagementTask(priority=4))
            
            journaling_manager.recordInfo(f"[BasalGanglia] ✅ Core tasks created: {', '.join(self._tasks.keys())}")
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] ❌ Error creating core tasks: {e}")
            import traceback
            journaling_manager.recordError(f"[BasalGanglia] Stack trace: {traceback.format_exc()}")
    
    def add_task(self, task):
        """Add a task to the basal ganglia."""
        self._tasks[task.name] = task
        journaling_manager.recordInfo(f"[BasalGanglia] ➕ Added task: {task.name}")
    
    def get_task(self, task_name):
        """Get a task by name."""
        task = self._tasks.get(task_name)
        if not task:
            journaling_manager.recordWarning(f"[BasalGanglia] ⚠️ Task not found: {task_name}")
        return task
    
    def get_communication_task(self):
        """Get the communication task."""
        return self.get_task("CommunicationTask")
    
    def get_hardware_info_task(self):
        """Get the hardware info task."""
        return self.get_task("HardwareInfoTask")
    
    def get_system_command_task(self):
        """Get the system command task."""
        return self.get_task("SystemCommandTask")
    
    def get_model_management_task(self):
        """Get the model management task."""
        return self.get_task("ModelManagementTask")
    
    async def task_loop(self):
        """Main task execution loop."""
        last_execution = {}
        
        while self._running:
            try:
                current_time = time.time()
                
                # Process tasks
                for task in sorted(self._tasks.values(), key=lambda t: t.priority):
                    if not task.active:
                        continue
                    
                    # Set appropriate intervals
                    interval = 1.0
                    if "HardwareInfoTask" in task.name:
                        interval = 60.0  # Once per minute
                    elif "ModelManagementTask" in task.name:
                        interval = 120.0  # Every 2 minutes
                    elif "SystemCommandTask" in task.name:
                        interval = 0.1  # Systems commands run immediately
                    
                    # Check if it's time to run
                    last_time = last_execution.get(task.name, 0)
                    if current_time - last_time >= interval:
                        try:
                            await task.execute()
                            last_execution[task.name] = current_time
                        except Exception as e:
                            journaling_manager.recordError(f"[BasalGanglia] ❌ Error executing {task.name}: {e}")
                
                # Sleep to prevent CPU spinning
                await asyncio.sleep(0.5)
                
            except Exception as e:
                journaling_manager.recordError(f"[BasalGanglia] ❌ Error in task loop: {e}")
                await asyncio.sleep(1)
    
    def shutdown(self):
        """Shutdown the basal ganglia task system."""
        self._running = False
        if hasattr(self, '_task_loop'):
            self._task_loop.cancel()
        journaling_manager.recordInfo("[BasalGanglia] 🛑 Task system shutdown")

    async def _background_cleanup(self):
        """Background task to periodically clean up stale tasks."""
        while True:
            try:
                # Only clean up every cleanup_interval seconds
                await asyncio.sleep(self._cleanup_interval)
                
                # Don't hold reference to this function in the tasks dict
                self._cleanup_tasks()
            except Exception as e:
                journaling_manager.recordError(f"Error in background cleanup: {e}")
                # Continue running even if there's an error
    
    def _cleanup_tasks(self):
        """Clean up completed and stale tasks."""
        current_time = time.time()
        
        # Track tasks to remove
        tasks_to_remove = []
        
        # Check each task
        for task_id, task in self._tasks.items():
            # 1. Task is inactive and completed - can be removed
            if not task.active and task.has_completed():
                tasks_to_remove.append(task_id)
                
            # 2. Task is inactive for too long - can be removed
            elif not task.active and hasattr(task, 'creation_time'):
                age = current_time - task.creation_time
                if age > 300:  # 5 minutes
                    tasks_to_remove.append(task_id)
            
            # 3. Task has been active for too long - likely hung
            elif task.active and hasattr(task, 'creation_time'):
                age = current_time - task.creation_time
                if age > 600:  # 10 minutes
                    # Force stop the task
                    journaling_manager.recordWarning(f"Force-stopping hung task: {task.name} (ID: {task_id})")
                    task.stop()
                    tasks_to_remove.append(task_id)
        
        # Remove the tasks and add to history
        for task_id in tasks_to_remove:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                # Add to history
                self._task_history.append({
                    "id": task_id,
                    "name": task.name if hasattr(task, "name") else "Unknown",
                    "removed_at": current_time
                })
                # Remove from active tasks
                del self._tasks[task_id]
        
        # Trim history if needed
        if len(self._task_history) > self._max_history:
            self._task_history = self._task_history[-self._max_history:]
        
        # Update last cleanup time
        self._last_cleanup = current_time
        
        # Log cleanup
        if tasks_to_remove:
            journaling_manager.recordInfo(f"Cleaned up {len(tasks_to_remove)} tasks. {len(self._tasks)} active tasks remaining.")
    
    def get_task_count(self):
        """Return the current number of active tasks."""
        return len(self._tasks)
    
    def get_task_stats(self):
        """Return statistics about tasks."""
        active_count = 0
        inactive_count = 0
        
        for task in self._tasks.values():
            if task.active:
                active_count += 1
            else:
                inactive_count += 1
        
        return {
            "active": active_count,
            "inactive": inactive_count,
            "total": len(self._tasks),
            "history": len(self._task_history),
            "last_cleanup": self._last_cleanup
        }
    
    def think(self, prompt, stream=False, priority=5):
        """Register a thinking task and return it.
        
        Args:
            prompt: The prompt to send to the model
            stream: Whether to stream the response
            priority: Task priority (lower is higher)
            
        Returns:
            The ThinkTask instance
        """
        # Clean up tasks before adding a new one
        self._cleanup_tasks()
        
        # Check if we have capacity for a new task
        if len(self._tasks) >= self._max_tasks:
            journaling_manager.recordError(f"Cannot add thinking task: Task system is full ({len(self._tasks)}/{self._max_tasks})")
            return None
        
        from Mind.Subcortex.BasalGanglia.tasks.think_task import ThinkTask
        import time
        
        # Create think task
        task = ThinkTask(prompt=prompt, priority=priority, stream=stream)
        
        # Generate a unique ID for the task
        unique_id = f"think_{id(task)}_{int(time.time())}"
        
        # Add the ID to the task
        task.id = unique_id
        
        # Schedule the task
        self._tasks[task.id] = task
        task.active = True
        
        # Use asyncio.create_task to schedule execution
        asyncio.create_task(self._execute_task(task))
        
        return task
    
    def system_command(self, command_type: str, data: Dict[str, Any] = None, 
                      priority: int = 1) -> SystemCommandTask:
        """Create and register a SystemCommandTask for system operations"""
        journaling_manager.recordScope("[BasalGanglia] Creating SystemCommandTask", command_type=command_type)
        task = SystemCommandTask(command_type=command_type, data=data, priority=priority)
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo(f"[BasalGanglia] Registered SystemCommandTask: {command_type}")
        return task
        
    def display_visual(self, content: str = None, display_type: str = "text", 
                      visualization_type: str = None, visualization_params: dict = None,
                      priority: int = 2) -> DisplayVisualTask:
        """Create and register a DisplayVisualTask for visual output"""
        journaling_manager.recordScope("[BasalGanglia] Creating DisplayVisualTask", 
                                    display_type=display_type, visualization_type=visualization_type)
        task = DisplayVisualTask(
            content=content, 
            display_type=display_type,
            visualization_type=visualization_type,
            visualization_params=visualization_params,
            priority=priority
        )
        self.basal_ganglia.register_task(task)
        
        if visualization_type:
            journaling_manager.recordInfo(f"[BasalGanglia] Registered DisplayVisualTask with visualization: {visualization_type}")
        else:
            journaling_manager.recordInfo(f"[BasalGanglia] Registered DisplayVisualTask with type: {display_type}")
        
        return task
        
    def get_pending_tasks(self) -> int:
        """Get count of pending tasks"""
        count = len([t for t in self.basal_ganglia.task_queue if t.active])
        journaling_manager.recordDebug(f"[BasalGanglia] Pending tasks: {count}")
        return count
        
    def display_llm_pixel_grid(self, initial_content: str = "", 
                              width: int = 64, 
                              height: int = 64,
                              wrap: bool = True,
                              color_mode: str = "grayscale",
                              priority: int = 2) -> DisplayVisualTask:
        """Create and register an LLM token-to-pixel grid visualization task"""
        journaling_manager.recordScope("[BasalGanglia] Creating LLM pixel grid visualization", 
                                    width=width, height=height, color_mode=color_mode)
        task = DisplayVisualTask(
            content=initial_content,
            visualization_type="llm_pixel_grid",
            visualization_params={
                "width": width,
                "height": height,
                "wrap": wrap,
                "color_mode": color_mode
            },
            stream_mode=True,  # This is a streaming task
            priority=priority
        )
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo(f"[BasalGanglia] Registered LLM pixel grid visualization task ({width}x{height})")
        return task

    def display_llm_stream(self, initial_content: str = "", 
                          highlight_keywords: bool = False,
                          keywords: list = None,
                          show_tokens: bool = False,
                          priority: int = 2) -> DisplayVisualTask:
        """Create and register an LLM stream visualization task"""
        journaling_manager.recordScope("[BasalGanglia] Creating LLM stream visualization")
        task = DisplayVisualTask(
            content=initial_content,
            visualization_type="llm_stream",
            visualization_params={
                "highlight_keywords": highlight_keywords,
                "keywords": keywords or [],
                "show_tokens": show_tokens
            },
            stream_mode=True,  # Important: This is a streaming task
            priority=priority
        )
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo("[BasalGanglia] Registered LLM stream visualization task")
        return task

    def initialize_communication(self, connection_type: str) -> bool:
        """Initialize the communication task with specified connection type"""
        comm_task = self.get_communication_task()
        # Run in event loop
        return asyncio.run(comm_task.initialize(connection_type))

    def register_cortex_communication_task(self, source_cortex: str, target_cortex: str, 
                                         data: dict, priority: int = 2) -> 'CortexCommunicationTask':
        """
        Register a task for inter-cortex communication
        
        Args:
            source_cortex: Source cortex name
            target_cortex: Target cortex name
            data: Data to communicate
            priority: Task priority
            
        Returns:
            The registered task
        """
        from Mind.Subcortex.BasalGanglia.tasks.cortex_communication_task import CortexCommunicationTask
        
        task = CortexCommunicationTask(
            source_cortex=source_cortex,
            target_cortex=target_cortex,
            data=data,
            priority=priority
        )
        
        self.basal_ganglia.register_task(task)
        journaling_manager.recordInfo(f"[BasalGanglia] Registered cortex communication task: {source_cortex} → {target_cortex}")
        return task 