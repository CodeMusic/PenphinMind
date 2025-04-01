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
