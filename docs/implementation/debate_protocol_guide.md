# Debate Protocol Implementation Guide

**Purpose**: Implement multi-round debate protocol for hypothesis refinement  
**Date**: December 6, 2025  
**Estimated Time**: 2-3 hours

---

## 🎯 Overview

The **Debate Protocol** orchestrates multi-round debates between RCA reasoners to:
1. Refine hypotheses based on judge feedback
2. Converge to the best root cause
3. Improve hypothesis quality through iteration
4. Achieve consensus among reasoners

---

## 📋 Architecture

### Debate Flow

```
Round 1: Initial Hypotheses
  ├── Log Reasoner → 3-5 hypotheses
  ├── KG Reasoner → 3-5 hypotheses
  ├── Hybrid Reasoner → 3-5 hypotheses
  └── Judge → Scores + Feedback
       │
       ▼
Round 2: Refinement
  ├── Reasoners (with feedback) → Refined hypotheses
  └── Judge → Updated scores
       │
       ▼
Round 3: Final Refinement
  ├── Reasoners (with updated feedback) → Final hypotheses
  └── Judge → Final scores
       │
       ▼
Best Hypothesis Selected
```

---

## 🏗️ Components

### 1. Debate Coordinator

```python
class DebateCoordinator:
    """
    Orchestrates multi-round debate between reasoners.
    """
    
    def __init__(self, reasoners, judge, max_rounds=3):
        self.reasoners = reasoners  # List of RCA reasoners
        self.judge = judge          # Judge agent
        self.max_rounds = max_rounds
        
    def run_debate(self, input_data):
        # Main debate loop
        
    def run_round(self, round_num, input_data, feedback):
        # Single debate round
        
    def check_convergence(self, round_results):
        # Check if hypotheses have converged
        
    def select_best_hypothesis(self, all_rounds):
        # Select final best hypothesis
```

---

## 📥 Input Structure

```python
input_data = {
    # From Log Parser
    "events": [...],
    "entities": [...],
    "error_messages": [...],
    "timeline": [...],
    
    # From KG Retrieval
    "similar_incidents": [...],
    "causal_paths": [...],
    "entity_context": {...},
    "patterns": [...]
}
```

---

## 📤 Output Structure

```python
output = {
    "rounds": [
        {
            "round_number": 1,
            "hypotheses": [...],
            "judge_evaluation": {...},
            "top_hypothesis": {...}
        },
        ...
    ],
    "final_hypothesis": {
        "hypothesis": "...",
        "confidence": 0.95,
        "judge_score": 92,
        "source": "hybrid",
        "reasoning": "...",
        "evidence": [...],
        "resolution": "...",
        "rounds_refined": 3
    },
    "convergence_achieved": true,
    "total_rounds": 3,
    "improvement_trajectory": [85, 90, 92]  # Scores over rounds
}
```

---

## 🎨 Debate Mechanism

### Round 1: Initial Hypotheses

**Input**: Raw incident data  
**Process**:
1. Each reasoner generates initial hypotheses
2. Judge evaluates all hypotheses
3. Judge provides feedback

**Output**: Scored hypotheses + feedback

---

### Round 2: Refinement

**Input**: Round 1 results + judge feedback  
**Process**:
1. Reasoners see:
   - Their own hypotheses + scores
   - Other reasoners' top hypotheses
   - Judge feedback on weaknesses
2. Reasoners refine their hypotheses
3. Judge re-evaluates

**Output**: Refined hypotheses + updated scores

---

### Round 3: Final Refinement

**Input**: Round 2 results + updated feedback  
**Process**:
1. Reasoners make final improvements
2. Focus on addressing remaining weaknesses
3. Judge provides final evaluation

**Output**: Final hypotheses + final scores

---

## 🎯 Convergence Detection

Debate stops early if:
1. **Score plateau**: Top score improves < 5 points
2. **Consensus reached**: All reasoners agree on same hypothesis
3. **Max rounds**: Reached maximum rounds (3)

