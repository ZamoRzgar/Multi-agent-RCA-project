#!/usr/bin/env python3
"""
Debug script to check config loading.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import yaml

def main():
    """Debug config loading."""
    print("=" * 60)
    print("CONFIG DEBUG - Checking Neo4j Configuration")
    print("=" * 60)
    
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    print(f"\n1. Loading config from: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Check knowledge_graph section
    print("\n2. Knowledge Graph Config:")
    if 'knowledge_graph' in config:
        kg_config = config['knowledge_graph']
        print(f"   - URI: {kg_config.get('uri', 'NOT FOUND')}")
        print(f"   - User: {kg_config.get('user', 'NOT FOUND')}")
        print(f"   - Password: {kg_config.get('password', 'NOT FOUND')}")
        print(f"   - Password type: {type(kg_config.get('password'))}")
        
        # Check if password needs replacement
        password = kg_config.get('password', '')
        if '${NEO4J_PASSWORD}' in str(password):
            print(f"   ⚠️  Password contains placeholder: {password}")
            print(f"   ✓  Will be replaced with: 1997Amaterasu")
        else:
            print(f"   ✓  Password is set correctly")
    else:
        print("   ❌ knowledge_graph section NOT FOUND!")
    
    # Test what builder.py is doing
    print("\n3. Testing builder.py logic:")
    kg_config = config.get('knowledge_graph', {})
    
    print(f"   - kg_config.get('uri'): {kg_config.get('uri', 'DEFAULT')}")
    print(f"   - kg_config.get('user'): {kg_config.get('user', 'DEFAULT')}")
    print(f"   - kg_config.get('password'): {kg_config.get('password', 'DEFAULT')}")
    
    # This is the BUG!
    print(f"\n   ❌ WRONG: kg_config.get('1997Amaterasu'): {kg_config.get('1997Amaterasu', 'neo4j')}")
    print(f"   ✅ CORRECT: kg_config.get('password'): {kg_config.get('password', 'neo4j')}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS:")
    print("=" * 60)
    print("The bug is in src/kg/builder.py line 34:")
    print("  WRONG: password = kg_config.get('1997Amaterasu', 'neo4j')")
    print("  RIGHT: password = kg_config.get('password', 'neo4j')")
    print("=" * 60)

if __name__ == "__main__":
    main()
