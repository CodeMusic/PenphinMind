# PenphinMind/Mind/Subcortex/BasalGanglia/task_base.py

from abc import ABC, abstractmethod
from typing import Optional, Any

class NeuralTask(ABC):
    """
    Base class for all neuro-behavioral tasks in the Basal Ganglia system.

    Symbolically represents a neural intent or behavior unit with a lifecycle.
    """

    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority  # Lower number = higher priority
        self.active = False       # Whether the task is currently running
        self.result: Optional[Any] = None  # Optional return value from task
        self._has_run = False     # Internal flag for single-run tasks

    @abstractmethod
    def run(self) -> None:
        """
        Core logic of the task.
        Subclasses must implement this method.
        """
        pass

    def pause(self) -> None:
        """Symbolic inhibition of task activity."""
        self.active = False

    def resume(self) -> None:
        """Resume active state (used for long-running or streamable tasks)."""
        self.active = True

    def stop(self) -> None:
        """Fully deactivate task and signal completion."""
        self.active = False
        self._has_run = True

    def has_completed(self) -> bool:
        """Return whether the task has fully finished."""
        return self._has_run

    def describe(self) -> str:
        """Return a descriptive string of the task for logging."""
        return f"{self.name} (Priority: {self.priority}, Active: {self.active})"
