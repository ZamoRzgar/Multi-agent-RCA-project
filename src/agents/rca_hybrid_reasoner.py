"""
Hybrid RCA Reasoner Agent.

This reasoner combines both log analysis and knowledge graph data
for comprehensive root cause analysis.
"""

from typing import Dict, Any, List
from loguru import logger

from src.agents.rca_reasoner_base import RCAReasonerAgent


class HybridReasoner(RCAReasonerAgent):
    """
    RCA Reasoner that combines log analysis and KG knowledge.
    
    Specializes in:
    - Comprehensive analysis using both logs and historical data
    - Cross-validation between current logs and past patterns
    - Balanced reasoning approach
    - Most thorough root cause identification
    """
    
    def __init__(self, **kwargs):
        """Initialize Hybrid Reasoner with Qwen2-7B."""
        super().__init__(
            name="HybridReasoner",
            model="qwen2:7b",
            reasoning_type="hybrid",
            temperature=0.3,
            max_tokens=2500,  # Slightly higher for comprehensive analysis
            **kwargs
        )
    
    def _build_reasoning_prompt(self, input_data: Dict[str, Any]) -> str:
        """
        Build hybrid reasoning prompt.
        
        Combines:
        - Log pattern analysis
        - Historical incident patterns
        - Causal relationships
        - Entity behavior
        
        Args:
            input_data: Input data with both logs and KG facts
            
        Returns:
            Formatted prompt string
        """
        # Log data
        events = input_data.get("events", [])
        errors = input_data.get("error_messages", [])
        timeline = input_data.get("timeline", events)
        entities = input_data.get("entities", [])
        
        # KG data
        similar_incidents = input_data.get("similar_incidents", [])
        causal_paths = input_data.get("causal_paths", [])
        entity_context = input_data.get("entity_context", {})
        patterns = input_data.get("patterns", [])
        
        # Format data for prompt
        events_str = self._format_events(events)
        errors_str = self._format_errors(errors)
        timeline_str = self._format_timeline(timeline)
        entities_str = self._format_entities(entities)
        similar_str = self._format_similar_incidents(similar_incidents)
        causal_str = self._format_causal_paths(causal_paths)
        context_str = self._format_entity_context(entity_context)
        patterns_str = self._format_patterns(patterns)
        
        prompt = f"""You are an expert in comprehensive root cause analysis, combining real-time log analysis with historical knowledge.

Your task is to identify the most likely root causes by synthesizing insights from both current log data and historical patterns.

=== CURRENT LOG DATA ===

Events:
{events_str}

Error Messages:
{errors_str}

Timeline:
{timeline_str}

Entities:
{entities_str}

=== HISTORICAL KNOWLEDGE GRAPH DATA ===

Similar Past Incidents:
{similar_str}

Known Causal Paths:
{causal_str}

Entity Historical Context:
{context_str}

Common Patterns:
{patterns_str}

=== ANALYSIS INSTRUCTIONS ===
Perform comprehensive analysis by:

1. **Log Analysis**:
   - Identify temporal patterns and sequences
   - Analyze error propagation
   - Detect anomalies in current logs

2. **Historical Analysis**:
   - Compare with similar past incidents
   - Leverage known causal relationships
   - Consider entity historical behavior

3. **Cross-Validation**:
   - Validate log findings against historical patterns
   - Identify novel vs. recurring issues
   - Assess confidence based on both sources

4. **Synthesis**:
   - Combine insights from both perspectives
   - Prioritize hypotheses supported by both logs and history
   - Flag discrepancies between current and historical patterns

=== OUTPUT FORMAT ===
Provide 3-5 root cause hypotheses in JSON array format:

[
  {{
    "hypothesis": "Clear description of the root cause",
    "confidence": 0.90,
    "reasoning": "Comprehensive explanation using both log and historical evidence",
    "evidence": [
      "Log evidence: specific events or patterns",
      "Historical evidence: similar incidents or known patterns"
    ],
    "category": "hardware|software|network|config|resource",
    "affected_components": ["List of affected components"],
    "suggested_resolution": "Resolution based on both current analysis and past successes"
  }}
]

**IMPORTANT**: 
- Synthesize insights from BOTH log data and historical knowledge
- Higher confidence when both sources agree
- Clearly distinguish between log-based and history-based evidence
- Provide the most comprehensive analysis possible
- Return ONLY the JSON array, no additional text

Generate your hypotheses now:"""

        return prompt
    
    def _format_entities(self, entities: List[Dict[str, Any]]) -> str:
        """Format entities for prompt."""
        if not entities:
            return "No entities identified"
        
        formatted = []
        for i, entity in enumerate(entities, 1):
            formatted.append(
                f"{i}. {entity.get('type', 'Unknown')} - "
                f"{entity.get('name', 'Unknown')} "
                f"({entity.get('context', 'No context')})"
            )
        
        return '\n'.join(formatted)
    
    def _format_similar_incidents(self, incidents: List[Dict[str, Any]]) -> str:
        """Format similar incidents for prompt."""
        if not incidents:
            return "No similar incidents found"
        
        formatted = []
        for i, incident in enumerate(incidents[:5], 1):
            formatted.append(
                f"{i}. {incident.get('incident_id', 'Unknown')} "
                f"(Similarity: {incident.get('similarity_score', 0):.2f})\n"
                f"   Root Cause: {incident.get('root_cause', 'Unknown')}\n"
                f"   Components: {', '.join(incident.get('components', []))}"
            )
        
        return '\n\n'.join(formatted)
    
    def _format_causal_paths(self, paths: List[Dict[str, Any]]) -> str:
        """Format causal paths for prompt."""
        if not paths:
            return "No known causal paths found"
        
        formatted = []
        for i, path in enumerate(paths[:3], 1):
            events_in_path = path.get('events', [])
            formatted.append(
                f"{i}. Chain: {' → '.join([e.get('component', '?') for e in events_in_path])} "
                f"→ {path.get('error_type', 'Error')}"
            )
        
        return '\n'.join(formatted)
    
    def _format_entity_context(self, context: Dict[str, Any]) -> str:
        """Format entity context for prompt."""
        if not context:
            return "No entity context available"
        
        formatted = []
        for entity_name, info in context.items():
            formatted.append(
                f"- {entity_name}: "
                f"{info.get('event_count', 0)} events, "
                f"{info.get('incident_count', 0)} incidents"
            )
        
        return '\n'.join(formatted)
    
    def _format_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """Format common patterns for prompt."""
        if not patterns:
            return "No common patterns found"
        
        formatted = []
        for i, pattern in enumerate(patterns, 1):
            formatted.append(
                f"{i}. {pattern.get('pattern', 'Unknown')} "
                f"(Frequency: {pattern.get('frequency', 0)})"
            )
        
        return '\n'.join(formatted)
