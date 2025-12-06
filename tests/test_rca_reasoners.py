"""
Test RCA Reasoner Agents.

This script tests all three RCA reasoners with sample data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.rca_log_reasoner import LogFocusedReasoner
from src.agents.rca_kg_reasoner import KGFocusedReasoner
from src.agents.rca_hybrid_reasoner import HybridReasoner
import json


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
            },
            {
                "type": "block",
                "name": "blk_123",
                "context": "HDFS block"
            }
        ],
        "timeline": [
            {
                "timestamp": "2025-12-06T10:00:00",
                "component": "DataNode",
                "message": "Disk usage at 95%"
            },
            {
                "timestamp": "2025-12-06T10:00:10",
                "component": "DataNode",
                "message": "Block replication failed"
            },
            {
                "timestamp": "2025-12-06T10:00:15",
                "component": "NameNode",
                "message": "Block marked as under-replicated"
            }
        ],
        
        # KG data (from KG Retrieval Agent)
        "similar_incidents": [
            {
                "incident_id": "HDFS_001",
                "similarity_score": 6.5,
                "dataset": "HDFS",
                "label": "Block Replication Failure",
                "root_cause": "DataNode disk full",
                "components": ["DataNode", "NameNode"]
            },
            {
                "incident_id": "HDFS_002",
                "similarity_score": 4.0,
                "dataset": "HDFS",
                "label": "Block Replication Failure",
                "root_cause": "Network connectivity issue",
                "components": ["DataNode", "NameNode"]
            }
        ],
        "causal_paths": [
            {
                "path_length": 2,
                "error_type": "DiskFullException",
                "events": [
                    {"component": "DataNode", "action": "disk_check"},
                    {"component": "DataNode", "action": "replication_failed"},
                    {"component": "NameNode", "action": "block_marked"}
                ]
            }
        ],
        "entity_context": {
            "/10.0.1.5": {
                "type": "host",
                "event_count": 2,
                "incident_count": 1,
                "recent_severities": ["WARN", "ERROR"]
            }
        },
        "patterns": [
            {
                "pattern": "DataNode → DataNode",
                "frequency": 2
            }
        ]
    }


def test_log_focused_reasoner():
    """Test Log-Focused Reasoner."""
    print("="*70)
    print("Testing Log-Focused Reasoner (Mistral-7B)")
    print("="*70)
    
    reasoner = LogFocusedReasoner()
    sample_data = get_sample_data()
    
    print("\n1. Input Data:")
    print(f"   - Events: {len(sample_data['events'])}")
    print(f"   - Errors: {len(sample_data['error_messages'])}")
    print(f"   - Entities: {len(sample_data['entities'])}")
    
    print("\n2. Generating hypotheses...")
    result = reasoner.process(sample_data)
    
    print(f"\n3. Results:")
    print(f"   ✓ Reasoning Type: {result['reasoning_type']}")
    print(f"   ✓ Model Used: {result['model_used']}")
    print(f"   ✓ Hypotheses Generated: {result['num_hypotheses']}")
    
    if result['hypotheses']:
        print(f"\n4. Top Hypothesis:")
        top = result['hypotheses'][0]
        print(f"   - Hypothesis: {top['hypothesis']}")
        print(f"   - Confidence: {top['confidence']:.2f}")
        print(f"   - Category: {top['category']}")
        print(f"   - Reasoning: {top['reasoning'][:150]}...")
        print(f"   - Evidence: {len(top['evidence'])} items")
        print(f"   - Resolution: {top['suggested_resolution'][:100]}...")
        
        print(f"\n5. All Hypotheses Summary:")
        for i, h in enumerate(result['hypotheses'], 1):
            print(f"   {i}. [{h['confidence']:.2f}] {h['hypothesis'][:80]}...")
    else:
        print("\n✗ No hypotheses generated")
    
    print("\n" + "="*70)
    return result


def test_kg_focused_reasoner():
    """Test KG-Focused Reasoner."""
    print("\n" + "="*70)
    print("Testing KG-Focused Reasoner (LLaMA2-7B)")
    print("="*70)
    
    reasoner = KGFocusedReasoner()
    sample_data = get_sample_data()
    
    print("\n1. Input Data:")
    print(f"   - Similar Incidents: {len(sample_data['similar_incidents'])}")
    print(f"   - Causal Paths: {len(sample_data['causal_paths'])}")
    print(f"   - Entity Context: {len(sample_data['entity_context'])}")
    print(f"   - Patterns: {len(sample_data['patterns'])}")
    
    print("\n2. Generating hypotheses...")
    result = reasoner.process(sample_data)
    
    print(f"\n3. Results:")
    print(f"   ✓ Reasoning Type: {result['reasoning_type']}")
    print(f"   ✓ Model Used: {result['model_used']}")
    print(f"   ✓ Hypotheses Generated: {result['num_hypotheses']}")
    
    if result['hypotheses']:
        print(f"\n4. Top Hypothesis:")
        top = result['hypotheses'][0]
        print(f"   - Hypothesis: {top['hypothesis']}")
        print(f"   - Confidence: {top['confidence']:.2f}")
        print(f"   - Category: {top['category']}")
        print(f"   - Reasoning: {top['reasoning'][:150]}...")
        print(f"   - Evidence: {len(top['evidence'])} items")
        
        print(f"\n5. All Hypotheses Summary:")
        for i, h in enumerate(result['hypotheses'], 1):
            print(f"   {i}. [{h['confidence']:.2f}] {h['hypothesis'][:80]}...")
    else:
        print("\n✗ No hypotheses generated")
    
    print("\n" + "="*70)
    return result


def test_hybrid_reasoner():
    """Test Hybrid Reasoner."""
    print("\n" + "="*70)
    print("Testing Hybrid Reasoner (Qwen2-7B)")
    print("="*70)
    
    reasoner = HybridReasoner()
    sample_data = get_sample_data()
    
    print("\n1. Input Data:")
    print(f"   - Events: {len(sample_data['events'])}")
    print(f"   - Errors: {len(sample_data['error_messages'])}")
    print(f"   - Similar Incidents: {len(sample_data['similar_incidents'])}")
    print(f"   - Causal Paths: {len(sample_data['causal_paths'])}")
    
    print("\n2. Generating hypotheses...")
    result = reasoner.process(sample_data)
    
    print(f"\n3. Results:")
    print(f"   ✓ Reasoning Type: {result['reasoning_type']}")
    print(f"   ✓ Model Used: {result['model_used']}")
    print(f"   ✓ Hypotheses Generated: {result['num_hypotheses']}")
    
    if result['hypotheses']:
        print(f"\n4. Top Hypothesis:")
        top = result['hypotheses'][0]
        print(f"   - Hypothesis: {top['hypothesis']}")
        print(f"   - Confidence: {top['confidence']:.2f}")
        print(f"   - Category: {top['category']}")
        print(f"   - Reasoning: {top['reasoning'][:150]}...")
        print(f"   - Evidence: {len(top['evidence'])} items")
        
        print(f"\n5. All Hypotheses Summary:")
        for i, h in enumerate(result['hypotheses'], 1):
            print(f"   {i}. [{h['confidence']:.2f}] {h['hypothesis'][:80]}...")
    else:
        print("\n✗ No hypotheses generated")
    
    print("\n" + "="*70)
    return result


def compare_results(log_result, kg_result, hybrid_result):
    """Compare results from all three reasoners."""
    print("\n" + "="*70)
    print("COMPARISON OF ALL THREE REASONERS")
    print("="*70)
    
    print("\n1. Number of Hypotheses:")
    print(f"   - Log-Focused:  {log_result['num_hypotheses']}")
    print(f"   - KG-Focused:   {kg_result['num_hypotheses']}")
    print(f"   - Hybrid:       {hybrid_result['num_hypotheses']}")
    
    print("\n2. Top Hypothesis Confidence:")
    if log_result['hypotheses']:
        print(f"   - Log-Focused:  {log_result['hypotheses'][0]['confidence']:.2f}")
    if kg_result['hypotheses']:
        print(f"   - KG-Focused:   {kg_result['hypotheses'][0]['confidence']:.2f}")
    if hybrid_result['hypotheses']:
        print(f"   - Hybrid:       {hybrid_result['hypotheses'][0]['confidence']:.2f}")
    
    print("\n3. Root Cause Categories:")
    for name, result in [("Log", log_result), ("KG", kg_result), ("Hybrid", hybrid_result)]:
        if result['hypotheses']:
            categories = [h['category'] for h in result['hypotheses']]
            print(f"   - {name:12}: {', '.join(set(categories))}")
    
    print("\n4. Consensus Analysis:")
    all_hypotheses = []
    if log_result['hypotheses']:
        all_hypotheses.extend([(h['hypothesis'], 'log') for h in log_result['hypotheses']])
    if kg_result['hypotheses']:
        all_hypotheses.extend([(h['hypothesis'], 'kg') for h in kg_result['hypotheses']])
    if hybrid_result['hypotheses']:
        all_hypotheses.extend([(h['hypothesis'], 'hybrid') for h in hybrid_result['hypotheses']])
    
    if all_hypotheses:
        print(f"   - Total unique perspectives: {len(all_hypotheses)}")
        print(f"   - Reasoners agree on disk/resource issues: "
              f"{sum(1 for h, _ in all_hypotheses if 'disk' in h.lower() or 'space' in h.lower())} times")
    
    print("\n" + "="*70)


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("RCA REASONER AGENTS - COMPREHENSIVE TEST")
    print("="*70)
    print("\nTesting all three RCA reasoning agents with sample HDFS incident data.")
    print("This will take several minutes as each agent calls its LLM...")
    
    try:
        # Test each reasoner
        log_result = test_log_focused_reasoner()
        kg_result = test_kg_focused_reasoner()
        hybrid_result = test_hybrid_reasoner()
        
        # Compare results
        compare_results(log_result, kg_result, hybrid_result)
        
        print("\n" + "="*70)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nNext Steps:")
        print("  1. Review the hypotheses generated by each reasoner")
        print("  2. Implement Judge Agent (Week 2, Day 6)")
        print("  3. Implement Debate Protocol (Week 2, Day 7)")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n✗ Some tests failed. Please check the errors above.")
        sys.exit(1)
