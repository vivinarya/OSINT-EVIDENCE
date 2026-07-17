from .confidence_scorer import ConfidenceScorer
from .cross_referencer import CrossReferencer
from .contradiction_detector import ContradictionDetector
from .source_tagger import SourceTaggerAgent
from .temporal_agent import TemporalAgent
from .network_graph_agent import NetworkGraphAgent
from .adversarial_agent import AdversarialAgent
from .orchestrator import ScoringOrchestrator

__all__ = [
    # New multi-agent pipeline (primary entry point)
    "ScoringOrchestrator",
    # Individual agents (usable standalone)
    "SourceTaggerAgent",
    "TemporalAgent",
    "NetworkGraphAgent",
    "AdversarialAgent",
    # Legacy (kept for backwards compatibility)
    "ConfidenceScorer",
    "CrossReferencer",
    "ContradictionDetector",
]
