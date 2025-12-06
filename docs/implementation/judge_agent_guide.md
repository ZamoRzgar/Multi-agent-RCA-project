# Judge Agent Implementation Guide

**Purpose**: Implement the Judge Agent to evaluate and score RCA hypotheses  
**Date**: December 6, 2025  
**Estimated Time**: 2-3 hours

---

## 🎯 Overview

The **Judge Agent** evaluates hypotheses from all three RCA reasoners and provides:
1. **Scores** for each hypothesis (0-100)
2. **Feedback** on strengths and weaknesses
3. **Rankings** of hypotheses
4. **Guidance** for debate refinement

---

## 📋 Architecture

### Judge Agent Structure

```python
class JudgeAgent(BaseAgent):
    """
    Agent that evaluates and scores RCA hypotheses.
    """
    
    def __init__(self, model="qwen2:7b"):
        # Use Qwen2 for judging (good at reasoning)
        
    def process(self, input_data):
        # Main entry point
        # Evaluates all hypotheses from reasoners
        
    def evaluate_hypotheses(self, hypotheses):
        # Score each hypothesis
        
    def _build_evaluation_prompt(self, hypotheses):
        # Build prompt for LLM evaluation
        
    def _parse_evaluation(self, response):
        # Parse LLM evaluation into scores and feedback
        
    def rank_hypotheses(self, evaluated_hypotheses):
        # Rank by score
```

---

## 📥 Input Structure

The Judge receives hypotheses from all three reasoners:

```python
input_data = {
    "log_focused_hypotheses": [
        {
            "hypothesis": "...",
            "confidence": 0.95,
            "reasoning": "...",
            "evidence": [...],
            "category": "resource",
            "affected_components": [...],
            "suggested_resolution": "..."
        },
        ...
    ],
    "kg_focused_hypotheses": [...],
    "hybrid_hypotheses": [...],
    
    # Original incident data for context
    "events": [...],
    "errors": [...],
    "similar_incidents": [...],
    "causal_paths": [...]
}
```

---

## 📤 Output Structure

The Judge produces:

```python
output = {
    "evaluated_hypotheses": [
        {
            # Original hypothesis
            "hypothesis": "...",
            "confidence": 0.95,
            "reasoning": "...",
            "source": "log_focused",
            
            # Judge's evaluation
            "judge_score": 92,  # 0-100
            "judge_feedback": "Strong evidence from logs...",
            "strengths": ["Clear temporal sequence", "Direct evidence"],
            "weaknesses": ["Doesn't consider historical patterns"],
            "rank": 1
        },
        ...
    ],
    "top_hypothesis": {...},  # Highest scoring
    "consensus_analysis": "All reasoners agree on disk space issue...",
    "debate_guidance": "Focus debate on resource vs hardware distinction..."
}
```

---

## 🎨 Evaluation Criteria

The Judge evaluates hypotheses based on:

### 1. **Evidence Quality** (0-30 points)
- Specificity of evidence
- Direct vs indirect evidence
- Number of supporting facts

### 2. **Reasoning Strength** (0-25 points)
- Logical coherence
- Causal chain clarity
- Explanation completeness

### 3. **Confidence Calibration** (0-20 points)
- Confidence matches evidence strength
- Not overconfident or underconfident
- Appropriate uncertainty acknowledgment

### 4. **Completeness** (0-15 points)
- Identifies affected components
- Provides resolution steps
- Considers side effects

### 5. **Consistency** (0-10 points)
- Aligns with other hypotheses
- Doesn't contradict evidence
- Fits known patterns

**Total**: 100 points

---

## 🎨 Prompt Engineering

### Judge Evaluation Prompt

```
You are an expert judge evaluating root cause analysis hypotheses.

Your task is to objectively evaluate each hypothesis based on evidence quality, reasoning strength, and completeness.

=== INCIDENT CONTEXT ===
Events: {events}
Errors: {errors}
Similar Past Incidents: {similar_incidents}

=== HYPOTHESES TO EVALUATE ===

Hypothesis 1 (from Log-Focused Reasoner):
{hypothesis_1}

Hypothesis 2 (from KG-Focused Reasoner):
{hypothesis_2}

Hypothesis 3 (from Hybrid Reasoner):
{hypothesis_3}

=== EVALUATION CRITERIA ===

For each hypothesis, evaluate:

1. **Evidence Quality (0-30)**: How strong and specific is the evidence?
2. **Reasoning Strength (0-25)**: How logical and coherent is the reasoning?
3. **Confidence Calibration (0-20)**: Is confidence appropriate for evidence?
4. **Completeness (0-15)**: Does it identify components and resolution?
5. **Consistency (0-10)**: Does it align with other evidence?

=== OUTPUT FORMAT ===

Return a JSON array with evaluations:

[
  {
    "hypothesis_id": 1,
    "source": "log_focused",
    "hypothesis": "Original hypothesis text",
    "judge_score": 85,
    "evidence_quality": 25,
    "reasoning_strength": 22,
    "confidence_calibration": 18,
    "completeness": 12,
    "consistency": 8,
    "strengths": ["Strength 1", "Strength 2"],
    "weaknesses": ["Weakness 1"],
    "feedback": "Detailed feedback on this hypothesis",
    "rank": 1
  },
  ...
]

Also provide:
- consensus_analysis: Overall agreement between hypotheses
- debate_guidance: What should be discussed in debate

**IMPORTANT**: Be objective and fair. Score based on evidence, not source.
```

---

## 🏗️ Implementation Steps

