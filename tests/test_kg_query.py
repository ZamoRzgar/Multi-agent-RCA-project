#!/usr/bin/env python3
"""
Test KG Query production code.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
from kg.query import KGQuery


def load_config():
    """Load configuration."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Test KG Query methods."""
    print("=" * 70)
    print("TESTING KG QUERY (Production Code)")
    print("=" * 70)
    
    config = load_config()
    kg_query = KGQuery(config)
    
    if not kg_query.driver:
        print("❌ Failed to connect to Neo4j")
        return
    
    print("\n✅ Connected to Neo4j\n")
    
    # Test 1: Find similar incidents for Network entity
    print("1️⃣  TEST: find_similar_incidents(['Network'])")
    print("-" * 70)
    incidents = kg_query.find_similar_incidents(['Network'], [], top_k=5)
    print(f"Found {len(incidents)} incidents:")
    for inc in incidents:
        print(f"  • {inc['incident_id']} ({inc['dataset']} S{inc['scenario_id']})")
        print(f"    Score: {inc['score']} | Matches: {inc['entity_matches']} entities")
        print(f"    Root Cause: {inc['root_cause']}")
    
    # Test 2: Get entity info
    print("\n2️⃣  TEST: get_entity_info('Network')")
    print("-" * 70)
    entity_info = kg_query.get_entity_info('Network')
    if entity_info:
        print(f"  Name: {entity_info['name']}")
        print(f"  Type: {entity_info['type']}")
        print(f"  Incident Count: {entity_info['incident_count']}")
        print(f"  Datasets: {', '.join(entity_info['datasets'])}")
    else:
        print("  ❌ Entity not found")
    
    # Test 3: Get all entities
    print("\n3️⃣  TEST: get_all_entities()")
    print("-" * 70)
    all_entities = kg_query.get_all_entities()
    print(f"Found {len(all_entities)} entities:")
    for ent in all_entities[:10]:  # Show top 10
        print(f"  • {ent['name']} ({ent['type']}): {ent['incident_count']} incidents")
    
    # Test 4: Multi-entity search
    print("\n4️⃣  TEST: find_similar_incidents(['Network', 'Configuration'])")
    print("-" * 70)
    incidents = kg_query.find_similar_incidents(['Network', 'Configuration'], [], top_k=3)
    print(f"Found {len(incidents)} incidents with Network OR Configuration:")
    for inc in incidents:
        print(f"  • {inc['dataset']} S{inc['scenario_id']}: {inc['hypothesis'][:60]}...")
        print(f"    Entity matches: {inc['entity_matches']}")
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)
    print("\n💡 The KG Query is ready to be used by KG Retrieval Agent!")


if __name__ == "__main__":
    main()
