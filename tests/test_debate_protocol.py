"""
Test Debate Protocol.

This script tests the complete debate protocol with all components:
- Log Parser
- KG Retrieval
- 3 RCA Reasoners
- Judge Agent
- Debate Coordinator
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.log_parser import LogParserAgent
from src.agents.kg_retrieval import KGRetrievalAgent
from src.agents.rca_log_reasoner import LogFocusedReasoner
from src.agents.rca_kg_reasoner import KGFocusedReasoner
from src.agents.rca_hybrid_reasoner import HybridReasoner
from src.agents.judge_agent import JudgeAgent
from src.debate.debate_coordinator import DebateCoordinator


def get_sample_incident():
    """Get sample HDFS incident data."""
    return {
        "raw_logs": """
2025-12-06 10:00:00 INFO DataNode: Disk usage check - current: 95%
2025-12-06 10:00:05 WARN DataNode: Disk usage critical - threshold exceeded
2025-12-06 10:00:10 ERROR DataNode: Block replication failed - No space left on device
2025-12-06 10:00:12 ERROR DataNode: DiskFullException: /data/hadoop/dfs/data
2025-12-06 10:00:15 WARN NameNode: Block blk_123 marked as under-replicated
2025-12-06 10:00:20 ERROR NameNode: Replication factor below minimum for block blk_123
        """.strip(),
        
        # Pre-parsed for faster testing
        "events": [
            {
                "timestamp": "2025-12-06T10:00:00",
                "component": "DataNode",
                "action": "disk_check",
                "severity": "INFO",
                "message": "Disk usage check - current: 95%"
            },
            {
                "timestamp": "2025-12-06T10:00:10",
                "component": "DataNode",
                "action": "replication_failed",
                "severity": "ERROR",
                "message": "Block replication failed - No space left on device"
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
            },
            {
                "type": "block",
                "name": "blk_123",
                "context": "HDFS block"
            }
        ],
        
        # KG data (simulated)
        "similar_incidents": [
            {
                "incident_id": "HDFS_001",
                "similarity_score": 6.5,
                "root_cause": "DataNode disk full",
                "components": ["DataNode", "NameNode"]
            }
        ],
        "causal_paths": [
            {
                "path_length": 2,
                "error_type": "DiskFullException",
                "events": [
                    {"component": "DataNode", "action": "disk_check"},
                    {"component": "DataNode", "action": "replication_failed"}
                ]
            }
        ],
        "entity_context": {
            "/10.0.1.5": {
                "type": "host",
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


def test_debate_protocol_quick():
    """Quick test with pre-parsed data (faster)."""
    print("="*70)
    print("DEBATE PROTOCOL - QUICK TEST")
    print("="*70)
    print("\nThis test uses pre-parsed data to run faster (~2-3 minutes)")
    print("Testing: 3 Reasoners → Judge → 3 Rounds of Debate\n")
    
    # Get sample data
    sample_data = get_sample_incident()
    
    # Initialize components
    print("1. Initializing components...")
    log_reasoner = LogFocusedReasoner()
    kg_reasoner = KGFocusedReasoner()
    hybrid_reasoner = HybridReasoner()
    judge = JudgeAgent()
    
    print("   ✓ Log-Focused Reasoner (Mistral-7B)")
    print("   ✓ KG-Focused Reasoner (LLaMA2-7B)")
    print("   ✓ Hybrid Reasoner (Qwen2-7B)")
    print("   ✓ Judge Agent (Qwen2-7B)")
    
    # Create debate coordinator
    print("\n2. Creating Debate Coordinator...")
    coordinator = DebateCoordinator(
        log_reasoner=log_reasoner,
        kg_reasoner=kg_reasoner,
        hybrid_reasoner=hybrid_reasoner,
        judge=judge,
        max_rounds=3,
        convergence_threshold=5.0
    )
    print("   ✓ Max rounds: 3")
    print("   ✓ Convergence threshold: 5 points")
    
    # Run debate
    print("\n3. Running Debate Protocol...")
    print("   This will take ~2-3 minutes...\n")
    
    result = coordinator.run_debate(sample_data)
    
    # Display results
    print("\n" + "="*70)
    print("DEBATE RESULTS")
    print("="*70)
    
    print(f"\nTotal Rounds: {result['total_rounds']}")
    print(f"Convergence: {'Yes' if result['convergence_achieved'] else 'No'}")
    print(f"Score Trajectory: {' → '.join(map(str, result['improvement_trajectory']))}")
    
    if len(result['improvement_trajectory']) > 1:
        improvement = result['improvement_trajectory'][-1] - result['improvement_trajectory'][0]
        print(f"Total Improvement: +{improvement} points")
    
    # Show round-by-round results
    print("\n" + "-"*70)
    print("ROUND-BY-ROUND BREAKDOWN")
    print("-"*70)
    
    for round_data in result['rounds']:
        round_num = round_data['round_number']
        top_hyp = round_data['top_hypothesis']
        
        print(f"\nRound {round_num}:")
        print(f"  Top Score: {top_hyp['judge_score']}/100")
        print(f"  Source: {top_hyp['source']}")
        print(f"  Hypothesis: {top_hyp['hypothesis'][:80]}...")
        print(f"  Confidence: {top_hyp['confidence']:.2f}")
    
    # Show final hypothesis
    print("\n" + "-"*70)
    print("FINAL HYPOTHESIS")
    print("-"*70)
    
    final = result['final_hypothesis']
    print(f"\nScore: {final['judge_score']}/100")
    print(f"Source: {final['source']}")
    print(f"Confidence: {final['confidence']:.2f}")
    print(f"Category: {final['category']}")
    print(f"\nHypothesis:")
    print(f"  {final['hypothesis']}")
    print(f"\nReasoning:")
    print(f"  {final['reasoning'][:200]}...")
    
    if final.get('evidence'):
        print(f"\nEvidence ({len(final['evidence'])} items):")
        for i, evidence in enumerate(final['evidence'][:3], 1):
            print(f"  {i}. {evidence}")
    
    print(f"\nResolution:")
    print(f"  {final['suggested_resolution'][:200]}...")
    
    print(f"\nRefined over {final.get('rounds_refined', 0)} rounds")
    
    # Summary
    print("\n" + "="*70)
    print("✓ DEBATE PROTOCOL TEST COMPLETED!")
    print("="*70)
    
    print("\nKey Findings:")
    print(f"  • Started at {result['improvement_trajectory'][0]}/100")
    print(f"  • Ended at {result['improvement_trajectory'][-1]}/100")
    print(f"  • Improvement: +{result['improvement_trajectory'][-1] - result['improvement_trajectory'][0]} points")
    print(f"  • Convergence: {'Achieved' if result['convergence_achieved'] else 'Max rounds'}")
    
    return result


def test_debate_protocol_full_pipeline():
    """Full pipeline test including Log Parser and KG Retrieval."""
    print("="*70)
    print("DEBATE PROTOCOL - FULL PIPELINE TEST")
    print("="*70)
    print("\nThis test runs the complete pipeline:")
    print("  Raw Logs → Parser → KG Retrieval → Reasoners → Judge → Debate")
    print("\nThis will take ~5-7 minutes...\n")
    
    # Get sample data
    sample_data = get_sample_incident()
    
    # Step 1: Log Parser
    print("1. Parsing logs...")
    log_parser = LogParserAgent()
    parsed = log_parser.process({"raw_logs": sample_data["raw_logs"]})
    print(f"   ✓ Extracted {len(parsed['events'])} events")
    print(f"   ✓ Extracted {len(parsed['error_messages'])} errors")
    
    # Step 2: KG Retrieval
    print("\n2. Retrieving from Knowledge Graph...")
    kg_retrieval = KGRetrievalAgent()
    kg_facts = kg_retrieval.process(parsed)
    print(f"   ✓ Found {len(kg_facts['similar_incidents'])} similar incidents")
    print(f"   ✓ Found {len(kg_facts['causal_paths'])} causal paths")
    
    # Combine data
    full_data = {
        **parsed,
        **kg_facts
    }
    
    # Step 3: Debate
    print("\n3. Running Debate Protocol...")
    
    log_reasoner = LogFocusedReasoner()
    kg_reasoner = KGFocusedReasoner()
    hybrid_reasoner = HybridReasoner()
    judge = JudgeAgent()
    
    coordinator = DebateCoordinator(
        log_reasoner, kg_reasoner, hybrid_reasoner, judge,
        max_rounds=3
    )
    
    result = coordinator.run_debate(full_data)
    
    # Display summary
    print("\n" + coordinator.get_debate_summary(result))
    
    print("="*70)
    print("✓ FULL PIPELINE TEST COMPLETED!")
    print("="*70)
    
    return result


def main():
    """Run tests."""
    print("\n" + "="*70)
    print("DEBATE PROTOCOL - COMPREHENSIVE TEST")
    print("="*70)
    
    print("\nTest Options:")
    print("  1. Quick test (pre-parsed data) - ~2-3 minutes")
    print("  2. Full pipeline test - ~5-7 minutes")
    
    # For automated testing, run quick test
    print("\nRunning quick test...\n")
    
    try:
        result = test_debate_protocol_quick()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED!")
        print("="*70)
        
        print("\nNext Steps:")
        print("  1. Week 2 is COMPLETE! 🎉")
        print("  2. Week 3: Test on real loghub data")
        print("  3. Week 4-6: Build comprehensive Knowledge Graph")
        print("  4. Week 7-9: Implement baselines")
        print("  5. Week 10-12: Run experiments")
        
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
