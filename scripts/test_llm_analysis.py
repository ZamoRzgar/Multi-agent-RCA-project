"""
Test LLM analysis on real loghub logs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.local_llm_client import LocalLLMClient
from src.utils.data_loader import LoghubDataLoader

def test_log_parsing():
    """Test LLM for log parsing."""
    print("\n" + "="*60)
    print("Test 1: Log Parsing with Qwen2")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("HDFS", use_structured=True)
    
    # Get sample log
    case = loader.extract_log_case(df, 10)
    
    client = LocalLLMClient(backend="ollama", model="qwen2:7b")
    
    prompt = f"""Parse this HDFS log entry and extract structured information:

Log: {case['raw_log']}

Extract and return in JSON format:
{{
    "component": "...",
    "action": "...",
    "entities": ["...", "..."],
    "event_type": "...",
    "severity": "..."
}}"""
    
    print(f"Input Log: {case['raw_log'][:100]}...")
    print("\nSending to Qwen2...")
    
    response = client.generate(prompt, temperature=0.2, max_tokens=300)
    print(f"\nParsed Output:\n{response}")

def test_hypothesis_generation():
    """Test LLM for hypothesis generation."""
    print("\n" + "="*60)
    print("Test 2: Hypothesis Generation with Mistral")
    print("="*60)
    
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("BGL", use_structured=True)
    
    # Get failure case
    failures = loader.get_failure_cases("BGL", max_cases=5)
    failure = failures[0]
    
    client = LocalLLMClient(backend="ollama", model="mistral:7b")
    
    prompt = f"""Analyze this system failure log and generate a root cause hypothesis:

Log: {failure['raw_log']}

Provide:
1. Root Cause (one sentence)
2. Reasoning (2-3 sentences)
3. Evidence from log (specific details)
4. Confidence (0-1)"""
    
    print(f"Failure Log: {failure['raw_log'][:150]}...")
    print("\nSending to Mistral...")
    
    response = client.generate(prompt, temperature=0.7, max_tokens=400)
    print(f"\nHypothesis:\n{response}")

def test_judging():
    """Test LLM for judging hypotheses."""
    print("\n" + "="*60)
    print("Test 3: Hypothesis Judging with Mistral")
    print("="*60)
    
    hypotheses = [
        {
            "agent": "log_focused",
            "root_cause": "Network timeout due to high latency",
            "confidence": 0.8
        },
        {
            "agent": "kg_focused",
            "root_cause": "Database connection pool exhausted",
            "confidence": 0.7
        },
        {
            "agent": "hybrid",
            "root_cause": "Firewall blocking port 3306",
            "confidence": 0.9
        }
    ]
    
    client = LocalLLMClient(backend="ollama", model="mistral:7b")
    
    prompt = f"""You are a judge evaluating root cause hypotheses.

Hypotheses:
1. {hypotheses[0]['agent']}: {hypotheses[0]['root_cause']} (confidence: {hypotheses[0]['confidence']})
2. {hypotheses[1]['agent']}: {hypotheses[1]['root_cause']} (confidence: {hypotheses[1]['confidence']})
3. {hypotheses[2]['agent']}: {hypotheses[2]['root_cause']} (confidence: {hypotheses[2]['confidence']})

Log Evidence: "ERROR: Connection timeout to database server 10.0.1.5:3306 after 30 seconds"

Select the best hypothesis and explain why. Score each on:
- Evidence support (0-1)
- Logical consistency (0-1)
- Completeness (0-1)"""
    
    print("Evaluating 3 competing hypotheses...")
    print("\nSending to Mistral...")
    
    response = client.generate(prompt, temperature=0.2, max_tokens=500)
    print(f"\nJudgment:\n{response}")

def test_multi_model_comparison():
    """Compare responses from different models."""
    print("\n" + "="*60)
    print("Test 4: Multi-Model Comparison")
    print("="*60)
    
    log = "WARN: Memory usage at 95%, garbage collection triggered"
    
    models = ["qwen2:7b", "mistral:7b", "llama2:7b"]
    
    prompt = f"""Analyze this log and identify the root cause:

Log: {log}

Provide a brief root cause analysis (2-3 sentences)."""
    
    print(f"Log: {log}\n")
    
    for model_name in models:
        print(f"\n--- {model_name.upper()} ---")
        client = LocalLLMClient(backend="ollama", model=model_name)
        response = client.generate(prompt, temperature=0.5, max_tokens=200)
        print(response)

def main():
    """Run all tests."""
    print("="*60)
    print("LLM Analysis Testing Suite")
    print("="*60)
    
    try:
        test_log_parsing()
        test_hypothesis_generation()
        test_judging()
        test_multi_model_comparison()
        
        print("\n" + "="*60)
        print("All Tests Complete!")
        print("="*60)
        print("\nKey Observations:")
        print("1. Qwen2 is good for structured extraction")
        print("2. Mistral provides detailed reasoning")
        print("3. Different models have different styles")
        print("\nNext: Implement agent logic using these patterns")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Make sure Ollama is running: ollama serve")

if __name__ == "__main__":
    main()
