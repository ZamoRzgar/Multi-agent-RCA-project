"""
Debate protocol for multi-agent collaboration.
"""

from .protocol import DebateProtocol
from .scoring import HypothesisScorer

__all__ = ["DebateProtocol", "HypothesisScorer"]
