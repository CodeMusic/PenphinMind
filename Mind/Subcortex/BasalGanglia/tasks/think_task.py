# Mind/Subcortex/BasalGanglia/tasks/think_task.py

from Mind.Subcortex.BasalGanglia.task_base import NeuralTask
from Mind.Subcortex.BasalGanglia.task_types import TaskType
from Mind.FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager
import logging

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class ThinkTask(NeuralTask):
    def __init__(self, prompt: str, stream: bool = False, priority: int = 3, 
                visual_task = None):
        super().__init__(name="ThinkTask", priority=priority)
        self.task_type = TaskType.THINK
        self.prompt = prompt
        self.stream = stream
        self.active = True
        self.visual_task = visual_task  # Optional link to a visual task
        self.log = logging.getLogger("ThinkTask")
        # Import LLMManager here instead of at module level
        from Mind.FrontalLobe.PrefrontalCortex.language_processor import LLMManager
        self.llm = LLMManager()
        journaling_manager.recordInfo(f"[BasalGanglia] Created ThinkTask with prompt: {prompt[:50]}...")

    def run(self):
        self.status = "running"
        journaling_manager.recordScope("[BasalGanglia] Running ThinkTask", prompt=self.prompt[:50])

        try:
            if self.stream:
                journaling_manager.recordInfo("[BasalGanglia] Streaming thought response")
                stream_response = self.llm.stream(self.prompt)
                self.result = ""
                for chunk in stream_response:
                    self.result += chunk
                    journaling_manager.recordDebug(f"[BasalGanglia] Streamed chunk: {len(chunk)} chars")
                    
                    # Update visual task if connected
                    if self.visual_task:
                        self.visual_task.update_stream(self.result)
            else:
                journaling_manager.recordInfo("[BasalGanglia] Generating thought response")
                self.result = self.llm.generate(self.prompt)
                journaling_manager.recordDebug(f"[BasalGanglia] Thought completed: {len(self.result)} chars")
                
                # Update visual task if connected
                if self.visual_task:
                    self.visual_task.update_stream(self.result, is_complete=True)
                    
        except Exception as e:
            journaling_manager.recordError(f"[BasalGanglia] Thought failed: {e}")
            self.result = {"error": str(e)}
            
            # Update visual task with error if connected
            if self.visual_task:
                self.visual_task.update_stream(f"Error: {str(e)}", is_complete=True)

        self.stop()  # Task completes after one thought
