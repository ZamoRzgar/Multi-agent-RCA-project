"""
Unit tests for debate protocol.
"""

import pytest
from src.debate import DebateProtocol
from src.agents import RCAReasonerAgent, JudgeAgent


class TestDebateProtocol:
    """Tests for DebateProtocol."""
    
    def test_initialization(self):
        """Test debate protocol initialization."""
        reasoners = [
            RCAReasonerAgent(focus="log"),
            RCAReasonerAgent(focus="kg"),
            RCAReasonerAgent(focus="hybrid")
        ]
        judge = JudgeAgent()
        
        debate = DebateProtocol(
            reasoners=reasoners,
            judge=judge,
            max_rounds=2
        )
        
        assert len(debate.reasoners) == 3
        assert debate.max_rounds == 2
        assert debate.judge is not None
    
    def test_generate_initial_hypotheses(self):
        """Test initial hypothesis generation."""
        reasoners = [
            RCAReasonerAgent(focus="log"),
            RCAReasonerAgent(focus="kg")
        ]
        judge = JudgeAgent()
        debate = DebateProtocol(reasoners, judge)
        
        hypotheses = debate._generate_initial_hypotheses(
            parsed_logs={},
            kg_facts={}
        )
        
        assert len(hypotheses) == 2
        assert all("agent" in h for h in hypotheses)
