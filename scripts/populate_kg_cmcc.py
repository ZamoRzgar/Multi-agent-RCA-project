#!/usr/bin/env python3
"""
Script to populate Knowledge Graph with CMCC/OpenStack-specific data.
Extracts entities from CMCC log CSV files for RAG and multi-agent pipelines.
"""

import sys
import re
import json
from pathlib import Path

# Add src to path
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


def extract_cmcc_entities(log_df: pd.DataFrame) -> list:
    """
    Extract CMCC/OpenStack-specific entities from log DataFrame.
    Returns list of dicts with name, type, and category.
    """
    entities = []
    seen = set()
    
    # Get unique components
    if 'Component' in log_df.columns:
        for component in log_df['Component'].dropna().unique():
            if component and component not in seen:
                seen.add(component)
                entities.append({
                    'name': str(component),
                    'type': 'openstack_component',
                    'category': _categorize_openstack_component(str(component))
                })
    
    # Extract from Content column
    if 'Content' in log_df.columns:
        content_text = ' '.join(log_df['Content'].dropna().astype(str).tolist())
        
        # Pattern for OpenStack service names
        service_pattern = re.compile(r'\b(nova|neutron|keystone|glance|cinder|swift|heat|horizon|oslo)[._-]?[a-zA-Z0-9_.]*', re.I)
        for match in service_pattern.findall(content_text):
            clean_name = match.lower()
            if clean_name not in seen and len(clean_name) > 3:
                seen.add(clean_name)
                entities.append({
                    'name': clean_name,
                    'type': 'openstack_service',
                    'category': _categorize_openstack_service(clean_name)
                })
        
        # Pattern for IP addresses
        ip_pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d+)?)')
        for match in ip_pattern.findall(content_text):
            if match not in seen:
                seen.add(match)
                entities.append({
                    'name': match,
                    'type': 'host',
                    'category': 'infrastructure'
                })
        
        # Pattern for instance/VM IDs (UUID format)
        uuid_pattern = re.compile(r'\b([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b', re.I)
        uuids_found = 0
        for match in uuid_pattern.findall(content_text):
            if match not in seen and uuids_found < 5:  # Limit UUIDs to avoid noise
                seen.add(match)
                entities.append({
                    'name': match,
                    'type': 'instance_id',
                    'category': 'compute'
                })
                uuids_found += 1
        
        # Pattern for database/queue related
        db_pattern = re.compile(r'\b(mysql|rabbitmq|amqp|database|db)\b', re.I)
        for match in db_pattern.findall(content_text):
            clean_name = match.lower()
            if clean_name not in seen:
                seen.add(clean_name)
                entities.append({
                    'name': clean_name,
                    'type': 'infrastructure_service',
                    'category': 'infrastructure'
                })
    
    return entities


def _categorize_openstack_component(component: str) -> str:
    """Categorize an OpenStack component."""
    comp_lower = component.lower()
    
    if 'nova' in comp_lower:
        return 'compute'
    elif 'neutron' in comp_lower or 'network' in comp_lower or 'linuxbridge' in comp_lower:
        return 'network'
    elif 'keystone' in comp_lower or 'auth' in comp_lower:
        return 'identity'
    elif 'glance' in comp_lower or 'image' in comp_lower:
        return 'image'
    elif 'cinder' in comp_lower or 'volume' in comp_lower:
        return 'storage'
    elif 'oslo' in comp_lower:
        return 'oslo_library'
    elif 'amqp' in comp_lower or 'rabbit' in comp_lower:
        return 'messaging'
    elif 'mysql' in comp_lower or 'db' in comp_lower:
        return 'database'
    else:
        return 'other'


def _categorize_openstack_service(service: str) -> str:
    """Categorize an OpenStack service name."""
    svc_lower = service.lower()
    
    if 'nova' in svc_lower:
        return 'compute'
    elif 'neutron' in svc_lower:
        return 'network'
    elif 'keystone' in svc_lower:
        return 'identity'
    elif 'glance' in svc_lower:
        return 'image'
    elif 'cinder' in svc_lower:
        return 'storage'
    elif 'oslo' in svc_lower:
        return 'oslo_library'
    else:
        return 'other'


def load_cmcc_labels() -> dict:
    """Load CMCC labels from config.json."""
    config_file = Path(__file__).parent.parent / "loghub" / "LogKG" / "data" / "config.json"
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    labels = {}
    for label, case_ids in config.items():
        for case_id in case_ids:
            labels[case_id] = label
    
    return labels


