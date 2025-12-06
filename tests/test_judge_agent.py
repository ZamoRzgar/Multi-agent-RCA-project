"""
Test Judge Agent.

This script tests the Judge Agent's ability to evaluate and score
hypotheses from all three RCA reasoners.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.rca_log_reasoner import LogFocusedReasoner
from src.agents.rca_kg_reasoner import KGFocusedReasoner
from src.agents.rca_hybrid_reasoner import HybridReasoner
from src.agents.judge_agent import JudgeAgent


def get_sample_data():
    """Get sample data for testing."""
    return {
        # Log data
        "events": [
            {
                "timestamp": "2025-12-06T10:00:00",
                "component": "DataNode",
                "action": "disk_check",
                "severity": "WARN",
                "message": "Disk usage at 95%"
            },
            {
                "timestamp": "2025-12-06T10:00:10",
                "component": "DataNode",
                "action": "replication_failed",
                "severity": "ERROR",
                "message": "Block replication failed: No space left on device"
            },
            {
                "timestamp": "2025-12-06T10:00:15",
                "component": "NameNode",
                "action": "block_marked_under_replicated",
                "severity": "WARN",
                "message": "Block blk_123 marked as under-replicated"
            }
        ],
        "error_messages": [
            {
                "error_type": "DiskFullException",
                "message": "No space left on device",
                "component": "DataNode"
            }
        ],
        "entities": [
            {
                "type": "host",
                "name": "/10.0.1.5",
                "context": "DataNode server"
            }
        ],
        
        # KG data
        "similar_incidents": [
            {
                "incident_id": "HDFS_001",
                "similarity_score": 6.5,
                "root_cause": "DataNode disk full"
            }
        ],
        "causal_paths": [
            {
                "path_length": 2,
                "error_type": "DiskFullException"
            }
        ],
        "entity_context": {
            "/10.0.1.5": {
                "event_count": 2,
                "incident_count": 1
            }
        },
        "patterns": [
            {
                "pattern": "DataNode → DataNode",
                "frequency": 2
            }
        ]
    }


def test_judge_agent_full_pipeline():
    """Test Judge Agent with full pipeline (reasoners + judge)."""
    print("="*70)
    print("JUDGE AGENT - FULL PIPELINE TEST")
    print("="*70)
    
    sample_data = get_sample_data()
    
    # Step 1: Generate hypotheses from all reasoners
    print("\n1. Generating hypotheses from reasoners...")
    print("   This will take ~1-2 minutes...")
    
    log_reasoner = LogFocusedReasoner()
    kg_reasoner = KGFocusedReasoner()
    hybrid_reasoner = HybridReasoner()
    
    log_result = log_reasoner.process(sample_data)
    print(f"   ✓ Log-Focused: {log_result['num_hypotheses']} hypotheses")
    
    kg_result = kg_reasoner.process(sample_data)
    print(f"   ✓ KG-Focused: {kg_result['num_hypotheses']} hypotheses")
    
    hybrid_result = hybrid_reasoner.process(sample_data)
    print(f"   ✓ Hybrid: {hybrid_result['num_hypotheses']} hypotheses")
    
    total_hypotheses = (
        log_result['num_hypotheses'] +
        kg_result['num_hypotheses'] +
        hybrid_result['num_hypotheses']
    )
    print(f"\n   Total hypotheses to evaluate: {total_hypotheses}")
    
    # Step 2: Prepare input for judge
    print("\n2. Preparing input for Judge Agent...")
    
    judge_input = {
        "log_focused_hypotheses": log_result["hypotheses"],
        "kg_focused_hypotheses": kg_result["hypotheses"],
        "hybrid_hypotheses": hybrid_result["hypotheses"],
        "events": sample_data["events"],
        "errors": sample_data["error_messages"],
        "similar_incidents": sample_data["similar_incidents"]
    }
    
    # Step 3: Evaluate with Judge
    print("\n3. Evaluating hypotheses with Judge Agent...")
    print("   This will take ~30-60 seconds...")
    
    judge = JudgeAgent()
    evaluation = judge.process(judge_input)
    
    print(f"   ✓ Evaluated: {evaluation['num_evaluated']} hypotheses")
    
    # Step 4: Display results
    print("\n" + "="*70)
    print("EVALUATION RESULTS")
    print("="*70)
    
    print(f"\nTotal Hypotheses Evaluated: {evaluation['num_evaluated']}")
    
    if evaluation['top_hypothesis']:
        print("\n" + "-"*70)
        print("TOP HYPOTHESIS")
        print("-"*70)
        
        top = evaluation['top_hypothesis']
        print(f"\nRank: #{top.get('rank', 'N/A')}")
        print(f"Source: {top.get('source', 'unknown')}")
        print(f"Judge Score: {top.get('judge_score', 0)}/100")
        print(f"\nHypothesis: {top.get('hypothesis', 'N/A')}")
        print(f"Original Confidence: {top.get('confidence', 0):.2f}")
        print(f"Category: {top.get('category', 'unknown')}")
        
        print(f"\nScore Breakdown:")
        print(f"  - Evidence Quality:        {top.get('evidence_quality', 0)}/30")
        print(f"  - Reasoning Strength:      {top.get('reasoning_strength', 0)}/25")
        print(f"  - Confidence Calibration:  {top.get('confidence_calibration', 0)}/20")
        print(f"  - Completeness:            {top.get('completeness', 0)}/15")
        print(f"  - Consistency:             {top.get('consistency', 0)}/10")
        
        if top.get('strengths'):
            print(f"\nStrengths:")
            for strength in top.get('strengths', []):
                print(f"  ✓ {strength}")
        
        if top.get('weaknesses'):
            print(f"\nWeaknesses:")
            for weakness in top.get('weaknesses', []):
                print(f"  ✗ {weakness}")
        
        if top.get('feedback'):
            print(f"\nJudge Feedback:")
            print(f"  {top.get('feedback', 'No feedback')[:200]}...")
    
    # Step 5: Show rankings
    print("\n" + "-"*70)
    print("COMPLETE RANKING")
    print("-"*70)
    
    for h in evaluation['evaluated_hypotheses']:
        print(f"\n{h.get('rank', '?')}. [{h.get('judge_score', 0):3d}/100] "
              f"({h.get('source', 'unknown'):12s}) "
              f"{h.get('hypothesis', 'No hypothesis')[:60]}...")
        print(f"   Original Confidence: {h.get('confidence', 0):.2f}")
    
    # Step 6: Show consensus analysis
    print("\n" + "-"*70)
    print("CONSENSUS ANALYSIS")
    print("-"*70)
    print(f"\n{evaluation.get('consensus_analysis', 'No analysis')}")
    
    # Step 7: Show debate guidance
    print("\n" + "-"*70)
    print("DEBATE GUIDANCE")
    print("-"*70)
    print(f"\n{evaluation.get('debate_guidance', 'No guidance')}")
    
    print("\n" + "="*70)
    print("✓ TEST COMPLETED SUCCESSFULLY!")
    print("="*70)
    
    print("\nNext Steps:")
    print("  1. Review the judge's evaluation and scores")
    print("  2. Implement Debate Protocol (Week 2, Day 7)")
    print("  3. Use judge feedback to refine hypotheses")
    
    return evaluation


def test_judge_agent_with_sample_hypotheses():
    """Test Judge Agent with pre-made sample hypotheses (faster)."""
    print("="*70)
    print("JUDGE AGENT - QUICK TEST (Sample Hypotheses)")
    print("="*70)
    
    # Sample hypotheses (simulating reasoner output)
    judge_input = {
        "log_focused_hypotheses": [
            {
                "hypothesis": "Disk space exhaustion on DataNode server",
                "confidence": 0.95,
                "reasoning": "Log sequence shows disk at 95% followed by DiskFullException",
                "evidence": ["Disk usage at 95%", "No space left on device"],
                "category": "resource",
                "affected_components": ["DataNode"],
                "suggested_resolution": "Add disk space or clear old data"
            },
            {
                "hypothesis": "Under-replication of HDFS blocks",
                "confidence": 0.80,
                "reasoning": "NameNode marked block as under-replicated",
                "evidence": ["Block marked as under-replicated"],
                "category": "software",
                "affected_components": ["NameNode", "DataNode"],
                "suggested_resolution": "Increase replication factor"
            }
        ],
        "kg_focused_hypotheses": [
            {
                "hypothesis": "Hardware failure on DataNode",
                "confidence": 0.75,
                "reasoning": "Similar to past incident HDFS_001",
                "evidence": ["Historical incident HDFS_001"],
                "category": "hardware",
                "affected_components": ["DataNode"],
                "suggested_resolution": "Check hardware and replace if needed"
            }
        ],
        "hybrid_hypotheses": [
            {
                "hypothesis": "DataNode disk full due to high replication rate",
                "confidence": 0.92,
                "reasoning": "Combines log evidence with historical patterns",
                "evidence": ["Disk at 95%", "DiskFullException", "Similar incident"],
                "category": "resource",
                "affected_components": ["DataNode", "NameNode"],
                "suggested_resolution": "Add storage and optimize replication"
            }
        ],
        "events": get_sample_data()["events"],
        "errors": get_sample_data()["error_messages"]
    }
    
    print("\nInput: 4 hypotheses from 3 reasoners")
    print("  - Log-Focused: 2 hypotheses")
    print("  - KG-Focused: 1 hypothesis")
    print("  - Hybrid: 1 hypothesis")
    
    print("\nEvaluating with Judge Agent...")
    
    judge = JudgeAgent()
    evaluation = judge.process(judge_input)
    
    print(f"\n✓ Evaluated {evaluation['num_evaluated']} hypotheses")
    
    print("\nTop 3 Hypotheses:")
    for i, h in enumerate(evaluation['evaluated_hypotheses'][:3], 1):
        print(f"\n{i}. Score: {h.get('judge_score', 0)}/100")
        print(f"   Source: {h.get('source', 'unknown')}")
        print(f"   Hypothesis: {h.get('hypothesis', 'N/A')[:60]}...")
    
    print("\n" + "="*70)
    print("✓ QUICK TEST COMPLETED!")
    print("="*70)
    
    return evaluation


def main():
    """Run tests."""
    print("\n" + "="*70)
    print("JUDGE AGENT - COMPREHENSIVE TEST")
    print("="*70)
    print("\nChoose test mode:")
    print("  1. Full pipeline (reasoners + judge) - ~2-3 minutes")
    print("  2. Quick test (sample hypotheses) - ~30 seconds")
    
    # For automated testing, run quick test
    print("\nRunning quick test...")
    
    try:
        result = test_judge_agent_with_sample_hypotheses()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