### Step 1: Create Judge Agent Class

**File**: `src/agents/judge_agent.py`

```python
from typing import Dict, Any, List
from loguru import logger
from src.agents.base_agent import BaseAgent
import json
import re

class JudgeAgent(BaseAgent):
    """
    Agent that evaluates and scores RCA hypotheses.
    
    Responsibilities:
    - Score hypotheses from all reasoners
    - Provide feedback on strengths/weaknesses
    - Rank hypotheses by quality
    - Guide debate process
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="JudgeAgent",
            model="qwen2:7b",  # Good at reasoning and evaluation
            temperature=0.2,   # Low temperature for consistent scoring
            max_tokens=3000,
            **kwargs
        )
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate hypotheses from all reasoners.
        
        Args:
            input_data: Dictionary with hypotheses from reasoners
            
        Returns:
            Evaluated and ranked hypotheses with scores
        """
        # Collect all hypotheses
        all_hypotheses = self._collect_hypotheses(input_data)
        
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(all_hypotheses, input_data)
        
        # Call LLM for evaluation
        response = self._call_llm(prompt)
        
        # Parse evaluation
        evaluated = self._parse_evaluation(response, all_hypotheses)
        
        # Rank hypotheses
        ranked = self.rank_hypotheses(evaluated)
        
        return {
            "evaluated_hypotheses": ranked,
            "top_hypothesis": ranked[0] if ranked else None,
            "num_evaluated": len(ranked)
        }
```

---

### Step 2: Implement Scoring Logic

```python
    def _collect_hypotheses(self, input_data):
        """Collect hypotheses from all reasoners."""
        hypotheses = []
        
        # From log-focused
        for h in input_data.get("log_focused_hypotheses", []):
            hypotheses.append({**h, "source": "log_focused"})
        
        # From KG-focused
        for h in input_data.get("kg_focused_hypotheses", []):
            hypotheses.append({**h, "source": "kg_focused"})
        
        # From hybrid
        for h in input_data.get("hybrid_hypotheses", []):
            hypotheses.append({**h, "source": "hybrid"})
        
        return hypotheses
    
    def rank_hypotheses(self, evaluated_hypotheses):
        """Rank hypotheses by judge score."""
        return sorted(
            evaluated_hypotheses,
            key=lambda x: x.get("judge_score", 0),
            reverse=True
        )
```

---

## 🧪 Testing

### Test Script Structure

```python
# tests/test_judge_agent.py

def test_judge_agent():
    """Test Judge Agent with sample hypotheses."""
    
    # Get hypotheses from reasoners
    log_hypotheses = log_reasoner.process(data)["hypotheses"]
    kg_hypotheses = kg_reasoner.process(data)["hypotheses"]
    hybrid_hypotheses = hybrid_reasoner.process(data)["hypotheses"]
    
    # Prepare input for judge
    judge_input = {
        "log_focused_hypotheses": log_hypotheses,
        "kg_focused_hypotheses": kg_hypotheses,
        "hybrid_hypotheses": hybrid_hypotheses,
        "events": data["events"],
        "errors": data["errors"]
    }
    
    # Evaluate
    judge = JudgeAgent()
    result = judge.process(judge_input)
    
    # Verify
    assert len(result["evaluated_hypotheses"]) > 0
    assert result["top_hypothesis"]["judge_score"] > 0
    
    # Print results
    print_evaluation_results(result)
```

---

## 📊 Expected Output

```
======================================================================
JUDGE AGENT EVALUATION
======================================================================

Evaluated 7 hypotheses from 3 reasoners

TOP HYPOTHESIS (Score: 92/100):
  Source: log_focused
  Hypothesis: Disk space exhaustion on DataNode server
  Confidence: 0.95
  
  Scores:
    - Evidence Quality: 28/30
    - Reasoning Strength: 24/25
    - Confidence Calibration: 18/20
    - Completeness: 14/15
    - Consistency: 8/10
  
  Strengths:
    - Clear temporal sequence in logs
    - Direct evidence from DiskFullException
    - Specific component identification
  
  Weaknesses:
    - Could consider historical patterns more
  
  Feedback: Strong hypothesis with excellent log evidence...

RANKING:
  1. [92] Disk space exhaustion (log_focused)
  2. [90] DataNode disk full (hybrid)
  3. [85] Under-replication issue (log_focused)
  4. [78] Network congestion (hybrid)
  5. [75] Cascading failure (log_focused)
  6. [72] Hardware failure (kg_focused)
  7. [68] Software bug (hybrid)

CONSENSUS: Strong agreement on disk/resource issues
DEBATE GUIDANCE: Focus on distinguishing between disk full vs hardware failure
```

---

## 🎯 Success Criteria

- [ ] Judge Agent implemented
- [ ] Evaluates hypotheses from all reasoners
- [ ] Assigns scores 0-100
- [ ] Provides feedback and strengths/weaknesses
- [ ] Ranks hypotheses correctly
- [ ] Generates consensus analysis
- [ ] Provides debate guidance
- [ ] Tests pass

---

## 🚀 Integration with Debate

The Judge's output feeds into the Debate Protocol:

```
Round 1:
  Reasoners → Hypotheses → Judge → Scores & Feedback

Round 2:
  Reasoners (with feedback) → Refined Hypotheses → Judge → Updated Scores

Round 3:
  Final Refinement → Judge → Final Ranking → Best Hypothesis
```

---

**Status**: Ready to implement  
**Estimated Time**: 2-3 hours  
**Next**: Implement Judge Agent class
