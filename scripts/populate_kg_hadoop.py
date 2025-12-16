#!/usr/bin/env python3
"""
Script to populate Knowledge Graph with Hadoop-specific data from validation results.
Extracts actual Java class names and entities from evidence snippets.
"""

import sys
import re
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
from loguru import logger
from neo4j import GraphDatabase


def load_config():
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    if 'knowledge_graph' in config:
        if '${NEO4J_PASSWORD}' in str(config['knowledge_graph'].get('password', '')):
            config['knowledge_graph']['password'] = '1997Amaterasu'
    
    return config


def extract_hadoop_entities(evidence_lines: list) -> list:
    """
    Extract Hadoop-specific entities from evidence snippets.
    Returns list of dicts with name, type, and optional metadata.
    """
    entities = []
    seen = set()
    
    # Pattern for fully-qualified Java class names (org.apache.hadoop.*)
    java_class_pattern = re.compile(r'(org\.apache\.hadoop\.[a-zA-Z0-9_.]+)')
    
    # Pattern for org.mortbay and other common packages
    other_class_pattern = re.compile(r'(org\.mortbay\.[a-zA-Z0-9_.]+)')
    
    # Pattern for IP addresses (hosts)
    ip_pattern = re.compile(r'(/?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)')
    
    # Pattern for HDFS paths
    hdfs_pattern = re.compile(r'(hdfs://[^\s]+)')
    
    # Pattern for container IDs
    container_pattern = re.compile(r'(container_\d+_\d+_\d+_\d+)')
    
    # Pattern for application IDs
    app_pattern = re.compile(r'(application_\d+_\d+)')
    
    # Pattern for block IDs
    block_pattern = re.compile(r'(blk_\d+_\d+|BP-[^\s:]+)')
    
    for line in evidence_lines:
        if not isinstance(line, str):
            continue
            
        # Extract Java class names
        for match in java_class_pattern.findall(line):
            # Clean up - remove trailing punctuation
            clean_name = match.rstrip('.,;:')
            if clean_name not in seen:
                seen.add(clean_name)
                entities.append({
                    'name': clean_name,
                    'type': 'hadoop_component',
                    'category': _categorize_hadoop_class(clean_name)
                })
        
        # Extract other class names (mortbay, etc.)
        for match in other_class_pattern.findall(line):
            clean_name = match.rstrip('.,;:')
            if clean_name not in seen:
                seen.add(clean_name)
                entities.append({
                    'name': clean_name,
                    'type': 'external_component',
                    'category': 'web_server'
                })
        
        # Extract IP addresses as hosts
        for match in ip_pattern.findall(line):
            clean_ip = match.lstrip('/')
            if clean_ip not in seen:
                seen.add(clean_ip)
                entities.append({
                    'name': clean_ip,
                    'type': 'host',
                    'category': 'infrastructure'
                })
    
    return entities


def _categorize_hadoop_class(class_name: str) -> str:
    """Categorize a Hadoop class name into a functional category."""
    name_lower = class_name.lower()
    
    if 'hdfs' in name_lower or 'dfs' in name_lower or 'datanode' in name_lower or 'namenode' in name_lower:
        return 'hdfs'
    elif 'mapred' in name_lower or 'mapreduce' in name_lower:
        return 'mapreduce'
    elif 'yarn' in name_lower:
        return 'yarn'
    elif 'ipc' in name_lower or 'rpc' in name_lower:
        return 'rpc'
    elif 'http' in name_lower or 'webapp' in name_lower:
        return 'web'
    elif 'metrics' in name_lower:
        return 'metrics'
    elif 'conf' in name_lower:
        return 'config'
    else:
        return 'core'


