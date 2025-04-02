# Mind/Subcortex/BasalGanglia/task_manager.py

import time
import threading
import logging

from .task_base import NeuralTask

class BasalGanglia:
    """
    Central orchestrator for prioritized cognitive and motor tasks.
    Emulates the behavior selection of the biological basal ganglia.
    """

    def __init__(self):
        self.task_queue: list[NeuralTask] = []
        self.running = False
        self.lock = threading.Lock()
        self.log = logging.getLogger("BasalGanglia")

    def register_task(self, task: NeuralTask):
        """
        Add a new task to the queue and sort by priority.
        """
        with self.lock:
            self.task_queue.append(task)
            self.task_queue.sort(key=lambda t: t.priority)
            self.log.info(f"[BasalGanglia] Registered task: {task.describe()}")

    def run_cycle(self):
        """
        One execution cycle: run all active tasks by order of priority.
        """
        with self.lock:
            # Clean up stale tasks BEFORE running the cycle
            self._clean_stale_tasks()
            
            for task in self.task_queue:
                if task.active:
                    self.log.info(f"[BasalGanglia] Running: {task.describe()}")
                    try:
                        task.run()
                    except Exception as e:
                        self.log.error(f"[BasalGanglia] Task failed: {task.name} - {e}")

    def start(self, interval: float = 0.1):
        """
        Begin the continuous execution loop.
        """
        if self.running:
            return

        def loop():
            self.running = True
            self.log.info("[BasalGanglia] Task loop started.")
            while self.running:
                self.run_cycle()
                time.sleep(interval)
            self.log.info("[BasalGanglia] Task loop stopped.")

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()

    def stop(self):
        """
        Gracefully stop the loop.
        """
        self.running = False

    def _clean_stale_tasks(self):
        """Remove stale or completed tasks from the task list."""
        stale_tasks = []
        
        for i, task in enumerate(self.task_queue):
            # Remove tasks that have completed but are still in the queue
            if hasattr(task, "has_completed") and task.has_completed():
                stale_tasks.append(i)
                self.log.info(f"Removing completed task: {task.name}")
                
            # Also remove tasks that have been inactive for too long
            elif not task.active and hasattr(task, 'creation_time'):
                current_time = time.time()
                if (current_time - getattr(task, 'creation_time', 0)) > 300:  # 5 minutes
                    stale_tasks.append(i)
                    self.log.info(f"Removing inactive task: {task.name}")
        
        # Remove the stale tasks in reverse order to avoid index shifting
        for i in sorted(stale_tasks, reverse=True):
            self.task_queue.pop(i)
        
        if stale_tasks:
            self.log.info(f"Cleaned {len(stale_tasks)} stale tasks. {len(self.task_queue)} tasks remaining.")
