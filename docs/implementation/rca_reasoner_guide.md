# RCA Reasoner Agents Implementation Guide

**Purpose**: Implement three specialized RCA reasoning agents  
**Date**: December 6, 2025  
**Estimated Time**: 4-6 hours

---

## 🎯 Overview

We need to implement **3 RCA Reasoner Agents**, each with different specializations:

1. **Log-Focused Reasoner** (Mistral-7B)
   - Analyzes raw log patterns and sequences
   - Focuses on temporal relationships
   - Identifies anomalies in log data

2. **KG-Focused Reasoner** (LLaMA2-7B)
   - Leverages knowledge graph facts
   - Uses historical incident patterns
   - Focuses on causal relationships from KG

3. **Hybrid Reasoner** (Qwen2-7B)
   - Combines both logs and KG facts
   - Most comprehensive analysis
   - Balanced approach

---

## 📋 Architecture

### Base RCA Reasoner Structure

```python
class RCAReasonerAgent(BaseAgent):
    """
    Base class for RCA reasoning agents.
    Each reasoner generates root cause hypotheses.
    """
    
    def __init__(self, name, model, reasoning_type, **kwargs):
        # reasoning_type: "log_focused", "kg_focused", "hybrid"
        
    def process(self, input_data):
        # Main entry point
        # Returns: list of hypotheses with confidence scores
        
    def _build_reasoning_prompt(self, input_data):
        # Build specialized prompt based on reasoning type
        
    def _parse_hypotheses(self, llm_response):
        # Parse LLM response into structured hypotheses
        
    def _rank_hypotheses(self, hypotheses):
        # Rank hypotheses by confidence
```

---

## 🔍 Input Data Structure

Each reasoner receives:

```python
input_data = {
    # From Log Parser
    "events": [...],
    "entities": [...],
    "error_messages": [...],
    "timeline": [...],
    
    # From KG Retrieval (optional for log-focused)
    "similar_incidents": [...],
    "causal_paths": [...],
    "entity_context": {...},
    "patterns": [...]
}
```

---

## 📤 Output Structure

Each reasoner produces:

```python
output = {
    "hypotheses": [
        {
            "hypothesis": "Root cause description",
            "confidence": 0.85,
            "reasoning": "Explanation of why this is the root cause",
            "evidence": ["Evidence 1", "Evidence 2", ...],
            "category": "hardware|software|network|config|resource",
            "affected_components": ["Component1", "Component2"],
            "suggested_resolution": "How to fix this"
        },
        ...
    ],
    "reasoning_type": "log_focused|kg_focused|hybrid",
    "model_used": "mistral:7b|llama2:7b|qwen2:7b"
}
```

---

## 🎨 Prompt Engineering

### Log-Focused Reasoner Prompt

```
You are an expert in analyzing system logs for root cause analysis.

Given the following log events and error messages, identify the most likely root cause of the incident.

EVENTS:
{events}

ERROR MESSAGES:
{errors}

TIMELINE:
{timeline}

Analyze the temporal sequence, error patterns, and component interactions.

Provide 3-5 root cause hypotheses in JSON format:
[
  {
    "hypothesis": "Description of root cause",
    "confidence": 0.0-1.0,
    "reasoning": "Why this is likely the root cause",
    "evidence": ["Evidence from logs"],
    "category": "hardware|software|network|config|resource",
    "affected_components": ["Component names"],
    "suggested_resolution": "How to fix"
  }
]
```

### KG-Focused Reasoner Prompt

```
You are an expert in using historical incident data for root cause analysis.

Given the following information from the knowledge graph:

SIMILAR PAST INCIDENTS:
{similar_incidents}

KNOWN CAUSAL PATHS:
{causal_paths}

ENTITY CONTEXT:
{entity_context}

COMMON PATTERNS:
{patterns}

CURRENT INCIDENT:
Events: {events}
Errors: {errors}

Based on historical patterns and known causal relationships, identify the most likely root cause.

Provide 3-5 root cause hypotheses in JSON format:
[...]
```

### Hybrid Reasoner Prompt

```
You are an expert in comprehensive root cause analysis using both log analysis and historical data.

LOG DATA:
Events: {events}
Errors: {errors}
Timeline: {timeline}

KNOWLEDGE GRAPH DATA:
Similar Incidents: {similar_incidents}
Causal Paths: {causal_paths}
Entity Context: {entity_context}
Patterns: {patterns}

Combine insights from both log patterns and historical knowledge to identify the root cause.

Provide 3-5 root cause hypotheses in JSON format:
[...]
```

---

## 🏗️ Implementation Steps

### Step 1: Create Base RCA Reasoner Class

File: `src/agents/rca_reasoner_base.py`

