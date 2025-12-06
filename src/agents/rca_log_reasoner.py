"""
Log-Focused RCA Reasoner Agent.

This reasoner specializes in analyzing raw log patterns and temporal sequences
to identify root causes.
"""

from typing import Dict, Any, List
from loguru import logger

from src.agents.rca_reasoner_base import RCAReasonerAgent


class LogFocusedReasoner(RCAReasonerAgent):
    """
    RCA Reasoner that focuses on log pattern analysis.
    
    Specializes in:
    - Temporal sequence analysis
    - Error pattern recognition
    - Component interaction analysis
    - Anomaly detection in logs
    """
    
    def __init__(self, **kwargs):
        """Initialize Log-Focused Reasoner with Mistral-7B."""
        super().__init__(
            name="LogFocusedReasoner",
            model="mistral:7b",
            reasoning_type="log_focused",
            temperature=0.3,  # Lower temperature for focused analysis
            max_tokens=2000,
            **kwargs
        )
    
    def _build_reasoning_prompt(self, input_data: Dict[str, Any]) -> str:
        """
        Build log-focused reasoning prompt.
        
        Focuses on:
        - Event sequences
        - Error messages
        - Temporal patterns
        - Component interactions
        
        Args:
            input_data: Input data with events, errors, timeline
            
        Returns:
            Formatted prompt string
        """
        events = input_data.get("events", [])
        errors = input_data.get("error_messages", [])
        timeline = input_data.get("timeline", events)
        entities = input_data.get("entities", [])
        
        # Format data for prompt
        events_str = self._format_events(events)
        errors_str = self._format_errors(errors)
        timeline_str = self._format_timeline(timeline)
        entities_str = self._format_entities(entities)
        
        prompt = f"""You are an expert system administrator analyzing log data for root cause analysis.

Your task is to identify the most likely root causes of a system incident by analyzing log events, error messages, and temporal patterns.

=== LOG EVENTS ===
{events_str}

=== ERROR MESSAGES ===
{errors_str}

=== TIMELINE (Temporal Sequence) ===
{timeline_str}

=== INVOLVED ENTITIES ===
{entities_str}

=== ANALYSIS INSTRUCTIONS ===
Analyze the log data focusing on:
1. **Temporal Patterns**: What sequence of events led to the failure?
2. **Error Propagation**: How did errors spread across components?
3. **Component Interactions**: Which components were involved and how?
4. **Anomalies**: What unusual patterns or behaviors are present?
5. **Trigger Events**: What was the initial event that started the cascade?

=== OUTPUT FORMAT ===
Provide 3-5 root cause hypotheses in JSON array format. Each hypothesis must include:

[
  {{
    "hypothesis": "Clear description of the root cause",
    "confidence": 0.85,
    "reasoning": "Detailed explanation based on log evidence",
    "evidence": ["Specific log entries or patterns supporting this hypothesis"],
    "category": "hardware|software|network|config|resource",
    "affected_components": ["List of affected components"],
    "suggested_resolution": "Actionable steps to resolve this root cause"
  }}
]

**IMPORTANT**: 
- Base your analysis ONLY on the log data provided
- Confidence scores should reflect certainty based on log evidence
- Provide specific log references in evidence
- Focus on temporal causality
- Return ONLY the JSON array, no additional text

Generate your hypotheses now:"""

        return prompt
    
    def _format_entities(self, entities: List[Dict[str, Any]]) -> str:
        """
        Format entities for prompt.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Formatted string
        """
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
