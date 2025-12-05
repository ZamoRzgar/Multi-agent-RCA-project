# KG Retrieval Agent Implementation Guide

**Purpose**: Implement the Knowledge Graph Retrieval Agent  
**Date**: December 5, 2025  
**Estimated Time**: 4-6 hours

---

## 🎯 Overview

The **KG Retrieval Agent** queries the Neo4j knowledge graph to:
1. Find similar past incidents
2. Discover causal paths
3. Retrieve entity context
4. Provide historical patterns for RCA

---

## 📋 Prerequisites

Before implementing:
- [x] Neo4j installed and running
- [x] Python neo4j driver installed
- [x] KG schema designed
- [x] Sample data populated (for testing)

---

## 🏗️ Architecture

```
KGRetrievalAgent
├── __init__()              # Initialize Neo4j connection
├── process()               # Main entry point
├── query_similar_incidents() # Find similar incidents
├── find_causal_paths()     # Discover cause-effect chains
├── get_entity_context()    # Retrieve entity information
├── get_common_patterns()   # Find recurring patterns
├── _execute_query()        # Execute Cypher query
└── close()                 # Close connection
```

---

## 📝 Implementation Steps

### Step 1: Create Base Class Structure

**File**: `src/agents/kg_retrieval.py`

```python
"""
Knowledge Graph Retrieval Agent

Queries Neo4j knowledge graph to retrieve:
- Similar past incidents
- Causal paths
- Entity context
- Historical patterns
"""

from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from loguru import logger
import yaml

from src.agents.base_agent import BaseAgent


class KGRetrievalAgent(BaseAgent):
    """
    Agent for retrieving information from knowledge graph.
    
    Responsibilities:
    - Query similar incidents
    - Find causal paths
    - Retrieve entity context
    - Identify patterns
    """
    
    def __init__(
        self,
        name: str = "KGRetrieval",
        model: str = "qwen2:7b",
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "your_password"
    ):
        """
        Initialize KG Retrieval Agent.
        
        Args:
            name: Agent name
            model: LLM model (for future use)
            uri: Neo4j connection URI
            username: Neo4j username
            password: Neo4j password
        """
        super().__init__(name=name, model=model)
        
        # Initialize Neo4j driver
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method.
        
        Args:
            input_data: Dictionary with:
                - events: List of events from Log Parser
                - entities: List of entities
                - error_messages: List of errors
                
        Returns:
            Dictionary with:
                - similar_incidents: List of similar past incidents
                - causal_paths: List of causal chains
                - entity_context: Context for entities
                - patterns: Common patterns
        """
        logger.info("Retrieving information from knowledge graph")
        
        events = input_data.get("events", [])
        entities = input_data.get("entities", [])
        errors = input_data.get("error_messages", [])
        
        # Query similar incidents
        similar_incidents = self.query_similar_incidents(events, entities, errors)
        
        # Find causal paths
        causal_paths = self.find_causal_paths(events, errors)
        
        # Get entity context
        entity_context = self.get_entity_context(entities)
        
        # Get common patterns
        patterns = self.get_common_patterns(events)
        
        result = {
            "similar_incidents": similar_incidents,
            "causal_paths": causal_paths,
            "entity_context": entity_context,
            "patterns": patterns
        }
        
        logger.info(f"Retrieved {len(similar_incidents)} similar incidents, "
                   f"{len(causal_paths)} causal paths")
        
        return result
    
    def close(self):
        """Close Neo4j connection."""
        if hasattr(self, 'driver'):
            self.driver.close()
            logger.info("Closed Neo4j connection")
```

---

### Step 2: Implement Similar Incident Query

