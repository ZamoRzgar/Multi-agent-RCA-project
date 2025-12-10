"""
Knowledge Graph Retrieval Agent: Retrieves relevant facts from KG.
"""

from typing import Dict, Any, List, Optional
from loguru import logger
import sys
from pathlib import Path

# Add src to path for kg.query import
sys.path.insert(0, str(Path(__file__).parent.parent))

from .base_agent import BaseAgent
from kg.query import KGQuery


class KGRetrievalAgent(BaseAgent):
    """
    Agent responsible for retrieving relevant knowledge graph facts:
    - Historical incident patterns
    - Causal relationships
    - Component dependencies
    - Known failure modes
    """
    
    def __init__(self, **kwargs):
        super().__init__(name="KGRetrievalAgent", **kwargs)
        self.top_k = self.config.get("top_k_facts", 5)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.7)
        
        # Initialize KG Query interface
        try:
            self.kg_query = KGQuery(self.config)
            logger.info("KG Retrieval Agent initialized with KGQuery")
        except Exception as e:
            logger.error(f"Failed to initialize KGQuery: {e}")
            self.kg_query = None
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve relevant KG facts based on parsed logs.
        
        Args:
            input_data: Dictionary containing 'entities', 'events', 'error_messages'
            
        Returns:
            Dictionary with retrieved KG facts:
            - similar_incidents: Similar historical incidents
            - entity_context: Context for entities
            - all_entities: All entities in KG for reference
        """
        if not self.kg_query or not self.kg_query.driver:
            logger.warning("KGQuery not initialized, returning empty results")
            return {
                "similar_incidents": [],
                "entity_context": {},
                "all_entities": []
            }
        
        entities = input_data.get("entities", [])
        events = input_data.get("events", [])
        
        logger.info(f"Retrieving KG facts for {len(events)} events, {len(entities)} entities")
        
        # Extract entity names from parsed data
        entity_names = self._extract_entity_names(entities, events)
        
        # Query similar incidents using KGQuery
        similar_incidents = self.kg_query.find_similar_incidents(
            entities=entity_names,
            symptoms=[],  # Future: extract symptoms from events
            top_k=self.top_k
        )
        
        # Get entity context for each entity
        entity_context = {}
        for entity_name in entity_names[:5]:  # Limit to top 5 entities
            info = self.kg_query.get_entity_info(entity_name)
            if info:
                entity_context[entity_name] = info
        
        # Get all entities for reference
        all_entities = self.kg_query.get_all_entities()
        
        kg_facts = {
            "similar_incidents": similar_incidents,
            "entity_context": entity_context,
            "all_entities": all_entities[:10]  # Top 10 most common
        }
        
        logger.info(f"Retrieved {len(similar_incidents)} similar incidents, "
                   f"{len(entity_context)} entity contexts")
        
        return kg_facts
    
    def _extract_entity_names(self, entities: List[Dict[str, Any]], events: List[Dict[str, Any]]) -> List[str]:
        """
        Extract entity names from parsed data.
        
        Args:
            entities: List of entity dictionaries
            events: List of event dictionaries
            
        Returns:
            List of unique entity names
        """
        entity_names = set()
        
        # From entities list
        for entity in entities:
            if isinstance(entity, dict) and 'name' in entity:
                entity_names.add(entity['name'])
            elif isinstance(entity, str):
                entity_names.add(entity)
        
        # From events (components, error types)
        for event in events:
            if isinstance(event, dict):
                if 'component' in event and event['component']:
                    entity_names.add(event['component'])
                if 'error_type' in event and event['error_type']:
                    entity_names.add(event['error_type'])
        
        return list(entity_names)
    
    def query_similar_incidents(
        self,
        events: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find similar past incidents based on events, entities, and errors.
        Uses KGQuery for data access.
        
        Args:
            events: List of events
            entities: List of entities
            errors: List of errors
            limit: Maximum number of results
            
        Returns:
            List of similar incidents with similarity scores
        """
        logger.info("Querying similar incidents via KGQuery")
        
        if not self.kg_query or not self.kg_query.driver:
            logger.warning("KGQuery not available")
            return []
        
        # Extract entity names
        entity_names = self._extract_entity_names(entities, events)
        
        # Extract symptoms from errors
        symptoms = [e.get("error_type", "") for e in errors if e.get("error_type")]
        
        if not entity_names:
            logger.warning("No entities to match")
            return []
        
        # Use KGQuery to find similar incidents
        incidents = self.kg_query.find_similar_incidents(
            entities=entity_names,
            symptoms=symptoms,
            top_k=limit
        )
        
        # Convert to expected format for backward compatibility
        similar_incidents = []
        for inc in incidents:
            similar_incidents.append({
                "incident_id": inc.get("incident_id"),
                "timestamp": None,  # Not stored in current schema
                "dataset": inc.get("dataset"),
                "label": None,  # Not stored in current schema
                "root_cause": inc.get("root_cause"),
                "root_cause_description": inc.get("root_cause"),
                "root_cause_category": None,  # Future enhancement
                "similarity_score": inc.get("entity_matches", 0),
                "components": entity_names,
                "hypothesis": inc.get("hypothesis"),
                "confidence": inc.get("confidence", 0.0)
            })
        
        logger.info(f"Found {len(similar_incidents)} similar incidents via KGQuery")
        return similar_incidents
    
    def find_causal_paths(
        self,
        events: List[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find causal paths leading to errors.
        Uses KGQuery for data access.
        
        Args:
            events: List of events
            errors: List of errors
            max_depth: Maximum path length
            
        Returns:
            List of causal paths
        """
        logger.info("Finding causal paths via KGQuery")
        
        if not self.kg_query or not self.kg_query.driver:
            logger.warning("KGQuery not available")
            return []
        
        # Extract entity names for source/target
        entity_names = self._extract_entity_names([], events)
        
        if len(entity_names) < 2:
            logger.debug("Not enough entities for causal path search")
            return []
        
        # Use KGQuery to find causal paths (currently returns empty - Week 5 feature)
        causal_paths = []
        for i in range(min(len(entity_names) - 1, 3)):  # Try first 3 pairs
            paths = self.kg_query.find_causal_paths(
                source=entity_names[i],
                target=entity_names[i + 1],
                max_hops=max_depth
            )
            causal_paths.extend(paths)
        
        logger.info(f"Found {len(causal_paths)} causal paths via KGQuery")
        return causal_paths
    
    def get_entity_context(
        self,
        entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Retrieve context for entities from knowledge graph.
        Uses KGQuery for data access.
        
        Args:
            entities: List of entities
            
        Returns:
            Dictionary with entity context
        """
        logger.info("Retrieving entity context via KGQuery")
        
        if not self.kg_query or not self.kg_query.driver:
            logger.warning("KGQuery not available")
            return {}
        
        entity_names = list(set(e.get("name", "") for e in entities if e.get("name")))
        
        if not entity_names:
            return {}
        
        # Use KGQuery to get entity information
        entity_context = {}
        for entity_name in entity_names:
            info = self.kg_query.get_entity_info(entity_name)
            if info:
                entity_context[entity_name] = {
                    "type": info.get("type"),
                    "context": None,  # Not in current schema
                    "event_count": 0,  # Not tracked in current schema
                    "incident_count": info.get("incident_count", 0),
                    "recent_severities": [],  # Not in current schema
                    "datasets": info.get("datasets", [])
                }
        
        logger.info(f"Retrieved context for {len(entity_context)} entities via KGQuery")
        return entity_context
    
    def get_common_patterns(
        self,
        events: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find common patterns in historical data.
        Uses entity frequency from KGQuery.
        
        Args:
            events: List of events
            limit: Maximum number of patterns
            
        Returns:
            List of common patterns
        """
        logger.info("Finding common patterns via KGQuery")
        
        if not self.kg_query or not self.kg_query.driver:
            logger.warning("KGQuery not available")
            return []
        
        # Get all entities to find patterns
        all_entities = self.kg_query.get_all_entities()
        
        # Convert to pattern format
        patterns = []
        for entity in all_entities[:limit]:
            patterns.append({
                "pattern": f"{entity['name']} ({entity['type']})",
                "frequency": entity['incident_count'],
                "entity_type": entity['type']
            })
        
        logger.info(f"Found {len(patterns)} common patterns via KGQuery")
        return patterns
    
    def _execute_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Cypher query and return results.
        DEPRECATED: Use KGQuery methods instead.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records
        """
        logger.warning("_execute_query is deprecated. Use KGQuery methods instead.")
        
        if not self.kg_query or not self.kg_query.driver:
            return []
        
        try:
            with self.kg_query.driver.session() as session:
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
        if hasattr(self, 'kg_query') and self.kg_query:
            # KGQuery handles its own connection cleanup
            logger.info("KG Retrieval Agent closed")