---

## 🎨 Prompt Engineering

### Refinement Prompt Template

```
You are refining your root cause hypothesis based on judge feedback.

=== YOUR PREVIOUS HYPOTHESIS ===
Hypothesis: {previous_hypothesis}
Score: {previous_score}/100
Confidence: {previous_confidence}

=== JUDGE FEEDBACK ===
Strengths:
{strengths}

Weaknesses:
{weaknesses}

Feedback: {detailed_feedback}

=== OTHER REASONERS' TOP HYPOTHESES ===
{other_hypotheses}

=== INSTRUCTIONS ===
Refine your hypothesis by:
1. Addressing the weaknesses identified by the judge
2. Incorporating insights from other reasoners
3. Strengthening evidence and reasoning
4. Improving resolution steps

Provide refined hypothesis in JSON format:
{{
  "hypothesis": "Refined root cause description",
  "confidence": 0.0-1.0,
  "reasoning": "Improved reasoning addressing feedback",
  "evidence": ["Enhanced evidence list"],
  "category": "hardware|software|network|config|resource",
  "affected_components": ["Components"],
  "suggested_resolution": "Improved resolution steps",
  "changes_made": "Summary of refinements"
}}
```

---

## 🏗️ Implementation Steps

### Step 1: Create Debate Coordinator

**File**: `src/debate/debate_coordinator.py`

```python
from typing import Dict, Any, List
from loguru import logger

class DebateCoordinator:
    """
    Coordinates multi-round debate between RCA reasoners.
    """
    
    def __init__(
        self,
        log_reasoner,
        kg_reasoner,
        hybrid_reasoner,
        judge,
        max_rounds: int = 3,
        convergence_threshold: float = 5.0
    ):
        self.reasoners = {
            "log_focused": log_reasoner,
            "kg_focused": kg_reasoner,
            "hybrid": hybrid_reasoner
        }
        self.judge = judge
        self.max_rounds = max_rounds
        self.convergence_threshold = convergence_threshold
        
    def run_debate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run multi-round debate."""
        rounds_results = []
        previous_top_score = 0
        
        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"Starting Round {round_num}")
            
            # Get feedback from previous round
            feedback = self._get_feedback(rounds_results)
            
            # Run round
            round_result = self.run_round(
                round_num,
                input_data,
                feedback
            )
            
            rounds_results.append(round_result)
            
            # Check convergence
            current_top_score = round_result["top_hypothesis"]["judge_score"]
            improvement = current_top_score - previous_top_score
            
            if self.check_convergence(improvement, round_num):
                logger.info(f"Convergence achieved at round {round_num}")
                break
            
            previous_top_score = current_top_score
        
        # Select final best hypothesis
        final_hypothesis = self.select_best_hypothesis(rounds_results)
        
        return {
            "rounds": rounds_results,
            "final_hypothesis": final_hypothesis,
            "total_rounds": len(rounds_results),
            "convergence_achieved": len(rounds_results) < self.max_rounds
        }
```

---

### Step 2: Implement Round Execution

```python
    def run_round(
        self,
        round_num: int,
        input_data: Dict[str, Any],
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute single debate round."""
        
        # Generate/refine hypotheses from each reasoner
        all_hypotheses = {}
        
        for name, reasoner in self.reasoners.items():
            if round_num == 1:
                # Initial hypotheses
                result = reasoner.process(input_data)
            else:
                # Refined hypotheses with feedback
                result = self._refine_hypotheses(
                    reasoner,
                    input_data,
                    feedback.get(name, {})
                )
            
            all_hypotheses[f"{name}_hypotheses"] = result["hypotheses"]
        
        # Judge evaluates all hypotheses
        judge_input = {
            **all_hypotheses,
            "events": input_data.get("events", []),
            "errors": input_data.get("error_messages", [])
        }
        
        evaluation = self.judge.process(judge_input)
        
        return {
            "round_number": round_num,
            "hypotheses": all_hypotheses,
            "evaluation": evaluation,
            "top_hypothesis": evaluation["top_hypothesis"]
        }
```

