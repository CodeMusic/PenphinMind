"""
Bicameral Mind Perspective Manager:
    - Manages multiple thinking perspectives
    - Integrates different viewpoints
    - Handles perspective switching
    - Coordinates thought processes
"""

from typing import Dict, Any, Optional
from ...CorpusCallosum.neural_commands import CommandType, LLMCommand
from ...CorpusCallosum.synaptic_pathways import SynapticPathways
from ...FrontalLobe.PrefrontalCortex.system_journeling_manager import SystemJournelingManager

# Initialize journaling manager
journaling_manager = SystemJournelingManager()

class PerspectiveThinkingManager:
    """Manages bicameral mind perspectives"""

    def __init__(self):
        """Initialize the perspective manager"""
        journaling_manager.recordScope("PerspectiveThinkingManager.__init__")
        self.perspectives = {
            "logical": self._logical_perspective,
            "creative": self._creative_perspective,
            "emotional": self._emotional_perspective,
            "intuitive": self._intuitive_perspective
        }
        self.current_perspective = "logical"
        journaling_manager.recordInfo("Perspective manager initialized")

    async def process_thought(self, input_text: str) -> str:
        """
        Process input through multiple perspectives and integrate responses
        """
        journaling_manager.recordScope("PerspectiveThinkingManager.process_thought", input_text=input_text)
        perspective_responses = {}
        
        for perspective_name, perspective_func in self.perspectives.items():
            journaling_manager.recordDebug(f"Processing through {perspective_name} perspective")
            response = await perspective_func(input_text)
            perspective_responses[perspective_name] = response
            journaling_manager.recordDebug(f"{perspective_name} perspective response: {response}")

        # Log the multi-perspective processing
        journaling_manager.recordInfo(f"Completed multi-perspective analysis for: {input_text}")

        return self._integrate_perspectives(perspective_responses)

    async def _logical_perspective(self, input_text: str) -> str:
        """
        Process input with logical, structured thinking
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._logical_perspective", input_text=input_text)
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=f"Analyze this logically: {input_text}",
            max_tokens=150,
            temperature=0.3
        )
        response = await SynapticPathways.transmit_json(command)
        return response.get("response", "")

    async def _creative_perspective(self, input_text: str) -> str:
        """
        Process input with creative, lateral thinking
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._creative_perspective", input_text=input_text)
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=f"Think creatively about: {input_text}",
            max_tokens=150,
            temperature=0.8
        )
        response = await SynapticPathways.transmit_json(command)
        return response.get("response", "")

    async def _emotional_perspective(self, input_text: str) -> str:
        """
        Process input with emotional intelligence
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._emotional_perspective", input_text=input_text)
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=f"Consider the emotional aspects of: {input_text}",
            max_tokens=150,
            temperature=0.6
        )
        response = await SynapticPathways.transmit_json(command)
        return response.get("response", "")

    async def _intuitive_perspective(self, input_text: str) -> str:
        """
        Process input with intuitive thinking
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._intuitive_perspective", input_text=input_text)
        command = LLMCommand(
            command_type=CommandType.LLM,
            prompt=f"Consider this from an intuitive perspective: {input_text}",
            max_tokens=150,
            temperature=0.7
        )
        response = await SynapticPathways.transmit_json(command)
        return response.get("response", "")

    def _integrate_perspectives(self, responses: Dict[str, str]) -> str:
        """
        Integrate responses from different perspectives
        """
        journaling_manager.recordScope("PerspectiveThinkingManager._integrate_perspectives", responses=responses)
        try:
            # Combine responses with perspective labels
            integrated = []
            for perspective, response in responses.items():
                integrated.append(f"{perspective.capitalize()} perspective: {response}")
            
            result = "\n\n".join(integrated)
            journaling_manager.recordDebug(f"Integrated perspectives result: {result}")
            return result
            
        except Exception as e:
            journaling_manager.recordError(f"Error integrating perspectives: {e}")
            return "Error integrating different perspectives" 