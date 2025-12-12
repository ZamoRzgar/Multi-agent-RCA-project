"""
Test RCA system on real HDFS data from loghub.

This script tests the complete multi-agent RCA system on actual
HDFS logs with real failure scenarios.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.loghub_loader import LoghubLoader
from src.agents.log_parser import LogParserAgent
from src.agents.kg_retrieval import KGRetrievalAgent
from src.agents.rca_log_reasoner import LogFocusedReasoner
from src.agents.rca_kg_reasoner import KGFocusedReasoner
from src.agents.rca_hybrid_reasoner import HybridReasoner
from src.agents.judge_agent import JudgeAgent
from src.debate.debate_coordinator import DebateCoordinator
from loguru import logger
import json
import yaml


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(title)
    print("="*70)


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


def test_hdfs_scenario(scenario_id: int = 1):
    """
    Test RCA system on a single HDFS scenario.
    
    Args:
        scenario_id: Which scenario to test (1-5)
    """
    print_section("HDFS REAL DATA TEST")
    print(f"Testing Scenario {scenario_id}")
    
    # Step 1: Load HDFS data
    print_section("STEP 1: LOADING HDFS DATA")
    
    loader = LoghubLoader()
    scenarios = loader.create_incident_scenarios(
        "HDFS",
        num_scenarios=5,
        logs_per_scenario=100
    )
    
    if scenario_id > len(scenarios):
        print(f"Error: Only {len(scenarios)} scenarios available")
        return
    
    scenario = scenarios[scenario_id - 1]
    
    print(f"✓ Loaded scenario {scenario_id}")
    print(f"  Dataset: {scenario['dataset']}")
    print(f"  Events: {scenario['num_events']}")
    print(f"  Entities: {len(scenario['entities'])}")
    print(f"  Errors: {len(scenario['error_messages'])}")
    
    # Step 2: Parse logs (already done by loader, but format for system)
    print_section("STEP 2: LOG PARSING")
    
    # The loader already provides parsed data in the right format
    parsed_data = {
        "events": scenario["events"],
        "entities": scenario["entities"],
        "error_messages": scenario["error_messages"],
        "timeline": scenario["events"]  # Already sorted by loader
    }
    
    print(f"✓ Parsed {len(parsed_data['events'])} events")
    print(f"✓ Extracted {len(parsed_data['entities'])} entities")
    print(f"✓ Found {len(parsed_data['error_messages'])} errors")
    
    # Step 3: KG Retrieval
    print_section("STEP 3: KNOWLEDGE GRAPH RETRIEVAL")
    
    # Load config for agents
    config = load_config()
    
    kg_agent = KGRetrievalAgent(config=config)
    
    try:
        kg_data = kg_agent.process(parsed_data)
        
        print(f"✓ Retrieved {len(kg_data.get('similar_incidents', []))} similar incidents")
        print(f"✓ Found {len(kg_data.get('entity_contexts', []))} entity contexts")
    except Exception as e:
        logger.warning(f"KG retrieval failed (expected if DB empty): {e}")
        kg_data = {
            "similar_incidents": [],
            "entity_contexts": []
        }
    
    # Combine data for reasoners
    combined_data = {**parsed_data, **kg_data}
    
    # Step 4: Run Debate Protocol
    print_section("STEP 4: DEBATE PROTOCOL")
    
    # Initialize reasoners with config
    log_reasoner = LogFocusedReasoner(config=config)
    kg_reasoner = KGFocusedReasoner(config=config)
    hybrid_reasoner = HybridReasoner(config=config)
    judge = JudgeAgent(config=config)
    
    # Initialize debate coordinator
    coordinator = DebateCoordinator(
        log_reasoner=log_reasoner,
        kg_reasoner=kg_reasoner,
        hybrid_reasoner=hybrid_reasoner,
        judge=judge,
        max_rounds=3,
        convergence_threshold=5.0
    )
    
    # Run debate
    results = coordinator.run_debate(combined_data)
    
    # Step 5: Display Results
    print_section("RESULTS")
    
    print(f"\nTotal Rounds: {results['total_rounds']}")
    print(f"Convergence: {'Yes' if results['convergence_achieved'] else 'No'}")
    print(f"Score Trajectory: {' → '.join(map(str, results['improvement_trajectory']))}")
    
    if len(results['improvement_trajectory']) > 1:
        improvement = results['improvement_trajectory'][-1] - results['improvement_trajectory'][0]
        print(f"Total Improvement: +{improvement} points")
    
    print("\n" + "-"*70)
    print("FINAL HYPOTHESIS")
    print("-"*70)
    
    final = results['final_hypothesis']
    print(f"\nScore: {final.get('judge_score', 0)}/100")
    print(f"Source: {final.get('source', 'N/A')}")
    print(f"Confidence: {final.get('confidence', 'N/A')}")
    print(f"Category: {final.get('category', 'N/A')}")
    
    print(f"\nHypothesis:")
    print(f"  {final['hypothesis']}")
    
    print(f"\nReasoning:")
    reasoning = final.get('reasoning', 'N/A')
    # Show full reasoning without truncation
    print(f"  {reasoning}")
    
    print(f"\nEvidence ({len(final.get('evidence', []))} items):")
    for i, evidence in enumerate(final.get('evidence', [])[:5], 1):
        print(f"  {i}. {evidence}")
    
    print(f"\nSuggested Resolution:")
    resolution = final.get('suggested_resolution', 'N/A')
    # Show full resolution without truncation
    print(f"  {resolution}")
    
    # Step 6: Analysis
    print_section("ANALYSIS")
    
    print("\nRound-by-Round Breakdown:")
    for round_result in results['rounds']:
        round_num = round_result['round_number']
        top = round_result['top_hypothesis']
        print(f"\nRound {round_num}:")
        print(f"  Top Score: {top['judge_score']}/100")
        print(f"  Source: {top['source']}")
        print(f"  Confidence: {top.get('confidence', 'N/A')}")
        print(f"  Category: {top.get('category', 'N/A')}")
        print(f"  Hypothesis: {top['hypothesis']}")  # Show full text
        print(f"  Reasoning: {top.get('reasoning', 'N/A')}")  # Show all chars
    
    print("\n" + "-"*70)
    
    # Save results
    output_file = f"hdfs_scenario_{scenario_id}_results.json"
    with open(output_file, 'w') as f:
        # Convert to JSON-serializable format
        json_results = {
            "scenario_id": scenario_id,
            "dataset": "HDFS",
            "num_events": scenario['num_events'],
            "total_rounds": results['total_rounds'],
            "convergence": results['convergence_achieved'],
            "score_trajectory": results['improvement_trajectory'],
            "final_score": final['judge_score'],
            "final_hypothesis": final['hypothesis'],
            "final_source": final['source']
        }
        json.dump(json_results, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    
    return results


def test_multiple_scenarios():
    """Test on multiple HDFS scenarios."""
    print_section("TESTING MULTIPLE HDFS SCENARIOS")
    
    all_results = []
    
    for scenario_id in range(1, 4):  # Test first 3 scenarios
        print(f"\n{'='*70}")
        print(f"SCENARIO {scenario_id}")
        print(f"{'='*70}")
        
        try:
            results = test_hdfs_scenario(scenario_id)
            all_results.append({
                "scenario_id": scenario_id,
                "success": True,
                "final_score": results['final_hypothesis']['judge_score'],
                "rounds": results['total_rounds'],
                "improvement": results['improvement_trajectory'][-1] - results['improvement_trajectory'][0]
            })
        except Exception as e:
            logger.error(f"Scenario {scenario_id} failed: {e}")
            all_results.append({
                "scenario_id": scenario_id,
                "success": False,
                "error": str(e)
            })
    
    # Summary
    print_section("SUMMARY - ALL SCENARIOS")
    
    successful = [r for r in all_results if r.get('success', False)]
    
    print(f"\nTotal Scenarios: {len(all_results)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(all_results) - len(successful)}")
    
    if successful:
        avg_score = sum(r['final_score'] for r in successful) / len(successful)
        avg_rounds = sum(r['rounds'] for r in successful) / len(successful)
        avg_improvement = sum(r['improvement'] for r in successful) / len(successful)
        
        print(f"\nAverage Final Score: {avg_score:.1f}/100")
        print(f"Average Rounds: {avg_rounds:.1f}")
        print(f"Average Improvement: +{avg_improvement:.1f} points")
    
    print("\n" + "="*70)
    print("✓ HDFS REAL DATA TESTING COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific scenario
        scenario_id = int(sys.argv[1])
        test_hdfs_scenario(scenario_id)
    else:
        # Test multiple scenarios
        test_multiple_scenarios()
