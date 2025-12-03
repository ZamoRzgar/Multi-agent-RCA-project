"""
Test script for local LLM setup with loghub data.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.local_llm_client import LocalLLMClient, MultiModelManager
from src.utils.data_loader import LoghubDataLoader, DatasetStatistics
from loguru import logger
import yaml


def test_ollama_connection():
    """Test Ollama server connection."""
    print("\n=== Testing Ollama Connection ===")
    
    client = LocalLLMClient(
        backend="ollama",
        model="qwen2:7b"
    )
    
    if client.is_available():
        print("✓ Ollama server is running")
        return True
    else:
        print("✗ Ollama server is not available")
        print("  Start it with: ollama serve")
        return False


def test_model_generation():
    """Test text generation with local model."""
    print("\n=== Testing Model Generation ===")
    
    client = LocalLLMClient(
        backend="ollama",
        model="qwen2:7b"
    )
    
    prompt = """Analyze this log entry and identify potential issues:
    
Log: "ERROR: Connection timeout to database server 10.0.1.5:3306 after 30 seconds"

Provide:
1. Issue type
2. Potential root cause
3. Recommended action"""
    
    print(f"Prompt: {prompt[:100]}...")
    
    try:
        response = client.generate(prompt, temperature=0.3, max_tokens=500)
        print(f"\nResponse:\n{response}")
        return True
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False


def test_multi_model_setup():
    """Test multi-model configuration."""
    print("\n=== Testing Multi-Model Setup ===")
    
    # Load config
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    manager = MultiModelManager(config)
    
    # Check availability
    status = manager.check_availability()
    
    print("\nModel Availability:")
    for role, available in status.items():
        status_icon = "✓" if available else "✗"
        print(f"  {status_icon} {role}")
    
    return all(status.values())


def test_with_loghub_data():
    """Test LLM with real loghub data."""
    print("\n=== Testing with Loghub Data ===")
    
    # Load data
    loader = LoghubDataLoader(loghub_path="loghub")
    
    try:
        df = loader.load_dataset("HDFS", use_structured=True)
        print(f"✓ Loaded HDFS dataset: {len(df)} logs")
        
        # Get statistics
        stats = DatasetStatistics.analyze_dataset(df)
        DatasetStatistics.print_statistics(stats)
        
        # Extract a sample case
        case = loader.extract_log_case(df, 0)
        print(f"\nSample Log Case:")
        print(f"  Timestamp: {case['timestamp']}")
        print(f"  Component: {case['component']}")
        print(f"  Content: {case['raw_log'][:100]}...")
        
        # Test LLM analysis
        client = LocalLLMClient(backend="ollama", model="qwen2:7b")
        
        prompt = f"""Analyze this HDFS log entry:

Component: {case['component']}
Log: {case['raw_log']}

Extract:
1. Event type
2. Entities involved (IPs, block IDs, etc.)
3. Action performed
4. Potential issues (if any)

Provide structured output."""
        
        print("\nSending to LLM for analysis...")
        response = client.generate(prompt, temperature=0.3, max_tokens=300)
        print(f"\nLLM Analysis:\n{response}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_agent_with_data():
    """Test agent with loghub data."""
    print("\n=== Testing Agent with Data ===")
    
    from src.agents import LogParserAgent
    
    # Load data
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("HDFS", use_structured=True)
    
    # Get first 5 logs
    sample_logs = "\n".join(df["Content"].head(5).tolist())
    
    # Initialize agent
    agent = LogParserAgent(model="qwen2:7b")
    
    print(f"Testing LogParserAgent with {len(df)} HDFS logs")
    print(f"\nSample input (first 5 logs):\n{sample_logs[:200]}...")
    
    try:
        # Process logs
        result = agent.process({"raw_logs": sample_logs})
        
        print(f"\nAgent Output:")
        print(f"  Events: {len(result.get('events', []))}")
        print(f"  Entities: {len(result.get('entities', []))}")
        print(f"  Templates: {len(result.get('templates', []))}")
        
        return True
    except Exception as e:
        print(f"✗ Agent test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Local LLM Setup Test Suite")
    print("=" * 60)
    
    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Model Generation", test_model_generation),
        ("Multi-Model Setup", test_multi_model_setup),
        ("Loghub Data Loading", test_with_loghub_data),
        ("Agent Integration", test_agent_with_data),
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    main()
