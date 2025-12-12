#!/usr/bin/env python3
"""
Populate Knowledge Graph with Temporal and Causal Relationships.

This script enhances the existing KG with:
- Event nodes with timestamps
- PRECEDES relationships (temporal ordering)
- CAUSES relationships (inferred causality)

Week 5 Enhancement.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.kg.builder import KGBuilder
import yaml
from loguru import logger


def load_config():
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Set Neo4j password if using placeholder
    kg_config = config.get('knowledge_graph', {})
    if kg_config.get('password') == '${NEO4J_PASSWORD}':
        kg_config['password'] = '1997Amaterasu'  # Default password
    
    return config


def main():
    """Main function to populate temporal relationships."""
    print("=" * 70)
    print("TEMPORAL KNOWLEDGE GRAPH POPULATION - WEEK 5")
    print("=" * 70)
    
    # Load configuration
    print("\n1. Loading configuration...")
    config = load_config()
    
    # Initialize KG Builder
    print("\n2. Initializing KG Builder...")
    builder = KGBuilder(config)
    
    if not builder.driver:
        print("✗ Failed to connect to Neo4j")
        print("\nPlease ensure:")
        print("  1. Neo4j is running")
        print("  2. Password in config/config.yaml is correct")
        return 1
    
    print("✓ Connected to Neo4j")
    
    # Get initial statistics
    print("\n3. Getting initial KG statistics...")
    initial_stats = builder.get_statistics()
    print(f"   Current state:")
    print(f"   - Incidents: {initial_stats.get('incidents', 0)}")
    print(f"   - Entities: {initial_stats.get('entities', 0)}")
    print(f"   - Root Causes: {initial_stats.get('root_causes', 0)}")
    print(f"   - Relationships: {initial_stats.get('relationships', 0)}")
    
    # Populate temporal relationships
    print("\n4. Populating temporal relationships from logs...")
    print("   This will:")
    print("   - Extract events from structured log files")
    print("   - Create PRECEDES relationships (temporal ordering)")
    print("   - Infer CAUSES relationships (causal links)")
    print()
    
    logs_dir = Path(__file__).parent.parent / "loghub"
    
    if not logs_dir.exists():
        print(f"✗ Logs directory not found: {logs_dir}")
        return 1
    
    # Process logs
    temporal_stats = builder.populate_temporal_relationships(str(logs_dir))
    
    print(f"\n✓ Temporal population complete!")
    print(f"   - Events created: {temporal_stats.get('events', 0)}")
    print(f"   - PRECEDES links: {temporal_stats.get('precedes_links', 0)}")
    print(f"   - CAUSES links: {temporal_stats.get('causes_links', 0)}")
    
    # Get final statistics
    print("\n5. Getting final KG statistics...")
    final_stats = builder.get_statistics()
    print(f"   Final state:")
    print(f"   - Total nodes: {final_stats.get('incidents', 0) + final_stats.get('entities', 0) + final_stats.get('root_causes', 0) + temporal_stats.get('events', 0)}")
    print(f"   - Total relationships: {final_stats.get('relationships', 0)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\n✅ Temporal KG enhancement complete!")
    print(f"\nNew capabilities:")
    print(f"  • Event-level granularity")
    print(f"  • Temporal ordering (PRECEDES)")
    print(f"  • Causal inference (CAUSES)")
    print(f"  • Path finding enabled")
    print(f"\nNext steps:")
    print(f"  1. Test causal path queries: python tests/test_temporal_kg.py")
    print(f"  2. Verify with: python scripts/query_temporal_kg.py")
    print(f"  3. Update KGQuery.find_causal_paths() implementation")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
