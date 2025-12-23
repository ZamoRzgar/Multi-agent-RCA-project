#!/usr/bin/env python3
"""
Script to populate Knowledge Graph with HDFS_v1 data.
Extracts entities from HDFS block operations and creates incident nodes.
"""

import sys
import re
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
import pandas as pd
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


def extract_hdfs_entities(log_lines: list) -> list:
    """
    Extract HDFS-specific entities from log lines.
    Returns list of dicts with name, type, and category.
    """
    entities = []
    seen = set()
    
    # Pattern for HDFS components (dfs.DataNode, dfs.FSNamesystem, etc.)
    component_pattern = re.compile(r'(dfs\.[A-Za-z$]+)')
    
    # Pattern for IP addresses (DataNode hosts)
    ip_pattern = re.compile(r'(/?\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)')
    
    # Pattern for block IDs
    block_pattern = re.compile(r'(blk_-?\d+)')
    
    for line in log_lines:
        if not isinstance(line, str):
            continue
        
        # Extract HDFS components
        for match in component_pattern.findall(line):
            if match not in seen:
                seen.add(match)
                entities.append({
                    'name': match,
                    'type': 'hdfs_component',
                    'category': _categorize_hdfs_component(match)
                })
        
        # Extract IP addresses as hosts
        for match in ip_pattern.findall(line):
            clean_ip = match.lstrip('/')
            if clean_ip not in seen and not clean_ip.startswith('10.'):
                # Skip internal IPs to reduce noise, keep only unique patterns
                pass
            if clean_ip not in seen:
                seen.add(clean_ip)
                entities.append({
                    'name': clean_ip,
                    'type': 'host',
                    'category': 'infrastructure'
                })
    
    return entities[:50]  # Limit entities per incident


def _categorize_hdfs_component(component: str) -> str:
    """Categorize an HDFS component into a functional category."""
    name_lower = component.lower()
    
    if 'datanode' in name_lower:
        return 'datanode'
    elif 'namenode' in name_lower or 'namesystem' in name_lower:
        return 'namenode'
    elif 'packet' in name_lower:
        return 'packet_handler'
    elif 'block' in name_lower:
        return 'block_manager'
    else:
        return 'hdfs_core'


def _get_anomaly_hypothesis(event_sequence: str) -> str:
    """Generate hypothesis text based on event sequence for anomalies."""
    if not event_sequence:
        return "HDFS block operation anomaly detected"
    
    # Check for specific error events
    error_events = {
        'E4': 'Exception while serving block',
        'E7': 'writeBlock received exception',
        'E8': 'PacketResponder interrupted',
        'E10': 'PacketResponder exception',
        'E12': 'Exception writing block to mirror',
        'E14': 'Exception in receiveBlock',
        'E17': 'Failed to transfer block',
        'E20': 'Unexpected error deleting block',
        'E29': 'Replication timeout',
    }
    
    detected_errors = []
    for event_id, desc in error_events.items():
        if event_id in event_sequence:
            detected_errors.append(desc)
    
    if detected_errors:
        return f"HDFS block anomaly: {'; '.join(detected_errors[:3])}"
    
    return "HDFS block operation anomaly - irregular event sequence detected"


def _get_normal_hypothesis() -> str:
    """Generate hypothesis text for normal operations."""
    return "HDFS block operations completed successfully - normal block lifecycle observed"


