import json
from typing import Optional, Dict, Any
from CorpusCallosum.neural_commands import NeuralCommands
from CorpusCallosum.synaptic_pathways import SynapticPathways

class SpeechManager:
    def __init__(self):
        self.listening = False
        self._initialize_neural_pathway()

    def _initialize_neural_pathway(self):
        """
        Initialize connection to neural pathway for JSON communication
        """
        try:
            SynapticPathways.initialize()
        except Exception as e:
            print(f"Error establishing neural pathway: {e}")
            raise

    def start_recording(self):
        """
        Start recording audio via JSON command
        """
        try:
            SynapticPathways.transmit_json(NeuralCommands.STT_START)
            self.listening = True
            print("Recording... Speak now")
        except Exception as e:
            print(f"Error in neural transmission: {e}")
            raise

    def stop_recording(self):
        """
        Stop recording and return transcribed text
        """
        if not self.listening:
            return "No audio recorded"
            
        try:
            response = SynapticPathways.transmit_json(NeuralCommands.STT_STOP)
            result = json.loads(response)
            print(f"You said: {result['text']}")
            return result['text']
        except Exception as e:
            return f"Error processing audio: {e}"
        finally:
            self.listening = False