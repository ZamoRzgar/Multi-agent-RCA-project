"""
KG-Focused RCA Reasoner Agent.

This reasoner specializes in leveraging knowledge graph data and historical
incidents to identify root causes.
"""

from typing import Dict, Any, List
from loguru import logger

from src.agents.rca_reasoner_base import RCAReasonerAgent


class KGFocusedReasoner(RCAReasonerAgent):
    """
    RCA Reasoner that focuses on knowledge graph analysis.
    
    Specializes in:
    - Historical incident patterns
    - Known causal relationships
    - Entity behavior patterns
    - Recurring failure modes
    """
    
    def __init__(self, **kwargs):
        """Initialize KG-Focused Reasoner with LLaMA2-7B."""
        super().__init__(
            name="KGFocusedReasoner",
            model="llama2:7b",
            reasoning_type="kg_focused",
            temperature=0.3,
            max_tokens=2000,
            **kwargs
        )
    
    def _build_reasoning_prompt(self, input_data: Dict[str, Any]) -> str:
        """
        Build KG-focused reasoning prompt.
        
        Focuses on:
        - Similar historical incidents
        - Known causal paths
        - Entity context from KG
        - Common patterns
        
        Args:
            input_data: Input data with KG facts and current incident data
            
        Returns:
            Formatted prompt string
        """
        # Current incident data
        events = input_data.get("events", [])
        errors = input_data.get("error_messages", [])
        
        # KG data
        similar_incidents = input_data.get("similar_incidents", [])
        causal_paths = input_data.get("causal_paths", [])
        entity_context = input_data.get("entity_context", {})
        patterns = input_data.get("patterns", [])
        
        # Format data for prompt
        events_str = self._format_events(events)
        errors_str = self._format_errors(errors)
        similar_str = self._format_similar_incidents(similar_incidents)
        causal_str = self._format_causal_paths(causal_paths)
        context_str = self._format_entity_context(entity_context)
        patterns_str = self._format_patterns(patterns)
        
        prompt = f"""You are an expert in root cause analysis using historical incident data and knowledge graphs.

Your task is to identify the most likely root causes by analyzing patterns from past incidents and known causal relationships.

=== CURRENT INCIDENT ===
Events:
{events_str}

Errors:
{errors_str}

=== HISTORICAL KNOWLEDGE ===

Similar Past Incidents:
{similar_str}

Known Causal Paths:
{causal_str}

Entity Historical Context:
{context_str}

Common Patterns:
{patterns_str}

=== ANALYSIS INSTRUCTIONS ===
Analyze the knowledge graph data focusing on:
1. **Historical Patterns**: What similar incidents occurred before?
2. **Root Cause Recurrence**: What root causes were identified in similar cases?
3. **Causal Relationships**: What known causal chains match this incident?
4. **Entity Behavior**: How have these entities behaved in past incidents?
5. **Pattern Matching**: What recurring patterns are present?

=== OUTPUT FORMAT ===
Provide 3-5 root cause hypotheses in JSON array format:

[
  {{
    "hypothesis": "Clear description of the root cause",
    "confidence": 0.85,
    "reasoning": "Explanation based on historical evidence",
    "evidence": ["References to similar incidents or known patterns"],
    "category": "hardware|software|network|config|resource",
    "affected_components": ["List of affected components"],
    "suggested_resolution": "Resolution based on past successful fixes"
  }}
]

**IMPORTANT**: 
- Base your analysis on historical patterns and KG data
- Higher confidence for root causes that match known patterns
- Reference specific past incidents in evidence
- Leverage known causal relationships
- Return ONLY the JSON array, no additional text

Generate your hypotheses now:"""

        return prompt
    
    def _format_similar_incidents(self, incidents: List[Dict[str, Any]]) -> str:
        """Format similar incidents for prompt."""
        if not incidents:
            return "No similar incidents found in knowledge graph"
        
        formatted = []
        for i, incident in enumerate(incidents[:5], 1):  # Top 5
            formatted.append(
                f"{i}. Incident {incident.get('incident_id', 'Unknown')} "
                f"(Similarity: {incident.get('similarity_score', 0):.2f})\n"
                f"   - Dataset: {incident.get('dataset', 'Unknown')}\n"
                f"   - Label: {incident.get('label', 'Unknown')}\n"
                f"   - Root Cause: {incident.get('root_cause', 'Unknown')}\n"
                f"   - Components: {', '.join(incident.get('components', []))}"
            )
        
        return '\n\n'.join(formatted)
    
    def _format_causal_paths(self, paths: List[Dict[str, Any]]) -> str:
        """Format causal paths for prompt."""
        if not paths:
            return "No known causal paths found"
        
        formatted = []
        for i, path in enumerate(paths[:3], 1):  # Top 3
            events_in_path = path.get('events', [])
            formatted.append(
                f"{i}. Causal Chain (Length: {path.get('path_length', 0)})\n"
                f"   - Error Type: {path.get('error_type', 'Unknown')}\n"
                f"   - Events: {' → '.join([e.get('component', 'Unknown') for e in events_in_path])}"
            )
        
        return '\n\n'.join(formatted)
    
    def _format_entity_context(self, context: Dict[str, Any]) -> str:
        """Format entity context for prompt."""
        if not context:
            return "No entity context available"
        
        formatted = []
        for entity_name, info in context.items():
            formatted.append(
                f"- {entity_name} ({info.get('type', 'Unknown')})\n"
                f"  Event Count: {info.get('event_count', 0)}, "
                f"Incident Count: {info.get('incident_count', 0)}\n"
                f"  Recent Severities: {', '.join(info.get('recent_severities', []))}"
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
