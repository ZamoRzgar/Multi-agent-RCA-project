"""
Unit tests for agent implementations.
"""

import pytest
from src.agents import LogParserAgent, KGRetrievalAgent, RCAReasonerAgent, JudgeAgent


class TestLogParserAgent:
    """Tests for LogParserAgent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = LogParserAgent()
        assert agent.name == "LogParserAgent"
        assert agent.parser_type == "drain"
    
    def test_process_empty_logs(self):
        """Test processing empty logs."""
        agent = LogParserAgent()
        result = agent.process({"raw_logs": ""})
        assert "events" in result
        assert "entities" in result


class TestKGRetrievalAgent:
    """Tests for KGRetrievalAgent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = KGRetrievalAgent()
        assert agent.name == "KGRetrievalAgent"
        assert agent.top_k == 10
    
    def test_process_empty_input(self):
        """Test processing empty input."""
        agent = KGRetrievalAgent()
        result = agent.process({"entities": [], "events": []})
        assert "related_incidents" in result


class TestRCAReasonerAgent:
    """Tests for RCAReasonerAgent."""
    
    @pytest.mark.parametrize("focus", ["log", "kg", "hybrid"])
    def test_initialization(self, focus):
        """Test agent initialization with different focuses."""
        agent = RCAReasonerAgent(focus=focus)
        assert agent.focus == focus
        assert focus in agent.name
    
    def test_process_generates_hypothesis(self):
        """Test hypothesis generation."""
        agent = RCAReasonerAgent(focus="hybrid")
        result = agent.process({
            "parsed_logs": {},
            "kg_facts": {}
        })
        assert "root_cause" in result
        assert "explanation" in result
        assert "confidence" in result


class TestJudgeAgent:
    """Tests for JudgeAgent."""
    
    def test_initialization(self):
        """Test agent initialization."""
        agent = JudgeAgent()
        assert agent.name == "JudgeAgent"
        assert len(agent.scoring_criteria) > 0
    
    def test_process_selects_hypothesis(self):
        """Test hypothesis selection."""
        agent = JudgeAgent()
        hypotheses = [
            {"root_cause": "cause1", "explanation": "exp1", "confidence": 0.8},
            {"root_cause": "cause2", "explanation": "exp2", "confidence": 0.6}
        ]
        result = agent.process({
            "hypotheses": hypotheses,
            "parsed_logs": {},
            "kg_facts": {}
        })
        assert "selected_hypothesis" in result
        assert "confidence" in result
