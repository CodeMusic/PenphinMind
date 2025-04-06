"""
Slots games module for PenphinMind.
"""

# Import all game classes to make them discoverable
from .base_slots_game import BaseSlotsGame
from .rover_slots import RoverSlots
from .codemusai_slots import CodeMusAISlots
from .penphin_magic_slots import PenphinMagicSlots

# Export the classes
__all__ = [
    'BaseSlotsGame',
    'RoverSlots',
    'CodeMusAISlots',
    'PenphinMagicSlots'
] 