def populate_kg_from_cmcc(driver, clear_first: bool = False):
    """
    Populate KG from CMCC dataset CSV files.
    """
    cmcc_dir = Path(__file__).parent.parent / "loghub" / "LogKG" / "data" / "CMCC_case"
    labels = load_cmcc_labels()
    
    logger.info(f"Found {len(labels)} CMCC cases")
    
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
        for case_id, label in labels.items():
            case_file = cmcc_dir / f"{case_id}.csv"
            if not case_file.exists():
                logger.warning(f"Case file not found: {case_file}")
                continue
            
            # Load CSV
            try:
                df = pd.read_csv(case_file)
            except Exception as e:
                logger.warning(f"Failed to load {case_file}: {e}")
                continue
            
            # Create Incident node with hypothesis and root_cause for RAG retrieval
            root_cause_desc = _get_root_cause_description(label)
            hypothesis_text = _get_hypothesis_text(label)
            session.run("""
                MERGE (i:Incident {incident_id: $incident_id})
                SET i.dataset = 'CMCC',
                    i.ground_truth = $ground_truth,
                    i.log_count = $log_count,
                    i.root_cause = $root_cause,
                    i.hypothesis = $hypothesis,
                    i.failure_type = $failure_type,
                    i.created_at = datetime()
            """,
                incident_id=case_id,
                ground_truth=label,
                log_count=len(df),
                root_cause=root_cause_desc,
                hypothesis=hypothesis_text,
                failure_type=label
            )
            stats['incidents'] += 1
            
            # Create RootCause node based on ground truth label
            session.run("""
                MATCH (i:Incident {incident_id: $incident_id})
                MERGE (rc:RootCause {name: $name})
                SET rc.description = $description,
                    rc.failure_type = $failure_type,
                    rc.category = $category
                MERGE (i)-[:HAS_ROOT_CAUSE]->(rc)
            """,
                incident_id=case_id,
                name=label,
                description=root_cause_desc,
                failure_type=label,
                category=_get_coarse_category(label)
            )
            stats['root_causes'] += 1
            stats['relationships'] += 1
            
            # Extract entities from log content
            entities = extract_cmcc_entities(df)
            
            # Separate entities by type
            openstack_entities = [e for e in entities if e['type'] in ('openstack_component', 'openstack_service')]
            host_entities = [e for e in entities if e['type'] == 'host']
            other_entities = [e for e in entities if e['type'] not in ('openstack_component', 'openstack_service', 'host')]
            
            # Batch insert OpenStack components
            if openstack_entities:
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    UNWIND $batch as item
                    MERGE (e:Entity:OpenStackComponent {name: item.name})
                    SET e.type = item.type, e.category = item.category
                    MERGE (i)-[:INVOLVES]->(e)
                """, incident_id=case_id, batch=openstack_entities)
            
            # Batch insert Host entities
            if host_entities:
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    UNWIND $batch as item
                    MERGE (e:Entity:Host {name: item.name})
                    SET e.type = item.type, e.category = item.category
                    MERGE (i)-[:INVOLVES]->(e)
                """, incident_id=case_id, batch=host_entities)
            
            # Batch insert other entities
            if other_entities:
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    UNWIND $batch as item
                    MERGE (e:Entity {name: item.name})
                    SET e.type = item.type, e.category = item.category
                    MERGE (i)-[:INVOLVES]->(e)
                """, incident_id=case_id, batch=other_entities)
            
            stats['entities'] += len(entities)
            stats['relationships'] += len(entities)
            
            logger.debug(f"Processed {case_id} ({label}): {len(entities)} entities")
        
        # Create similarity relationships between incidents with same failure type
        session.run("""
            MATCH (i1:Incident), (i2:Incident)
            WHERE i1 <> i2 
              AND i1.ground_truth = i2.ground_truth
              AND i1.ground_truth IS NOT NULL
            MERGE (i1)-[s:SIMILAR_TO]-(i2)
            SET s.reason = 'same_failure_type'
        """)
        
        # Create relationships between incidents sharing entities
        session.run("""
            MATCH (i1:Incident)-[:INVOLVES]->(e:Entity)<-[:INVOLVES]-(i2:Incident)
            WHERE i1 <> i2
            WITH i1, i2, count(e) as shared_entities
            WHERE shared_entities >= 2
            MERGE (i1)-[s:SHARES_ENTITIES]-(i2)
            SET s.count = shared_entities
        """)
    
    return stats


def _get_root_cause_description(label: str) -> str:
    """Get a description for the root cause based on label."""
    descriptions = {
        'Normal': 'System operating normally with no detected faults',
        'AMQP': 'Message queue (RabbitMQ/AMQP) connection or communication failure',
        'Mysql': 'Database (MySQL) connection or query failure',
        'Down': 'Service unavailable or not responding',
        'CreateErrorFlavor': 'OpenStack flavor creation failed due to configuration or resource issues',
        'CreateErrorLinuxbridgeAgent': 'Network agent (Linuxbridge) failed to initialize or communicate',
        'CreateErrorNovaConductor': 'Nova conductor service failed during orchestration'
    }
    return descriptions.get(label, f'Unknown failure type: {label}')


def _get_hypothesis_text(label: str) -> str:
    """Get a detailed hypothesis text for RAG retrieval based on label."""
    hypotheses = {
        'Normal': 'The system is operating normally. All OpenStack services (Nova, Neutron, Keystone) are functioning correctly with no errors detected in the logs.',
        'AMQP': 'RabbitMQ message broker connection failure detected. The OpenStack services cannot communicate via AMQP protocol. Look for AMQPConnectionError, connection refused to broker, oslo.messaging timeout, or RPC response timeout errors. Resolution: Check RabbitMQ service status and network connectivity.',
        'Mysql': 'MySQL database connection failure detected. OpenStack services cannot connect to the database backend. Look for OperationalError, connection lost, database connection refused, or MySQL server has gone away errors. Resolution: Check MySQL service status and credentials.',
        'Down': 'One or more OpenStack services are down or not responding. Look for connection refused errors, service unreachable, errno 111, or timeout errors when connecting to service endpoints. Resolution: Restart the affected service and check system resources.',
        'CreateErrorFlavor': 'Nova flavor creation or lookup failed. The requested instance flavor (e.g., m1.small, m1.medium) could not be found or created. Look for FlavorNotFound, invalid flavor, or flavor creation errors. Resolution: Verify flavor exists in Nova and check Nova API.',
        'CreateErrorLinuxbridgeAgent': 'Neutron Linuxbridge agent failed to initialize or communicate. Network configuration for VMs cannot be applied. Look for linuxbridge agent errors, arp_protect failures, or bridge interface errors. Resolution: Check Neutron agent status and network configuration.',
        'CreateErrorNovaConductor': 'Nova conductor service failed during VM orchestration. The conductor cannot coordinate between Nova components. Look for nova-conductor errors, RPC to conductor failures, or conductor service unavailable. Resolution: Restart nova-conductor and check RabbitMQ connectivity.'
    }
    return hypotheses.get(label, f'Unknown failure type requiring investigation: {label}')


def _get_coarse_category(label: str) -> str:
    """Get coarse category for a label."""
    if label == 'Normal':
        return 'normal'
    elif label in ('AMQP', 'Mysql'):
        return 'infrastructure'
    elif label == 'Down':
        return 'service_down'
    elif label in ('CreateErrorFlavor', 'CreateErrorLinuxbridgeAgent', 'CreateErrorNovaConductor'):
        return 'openstack_error'
    return 'unknown'


def main():
    """Main function to populate KG with CMCC data."""
    logger.info("=" * 60)
    logger.info("CMCC Knowledge Graph Population")
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
    
    # Populate KG (clear existing data first)
    stats = populate_kg_from_cmcc(driver, clear_first=True)
    
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
        
        # Show incidents by failure type
        result = session.run("""
            MATCH (i:Incident)
            RETURN i.ground_truth as failure_type, count(*) as count
            ORDER BY count DESC
        """)
        logger.info(f"\nIncidents by failure type:")
        for record in result:
            logger.info(f"  - {record['failure_type']}: {record['count']}")
        
        # Show sample OpenStack entities
        result = session.run("""
            MATCH (e:Entity)
            WHERE e.type IN ['openstack_component', 'openstack_service']
            RETURN DISTINCT e.name as name, e.category as category
            LIMIT 15
        """)
        logger.info(f"\nSample OpenStack entities:")
        for record in result:
            logger.info(f"  - {record['name']} ({record['category']})")
    
    driver.close()
    logger.success("\n✅ CMCC KG population complete!")


if __name__ == "__main__":
    main()