```python
    def query_similar_incidents(
        self,
        events: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar past incidents based on events, entities, and errors.
        
        Args:
            events: List of events
            entities: List of entities
            errors: List of errors
            limit: Maximum number of results
            
        Returns:
            List of similar incidents with similarity scores
        """
        logger.info("Querying similar incidents")
        
        # Extract components and error types for matching
        components = list(set(e.get("component", "") for e in events if e.get("component")))
        error_types = list(set(e.get("error_type", "") for e in errors if e.get("error_type")))
        entity_names = list(set(e.get("name", "") for e in entities if e.get("name")))
        
        # Build Cypher query
        query = """
        // Find incidents with similar components
        MATCH (i:Incident)-[:CONTAINS]->(e:Event)
        WHERE e.component IN $components
        
        // Optional: Match error types
        OPTIONAL MATCH (e)-[:REPORTS]->(err:Error)
        WHERE err.error_type IN $error_types
        
        // Optional: Match entities
        OPTIONAL MATCH (e)-[:INVOLVES]->(entity:Entity)
        WHERE entity.name IN $entity_names
        
        // Calculate similarity score
        WITH i, 
             count(DISTINCT e) AS event_matches,
             count(DISTINCT err) AS error_matches,
             count(DISTINCT entity) AS entity_matches
        
        WITH i,
             (event_matches * 1.0 + error_matches * 2.0 + entity_matches * 1.5) AS similarity_score
        
        WHERE similarity_score > 0
        
        // Get incident details
        MATCH (i)-[:CONTAINS]->(ie:Event)
        OPTIONAL MATCH (i)-[:HAS_ROOT_CAUSE]->(rc:RootCause)
        
        RETURN i.id AS incident_id,
               i.timestamp AS timestamp,
               i.dataset AS dataset,
               i.label AS label,
               i.root_cause AS root_cause,
               similarity_score,
               collect(DISTINCT ie.component) AS components,
               rc.description AS root_cause_description,
               rc.category AS root_cause_category
        
        ORDER BY similarity_score DESC
        LIMIT $limit
        """
        
        parameters = {
            "components": components,
            "error_types": error_types,
            "entity_names": entity_names,
            "limit": limit
        }
        
        results = self._execute_query(query, parameters)
        
        # Format results
        similar_incidents = []
        for record in results:
            similar_incidents.append({
                "incident_id": record["incident_id"],
                "timestamp": str(record["timestamp"]),
                "dataset": record["dataset"],
                "label": record["label"],
                "root_cause": record["root_cause"],
                "root_cause_description": record["root_cause_description"],
                "root_cause_category": record["root_cause_category"],
                "similarity_score": record["similarity_score"],
                "components": record["components"]
            })
        
        logger.info(f"Found {len(similar_incidents)} similar incidents")
        return similar_incidents
```

---

### Step 3: Implement Causal Path Discovery

```python
    def find_causal_paths(
        self,
        events: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find causal paths leading to errors.
        
        Args:
            events: List of events
            errors: List of errors
            max_depth: Maximum path length
            
        Returns:
            List of causal paths
        """
        logger.info("Finding causal paths")
        
        # Extract error types
        error_types = list(set(e.get("error_type", "") for e in errors if e.get("error_type")))
        
        if not error_types:
            logger.warning("No error types provided, skipping causal path search")
            return []
        
        # Build Cypher query
        query = f"""
        // Find causal chains leading to errors
        MATCH path = (e1:Event)-[:CAUSES*1..{max_depth}]->(e2:Event)-[:REPORTS]->(err:Error)
        WHERE err.error_type IN $error_types
        
        // Get path details
        WITH path, err, length(path) AS path_length
        
        // Extract nodes and relationships
        UNWIND nodes(path) AS node
        WITH path, err, path_length, collect(DISTINCT node) AS path_nodes
        
        UNWIND relationships(path) AS rel
        WITH path, err, path_length, path_nodes, collect(DISTINCT rel) AS path_rels
        
        // Return path information
        RETURN 
            [n IN path_nodes | {{
                component: n.component,
                action: n.action,
                timestamp: toString(n.timestamp),
                message: n.message
            }}] AS events,
            [r IN path_rels | {{
                type: type(r),
                confidence: r.confidence,
                delay: r.delay
            }}] AS relationships,
            err.error_type AS error_type,
            err.message AS error_message,
            path_length
        
        ORDER BY path_length DESC
        LIMIT 10
        """
        
        parameters = {"error_types": error_types}
        
        results = self._execute_query(query, parameters)
        
        # Format results
        causal_paths = []
        for record in results:
            causal_paths.append({
                "events": record["events"],
                "relationships": record["relationships"],
                "error_type": record["error_type"],
                "error_message": record["error_message"],
                "path_length": record["path_length"]
            })
        
        logger.info(f"Found {len(causal_paths)} causal paths")
        return causal_paths
```

---

### Step 4: Implement Entity Context Retrieval

```python
    def get_entity_context(
        self,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Retrieve context for entities from knowledge graph.
        
        Args:
            entities: List of entities
            
        Returns:
            Dictionary with entity context
        """
        logger.info("Retrieving entity context")
        
        entity_names = list(set(e.get("name", "") for e in entities if e.get("name")))
        
        if not entity_names:
            return {}
        
        # Build Cypher query
        query = """
        // Find entities and their relationships
        MATCH (entity:Entity)
        WHERE entity.name IN $entity_names
        
        // Find events involving this entity
        OPTIONAL MATCH (e:Event)-[:INVOLVES]->(entity)
        
        // Find incidents involving this entity
        OPTIONAL MATCH (i:Incident)-[:CONTAINS]->(e)
        
        // Aggregate information
        RETURN 
            entity.name AS name,
            entity.type AS type,
            entity.context AS context,
            count(DISTINCT e) AS event_count,
            count(DISTINCT i) AS incident_count,
            collect(DISTINCT e.severity)[0..5] AS recent_severities
        """
        
        parameters = {"entity_names": entity_names}
        
        results = self._execute_query(query, parameters)
        
        # Format results
        entity_context = {}
        for record in results:
            entity_context[record["name"]] = {
                "type": record["type"],
                "context": record["context"],
                "event_count": record["event_count"],
                "incident_count": record["incident_count"],
                "recent_severities": record["recent_severities"]
            }
        
        logger.info(f"Retrieved context for {len(entity_context)} entities")
        return entity_context
```

