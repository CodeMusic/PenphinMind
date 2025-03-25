"""
system_journeling_manager.py

A psychologically inspired logging (journaling) system that supports four levels:
ERROR, INFO, DEBUG, and SCOPE.

'SCOPE' logs every method call (with parameters) plus all lower-level messages.
"""

from enum import Enum

class SystemJournelingLevel(Enum):
    """
    Describes the log detail level for system journaling.
    """
    ERROR = 1  # Only show errors
    INFO = 2   # Show info + error
    DEBUG = 3  # Show debug + info + error
    SCOPE = 4  # Show scope-based method calls + debug + info + error

class SystemJournelingManager:
    """
    A psychology-inspired journaling manager that provides multi-level logging.
    """

    def __init__(self, level=SystemJournelingLevel.ERROR):
        """
        Initialize with a chosen journaling level.
        """
        self.currentLevel = level

    def setLevel(self, newLevel):
        """
        Update the journaling level at runtime.
        """
        self.currentLevel = newLevel

    def recordError(self, message):
        """
        Record an error message if current level is >= ERROR.
        """
        if self.currentLevel.value >= SystemJournelingLevel.ERROR.value:
            print(f"[ERROR] ✖  {message}")

    def recordInfo(self, message):
        """
        Record an informational message if current level is >= INFO.
        """
        if self.currentLevel.value >= SystemJournelingLevel.INFO.value:
            print(f"[INFO]  ℹ  {message}")

    def recordDebug(self, message):
        """
        Record a debug message if current level is >= DEBUG.
        """
        if self.currentLevel.value >= SystemJournelingLevel.DEBUG.value:
            print(f"[DEBUG] ⚙  {message}")

    def recordScope(self, methodName, *args, **kwargs):
        """
        Record a scope-level method call if current level is >= SCOPE.
        Displays the method name and parameters for deeper psychological insight.
        """
        if self.currentLevel.value >= SystemJournelingLevel.SCOPE.value:
            print(f"[SCOPE] ⚗  Method: {methodName}, Args: {args}, Kwargs: {kwargs}")


# Example usage (remove or edit this when integrating):
if __name__ == "__main__":
    journalingManager = SystemJournelingManager(SystemJournelingLevel.ERROR)

    journalingManager.recordError("This is an error message.")
    journalingManager.recordInfo("An informational update.")
    journalingManager.recordDebug("Some debug details.")
    journalingManager.recordScope("fakeMethod", 123, user="Alice")

    # Elevate the log level to SCOPE for full insight
    journalingManager.setLevel(SystemJournelingLevel.SCOPE)
    journalingManager.recordScope("anotherFakeMethod", "testParam", debug=True)
    journalingManager.recordDebug("Debug message at SCOPE level.")
    journalingManager.recordInfo("Info message at SCOPE level.")
    journalingManager.recordError("Error message at SCOPE level.") 