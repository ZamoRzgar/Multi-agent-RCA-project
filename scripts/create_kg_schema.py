"""
Create Knowledge Graph Schema in Neo4j.

This script creates:
- Constraints for uniqueness
- Indexes for performance
"""

from neo4j import GraphDatabase

# Connection details - UPDATE THESE IF NEEDED
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "1997Amaterasu"  # Change this to your actual password

def create_schema():
    """Create KG schema (constraints and indexes)."""
    print("Creating Knowledge Graph schema...")
    print("="*60)
    
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    
    try:
        with driver.session() as session:
            # Create constraints for uniqueness
            print("\n1. Creating constraints...")
            
            constraints = [
                "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
                "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT error_id IF NOT EXISTS FOR (e:Error) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT template_id IF NOT EXISTS FOR (t:Template) REQUIRE t.id IS UNIQUE",
                "CREATE CONSTRAINT root_cause_id IF NOT EXISTS FOR (rc:RootCause) REQUIRE rc.id IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                    constraint_name = constraint.split()[2]
                    print(f"  ✓ Created constraint: {constraint_name}")
                except Exception as e:
                    if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                        constraint_name = constraint.split()[2]
                        print(f"  ✓ Constraint already exists: {constraint_name}")
                    else:
                        print(f"  ✗ Error creating constraint: {e}")
            
            # Create indexes for performance
            print("\n2. Creating indexes...")
            
            indexes = [
                ("CREATE INDEX incident_timestamp IF NOT EXISTS FOR (i:Incident) ON (i.timestamp)", "incident_timestamp"),
                ("CREATE INDEX incident_dataset IF NOT EXISTS FOR (i:Incident) ON (i.dataset)", "incident_dataset"),
                ("CREATE INDEX incident_severity IF NOT EXISTS FOR (i:Incident) ON (i.severity)", "incident_severity"),
                ("CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp)", "event_timestamp"),
                ("CREATE INDEX event_component IF NOT EXISTS FOR (e:Event) ON (e.component)", "event_component"),
                ("CREATE INDEX event_severity IF NOT EXISTS FOR (e:Event) ON (e.severity)", "event_severity"),
                ("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)", "entity_name"),
                ("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)", "entity_type"),
                ("CREATE INDEX error_type IF NOT EXISTS FOR (e:Error) ON (e.error_type)", "error_type"),
                ("CREATE INDEX template_pattern IF NOT EXISTS FOR (t:Template) ON (t.pattern)", "template_pattern")
            ]
            
            for index_query, index_name in indexes:
                try:
                    session.run(index_query)
                    print(f"  ✓ Created index: {index_name}")
                except Exception as e:
                    if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                        print(f"  ✓ Index already exists: {index_name}")
                    else:
                        print(f"  ✗ Error creating index: {e}")
            
            # Verify schema
            print("\n3. Verifying schema...")
            
            # Check constraints
            result = session.run("SHOW CONSTRAINTS")
            constraint_count = len(list(result))
            print(f"  ✓ Total constraints: {constraint_count}")
            
            # Check indexes
            result = session.run("SHOW INDEXES")
            index_count = len(list(result))
            print(f"  ✓ Total indexes: {index_count}")
            
            print("\n" + "="*60)
            print("✓ Schema created successfully!")
            print("="*60)
            
    except Exception as e:
        print(f"\n✗ Error creating schema: {e}")
        return False
    
    finally:
        driver.close()
    
    return True

if __name__ == "__main__":
    success = create_schema()
    if not success:
        print("\nPlease fix the errors above and try again.")