---

### Step 5: Implement Pattern Discovery

```python
    def get_common_patterns(
        self,
        events: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find common patterns in historical data.
        
        Args:
            events: List of events
            limit: Maximum number of patterns
            
        Returns:
            List of common patterns
        """
        logger.info("Finding common patterns")
        
        components = list(set(e.get("component", "") for e in events if e.get("component")))
        
        if not components:
            return []
        
        # Build Cypher query
        query = """
        // Find common event sequences
        MATCH (e1:Event)-[:PRECEDES]->(e2:Event)
        WHERE e1.component IN $components OR e2.component IN $components
        
        // Group by component pair
        WITH e1.component AS comp1, e2.component AS comp2, count(*) AS frequency
        WHERE frequency > 1
        
        RETURN comp1, comp2, frequency
        ORDER BY frequency DESC
        LIMIT $limit
        """
        
        parameters = {
            "components": components,
            "limit": limit
        }
        
        results = self._execute_query(query, parameters)
        
        # Format results
        patterns = []
        for record in results:
            patterns.append({
                "pattern": f"{record['comp1']} → {record['comp2']}",
                "frequency": record["frequency"]
            })
        
        logger.info(f"Found {len(patterns)} common patterns")
        return patterns
```

---

### Step 6: Implement Query Execution Helper

```python
    def _execute_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                records = [dict(record) for record in result]
                return records
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}")
            logger.debug(f"Parameters: {parameters}")
            return []
```

---

## 🧪 Testing

### Test 1: Connection Test

**File**: `tests/test_kg_retrieval_connection.py`

```python
"""Test KG Retrieval Agent connection."""

from src.agents.kg_retrieval import KGRetrievalAgent

def test_connection():
    """Test Neo4j connection."""
    agent = KGRetrievalAgent(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="your_password"
    )
    
    print("✓ Connected to Neo4j successfully!")
    
    agent.close()
    print("✓ Connection closed successfully!")

if __name__ == "__main__":
    test_connection()
```

---

### Test 2: Query Test

**File**: `tests/test_kg_retrieval_queries.py`

```python
"""Test KG Retrieval Agent queries."""

from src.agents.kg_retrieval import KGRetrievalAgent

def test_queries():
    """Test KG queries."""
    agent = KGRetrievalAgent(
        uri="bolt://localhost:7687",
        username="neo4j",
        password="your_password"
    )
    
    # Sample input data
    input_data = {
        "events": [
            {
                "component": "DataNode",
                "action": "replication_failed",
                "severity": "ERROR"
            }
        ],
        "entities": [
            {
                "type": "host",
                "name": "/10.0.1.5"
            }
        ],
        "error_messages": [
            {
                "error_type": "DiskFullException",
                "message": "No space left on device"
            }
        ]
    }
    
    # Test process method
    result = agent.process(input_data)
    
    print(f"✓ Similar incidents: {len(result['similar_incidents'])}")
    print(f"✓ Causal paths: {len(result['causal_paths'])}")
    print(f"✓ Entity context: {len(result['entity_context'])}")
    print(f"✓ Patterns: {len(result['patterns'])}")
    
    # Print sample results
    if result['similar_incidents']:
        print("\nSample Similar Incident:")
        print(result['similar_incidents'][0])
    
    agent.close()

if __name__ == "__main__":
    test_queries()
```

---

## 📊 Expected Output

```
✓ Connected to Neo4j successfully!
✓ Similar incidents: 5
✓ Causal paths: 3
✓ Entity context: 1
✓ Patterns: 2

Sample Similar Incident:
{
    'incident_id': 'HDFS_001',
    'timestamp': '2025-12-05 10:00:00',
    'dataset': 'HDFS',
    'label': 'Block Replication Failure',
    'root_cause': 'DataNode disk full',
    'similarity_score': 4.5,
    'components': ['DataNode', 'NameNode']
}
```

---

## 🎯 Next Steps

1. ✅ Implement KGRetrievalAgent class
2. ⏳ Test with sample data
3. ⏳ Populate KG with loghub data
4. ⏳ Integrate with Log Parser output
5. ⏳ Optimize queries for performance

---

**Status**: Implementation guide complete  
**Next**: Code the KGRetrievalAgent class  
**Estimated Time**: 3-4 hours