---

### Step 3: Implement Convergence Check

```python
    def check_convergence(
        self,
        improvement: float,
        round_num: int
    ) -> bool:
        """Check if debate should stop."""
        
        # Max rounds reached
        if round_num >= self.max_rounds:
            return True
        
        # Score plateau (< 5 point improvement)
        if improvement < self.convergence_threshold:
            logger.info(f"Score plateau: improvement = {improvement:.1f}")
            return True
        
        return False
```

---

## 🧪 Testing

### Test Script Structure

```python
# tests/test_debate_protocol.py

def test_debate_protocol():
    """Test full debate protocol."""
    
    # Initialize components
    log_reasoner = LogFocusedReasoner()
    kg_reasoner = KGFocusedReasoner()
    hybrid_reasoner = HybridReasoner()
    judge = JudgeAgent()
    
    # Create coordinator
    coordinator = DebateCoordinator(
        log_reasoner,
        kg_reasoner,
        hybrid_reasoner,
        judge,
        max_rounds=3
    )
    
    # Run debate
    result = coordinator.run_debate(sample_data)
    
    # Verify
    assert result["total_rounds"] <= 3
    assert result["final_hypothesis"] is not None
    assert result["final_hypothesis"]["judge_score"] > 0
    
    # Display results
    print_debate_results(result)
```

---

## 📊 Expected Output

```
======================================================================
DEBATE PROTOCOL - 3 ROUNDS
======================================================================

ROUND 1: Initial Hypotheses
  - Log-Focused: 3 hypotheses
  - KG-Focused: 1 hypothesis  
  - Hybrid: 3 hypotheses
  - Judge Evaluation: Top score = 85/100

ROUND 2: Refinement
  - Reasoners refined based on feedback
  - Judge Evaluation: Top score = 90/100
  - Improvement: +5 points

ROUND 3: Final Refinement
  - Final improvements made
  - Judge Evaluation: Top score = 92/100
  - Improvement: +2 points
  - Convergence: Score plateau detected

======================================================================
FINAL RESULT
======================================================================

Best Hypothesis (Score: 92/100):
  Source: hybrid
  Hypothesis: DataNode disk space exhausted due to high replication rate
  Confidence: 0.95
  Rounds Refined: 3
  
  Evidence:
    - Log: Disk usage at 95% before failure
    - Log: DiskFullException error
    - Historical: Similar incident HDFS_001
    - Pattern: DataNode → DataNode sequence
  
  Resolution:
    1. Immediately clear disk space on affected DataNode
    2. Add storage capacity or optimize data retention
    3. Adjust replication factor to prevent recurrence
    4. Monitor disk usage with alerts at 85%

Improvement Trajectory: 85 → 90 → 92 (+7 points over 3 rounds)
Convergence: Achieved (score plateau)
```

---

## 🎯 Success Criteria

- [ ] Debate Coordinator implemented
- [ ] Multi-round mechanism working
- [ ] Feedback incorporation functional
- [ ] Convergence detection working
- [ ] Final hypothesis selection correct
- [ ] Tests pass
- [ ] Full pipeline integration works

---

## 🚀 Integration

Complete pipeline:

```
Input: Raw Logs
  ↓
Log Parser → Structured Events
  ↓
KG Retrieval → Historical Context
  ↓
DEBATE PROTOCOL:
  Round 1 → Reasoners → Judge → Feedback
  Round 2 → Refined → Judge → Feedback
  Round 3 → Final → Judge → Best
  ↓
Output: Final Root Cause with high confidence
```

---

**Status**: Ready to implement  
**Estimated Time**: 2-3 hours  
**Next**: Implement Debate Coordinator class