```python
from typing import Dict, Any, List
from loguru import logger
from src.agents.base_agent import BaseAgent
import json
import re

class RCAReasonerAgent(BaseAgent):
    """Base class for RCA reasoning agents."""
    
    def __init__(
        self,
        name: str,
        model: str,
        reasoning_type: str,
        **kwargs
    ):
        super().__init__(name=name, model=model, **kwargs)
        self.reasoning_type = reasoning_type  # log_focused, kg_focused, hybrid
        
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate root cause hypotheses."""
        # Build prompt
        prompt = self._build_reasoning_prompt(input_data)
        
        # Call LLM
        response = self._call_llm(prompt)
        
        # Parse hypotheses
        hypotheses = self._parse_hypotheses(response)
        
        # Rank hypotheses
        ranked_hypotheses = self._rank_hypotheses(hypotheses)
        
        return {
            "hypotheses": ranked_hypotheses,
            "reasoning_type": self.reasoning_type,
            "model_used": self.model
        }
    
    def _build_reasoning_prompt(self, input_data: Dict[str, Any]) -> str:
        """Build prompt based on reasoning type."""
        raise NotImplementedError("Subclasses must implement this")
    
    def _parse_hypotheses(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into hypotheses."""
        # Extract JSON from response
        # Handle malformed JSON
        # Return list of hypotheses
        pass
    
    def _rank_hypotheses(self, hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank hypotheses by confidence."""
        return sorted(hypotheses, key=lambda x: x.get("confidence", 0), reverse=True)
```

---

### Step 2: Implement Log-Focused Reasoner

File: `src/agents/rca_log_reasoner.py`

```python
from src.agents.rca_reasoner_base import RCAReasonerAgent

class LogFocusedReasoner(RCAReasonerAgent):
    """Reasoner that focuses on log patterns."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="LogFocusedReasoner",
            model="mistral:7b",
            reasoning_type="log_focused",
            **kwargs
        )
    
    def _build_reasoning_prompt(self, input_data):
        # Build log-focused prompt
        pass
```

---

### Step 3: Implement KG-Focused Reasoner

File: `src/agents/rca_kg_reasoner.py`

```python
from src.agents.rca_reasoner_base import RCAReasonerAgent

class KGFocusedReasoner(RCAReasonerAgent):
    """Reasoner that focuses on knowledge graph."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="KGFocusedReasoner",
            model="llama2:7b",
            reasoning_type="kg_focused",
            **kwargs
        )
    
    def _build_reasoning_prompt(self, input_data):
        # Build KG-focused prompt
        pass
```

---

### Step 4: Implement Hybrid Reasoner

File: `src/agents/rca_hybrid_reasoner.py`

```python
from src.agents.rca_reasoner_base import RCAReasonerAgent

class HybridReasoner(RCAReasonerAgent):
    """Reasoner that combines logs and KG."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="HybridReasoner",
            model="qwen2:7b",
            reasoning_type="hybrid",
            **kwargs
        )
    
    def _build_reasoning_prompt(self, input_data):
        # Build hybrid prompt
        pass
```

---

## 🧪 Testing

### Test Script Structure

```python
# tests/test_rca_reasoners.py

def test_log_focused_reasoner():
    reasoner = LogFocusedReasoner()
    result = reasoner.process(sample_data)
    assert len(result['hypotheses']) > 0
    
def test_kg_focused_reasoner():
    reasoner = KGFocusedReasoner()
    result = reasoner.process(sample_data)
    assert len(result['hypotheses']) > 0
    
def test_hybrid_reasoner():
    reasoner = HybridReasoner()
    result = reasoner.process(sample_data)
    assert len(result['hypotheses']) > 0
```

---

## 📊 Expected Performance

### Response Time:
- Log-Focused: ~5-10 seconds
- KG-Focused: ~5-10 seconds
- Hybrid: ~10-15 seconds (more context)

### Quality Metrics:
- Number of hypotheses: 3-5 per reasoner
- Confidence scores: 0.0-1.0
- Evidence quality: Specific references to logs/KG

---

## 🎯 Success Criteria

- [ ] All 3 reasoners implemented
- [ ] Each reasoner generates 3-5 hypotheses
- [ ] Hypotheses include confidence scores
- [ ] Hypotheses include reasoning and evidence
- [ ] JSON parsing is robust
- [ ] Tests pass for all reasoners
- [ ] Integration with Log Parser and KG Retrieval works

---

## 🚀 Next Steps After Implementation

1. Test with real loghub data
2. Compare hypotheses across reasoners
3. Implement Judge Agent (Day 6)
4. Implement Debate Protocol (Day 7)

---

**Status**: Ready to implement  
**Estimated Time**: 4-6 hours  
**Files to Create**: 4 Python files + 1 test file