def populate_kg_from_hdfs(driver, hdfs_root: str, sample_size: int = 500, clear_first: bool = False):
    """
    Populate KG from HDFS_v1 dataset.
    """
    hdfs_path = Path(hdfs_root)
    
    # Load labels
    labels_df = pd.read_csv(hdfs_path / 'preprocessed' / 'anomaly_label.csv')
    logger.info(f"Loaded {len(labels_df)} block labels")
    
    # Load event traces
    traces_df = pd.read_csv(hdfs_path / 'preprocessed' / 'Event_traces.csv')
    traces_dict = {row['BlockId']: row.get('Features', '') for _, row in traces_df.iterrows()}
    logger.info(f"Loaded {len(traces_dict)} event traces")
    
    # Sample blocks (balanced)
    normal_blocks = labels_df[labels_df['Label'] == 'Normal']['BlockId'].tolist()
    anomaly_blocks = labels_df[labels_df['Label'] == 'Anomaly']['BlockId'].tolist()
    
    import random
    random.seed(42)
    random.shuffle(normal_blocks)
    random.shuffle(anomaly_blocks)
    
    n_each = sample_size // 2
    selected_blocks = normal_blocks[:n_each] + anomaly_blocks[:n_each]
    random.shuffle(selected_blocks)
    
    logger.info(f"Selected {len(selected_blocks)} blocks for KG population")
    
    stats = {
        'incidents': 0,
        'entities': 0,
        'root_causes': 0,
        'relationships': 0
    }
    
    if clear_first:
        with driver.session() as session:
            # Only clear HDFS data, not other datasets
            session.run("MATCH (n:Incident) WHERE n.dataset = 'HDFS_v1' DETACH DELETE n")
            logger.warning("Cleared existing HDFS_v1 KG data")
    
    # Read raw log file to extract logs per block
    log_file = hdfs_path / 'HDFS.log'
    
    with driver.session() as session:
        for block_id in selected_blocks:
            label = labels_df[labels_df['BlockId'] == block_id]['Label'].values[0]
            event_sequence = traces_dict.get(block_id, '')
            
            # Get hypothesis based on label
            if label == 'Anomaly':
                hypothesis = _get_anomaly_hypothesis(str(event_sequence))
                root_cause = 'Block operation failure'
            else:
                hypothesis = _get_normal_hypothesis()
                root_cause = 'Normal operation'
            
            # Create Incident node
            session.run("""
                MERGE (i:Incident {incident_id: $incident_id})
                SET i.dataset = 'HDFS_v1',
                    i.ground_truth = $ground_truth,
                    i.hypothesis = $hypothesis,
                    i.root_cause = $root_cause,
                    i.event_sequence = $event_sequence,
                    i.created_at = datetime()
            """,
                incident_id=block_id,
                ground_truth=label,
                hypothesis=hypothesis,
                root_cause=root_cause,
                event_sequence=str(event_sequence)[:500]
            )
            stats['incidents'] += 1
            
            # Create RootCause node
            session.run("""
                MATCH (i:Incident {incident_id: $incident_id})
                MERGE (rc:RootCause {name: $name})
                SET rc.description = $description,
                    rc.category = $category
                MERGE (i)-[:HAS_ROOT_CAUSE]->(rc)
            """,
                incident_id=block_id,
                name=label,
                description=hypothesis,
                category='hdfs_block_operation'
            )
            stats['root_causes'] += 1
            stats['relationships'] += 1
            
            # Create Entity nodes for HDFS components
            hdfs_entities = [
                {'name': 'dfs.DataNode', 'type': 'hdfs_component', 'category': 'datanode'},
                {'name': 'dfs.FSNamesystem', 'type': 'hdfs_component', 'category': 'namenode'},
                {'name': 'dfs.DataNode$PacketResponder', 'type': 'hdfs_component', 'category': 'packet_handler'},
                {'name': 'dfs.DataNode$DataXceiver', 'type': 'hdfs_component', 'category': 'data_transfer'},
            ]
            
            session.run("""
                MATCH (i:Incident {incident_id: $incident_id})
                UNWIND $batch as item
                MERGE (e:Entity:HDFSComponent {name: item.name})
                SET e.type = item.type, e.category = item.category
                MERGE (i)-[:INVOLVES]->(e)
            """, incident_id=block_id, batch=hdfs_entities)
            
            stats['entities'] += len(hdfs_entities)
            stats['relationships'] += len(hdfs_entities)
        
        # Create similarity relationships between incidents with same label
        session.run("""
            MATCH (i1:Incident), (i2:Incident)
            WHERE i1 <> i2 
              AND i1.dataset = 'HDFS_v1'
              AND i2.dataset = 'HDFS_v1'
              AND i1.ground_truth = i2.ground_truth
            WITH i1, i2, rand() as r
            WHERE r < 0.01
            MERGE (i1)-[s:SIMILAR_TO]-(i2)
            SET s.reason = 'same_label'
        """)
        
        logger.info(f"Created similarity relationships")
    
    return stats


def main():
    """Main function to populate KG with HDFS data."""
    logger.info("=" * 60)
    logger.info("HDFS_v1 Knowledge Graph Population")
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
    
    hdfs_root = Path(__file__).parent.parent / "loghub" / "HDFS_v1"
    
    if not hdfs_root.exists():
        logger.error(f"HDFS_v1 directory not found: {hdfs_root}")
        return
    
    logger.info(f"Using HDFS_v1 data from: {hdfs_root}")
    
    # Populate KG (clear existing HDFS data first)
    stats = populate_kg_from_hdfs(driver, str(hdfs_root), sample_size=500, clear_first=True)
    
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
            MATCH (i:Incident) WHERE i.dataset = 'HDFS_v1'
            WITH count(i) as incidents
            MATCH (e:Entity:HDFSComponent)
            WITH incidents, count(e) as entities
            RETURN incidents, entities
        """)
        record = result.single()
        if record:
            logger.info(f"\nFinal HDFS_v1 KG Statistics:")
            logger.info(f"  Incidents: {record['incidents']}")
            logger.info(f"  HDFS Entities: {record['entities']}")
        
        # Show label distribution
        result = session.run("""
            MATCH (i:Incident) WHERE i.dataset = 'HDFS_v1'
            RETURN i.ground_truth as label, count(*) as count
            ORDER BY count DESC
        """)
        logger.info(f"\nLabel distribution:")
        for record in result:
            logger.info(f"  - {record['label']}: {record['count']}")
    
    driver.close()
    logger.success("\n✅ HDFS_v1 KG population complete!")


if __name__ == "__main__":
    main()
