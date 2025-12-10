#!/usr/bin/env python3
"""
Query and explore the Knowledge Graph.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
from neo4j import GraphDatabase
from loguru import logger


def load_config():
    """Load configuration."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_queries():
    """Run exploratory queries on the KG."""
    config = load_config()
    kg_config = config['knowledge_graph']
    
    driver = GraphDatabase.driver(
        kg_config['uri'],
        auth=(kg_config['user'], kg_config['password'])
    )
    
    print("=" * 70)
    print("KNOWLEDGE GRAPH EXPLORATION")
    print("=" * 70)
    
    with driver.session() as session:
        # Query 1: All incidents
        print("\n1️⃣  ALL INCIDENTS")
        print("-" * 70)
        result = session.run("""
            MATCH (i:Incident)
            RETURN i.incident_id, i.dataset, i.scenario_id, i.final_score, i.final_hypothesis
            ORDER BY i.dataset, i.scenario_id
        """)
        for record in result:
            print(f"  📋 {record['i.incident_id']}")
            print(f"     Dataset: {record['i.dataset']} | Scenario: {record['i.scenario_id']} | Score: {record['i.final_score']}")
            print(f"     Diagnosis: {record['i.final_hypothesis']}")
            print()
        
        # Query 2: Entity distribution
        print("\n2️⃣  ENTITY DISTRIBUTION")
        print("-" * 70)
        result = session.run("""
            MATCH (e:Entity)<-[:INVOLVES]-(i:Incident)
            RETURN e.name, e.type, count(i) as incident_count
            ORDER BY incident_count DESC
        """)
        for record in result:
            print(f"  🔹 {record['e.name']} ({record['e.type']}): {record['incident_count']} incidents")
        
        # Query 3: Similar incidents
        print("\n3️⃣  SIMILAR INCIDENTS (Connected by SIMILAR_TO)")
        print("-" * 70)
        result = session.run("""
            MATCH (i1:Incident)-[s:SIMILAR_TO]-(i2:Incident)
            WHERE elementId(i1) < elementId(i2)
            RETURN i1.dataset, i1.scenario_id, i2.dataset, i2.scenario_id, s.score_diff
            ORDER BY s.score_diff
            LIMIT 10
        """)
        count = 0
        for record in result:
            print(f"  🔗 {record['i1.dataset']} S{record['i1.scenario_id']} ↔ {record['i2.dataset']} S{record['i2.scenario_id']} (score diff: {record['s.score_diff']})")
            count += 1
        if count == 0:
            print("  ℹ️  No similar incidents found (may need to adjust similarity threshold)")
        
        # Query 4: Root causes by dataset
        print("\n4️⃣  ROOT CAUSES BY DATASET")
        print("-" * 70)
        result = session.run("""
            MATCH (i:Incident)-[:HAS_ROOT_CAUSE]->(rc:RootCause)
            RETURN i.dataset, rc.description, rc.confidence, count(*) as frequency
            ORDER BY i.dataset, frequency DESC
        """)
        current_dataset = None
        for record in result:
            if current_dataset != record['i.dataset']:
                current_dataset = record['i.dataset']
                print(f"\n  📊 {current_dataset}:")
            print(f"     • {record['rc.description']}")
            print(f"       Confidence: {record['rc.confidence']:.2f} | Frequency: {record['frequency']}")
        
        # Query 5: Network-related incidents (example retrieval)
        print("\n5️⃣  EXAMPLE RETRIEVAL: Network-Related Incidents")
        print("-" * 70)
        result = session.run("""
            MATCH (i:Incident)-[:INVOLVES]->(e:Entity)
            WHERE e.name = 'Network'
            RETURN i.incident_id, i.dataset, i.final_hypothesis, i.final_score
            ORDER BY i.final_score DESC
        """)
        count = 0
        for record in result:
            print(f"  🌐 {record['i.incident_id']}")
            print(f"     Score: {record['i.final_score']} | {record['i.final_hypothesis']}")
            count += 1
        if count == 0:
            print("  ℹ️  No network-related incidents found")
        else:
            print(f"\n  ✅ Found {count} network-related incidents!")
        
        # Query 6: Graph statistics
        print("\n6️⃣  GRAPH STATISTICS")
        print("-" * 70)
        result = session.run("""
            MATCH (i:Incident)
            WITH count(i) as incidents
            MATCH (e:Entity)
            WITH incidents, count(e) as entities
            MATCH (rc:RootCause)
            WITH incidents, entities, count(rc) as root_causes
            MATCH ()-[r]->()
            RETURN incidents, entities, root_causes, count(r) as relationships
        """)
        record = result.single()
        print(f"  📈 Nodes:")
        print(f"     - Incidents: {record['incidents']}")
        print(f"     - Entities: {record['entities']}")
        print(f"     - Root Causes: {record['root_causes']}")
        print(f"  📈 Relationships: {record['relationships']}")
    
    driver.close()
    
    print("\n" + "=" * 70)
    print("✅ KG Exploration Complete!")
    print("=" * 70)
    print("\n💡 Next: Open Neo4j Browser at http://localhost:7474 to visualize!")
    print("   Try this query: MATCH (i:Incident)-[r]->(n) RETURN i,r,n LIMIT 25")


if __name__ == "__main__":
    run_queries()
