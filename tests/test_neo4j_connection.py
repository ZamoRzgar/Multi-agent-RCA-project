"""
Test Neo4j connection.

This script verifies that Neo4j is running and accessible.
"""

from neo4j import GraphDatabase

# Connection details - UPDATE THESE IF NEEDED
URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "1997Amaterasu"  # Change this to your actual password

def test_connection():
    """Test Neo4j connection."""
    try:
        # Create driver
        print(f"Connecting to Neo4j at {URI}...")
        driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
        
        # Verify connectivity
        driver.verify_connectivity()
        print("✓ Connected to Neo4j successfully!")
        
        # Test query
        with driver.session() as session:
            result = session.run("RETURN 'Hello, Neo4j!' AS message")
            message = result.single()["message"]
            print(f"✓ Query result: {message}")
        
        # Check Neo4j version
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions[0] AS version")
            for record in result:
                print(f"✓ {record['name']} version: {record['version']}")
        
        # Close connection
        driver.close()
        print("✓ Connection closed successfully!")
        
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check if Neo4j is running")
        print("2. Verify the URI (bolt://localhost:7687)")
        print("3. Check username and password")
        print("4. Ensure port 7687 is not blocked")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n" + "="*60)
        print("✓ Neo4j is ready to use!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("✗ Please fix the connection issues above")
        print("="*60)
