#!/usr/bin/env python3
"""
Script to populate Knowledge Graph from RCA results.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml
from loguru import logger
from kg.builder import KGBuilder


def load_config():
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Set default Neo4j password if not in environment
    if 'knowledge_graph' in config:
        if '${NEO4J_PASSWORD}' in str(config['knowledge_graph'].get('password', '')):
            config['knowledge_graph']['password'] = '1997Amaterasu'  # Default password
    
    return config


def main():
    """Main function to populate KG."""
    logger.info("=" * 60)
    logger.info("Knowledge Graph Population - Week 4")
    logger.info("=" * 60)
    
    # Load config
    config = load_config()
    
    # Initialize KG Builder
    logger.info("\n1. Initializing KG Builder...")
    builder = KGBuilder(config)
    
    if not builder.driver:
        logger.error("Failed to connect to Neo4j. Please ensure Neo4j is running.")
        logger.error("Connection: bolt://localhost:7687")
        logger.error("Default credentials: neo4j/neo4j")
        return
    
    # Get initial statistics
    logger.info("\n2. Checking current KG state...")
    initial_stats = builder.get_statistics()
    logger.info(f"Current KG: {initial_stats}")
    
    # Populate from results
    logger.info("\n3. Populating KG from RCA results...")
    results_dir = Path(__file__).parent.parent / "experiments" / "results"
    logger.info(f"Results directory: {results_dir}")
    
    population_stats = builder.populate_from_results(str(results_dir))
    
    # Get final statistics
    logger.info("\n4. Checking final KG state...")
    final_stats = builder.get_statistics()
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("POPULATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Files processed: {len(list(results_dir.glob('*_results*.json')))}")
    logger.info(f"\nNodes created:")
    logger.info(f"  - Incidents: {population_stats.get('incidents', 0)}")
    logger.info(f"  - Entities: {population_stats.get('entities', 0)}")
    logger.info(f"  - Root Causes: {population_stats.get('hypotheses', 0)}")
    logger.info(f"\nRelationships created: {population_stats.get('relationships', 0)}")
    logger.info(f"\nFinal KG Statistics:")
    logger.info(f"  - Total Incidents: {final_stats.get('incidents', 0)}")
    logger.info(f"  - Total Entities: {final_stats.get('entities', 0)}")
    logger.info(f"  - Total Root Causes: {final_stats.get('root_causes', 0)}")
    logger.info(f"  - Total Relationships: {final_stats.get('relationships', 0)}")
    logger.info("=" * 60)
    
    logger.success("\n✅ Knowledge Graph population complete!")
    logger.info("\nYou can now:")
    logger.info("  1. Open Neo4j Browser at http://localhost:7474")
    logger.info("  2. Run queries like: MATCH (i:Incident) RETURN i LIMIT 10")
    logger.info("  3. Visualize the graph structure")


if __name__ == "__main__":
    main()
