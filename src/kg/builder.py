"""
Knowledge Graph Builder: Constructs KG from historical RCA results.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from neo4j import GraphDatabase
from loguru import logger


class KGBuilder:
    """
    Builds knowledge graph from historical RCA results:
    - Stores incidents with their diagnoses
    - Extracts entities and events from logs
    - Creates causal relationships
    - Enables similarity-based retrieval
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize KG builder with Neo4j connection.
        
        Args:
            config: Configuration dictionary with KG settings
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
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
        
        # Initialize schema
        if self.driver:
            self._create_schema()
    
    def __del__(self):
        """Close Neo4j connection."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
    
    def _create_schema(self) -> None:
        """Create Neo4j schema with constraints and indexes."""
        with self.driver.session() as session:
            # Create constraints for unique IDs
            constraints = [
                "CREATE CONSTRAINT incident_id IF NOT EXISTS FOR (i:Incident) REQUIRE i.incident_id IS UNIQUE",
                "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE",
                "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (ent:Entity) REQUIRE ent.name IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint already exists or failed: {e}")
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX incident_dataset IF NOT EXISTS FOR (i:Incident) ON (i.dataset)",
                "CREATE INDEX incident_score IF NOT EXISTS FOR (i:Incident) ON (i.final_score)",
                "CREATE INDEX event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp)",
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.debug(f"Index already exists or failed: {e}")
        
        logger.info("Neo4j schema created/verified")
    
    def populate_from_results(self, results_dir: str) -> Dict[str, int]:
        """
        Populate KG from RCA result JSON files.
        
        Args:
            results_dir: Directory containing result JSON files
            
        Returns:
            Statistics about populated data
        """
        results_path = Path(results_dir)
        if not results_path.exists():
            logger.error(f"Results directory not found: {results_dir}")
            return {}
        
        json_files = list(results_path.glob("*_results*.json"))
        logger.info(f"Found {len(json_files)} result files to process")
        
        stats = {
            'incidents': 0,
            'events': 0,
            'entities': 0,
            'hypotheses': 0,
            'relationships': 0
        }
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    result_data = json.load(f)
                
                incident_stats = self._store_incident(result_data, json_file.stem)
                
                # Aggregate stats
                for key in stats:
                    stats[key] += incident_stats.get(key, 0)
                
                logger.info(f"Processed {json_file.name}")
            except Exception as e:
                logger.error(f"Failed to process {json_file.name}: {e}")
        
        logger.info(f"KG Population complete: {stats}")
        return stats
    
    def _store_incident(self, result_data: Dict[str, Any], file_stem: str) -> Dict[str, int]:
        """
        Store a single incident in the KG.
        
        Args:
            result_data: RCA result data
            file_stem: File name stem for incident ID
            
        Returns:
            Statistics for this incident
        """
        if not self.driver:
            logger.warning("No Neo4j connection, skipping storage")
            return {}
        
        stats = {'incidents': 0, 'events': 0, 'entities': 0, 'hypotheses': 0, 'relationships': 0}
        
        with self.driver.session() as session:
            # Create Incident node
            incident_id = file_stem
            dataset = result_data.get('dataset', 'Unknown')
            scenario_id = result_data.get('scenario_id', 0)
            
            session.run("""
                MERGE (i:Incident {incident_id: $incident_id})
                SET i.dataset = $dataset,
                    i.scenario_id = $scenario_id,
                    i.num_events = $num_events,
                    i.total_rounds = $total_rounds,
                    i.convergence = $convergence,
                    i.final_score = $final_score,
                    i.final_hypothesis = $final_hypothesis,
                    i.final_source = $final_source,
                    i.created_at = datetime()
            """, 
                incident_id=incident_id,
                dataset=dataset,
                scenario_id=scenario_id,
                num_events=result_data.get('num_events', 0),
                total_rounds=result_data.get('total_rounds', 0),
                convergence=result_data.get('convergence', False),
                final_score=result_data.get('final_score', 0),
                final_hypothesis=result_data.get('final_hypothesis', ''),
                final_source=result_data.get('final_source', '')
            )
            stats['incidents'] = 1
            
            # Extract and store entities from hypothesis
            entities = self._extract_entities_from_text(
                result_data.get('final_hypothesis', '')
            )
            
            for entity in entities:
                session.run("""
                    MERGE (ent:Entity {name: $name})
                    SET ent.type = $type
                    WITH ent
                    MATCH (i:Incident {incident_id: $incident_id})
                    MERGE (i)-[:INVOLVES]->(ent)
                """,
                    name=entity['name'],
                    type=entity['type'],
                    incident_id=incident_id
                )
                stats['entities'] += 1
                stats['relationships'] += 1
            
            # Store hypothesis as RootCause node
            if result_data.get('final_hypothesis'):
                session.run("""
                    MATCH (i:Incident {incident_id: $incident_id})
                    MERGE (rc:RootCause {description: $hypothesis})
                    SET rc.confidence = $score,
                        rc.source = $source
                    MERGE (i)-[:HAS_ROOT_CAUSE]->(rc)
                """,
                    incident_id=incident_id,
                    hypothesis=result_data['final_hypothesis'],
                    score=result_data.get('final_score', 0) / 100.0,
                    source=result_data.get('final_source', '')
                )
                stats['hypotheses'] = 1
                stats['relationships'] += 1
            
            # Create similarity relationships between incidents of same dataset
            session.run("""
                MATCH (i1:Incident {incident_id: $incident_id})
                MATCH (i2:Incident)
                WHERE i1 <> i2 
                  AND i1.dataset = i2.dataset
                  AND abs(i1.final_score - i2.final_score) < 10
                MERGE (i1)-[s:SIMILAR_TO]-(i2)
                SET s.score_diff = abs(i1.final_score - i2.final_score)
            """,
                incident_id=incident_id
            )
        
        return stats
    
    def _extract_entities_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Extract entities from hypothesis text.
        
        Args:
            text: Hypothesis text
            
        Returns:
            List of entities with name and type
        """
        entities = []
        
        # Common entity patterns in log analysis
        entity_keywords = {
            'component': ['DataNode', 'NameNode', 'ResourceManager', 'NodeManager', 
                         'Executor', 'Driver', 'Master', 'Worker', 'HDFS', 'Spark', 'Hadoop'],
            'resource': ['Memory', 'Disk', 'CPU', 'Network', 'Storage', 'Bandwidth'],
            'issue': ['Failure', 'Error', 'Issue', 'Problem', 'Overload', 'Exhaustion'],
            'config': ['Configuration', 'Setting', 'Parameter', 'Allocation']
        }
        
        text_lower = text.lower()
        
        for entity_type, keywords in entity_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    entities.append({
                        'name': keyword,
                        'type': entity_type
                    })
        
        return entities
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get KG statistics.
        
        Returns:
            Dictionary with node and relationship counts
        """
        if not self.driver:
            return {}
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (i:Incident) 
                WITH count(i) as incidents
                MATCH (e:Entity)
                WITH incidents, count(e) as entities
                MATCH (rc:RootCause)
                WITH incidents, entities, count(rc) as root_causes
                MATCH ()-[r]->()
                RETURN incidents, entities, root_causes, count(r) as relationships
            """)
            
            record = result.single()
            if record:
                return {
                    'incidents': record['incidents'],
                    'entities': record['entities'],
                    'root_causes': record['root_causes'],
                    'relationships': record['relationships']
                }
        
        return {}
    
    def clear_database(self) -> None:
        """Clear all data from the KG (use with caution!)."""
        if not self.driver:
            logger.warning("No Neo4j connection")
            return
        
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        logger.warning("KG database cleared!")
