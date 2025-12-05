"""
Test KG Retrieval Agent.

This script tests the KGRetrievalAgent with sample data.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.kg_retrieval import KGRetrievalAgent
import json

def test_kg_retrieval_agent():
    """Test KG Retrieval Agent with sample data."""
    print("="*60)
    print("Testing KG Retrieval Agent")
    print("="*60)
    
    # Initialize agent
    print("\n1. Initializing KG Retrieval Agent...")
    agent = KGRetrievalAgent()
    
    if not agent.driver:
        print("✗ Failed to connect to Neo4j")
        print("\nPlease ensure:")
        print("  1. Neo4j is running")
        print("  2. Credentials in config/neo4j_config.yaml are correct")
        return False
    
    print("✓ Agent initialized successfully")
    
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
    print(f"   ✓ Similar incidents: {len(result['similar_incidents'])}")
    print(f"   ✓ Causal paths: {len(result['causal_paths'])}")
    print(f"   ✓ Entity context: {len(result['entity_context'])}")
    print(f"   ✓ Patterns: {len(result['patterns'])}")
    
    # Show sample results if available
    if result['similar_incidents']:
        print("\n5. Sample Similar Incident:")
        incident = result['similar_incidents'][0]
        print(f"   - ID: {incident['incident_id']}")
        print(f"   - Dataset: {incident['dataset']}")
        print(f"   - Label: {incident['label']}")
        print(f"   - Similarity: {incident['similarity_score']:.2f}")
        print(f"   - Root Cause: {incident['root_cause']}")
    else:
        print("\n5. No similar incidents found (KG is empty)")
        print("   This is expected if you haven't populated the KG yet")
    
    if result['causal_paths']:
        print("\n6. Sample Causal Path:")
        path = result['causal_paths'][0]
        print(f"   - Length: {path['path_length']}")
        print(f"   - Error Type: {path['error_type']}")
        print(f"   - Events in path: {len(path['events'])}")
    else:
        print("\n6. No causal paths found (KG is empty)")
    
    if result['entity_context']:
        print("\n7. Sample Entity Context:")
        entity_name = list(result['entity_context'].keys())[0]
        context = result['entity_context'][entity_name]
        print(f"   - Entity: {entity_name}")
        print(f"   - Type: {context['type']}")
        print(f"   - Event count: {context['event_count']}")
        print(f"   - Incident count: {context['incident_count']}")
    else:
        print("\n7. No entity context found (KG is empty)")
    
    if result['patterns']:
        print("\n8. Sample Pattern:")
        pattern = result['patterns'][0]
        print(f"   - Pattern: {pattern['pattern']}")
        print(f"   - Frequency: {pattern['frequency']}")
    else:
        print("\n8. No patterns found (KG is empty)")
    
    # Close connection
    agent.close()
    print("\n" + "="*60)
    print("✓ Test completed successfully!")
    print("="*60)
    
    # Note about empty results
    if not any([result['similar_incidents'], result['causal_paths'], 
                result['entity_context'], result['patterns']]):
        print("\nℹ️  Note: All results are empty because the KG hasn't been")
        print("   populated yet. This is expected at this stage.")
        print("\n   Next steps:")
        print("   1. Run: python scripts/create_kg_schema.py")
        print("   2. Populate KG with sample data")
        print("   3. Run this test again")
    
    return True

if __name__ == "__main__":
    success = test_kg_retrieval_agent()
    if not success:
        print("\n✗ Test failed. Please check the errors above.")
