# Mind/Subcortex/BasalGanglia/task_types.py

from enum import Enum, auto

class TaskType(Enum):
    """Enumeration of different neural task types"""
    THINKING = auto()                 # Thinking/reasoning tasks using LLM
    SYSTEM_COMMAND = auto()        # System operation commands
    DISPLAY_VISUAL = auto()        # Visual display operations
    SPEECH = auto()                # Speech generation
    LISTEN = auto()                # Audio input processing
    MEMORY = auto()                # Memory operations
    COMMUNICATION = auto()         # Hardware communication tasks
    HARDWARE_INFO = auto()         # Hardware information monitoring
    MODEL_MANAGEMENT = auto()      # Model selection and management
    CORTEX_COMMUNICATION = auto()  # Inter-cortex communication
    DEVICE_CONTROL = auto()        # Device control operations (reboot, etc.)
    INPUT_PROCESSING = auto()      # User input processing
    OUTPUT_FORMATTING = auto()     # Output formatting and presentation
    ERROR_HANDLING = auto()        # Specialized error handling and recovery

class TaskCategory(Enum):
    """
    Broader classification for filtering or analytics.
    """
    COGNITIVE = auto()       # LLM, decision, planning
    SENSORY = auto()         # ASR, KWS
    MOTOR = auto()           # TTS, display, system
    COMMUNICATION = auto()   # Hardware communication tasks
    META = auto()            # Internal state, idle, logging

# Optional: tag mapping
TASK_CATEGORY_MAP = {
    TaskType.THINKING: TaskCategory.COGNITIVE,
    TaskType.SYSTEM_COMMAND: TaskCategory.META,
    TaskType.DISPLAY_VISUAL: TaskCategory.MOTOR,
    TaskType.SPEECH: TaskCategory.MOTOR,
    TaskType.LISTEN: TaskCategory.SENSORY,
    TaskType.MEMORY: TaskCategory.COGNITIVE,
    TaskType.COMMUNICATION: TaskCategory.COGNITIVE,
}
