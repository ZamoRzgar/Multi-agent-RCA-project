"""
Log Parser Agent: Extracts structured information from raw logs.
"""

from typing import Dict, Any, List
import json
import re
from loguru import logger

from .base_agent import BaseAgent


class LogParserAgent(BaseAgent):
    """
    Agent responsible for parsing raw logs and extracting:
    - Events and their timestamps
    - Entities (services, hosts, components)
    - Error messages and stack traces
    - Temporal relationships
    """
    
    def __init__(self, **kwargs):
        super().__init__(name="LogParserAgent", **kwargs)
        self.parser_type = self.config.get("parser_type", "drain")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw logs into structured format.
        
        Args:
            input_data: Dictionary containing 'raw_logs' key
            
        Returns:
            Dictionary with parsed log information:
            - events: List of log events
            - entities: Extracted entities
            - timeline: Temporal sequence
            - error_messages: Extracted errors
        """
        raw_logs = input_data.get("raw_logs", "")
        
        logger.info(f"Parsing {len(raw_logs)} characters of logs")
        
        # Build prompt for LLM
        prompt = self._build_enhanced_prompt(raw_logs)
        
        # Set temperature and max_tokens for parsing (overriding defaults)
        original_temp = self.temperature
        original_max = self.max_tokens
        self.temperature = 0.2   # Low temperature for structured extraction
        self.max_tokens = 1500   # Increased to ensure complete JSON response
        
        # Call LLM (Qwen2-7B via base class)
        response = self._call_llm(prompt)
        
        # Restore original settings
        self.temperature = original_temp
        self.max_tokens = original_max
        
        # Parse LLM response
        parsed_data = self._parse_llm_response(response)
        
        # Build timeline from events
        if parsed_data.get("events"):
            parsed_data["timeline"] = self.build_timeline(parsed_data["events"])
        
        logger.info(f"Extracted {len(parsed_data.get('events', []))} events, "
                   f"{len(parsed_data.get('entities', []))} entities, "
                   f"{len(parsed_data.get('error_messages', []))} errors")
        
        return parsed_data
    
    def _build_prompt(self, raw_logs: str) -> str:
        """
        Build prompt for LLM-based log parsing enhancement.
        
        Args:
            raw_logs: Raw log text
            
        Returns:
            Formatted prompt
        """
        prompt = f"""You are a log analysis expert. Parse the following system logs and extract:
1. Key events and their timestamps
2. Entities (services, hosts, components, users)
3. Error messages and exceptions
4. Causal relationships between events

Logs:
{raw_logs}

Provide a structured analysis in JSON format."""
        
        return prompt
    
    def _build_enhanced_prompt(self, raw_logs: str) -> str:
        """
        Build detailed prompt for log parsing.
        
        Args:
            raw_logs: Raw log text
            
        Returns:
            Formatted prompt for structured extraction
        """
        # Limit to first 2000 chars to avoid token limits
        log_sample = raw_logs[:2000] if len(raw_logs) > 2000 else raw_logs
        
        prompt = f"""You are a log analysis expert. Parse these system logs and extract structured information.

Logs:
{log_sample}

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
            "type": "service|host|component|user|file|ip|block",
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
        """
        Parse LLM response into structured format.
        
        Args:
            response: LLM response text
            
        Returns:
            Parsed dictionary with events, entities, errors, relationships
        """
        # Try to extract JSON from response
        try:
            # Look for JSON block in markdown code fence
            json_match = re.search(r'```json\s*({.*?})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for JSON block without fence - greedy match to get full JSON
                json_match = re.search(r'({[\s\S]*})', response)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # Use entire response
                    json_str = response
            
            # Clean up common JSON issues
            json_str = self._clean_json_string(json_str)
            
            # Parse JSON
            parsed = json.loads(json_str)
            
            # Ensure all required keys exist
            result = {
                "events": parsed.get("events", []),
                "entities": parsed.get("entities", []),
                "error_messages": parsed.get("error_messages", []),
                "relationships": parsed.get("relationships", []),
                "timeline": [],
                "templates": []
            }
            
            logger.info(f"Successfully parsed JSON: {len(result['events'])} events, "
                       f"{len(result['entities'])} entities")
            
            return result
        
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response[:500]}...")
            
            # Fallback: extract basic info using regex
            return self._fallback_parse(response)
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean up common JSON formatting issues from LLM output.
        
        Args:
            json_str: Raw JSON string
            
        Returns:
            Cleaned JSON string
        """
        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix incomplete strings (truncated at end)
        # If last character is not } or ], try to close the JSON
        json_str = json_str.strip()
        if not json_str.endswith('}'):
            # Count opening and closing braces
            open_braces = json_str.count('{')
            close_braces = json_str.count('}')
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            
            # Add missing closing brackets/braces
            json_str += ']' * (open_brackets - close_brackets)
            json_str += '}' * (open_braces - close_braces)
        
        return json_str
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """
        Fallback parser when JSON parsing fails.
        
        Args:
            response: LLM response text
            
        Returns:
            Dictionary with extracted information
        """
        logger.info("Using fallback parsing method")
        
        result = {
            "events": [],
            "entities": [],
            "error_messages": [],
            "relationships": [],
            "timeline": [],
            "templates": [],
            "raw_analysis": response
        }
        
        # Try to extract error keywords
        error_keywords = ["error", "exception", "failed", "timeout", "crash"]
        for keyword in error_keywords:
            if keyword.lower() in response.lower():
                result["error_messages"].append({
                    "error_type": keyword,
                    "message": f"Detected {keyword} in analysis",
                    "component": "unknown"
                })
        
        return result
    
    def extract_entities(self, logs: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from logs.
        
        Args:
            logs: Log text
            
        Returns:
            List of entities with types and positions
        """
        # TODO: Implement NER using spaCy or LLM
        return []
    
    def build_timeline(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build temporal timeline from events.
        
        Args:
            events: List of log events
            
        Returns:
            Sorted timeline of events
        """
        # TODO: Implement timeline construction
        return sorted(events, key=lambda x: x.get("timestamp", 0))
