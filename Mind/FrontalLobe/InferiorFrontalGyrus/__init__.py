"""
Inferior Frontal Gyrus package containing language processing components:
- Broca's Area (language production)
- Wernicke's Area (language comprehension)
- LLM (core language model)
"""

from .llm import LLM
from .broca_area import BrocaArea
from .wernicke_area import WernickeArea

__all__ = ['LLM', 'BrocaArea', 'WernickeArea'] 