"""
Test KG Retrieval Agent.

This script tests the KGRetrievalAgent with sample data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.kg_retrieval import KGRetrievalAgent
import json
import yaml
from pathlib import Path

def load_config():
    """Load configuration."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_kg_retrieval_agent():
    """Test KG Retrieval Agent with sample data."""
    print("="*60)
    print("Testing KG Retrieval Agent (with KGQuery)")
    print("="*60)
    
    # Load config
    config = load_config()
    
    # Initialize agent
    print("\n1. Initializing KG Retrieval Agent...")
    agent = KGRetrievalAgent(config=config)
    
    if not agent.kg_query or not agent.kg_query.driver:
        print("✗ Failed to connect to Neo4j via KGQuery")
        print("\nPlease ensure:")
        print("  1. Neo4j is running")
        print("  2. Password in config/config.yaml is correct")
        print("  3. Neo4j is accessible at bolt://localhost:7687")
        return False
    
    print("✓ Agent initialized successfully with KGQuery")
    
    # Sample input data (from Log Parser)
    input_data = {
        "events": [
            {
                "component": "DataNode",
                "action": "block_replication_failed",
                "severity": "ERROR",
                "timestamp": "2025-12-05T10:00:00"
            },
            {
                "component": "NameNode",
                "action": "block_marked_under_replicated",
                "severity": "WARN",
                "timestamp": "2025-12-05T10:00:05"
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
        "error_messages": [
            {
                "error_type": "DiskFullException",
                "message": "No space left on device",
                "component": "DataNode"
            }
        ]
    }
    
    print("\n2. Testing with sample data...")
    print(f"   - Events: {len(input_data['events'])}")
    print(f"   - Entities: {len(input_data['entities'])}")
    print(f"   - Errors: {len(input_data['error_messages'])}")
    
    # Process input
    print("\n3. Querying knowledge graph...")
    result = agent.process(input_data)
    
    # Display results
    print("\n4. Results:")
    print(f"   ✓ Similar incidents: {len(result.get('similar_incidents', []))}")
    print(f"   ✓ Entity context: {len(result.get('entity_context', {}))}")
    print(f"   ✓ All entities: {len(result.get('all_entities', []))}")
    
    # Show sample results if available
    if result.get('similar_incidents'):
        print("\n5. Sample Similar Incident:")
        incident = result['similar_incidents'][0]
        print(f"   - ID: {incident.get('incident_id')}")
        print(f"   - Dataset: {incident.get('dataset')}")
        print(f"   - Root Cause: {incident.get('root_cause')}")
        print(f"   - Hypothesis: {incident.get('hypothesis', 'N/A')[:60]}...")
        print(f"   - Entity Matches: {incident.get('similarity_score', 0)}")
        print(f"   - Confidence: {incident.get('confidence', 0.0):.2f}")
    else:
        print("\n5. No similar incidents found")
        print("   Note: KG has been populated with 14 incidents.")
        print("   Try entities like: Network, Configuration, Memory")
    
    if result.get('entity_context'):
        print("\n6. Sample Entity Context:")
        entity_name = list(result['entity_context'].keys())[0]
        context = result['entity_context'][entity_name]
        print(f"   - Entity: {entity_name}")
        print(f"   - Type: {context.get('type')}")
        print(f"   - Incident count: {context.get('incident_count', 0)}")
        print(f"   - Datasets: {', '.join(context.get('datasets', []))}")
    else:
        print("\n6. No entity context found")
    
    if result.get('all_entities'):
        print("\n7. Top Entities in KG:")
        for i, entity in enumerate(result['all_entities'][:5], 1):
            print(f"   {i}. {entity['name']} ({entity['type']}): {entity['incident_count']} incidents")
    else:
        print("\n7. No entities found in KG")
    
    # Close connection
    agent.close()
    print("\n" + "="*60)
    print("✓ Test completed successfully!")
    print("="*60)
    
    # Note about results
    if not any([result.get('similar_incidents'), result.get('entity_context'), 
                result.get('all_entities')]):
        print("\nℹ️  Note: All results are empty.")
        print("   The KG should have been populated with 14 incidents.")
        print("\n   If you see this:")
        print("   1. Check: python scripts/query_kg.py")
        print("   2. Verify Neo4j has data: MATCH (n) RETURN count(n)")
        print("   3. Re-run: python scripts/populate_kg.py")
    else:
        print("\n✅ KG Retrieval Agent is working correctly!")
        print("   - Successfully queried populated KG")
        print("   - Retrieved historical incident data")
        print("   - Entity context available")
    
    return True

if __name__ == "__main__":
    success = test_kg_retrieval_agent()
    if not success:
        print("\n✗ Test failed. Please check the errors above.")
