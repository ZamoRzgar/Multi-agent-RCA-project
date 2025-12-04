# Log Parser Agent Implementation Guide

## Overview
The Log Parser Agent extracts structured information from raw logs using LLM (Qwen2-7B).

## Implementation Steps

### Step 1: Basic Implementation (1-2 hours)

Edit `src/agents/log_parser.py`:

```python
def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse raw logs into structured format."""
    raw_logs = input_data.get("raw_logs", "")
    
    logger.info(f"Parsing {len(raw_logs)} characters of logs")
    
    # Build prompt for LLM
    prompt = self._build_enhanced_prompt(raw_logs)
    
    # Call LLM (Qwen2-7B via base class)
    response = self._call_llm(prompt, temperature=0.2, max_tokens=800)
    
    # Parse LLM response
    parsed_data = self._parse_llm_response(response)
    
    return parsed_data

def _build_enhanced_prompt(self, raw_logs: str) -> str:
    """Build detailed prompt for log parsing."""
    prompt = f"""You are a log analysis expert. Parse these system logs and extract structured information.

Logs:
{raw_logs[:2000]}  # Limit to first 2000 chars

Extract and return in JSON format:
{{
    "events": [
        {{
            "timestamp": "...",
            "component": "...",
            "action": "...",
            "severity": "INFO|WARN|ERROR",
            "message": "..."
        }}
    ],
    "entities": [
        {{
            "type": "service|host|component|user|file|ip",
            "name": "...",
            "context": "..."
        }}
    ],
    "error_messages": [
        {{
            "error_type": "...",
            "message": "...",
            "component": "..."
        }}
    ],
    "relationships": [
        {{
            "source": "...",
            "target": "...",
            "type": "causes|triggers|depends_on"
        }}
    ]
}}

Focus on extracting actionable information for root cause analysis."""
    
    return prompt

def _parse_llm_response(self, response: str) -> Dict[str, Any]:
    """Parse LLM response into structured format."""
    import json
    import re
    
    # Try to extract JSON from response
    try:
        # Look for JSON block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(1))
        else:
            # Try to parse entire response
            parsed = json.loads(response)
        
        return parsed
    
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON, using fallback")
        
        # Fallback: extract basic info
        return {
            "events": [],
            "entities": [],
            "error_messages": [],
            "relationships": [],
            "raw_analysis": response
        }
```

### Step 2: Test Implementation (30 minutes)

Create `tests/test_log_parser_impl.py`:

```python
"""Test Log Parser Agent implementation."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.log_parser import LogParserAgent
from src.utils.data_loader import LoghubDataLoader

def test_hdfs_parsing():
    """Test parsing HDFS logs."""
    print("\n" + "="*60)
    print("Testing Log Parser on HDFS Logs")
    print("="*60)
    
    # Load sample logs
    loader = LoghubDataLoader(loghub_path="loghub")
    df = loader.load_dataset("HDFS", use_structured=True)
    
    # Get 10 sample logs
    sample_logs = "\n".join(df["Content"].head(10).tolist())
    
    # Initialize agent
    agent = LogParserAgent(model="qwen2:7b")
    
    # Process logs
    result = agent.process({"raw_logs": sample_logs})
    
    # Display results
    print(f"\nExtracted {len(result.get('events', []))} events")
    print(f"Extracted {len(result.get('entities', []))} entities")
    print(f"Extracted {len(result.get('error_messages', []))} errors")
    
    print("\nSample Events:")
    for event in result.get('events', [])[:3]:
        print(f"  - [{event.get('severity')}] {event.get('component')}: {event.get('action')}")
    
    print("\nSample Entities:")
    for entity in result.get('entities', [])[:5]:
        print(f"  - {entity.get('type')}: {entity.get('name')}")
    
    return result

def test_bgl_failure_parsing():
    """Test parsing BGL failure logs."""
    print("\n" + "="*60)
    print("Testing Log Parser on BGL Failure Logs")
    print("="*60)
    
    # Load failure cases
    loader = LoghubDataLoader(loghub_path="loghub")
    failures = loader.get_failure_cases("BGL", max_cases=5)
    
    # Get first failure
    failure_logs = "\n".join([f['raw_log'] for f in failures[:3]])
    
    # Initialize agent
    agent = LogParserAgent(model="qwen2:7b")
    
    # Process logs
    result = agent.process({"raw_logs": failure_logs})
    
    # Display results
    print(f"\nExtracted {len(result.get('error_messages', []))} error messages")
    
    print("\nError Messages:")
    for error in result.get('error_messages', []):
        print(f"  - {error.get('error_type')}: {error.get('message')[:80]}...")
    
    return result

if __name__ == "__main__":
    test_hdfs_parsing()
    test_bgl_failure_parsing()
    print("\n" + "="*60)
    print("Log Parser Tests Complete!")
    print("="*60)
```

### Step 3: Advanced Features (Optional, 2-3 hours)

Add Drain parser integration:

```python
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

def __init__(self, **kwargs):
    super().__init__(name="LogParserAgent", **kwargs)
    self.parser_type = self.config.get("parser_type", "drain")
    
    # Initialize Drain parser
    config = TemplateMinerConfig()
    config.load("config/drain3.ini")  # Create this config file
    self.drain_parser = TemplateMiner(config=config)

def _extract_templates(self, logs: List[str]) -> List[Dict[str, Any]]:
    """Extract log templates using Drain."""
    templates = []
    
    for log in logs:
        result = self.drain_parser.add_log_message(log)
        templates.append({
            "cluster_id": result["cluster_id"],
            "template": result["template_mined"]
        })
    
    return templates
```

## Testing Checklist

- [ ] Parse 10 HDFS logs successfully
- [ ] Extract events with timestamps
- [ ] Extract entities (components, IPs, blocks)
- [ ] Identify error messages
- [ ] Return valid JSON structure
- [ ] Handle malformed logs gracefully
- [ ] Process BGL failure logs
- [ ] Extract relationships between events

## Expected Output Format

```json
{
    "events": [
        {
            "timestamp": "081109 203615",
            "component": "dfs.DataNode$PacketResponder",
            "action": "terminating",
            "severity": "INFO",
            "message": "PacketResponder 1 for block blk_38865049064139660 terminating"
        }
    ],
    "entities": [
        {
            "type": "component",
            "name": "DataNode",
            "context": "packet responder"
        },
        {
            "type": "block",
            "name": "blk_38865049064139660",
            "context": "HDFS block"
        }
    ],
    "error_messages": [],
    "relationships": []
}
```

## Performance Tips

1. **Limit log size**: Process max 2000 chars at a time
2. **Batch processing**: Group similar logs together
3. **Cache templates**: Store common patterns
4. **Temperature**: Use 0.2-0.3 for structured extraction
5. **Max tokens**: 500-800 for JSON responses

## Next Steps After Implementation

1. Test on all 3 datasets (HDFS, BGL, Hadoop)
2. Measure parsing accuracy
3. Implement KG Retrieval Agent
4. Integrate with RCA Reasoner Agents
