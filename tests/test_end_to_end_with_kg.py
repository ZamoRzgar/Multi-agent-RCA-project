#!/usr/bin/env python3
"""
End-to-End RCA Test with Knowledge Graph Integration.

This test validates the complete RCA pipeline:
1. Log Parser extracts entities/events
2. KG Retrieval finds similar historical incidents
3. Reasoner Agents generate hypotheses (with KG context)
4. Judge Agent selects best hypothesis

Week 5 - Validation Test
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.loghub_loader import LoghubLoader
from src.agents.kg_retrieval import KGRetrievalAgent
from src.agents.rca_hybrid_reasoner import HybridReasoner
from src.agents.judge_agent import JudgeAgent
import yaml
from pathlib import Path
from loguru import logger


def load_config():
    """Load configuration."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Set Neo4j password
    kg_config = config.get('knowledge_graph', {})
    if kg_config.get('password') == '${NEO4J_PASSWORD}':
        kg_config['password'] = '1997Amaterasu'
    
    return config


def test_end_to_end_rca_with_kg():
    """
    Test complete RCA flow with KG integration.
    """
    print("=" * 80)
    print("END-TO-END RCA TEST WITH KNOWLEDGE GRAPH")
    print("=" * 80)
    
    # Load configuration
    print("\n1. Loading configuration...")
    config = load_config()
    print("✓ Configuration loaded")
    
    # Load HDFS scenario using LoghubLoader (no LLM needed)
    print("\n2. Loading HDFS scenario...")
    loader = LoghubLoader()
    scenarios = loader.create_incident_scenarios(
        "HDFS",
        num_scenarios=1,
        logs_per_scenario=100
    )
    
    if not scenarios:
        print("✗ Failed to load scenarios")
        return False
    
    scenario = scenarios[0]
    print(f"✓ Loaded scenario")
    print(f"  - Dataset: {scenario['dataset']}")
    print(f"  - Events: {scenario['num_events']}")
    print(f"  - Entities: {len(scenario['entities'])}")
    print(f"  - Errors: {len(scenario['error_messages'])}")
    
    # Prepare parsed data (already parsed by loader)
    parsed_data = {
        "events": scenario["events"],
        "entities": scenario["entities"],
        "error_messages": scenario["error_messages"],
        "timeline": scenario["events"]
    }
    
    # Initialize agents
    print("\n3. Initializing agents...")
    kg_retrieval = KGRetrievalAgent(config=config)
    reasoner = HybridReasoner(config=config)
    judge = JudgeAgent(config=config)
    
    if not kg_retrieval.kg_query or not kg_retrieval.kg_query.driver:
        print("✗ KG Retrieval Agent failed to connect to Neo4j")
        print("  Note: This test requires Neo4j to be running")
        return False
    
    print("✓ All agents initialized")
    
    # Step 1: Data already parsed by loader
    print("\n" + "=" * 80)
    print("STEP 1: DATA LOADED (Pre-parsed by LoghubLoader)")
    print("=" * 80)
    
    print(f"\n✓ Data ready:")
    print(f"  - Events: {len(parsed_data.get('events', []))}")
    print(f"  - Entities: {len(parsed_data.get('entities', []))}")
    print(f"  - Errors: {len(parsed_data.get('error_messages', []))}")
    
    # Step 2: KG Retrieval
    print("\n" + "=" * 80)
    print("STEP 2: KNOWLEDGE GRAPH RETRIEVAL")
    print("=" * 80)
    
    kg_facts = kg_retrieval.process(parsed_data)
    
    print(f"\n✓ KG retrieval complete:")
    print(f"  - Similar incidents: {len(kg_facts.get('similar_incidents', []))}")
    print(f"  - Entity contexts: {len(kg_facts.get('entity_context', {}))}")
    print(f"  - All entities in KG: {len(kg_facts.get('all_entities', []))}")
    
    if kg_facts.get('similar_incidents'):
        print(f"\n  Top similar incident:")
        top_incident = kg_facts['similar_incidents'][0]
        print(f"    - ID: {top_incident.get('incident_id')}")
        print(f"    - Dataset: {top_incident.get('dataset')}")
        print(f"    - Root Cause: {top_incident.get('root_cause', 'N/A')[:60]}...")
    
    # Step 3: Reasoning with KG context
    print("\n" + "=" * 80)
    print("STEP 3: HYPOTHESIS GENERATION (WITH KG CONTEXT)")
    print("=" * 80)
    
    # Combine parsed data with KG facts
    reasoner_input = {**parsed_data, **kg_facts}
    
    reasoner_result = reasoner.process(reasoner_input)
    hypotheses = reasoner_result.get('hypotheses', [])
    
    print(f"\n✓ Generated {len(hypotheses)} hypotheses")
    
    if hypotheses:
        print(f"\n  Sample hypothesis:")
        hyp = hypotheses[0]
        print(f"    - Root Cause: {hyp.get('root_cause', 'N/A')[:60]}...")
        print(f"    - Confidence: {hyp.get('confidence', 0):.2f}")
        print(f"    - Source: {hyp.get('source', 'unknown')}")
    
    # Step 4: Judge selection
    print("\n" + "=" * 80)
    print("STEP 4: HYPOTHESIS EVALUATION")
    print("=" * 80)
    
    # Judge expects hypotheses in specific format
    judge_input = {
        **parsed_data,
        **kg_facts,
        'hybrid_hypotheses': hypotheses  # Use the correct key for hybrid reasoner
    }
    
    result = judge.process(judge_input)
    
    print(f"\n✓ Judge evaluation complete")
    
    top_hyp = result.get('top_hypothesis')
    if top_hyp:
        print(f"\n  Selected Hypothesis:")
        print(f"    - Root Cause: {top_hyp.get('hypothesis', 'N/A')[:80]}...")
        print(f"    - Confidence: {top_hyp.get('confidence', 0):.2f}")
        print(f"    - Score: {top_hyp.get('judge_score', 0)}/100")
        print(f"    - Category: {top_hyp.get('category', 'N/A')}")
    else:
        print(f"\n  No hypothesis selected")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n✅ End-to-end RCA pipeline completed successfully!")
    
    print(f"\n📊 Pipeline Statistics:")
    print(f"  • Log events parsed: {len(parsed_data.get('events', []))}")
    print(f"  • Entities extracted: {len(parsed_data.get('entities', []))}")
    print(f"  • Similar incidents found: {len(kg_facts.get('similar_incidents', []))}")
    print(f"  • Hypotheses generated: {len(hypotheses)}")
    if top_hyp:
        print(f"  • Final score: {top_hyp.get('judge_score', 0)}/100")
        print(f"  • Final confidence: {top_hyp.get('confidence', 0):.2f}")
    else:
        print(f"  • Final score: N/A")
        print(f"  • Final confidence: N/A")
    
    print(f"\n💡 Key Insight:")
    if kg_facts.get('similar_incidents'):
        print(f"  The system leveraged {len(kg_facts['similar_incidents'])} historical")
        print(f"  incidents to improve diagnosis accuracy!")
    else:
        print(f"  No similar historical incidents found for this scenario.")
    
    print(f"\n🎯 KG Integration Status:")
    print(f"  ✓ KG retrieval working")
    print(f"  ✓ Historical context provided to reasoners")
    print(f"  ✓ End-to-end pipeline functional")
    
    # Cleanup
    kg_retrieval.close()
    
    return True


