"""
Knowledge Graph Retrieval Agent: Retrieves relevant facts from KG.
"""

from typing import Dict, Any, List, Optional
from loguru import logger
from neo4j import GraphDatabase
import yaml

from .base_agent import BaseAgent


class KGRetrievalAgent(BaseAgent):
    """
    Agent responsible for retrieving relevant knowledge graph facts:
    - Historical incident patterns
    - Causal relationships
    - Component dependencies
    - Known failure modes
    """
    
    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = None,
        **kwargs
    ):
        super().__init__(name="KGRetrievalAgent", **kwargs)
        self.top_k = self.config.get("top_k_facts", 10)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.7)
        
        # Load config if password not provided
        if password is None:
            try:
                with open("config/neo4j_config.yaml", "r") as f:
                    config = yaml.safe_load(f)
                    password = config["neo4j"]["password"]
                    uri = config["neo4j"].get("uri", uri)
                    username = config["neo4j"].get("username", username)
            except Exception as e:
                logger.warning(f"Could not load Neo4j config: {e}")
        
        # Initialize Neo4j driver
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant KG facts based on parsed logs.
        
        Args:
            input_data: Dictionary containing 'entities', 'events', 'error_messages'
            
        Returns:
            Dictionary with retrieved KG facts:
            - similar_incidents: Similar historical incidents
            - causal_paths: Potential causal chains
            - entity_context: Context for entities
            - patterns: Common patterns
        """
        if not self.driver:
            logger.warning("Neo4j driver not initialized, returning empty results")
            return {
                "similar_incidents": [],
                "causal_paths": [],
                "entity_context": {},
                "patterns": []
            }
        
        entities = input_data.get("entities", [])
        events = input_data.get("events", [])
        errors = input_data.get("error_messages", [])
        
        logger.info(f"Retrieving KG facts for {len(events)} events, {len(entities)} entities")
        
        # Query similar incidents
        similar_incidents = self.query_similar_incidents(events, entities, errors)
        
        # Find causal paths
        causal_paths = self.find_causal_paths(events, errors)
        
        # Get entity context
        entity_context = self.get_entity_context(entities)
        
        # Get common patterns
        patterns = self.get_common_patterns(events)
        
        kg_facts = {
            "similar_incidents": similar_incidents,
            "causal_paths": causal_paths,
            "entity_context": entity_context,
            "patterns": patterns
        }
        
        logger.info(f"Retrieved {len(similar_incidents)} similar incidents, "
                   f"{len(causal_paths)} causal paths")
        
        return kg_facts
    
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
        
        if not components and not error_types and not entity_names:
            logger.warning("No components, errors, or entities to match")
            return []
        
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
                "timestamp": str(record["timestamp"]) if record["timestamp"] else None,
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
        if not self.driver:
            return []
        
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
    
    def close(self):
        """Close Neo4j connection."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")
