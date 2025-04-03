"""
CorpusCallosum - Neural communication pathways for PenphinOS
"""

from ..Subcortex.api_commands import (
    create_command,
    parse_response,
    SYSTEM_COMMANDS,
    LLM_COMMANDS,
    AUDIO_COMMANDS,
    ASR_COMMANDS,
    TTS_COMMANDS
)

from .synaptic_pathways import (
    SynapticPathways,
    SerialConnectionError,
    CommandTransmissionError
)

__all__ = [
    'create_command',
    'parse_response',
    'SYSTEM_COMMANDS',
    'LLM_COMMANDS',
    'AUDIO_COMMANDS',
    'ASR_COMMANDS',
    'TTS_COMMANDS',
    'SynapticPathways',
    'SerialConnectionError',
    'CommandTransmissionError'
] 