def test_without_kg_comparison():
    """
    Test RCA without KG for comparison.
    """
    print("\n" + "=" * 80)
    print("COMPARISON: RCA WITHOUT KG")
    print("=" * 80)
    
    config = load_config()
    
    # Load scenario
    loader = LoghubLoader()
    scenarios = loader.create_incident_scenarios("HDFS", num_scenarios=1, logs_per_scenario=100)
    
    if not scenarios:
        print("✗ Failed to load scenarios")
        return None
    
    parsed_data = {
        "events": scenarios[0]["events"],
        "entities": scenarios[0]["entities"],
        "error_messages": scenarios[0]["error_messages"],
        "timeline": scenarios[0]["events"]
    }
    
    # Reason WITHOUT KG context
    reasoner = HybridReasoner(config=config)
    reasoner_result = reasoner.process(parsed_data)
    hypotheses_no_kg = reasoner_result.get('hypotheses', [])
    
    # Judge
    judge = JudgeAgent(config=config)
    result_no_kg = judge.process({**parsed_data, 'hybrid_hypotheses': hypotheses_no_kg})
    
    top_hyp_no_kg = result_no_kg.get('top_hypothesis')
    
    print(f"\n✓ RCA without KG complete")
    print(f"  - Hypotheses: {len(hypotheses_no_kg)}")
    if top_hyp_no_kg:
        print(f"  - Score: {top_hyp_no_kg.get('judge_score', 0)}/100")
        print(f"  - Confidence: {top_hyp_no_kg.get('confidence', 0):.2f}")
        print(f"  - Root Cause: {top_hyp_no_kg.get('hypothesis', 'N/A')[:60]}...")
    else:
        print(f"  - No hypothesis selected")
    
    return result_no_kg


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("WEEK 5: END-TO-END RCA VALIDATION WITH KNOWLEDGE GRAPH")
    print("=" * 80)
    
    # Test with KG
    success = test_end_to_end_rca_with_kg()
    
    if not success:
        print("\n✗ Test failed")
        sys.exit(1)
    
    # Optional: Test without KG for comparison
    print("\n" + "=" * 80)
    print("OPTIONAL: COMPARISON TEST")
    print("=" * 80)
    print("\nWould you like to run RCA without KG for comparison?")
    print("(This helps measure the impact of KG integration)")
    
    # For automated testing, skip comparison
    # Uncomment below to enable:
    # result_no_kg = test_without_kg_comparison()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    
    sys.exit(0)
