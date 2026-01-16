"""
NLP processing module for hybrid scispaCy pipeline.

Provides NLP preprocessing capabilities for statement generation:
- NegationDetector: Detect negation using dependency parsing
- AtomicityAnalyzer: Determine statement split/merge recommendations
- FactCandidateGenerator: Generate structured fact candidates
- NLPPreprocessor: Orchestrate NLP analysis pipeline

Usage:
    from src.processing.nlp import NLPPreprocessor

    preprocessor = NLPPreprocessor()
    artifacts = preprocessor.process(text, "critique")
"""

from .negation_detector import NegationDetector
from .atomicity_analyzer import AtomicityAnalyzer
from .fact_candidate_generator import FactCandidateGenerator
from .preprocessor import NLPPreprocessor

__all__ = [
    "NegationDetector",
    "AtomicityAnalyzer",
    "FactCandidateGenerator",
    "NLPPreprocessor",
]