def populate_kg_from_hadoop_results(driver, results_file: str, clear_first: bool = False):
    """
    Populate KG from Hadoop validation results JSON.
    """
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    logger.info(f"Loaded {len(results)} Hadoop application results")
    
    stats = {
        'incidents': 0,
        'entities': 0,
        'root_causes': 0,
        'relationships': 0
    }
    
    if clear_first:
        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.warning("Cleared existing KG data")
    
    with driver.session() as session:
        for result in results:
            app_id = result.get('application_id', 'unknown')
            dataset = result.get('dataset', 'Hadoop1')
            
            # Create Incident node
            session.run("""
                MERGE (i:Incident {incident_id: $incident_id})
                SET i.dataset = $dataset,
                    i.ground_truth = $ground_truth,
                    i.predicted_category = $predicted_category,
                    i.predicted_failure_type = $predicted_failure_type,
                    i.final_score = $final_score,
                    i.final_hypothesis = $hypothesis,
                    i.confidence = $confidence,
                    i.strict_match = $strict_match,
                    i.created_at = datetime()
            """,
                incident_id=app_id,
                dataset=dataset,
                ground_truth=result.get('ground_truth', ''),
                predicted_category=result.get('predicted_category', ''),
                predicted_failure_type=result.get('predicted_failure_type', ''),
                final_score=result.get('final_score', 0),
                hypothesis=result.get('hypothesis', ''),
                confidence=result.get('confidence', 0),
                strict_match=result.get('strict_match', False)
            )
            stats['incidents'] += 1
            
            # Create RootCause node
            hypothesis = result.get('hypothesis', '')
            if hypothesis:
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    MERGE (rc:RootCause {description: $hypothesis})
                    SET rc.confidence = $confidence,
                        rc.failure_type = $failure_type
                    MERGE (i)-[:HAS_ROOT_CAUSE]->(rc)
                """,
                    incident_id=app_id,
                    hypothesis=hypothesis,
                    confidence=result.get('confidence', 0),
                    failure_type=result.get('predicted_failure_type', '')
                )
                stats['root_causes'] += 1
                stats['relationships'] += 1
            
            # Extract and create Entity nodes from evidence (BATCHED for performance)
            evidence = result.get('evidence_snippet', [])
            entities = extract_hadoop_entities(evidence)
            
            # Separate entities by type for batched insertion
            hadoop_entities = [
                {'name': e['name'], 'type': e['type'], 'category': e['category']}
                for e in entities if e['type'] == 'hadoop_component'
            ]
            host_entities = [
                {'name': e['name'], 'type': e['type'], 'category': e['category']}
                for e in entities if e['type'] == 'host'
            ]
            other_entities = [
                {'name': e['name'], 'type': e['type'], 'category': e['category']}
                for e in entities if e['type'] not in ('hadoop_component', 'host')
            ]
            
            # Batch insert Hadoop components
            if hadoop_entities:
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    UNWIND $batch as item
                    MERGE (e:Entity:HadoopComponent {name: item.name})
                    SET e.type = item.type, e.category = item.category
                    MERGE (i)-[:INVOLVES]->(e)
                """, incident_id=app_id, batch=hadoop_entities)
            
            # Batch insert Host entities
            if host_entities:
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    UNWIND $batch as item
                    MERGE (e:Entity:Host {name: item.name})
                    SET e.type = item.type, e.category = item.category
                    MERGE (i)-[:INVOLVES]->(e)
                """, incident_id=app_id, batch=host_entities)
            
            # Batch insert other entities
            if other_entities:
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    UNWIND $batch as item
                    MERGE (e:Entity {name: item.name})
                    SET e.type = item.type, e.category = item.category
                    MERGE (i)-[:INVOLVES]->(e)
                """, incident_id=app_id, batch=other_entities)
            
            stats['entities'] += len(entities)
            stats['relationships'] += len(entities)
            
            logger.debug(f"Processed {app_id}: {len(entities)} entities")
        
        # Create similarity relationships between incidents with same failure type
        session.run("""
            MATCH (i1:Incident), (i2:Incident)
            WHERE i1 <> i2 
              AND i1.predicted_failure_type = i2.predicted_failure_type
              AND i1.predicted_failure_type IS NOT NULL
              AND i1.predicted_failure_type <> 'unknown'
            MERGE (i1)-[s:SIMILAR_TO]-(i2)
            SET s.reason = 'same_failure_type'
        """)
        
        # Create relationships between incidents sharing entities
        session.run("""
            MATCH (i1:Incident)-[:INVOLVES]->(e:Entity)<-[:INVOLVES]-(i2:Incident)
            WHERE i1 <> i2
            WITH i1, i2, count(e) as shared_entities
            WHERE shared_entities >= 3
            MERGE (i1)-[s:SHARES_ENTITIES]-(i2)
            SET s.count = shared_entities
        """)
    
    return stats


def main():
    """Main function to populate KG with Hadoop data."""
    logger.info("=" * 60)
    logger.info("Hadoop Knowledge Graph Population")
    logger.info("=" * 60)
    
    config = load_config()
    kg_config = config.get('knowledge_graph', {})
    
    uri = kg_config.get('uri', 'bolt://localhost:7687')
    user = kg_config.get('user', 'neo4j')
    password = kg_config.get('password', 'neo4j')
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {uri}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return
    
    # Find Hadoop results file
    results_file = Path(__file__).parent.parent / "docs" / "week6_validation_results" / "HADOOP1_GROUND_TRUTH_RESULTS.json"
    
    if not results_file.exists():
        # Try alternative location
        results_file = Path(__file__).parent.parent / "docs" / "HADOOP1_GROUND_TRUTH_RESULTS.json"
    
    if not results_file.exists():
        logger.error(f"Hadoop results file not found")
        return
    
    logger.info(f"Using results file: {results_file}")
    
    # Populate KG (clear existing data first)
    stats = populate_kg_from_hadoop_results(driver, str(results_file), clear_first=True)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("POPULATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Incidents created: {stats['incidents']}")
    logger.info(f"Entities created: {stats['entities']}")
    logger.info(f"Root causes created: {stats['root_causes']}")
    logger.info(f"Relationships created: {stats['relationships']}")
    
    # Verify with counts
    with driver.session() as session:
        result = session.run("""
            MATCH (i:Incident) WITH count(i) as incidents
            MATCH (e:Entity) WITH incidents, count(e) as entities
            MATCH (rc:RootCause) WITH incidents, entities, count(rc) as root_causes
            MATCH ()-[r]->() 
            RETURN incidents, entities, root_causes, count(r) as relationships
        """)
        record = result.single()
        if record:
            logger.info(f"\nFinal KG Statistics:")
            logger.info(f"  Incidents: {record['incidents']}")
            logger.info(f"  Entities: {record['entities']}")
            logger.info(f"  Root Causes: {record['root_causes']}")
            logger.info(f"  Relationships: {record['relationships']}")
        
        # Show sample Hadoop entities
        result = session.run("""
            MATCH (e:Entity)
            WHERE e.type = 'hadoop_component'
            RETURN e.name as name, e.category as category
            LIMIT 15
        """)
        logger.info(f"\nSample Hadoop entities:")
        for record in result:
            logger.info(f"  - {record['name']} ({record['category']})")
    
    driver.close()
    logger.success("\n✅ Hadoop KG population complete!")


if __name__ == "__main__":
    main()
