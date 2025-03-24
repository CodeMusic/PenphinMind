"""
CorpusCallosum - Neural communication pathways for PenphinOS
"""

from .neural_commands import (
    BaseCommand, CommandType, CommandFactory, CommandSerializer,
    TTSCommand, ASRCommand, VADCommand, LLMCommand, VLMCommand,
    KWSCommand, SystemCommand, AudioCommand, CameraCommand,
    YOLOCommand, WhisperCommand, MeloTTSCommand
)

from .synaptic_pathways import (
    SynapticPathways,
    SerialConnectionError,
    CommandTransmissionError
)

__all__ = [
    'BaseCommand',
    'CommandType',
    'CommandFactory',
    'CommandSerializer',
    'TTSCommand',
    'ASRCommand',
    'VADCommand',
    'LLMCommand',
    'VLMCommand',
    'KWSCommand',
    'SystemCommand',
    'AudioCommand',
    'CameraCommand',
    'YOLOCommand',
    'WhisperCommand',
    'MeloTTSCommand',
    'SynapticPathways',
    'SerialConnectionError',
    'CommandTransmissionError'
] 