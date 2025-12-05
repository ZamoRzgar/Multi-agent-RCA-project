"""
Populate Knowledge Graph with Sample Data.

This script creates sample incidents, events, entities, and relationships
for testing the KG Retrieval Agent.
"""

from neo4j import GraphDatabase
import yaml

# Load Neo4j config
with open("config/neo4j_config.yaml", "r") as f:
    config = yaml.safe_load(f)
    URI = config["neo4j"]["uri"]
    USERNAME = config["neo4j"]["username"]
    PASSWORD = config["neo4j"]["password"]

def populate_sample_data():
    """Populate KG with sample data."""
    print("="*60)
    print("Populating Knowledge Graph with Sample Data")
    print("="*60)
    
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
    try:
        with driver.session() as session:
            # Clear existing data (optional - comment out if you want to keep existing data)
            print("\n1. Clearing existing data...")
            session.run("MATCH (n) DETACH DELETE n")
            print("   ✓ Cleared")
            
            # Create sample incident 1: HDFS Block Replication Failure
            print("\n2. Creating sample incidents...")
            
            session.run("""
                CREATE (i:Incident {
                    id: 'HDFS_001',
                    timestamp: datetime('2025-12-01T10:00:00'),
                    dataset: 'HDFS',
                    label: 'Block Replication Failure',
                    severity: 'ERROR',
                    duration: 300,
                    resolved: true,
                    root_cause: 'DataNode disk full'
                })
            """)
            
            session.run("""
                CREATE (i:Incident {
                    id: 'HDFS_002',
                    timestamp: datetime('2025-12-02T14:30:00'),
                    dataset: 'HDFS',
                    label: 'Block Replication Failure',
                    severity: 'ERROR',
                    duration: 450,
                    resolved: true,
                    root_cause: 'Network connectivity issue'
                })
            """)
            
            session.run("""
                CREATE (i:Incident {
                    id: 'BGL_001',
                    timestamp: datetime('2025-12-03T08:15:00'),
                    dataset: 'BGL',
                    label: 'Node Failure',
                    severity: 'CRITICAL',
                    duration: 600,
                    resolved: true,
                    root_cause: 'Hardware failure'
                })
            """)
            
            print("   ✓ Created 3 incidents")
            
            # Create events for HDFS_001
            print("\n3. Creating events...")
            
            session.run("""
                MATCH (i:Incident {id: 'HDFS_001'})
                CREATE (e1:Event {
                    id: 'EVT_001',
                    timestamp: datetime('2025-12-01T09:59:50'),
                    component: 'DataNode',
                    action: 'disk_check',
                    severity: 'WARN',
                    message: 'Disk usage at 95%'
                })
                CREATE (e2:Event {
                    id: 'EVT_002',
                    timestamp: datetime('2025-12-01T10:00:00'),
                    component: 'DataNode',
                    action: 'replication_failed',
                    severity: 'ERROR',
                    message: 'Block replication failed: No space left'
                })
                CREATE (e3:Event {
                    id: 'EVT_003',
                    timestamp: datetime('2025-12-01T10:00:05'),
                    component: 'NameNode',
                    action: 'block_marked_under_replicated',
                    severity: 'WARN',
                    message: 'Block marked as under-replicated'
                })
                CREATE (i)-[:CONTAINS {sequence: 1}]->(e1)
                CREATE (i)-[:CONTAINS {sequence: 2}]->(e2)
                CREATE (i)-[:CONTAINS {sequence: 3}]->(e3)
                CREATE (e1)-[:CAUSES {confidence: 0.9, delay: 10}]->(e2)
                CREATE (e2)-[:CAUSES {confidence: 0.8, delay: 5}]->(e3)
                CREATE (e1)-[:PRECEDES {delay: 10}]->(e2)
                CREATE (e2)-[:PRECEDES {delay: 5}]->(e3)
            """)
            
            # Create events for HDFS_002
            session.run("""
                MATCH (i:Incident {id: 'HDFS_002'})
                CREATE (e4:Event {
                    id: 'EVT_004',
                    timestamp: datetime('2025-12-02T14:29:50'),
                    component: 'DataNode',
                    action: 'network_timeout',
                    severity: 'WARN',
                    message: 'Network timeout to NameNode'
                })
                CREATE (e5:Event {
                    id: 'EVT_005',
                    timestamp: datetime('2025-12-02T14:30:00'),
                    component: 'DataNode',
                    action: 'replication_failed',
                    severity: 'ERROR',
                    message: 'Block replication failed: Connection timeout'
                })
                CREATE (i)-[:CONTAINS {sequence: 1}]->(e4)
                CREATE (i)-[:CONTAINS {sequence: 2}]->(e5)
                CREATE (e4)-[:CAUSES {confidence: 0.85, delay: 10}]->(e5)
                CREATE (e4)-[:PRECEDES {delay: 10}]->(e5)
            """)
            
            print("   ✓ Created 5 events")
            
            # Create entities
            print("\n4. Creating entities...")
            
            session.run("""
                CREATE (e:Entity:Host {
                    id: 'HOST_001',
                    type: 'host',
                    name: '/10.0.1.5',
                    context: 'DataNode server'
                })
                CREATE (e2:Entity:Host {
                    id: 'HOST_002',
                    type: 'host',
                    name: '/10.0.1.6',
                    context: 'DataNode server'
                })
                CREATE (e3:Entity:Component {
                    id: 'COMP_001',
                    type: 'component',
                    name: 'DataNode',
                    context: 'HDFS DataNode service'
                })
                CREATE (e4:Entity:Component {
                    id: 'COMP_002',
                    type: 'component',
                    name: 'NameNode',
                    context: 'HDFS NameNode service'
                })
            """)
            
            print("   ✓ Created 4 entities")
            
            # Create errors
            print("\n5. Creating errors...")
            
            session.run("""
                CREATE (err1:Error {
                    id: 'ERR_001',
                    error_type: 'DiskFullException',
                    message: 'No space left on device',
                    component: 'DataNode',
                    frequency: 15
                })
                CREATE (err2:Error {
                    id: 'ERR_002',
                    error_type: 'NetworkTimeoutException',
                    message: 'Connection timeout',
                    component: 'DataNode',
                    frequency: 8
                })
            """)
            
            print("   ✓ Created 2 errors")
            
            # Create root causes
            print("\n6. Creating root causes...")
            
            session.run("""
                CREATE (rc1:RootCause {
                    id: 'RC_001',
                    description: 'Disk space exhausted on DataNode',
                    category: 'resource',
                    confidence: 0.95,
                    resolution: 'Clear disk space or add storage',
                    frequency: 12
                })
                CREATE (rc2:RootCause {
                    id: 'RC_002',
                    description: 'Network connectivity issue',
                    category: 'network',
                    confidence: 0.85,
                    resolution: 'Check network configuration and firewall',
                    frequency: 8
                })
            """)
            
            print("   ✓ Created 2 root causes")
            
            # Create relationships
            print("\n7. Creating relationships...")
            
            # Link events to entities
            session.run("""
                MATCH (e:Event {id: 'EVT_001'}), (entity:Entity {name: '/10.0.1.5'})
                CREATE (e)-[:INVOLVES {role: 'source'}]->(entity)
            """)
            
            session.run("""
                MATCH (e:Event {id: 'EVT_002'}), (entity:Entity {name: '/10.0.1.5'})
                CREATE (e)-[:INVOLVES {role: 'source'}]->(entity)
            """)
            
            # Link events to errors
            session.run("""
                MATCH (e:Event {id: 'EVT_002'}), (err:Error {id: 'ERR_001'})
                CREATE (e)-[:REPORTS]->(err)
            """)
            
            session.run("""
                MATCH (e:Event {id: 'EVT_005'}), (err:Error {id: 'ERR_002'})
                CREATE (e)-[:REPORTS]->(err)
            """)
            
            # Link incidents to root causes
            session.run("""
                MATCH (i:Incident {id: 'HDFS_001'}), (rc:RootCause {id: 'RC_001'})
                CREATE (i)-[:HAS_ROOT_CAUSE {confidence: 0.95}]->(rc)
            """)
            
            session.run("""
                MATCH (i:Incident {id: 'HDFS_002'}), (rc:RootCause {id: 'RC_002'})
                CREATE (i)-[:HAS_ROOT_CAUSE {confidence: 0.85}]->(rc)
            """)
            
            # Create similarity relationships (bidirectional)
            session.run("""
                MATCH (i1:Incident {id: 'HDFS_001'}), (i2:Incident {id: 'HDFS_002'})
                CREATE (i1)-[:SIMILAR_TO {similarity: 0.75, method: 'component_overlap'}]->(i2)
                CREATE (i2)-[:SIMILAR_TO {similarity: 0.75, method: 'component_overlap'}]->(i1)
            """)
            
            print("   ✓ Created relationships")
            
            # Verify data
            print("\n8. Verifying data...")
            
            result = session.run("MATCH (i:Incident) RETURN count(i) AS count")
            incident_count = result.single()["count"]
            print(f"   ✓ Incidents: {incident_count}")
            
            result = session.run("MATCH (e:Event) RETURN count(e) AS count")
            event_count = result.single()["count"]
            print(f"   ✓ Events: {event_count}")
            
            result = session.run("MATCH (e:Entity) RETURN count(e) AS count")
            entity_count = result.single()["count"]
            print(f"   ✓ Entities: {entity_count}")
            
            result = session.run("MATCH (e:Error) RETURN count(e) AS count")
            error_count = result.single()["count"]
            print(f"   ✓ Errors: {error_count}")
            
            result = session.run("MATCH (rc:RootCause) RETURN count(rc) AS count")
            rc_count = result.single()["count"]
            print(f"   ✓ Root Causes: {rc_count}")
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            rel_count = result.single()["count"]
            print(f"   ✓ Relationships: {rel_count}")
            
            print("\n" + "="*60)
            print("✓ Sample data populated successfully!")
            print("="*60)
            print("\nYou can now test the KG Retrieval Agent:")
            print("  python tests/test_kg_retrieval.py")
            
    except Exception as e:
        print(f"\n✗ Error populating data: {e}")
        return False
    
    finally:
        driver.close()
    
    return True

if __name__ == "__main__":
    success = populate_sample_data()
    if not success:
        print("\n✗ Failed to populate data. Please check the errors above.")
