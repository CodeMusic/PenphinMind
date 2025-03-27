"""
system_journeling_manager.py

A psychologically inspired logging (journaling) system that supports four levels:
ERROR, INFO, DEBUG, and SCOPE.

'SCOPE' logs every method call (with parameters) plus all lower-level messages.
"""

from enum import Enum
from typing import Union, Any

class SystemJournelingLevel(Enum):
    """
    Describes the log detail level for system journaling.
    """
    ERROR = 1  # Only show errors
    INFO = 2   # Show info + error
    DEBUG = 3  # Show debug + info + error
    SCOPE = 4  # Show scope-based method calls + debug + info + error

    @classmethod
    def from_string(cls, level_str: str) -> 'SystemJournelingLevel':
        """
        Convert a string to a SystemJournelingLevel.
        Raises ValueError if the string is not a valid level.
        """
        try:
            return cls[level_str.upper()]
        except KeyError:
            valid_levels = [level.name for level in cls]
            raise ValueError(f"Invalid log level: {level_str}. Must be one of {valid_levels}")

class SystemJournelingManager:
    """
    A psychology-inspired journaling manager that provides multi-level logging.
    """

    def __init__(self, level: Union[str, SystemJournelingLevel] = SystemJournelingLevel.ERROR):
        """
        Initialize with a chosen journaling level.
        Default is ERROR to ensure critical issues are always logged.
        
        Args:
            level: Either a SystemJournelingLevel enum value or a string representing the level
        """
        if isinstance(level, str):
            level = SystemJournelingLevel.from_string(level)
        elif not isinstance(level, SystemJournelingLevel):
            raise ValueError(f"Invalid log level: {level}. Must be a SystemJournelingLevel enum value or string.")
            
        self.currentLevel = level
        self.recordDebug(f"SystemJournelingManager initialized with level: {level.name}")

    def setLevel(self, newLevel: Union[str, SystemJournelingLevel]) -> None:
        """
        Update the journaling level at runtime.
        
        Args:
            newLevel: Either a SystemJournelingLevel enum value or a string representing the level
        """
        if isinstance(newLevel, str):
            newLevel = SystemJournelingLevel.from_string(newLevel)
        elif not isinstance(newLevel, SystemJournelingLevel):
            raise ValueError(f"Invalid log level: {newLevel}. Must be a SystemJournelingLevel enum value or string.")
            
        self.currentLevel = newLevel
        self.recordDebug(f"Logging level changed to: {newLevel.name}")

    def getLevel(self) -> SystemJournelingLevel:
        """
        Get the current journaling level.
        """
        return self.currentLevel

    def recordError(self, message: str, exc_info: bool = False) -> None:
        """
        Record an error message if current level is >= ERROR.
        
        Args:
            message: The error message to record
            exc_info: If True, include exception info in the message
        """
        if self.currentLevel.value >= SystemJournelingLevel.ERROR.value:
            if exc_info:
                import traceback
                print(f"[ERROR] ✖  {message}")
                print(traceback.format_exc())
            else:
                print(f"[ERROR] ✖  {message}")

    def recordInfo(self, message: str) -> None:
        """
        Record an informational message if current level is >= INFO.
        """
        if self.currentLevel.value >= SystemJournelingLevel.INFO.value:
            print(f"[INFO]  ℹ  {message}")

    def recordDebug(self, message: str) -> None:
        """
        Record a debug message if current level is >= DEBUG.
        """
        if self.currentLevel.value >= SystemJournelingLevel.DEBUG.value:
            print(f"[DEBUG] ⚙  {message}")

    def recordScope(self, methodName: str, *args: Any, **kwargs: Any) -> None:
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