from dataclasses import dataclass
from typing import Dict, List

@dataclass
class TranscriptionResult:
    """Classe pour stocker les résultats de la transcription"""
    text: str
    segments: List[Dict]
    timestamps: List[Dict]
    language: str

@dataclass
class SummaryResult:
    """Classe pour stocker les différents résumés"""
    short: str
    medium: str
    long: str 