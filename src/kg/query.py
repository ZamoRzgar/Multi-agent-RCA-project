"""
Knowledge Graph Query: Queries KG for relevant information.
"""

from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from loguru import logger


class KGQuery:
    """
    Queries knowledge graph for:
    - Entity information
    - Causal paths
    - Similar incidents
    - Component dependencies
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize KG query interface.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        kg_config = config.get('knowledge_graph', {})
        
        # Connect to Neo4j
        uri = kg_config.get('uri', 'bolt://localhost:7687')
        user = kg_config.get('user', 'neo4j')
        password = kg_config.get('password', 'neo4j')
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            logger.info(f"KG Query connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
        
        logger.info("Initialized KG Query")
    
    def __del__(self):
        """Close Neo4j connection."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
    
    def find_similar_incidents(
        self,
        entities: List[str],
        symptoms: List[str],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar historical incidents based on entities.
        
        Args:
            entities: List of entity names to match
            symptoms: List of symptoms (currently unused, for future)
            top_k: Number of results to return
            
        Returns:
            List of similar incidents with their diagnoses
        """
        if not self.driver or not entities:
            return []
        
        try:
            with self.driver.session() as session:
                # Find incidents that involve any of the given entities
                result = session.run("""
                    MATCH (i:Incident)-[:INVOLVES]->(e:Entity)
                    WHERE e.name IN $entities
                    WITH i, count(DISTINCT e) as entity_matches
                    MATCH (i)-[:HAS_ROOT_CAUSE]->(rc:RootCause)
                    RETURN i.incident_id as incident_id,
                           i.dataset as dataset,
                           i.scenario_id as scenario_id,
                           i.final_score as score,
                           i.final_hypothesis as hypothesis,
                           rc.description as root_cause,
                           rc.confidence as confidence,
                           entity_matches
                    ORDER BY entity_matches DESC, i.final_score DESC
                    LIMIT $top_k
                """, entities=entities, top_k=top_k)
                
                incidents = []
                for record in result:
                    incidents.append({
                        'incident_id': record['incident_id'],
                        'dataset': record['dataset'],
                        'scenario_id': record['scenario_id'],
                        'score': record['score'],
                        'hypothesis': record['hypothesis'],
                        'root_cause': record['root_cause'],
                        'confidence': record['confidence'],
                        'entity_matches': record['entity_matches']
                    })
                
                logger.info(f"Found {len(incidents)} similar incidents for entities: {entities}")
                return incidents
        
        except Exception as e:
            logger.error(f"Error finding similar incidents: {e}")
            return []
    
    def find_causal_paths(
        self,
        source: str,
        target: str,
        max_hops: int = 3
    ) -> List[List[Dict[str, Any]]]:
        """
        Find causal paths between entities (future feature).
        
        Args:
            source: Source entity
            target: Target entity
            max_hops: Maximum path length
            
        Returns:
            List of causal paths
        """
        # Note: Causal relationships require temporal analysis
        # This is a Week 5-6 feature for KG enhancement
        logger.debug(f"Causal path finding not yet implemented (Week 5 feature)")
        return []
    
    def get_entity_info(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about an entity.
        
        Args:
            entity_name: Entity name
            
        Returns:
            Entity information dictionary with incident count
        """
        if not self.driver or not entity_name:
            return None
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity {name: $entity_name})<-[:INVOLVES]-(i:Incident)
                    WITH e, count(i) as incident_count, collect(i.dataset) as datasets
                    RETURN e.name as name,
                           e.type as type,
                           incident_count,
                           datasets
                """, entity_name=entity_name)
                
                record = result.single()
                if record:
                    return {
                        'name': record['name'],
                        'type': record['type'],
                        'incident_count': record['incident_count'],
                        'datasets': list(set(record['datasets']))  # Unique datasets
                    }
                return None
        
        except Exception as e:
            logger.error(f"Error getting entity info: {e}")
            return None
    
    def get_component_dependencies(
        self,
        component: str
    ) -> Dict[str, List[str]]:
        """
        Get component dependencies (future feature).
        
        Args:
            component: Component name
            
        Returns:
            Dictionary with upstream/downstream dependencies
        """
        # Note: Dependency relationships require system architecture knowledge
        # This is a Week 5-6 feature for KG enhancement
        logger.debug(f"Component dependency query not yet implemented (Week 5 feature)")
        return {"upstream": [], "downstream": []}
    
    def get_all_entities(self) -> List[Dict[str, Any]]:
        """
        Get all entities in the KG.
        
        Returns:
            List of all entities with their types and incident counts
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (e:Entity)<-[:INVOLVES]-(i:Incident)
                    RETURN e.name as name,
                           e.type as type,
                           count(i) as incident_count
                    ORDER BY incident_count DESC
                """)
                
                entities = []
                for record in result:
                    entities.append({
                        'name': record['name'],
                        'type': record['type'],
                        'incident_count': record['incident_count']
                    })
                
                return entities
        
        except Exception as e:
            logger.error(f"Error getting all entities: {e}")
            return []
