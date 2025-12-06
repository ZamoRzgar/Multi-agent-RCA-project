"""
Base RCA Reasoner Agent.

This module provides the base class for all RCA reasoning agents.
Each reasoner generates root cause hypotheses based on different data sources.
"""

from typing import Dict, Any, List
from loguru import logger
from abc import abstractmethod
import json
import re

from src.agents.base_agent import BaseAgent


class RCAReasonerAgent(BaseAgent):
    """
    Base class for RCA reasoning agents.
    
    Each reasoner analyzes incident data and generates root cause hypotheses
    with confidence scores, reasoning, and evidence.
    """
    
    def __init__(
        self,
        name: str,
        model: str,
        reasoning_type: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        **kwargs
    ):
        """
        Initialize RCA Reasoner.
        
        Args:
            name: Agent name
            model: LLM model to use
            reasoning_type: Type of reasoning (log_focused, kg_focused, hybrid)
            temperature: LLM temperature (lower for more focused reasoning)
            max_tokens: Maximum tokens for response
        """
        super().__init__(
            name=name,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        self.reasoning_type = reasoning_type
        logger.info(f"Initialized {name} with reasoning type: {reasoning_type}")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate root cause hypotheses.
        
        Args:
            input_data: Dictionary containing:
                - events: List of log events
                - entities: List of entities
                - error_messages: List of errors
                - timeline: Temporal sequence (optional)
                - similar_incidents: From KG (optional)
                - causal_paths: From KG (optional)
                - entity_context: From KG (optional)
                - patterns: From KG (optional)
        
        Returns:
            Dictionary with:
                - hypotheses: List of root cause hypotheses
                - reasoning_type: Type of reasoning used
                - model_used: LLM model used
        """
        logger.info(f"Generating hypotheses using {self.reasoning_type} reasoning")
        
        # Build prompt based on reasoning type
        prompt = self._build_reasoning_prompt(input_data)
        
        # Call LLM
        logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
        response = self._call_llm(prompt)
        
        # Parse hypotheses from response
        hypotheses = self._parse_hypotheses(response)
        
        # Rank hypotheses by confidence
        ranked_hypotheses = self._rank_hypotheses(hypotheses)
        
        logger.info(f"Generated {len(ranked_hypotheses)} hypotheses")
        
        return {
            "hypotheses": ranked_hypotheses,
            "reasoning_type": self.reasoning_type,
            "model_used": self.model,
            "num_hypotheses": len(ranked_hypotheses)
        }
    
    def refine_hypotheses(
        self,
        input_data: Dict[str, Any],
        previous_hypotheses: List[Dict[str, Any]],
        judge_feedback: List[Dict[str, Any]],
        other_top_hypotheses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Refine hypotheses based on judge feedback and other reasoners' hypotheses.
        
        Args:
            input_data: Original incident data
            previous_hypotheses: This reasoner's previous hypotheses
            judge_feedback: Feedback from judge on previous hypotheses
            other_top_hypotheses: Top hypotheses from other reasoners
            
        Returns:
            Dictionary with refined hypotheses
        """
        logger.info(f"Refining hypotheses based on judge feedback")
        
        # Build refinement prompt
        prompt = self._build_refinement_prompt(
            input_data,
            previous_hypotheses,
            judge_feedback,
            other_top_hypotheses
        )
        
        # Call LLM
        logger.debug(f"Calling LLM for refinement with prompt length: {len(prompt)}")
        response = self._call_llm(prompt)
        
        # Parse refined hypotheses
        refined_hypotheses = self._parse_hypotheses(response)
        
        # Rank by confidence
        ranked = self._rank_hypotheses(refined_hypotheses)
        
        logger.info(f"Generated {len(ranked)} refined hypotheses")
        
        return {
            "hypotheses": ranked,
            "reasoning_type": self.reasoning_type,
            "model_used": self.model,
            "num_hypotheses": len(ranked),
            "refined": True
        }
    
    def _build_refinement_prompt(
        self,
        input_data: Dict[str, Any],
        previous_hypotheses: List[Dict[str, Any]],
        judge_feedback: List[Dict[str, Any]],
        other_top_hypotheses: List[Dict[str, Any]]
    ) -> str:
        """
        Build refinement prompt with feedback.
        
        Args:
            input_data: Original incident data
            previous_hypotheses: Previous hypotheses
            judge_feedback: Judge's feedback
            other_top_hypotheses: Other reasoners' top hypotheses
            
        Returns:
            Refinement prompt string
        """
        # Format previous hypotheses with feedback
        prev_hyp_str = self._format_previous_hypotheses(previous_hypotheses, judge_feedback)
        
        # Format other reasoners' hypotheses
        other_hyp_str = self._format_other_hypotheses(other_top_hypotheses)
        
        # Get base context
        base_prompt = self._build_reasoning_prompt(input_data)
        
        refinement_prompt = f"""You are refining your root cause hypotheses based on judge feedback and insights from other reasoners.

=== YOUR PREVIOUS HYPOTHESES & JUDGE FEEDBACK ===

{prev_hyp_str}

=== OTHER REASONERS' TOP HYPOTHESES ===

{other_hyp_str}

=== INSTRUCTIONS FOR REFINEMENT ===

Based on the judge's feedback and other reasoners' insights:

1. **Address weaknesses** identified by the judge
2. **Strengthen evidence** and reasoning
3. **Incorporate insights** from other reasoners where relevant
4. **Improve resolution** steps to be more specific and actionable
5. **Adjust confidence** based on evidence strength

You may:
- Refine existing hypotheses to address weaknesses
- Merge similar hypotheses if they complement each other
- Generate new hypotheses if you identify gaps
- Increase confidence if evidence is stronger
- Decrease confidence if weaknesses are significant

=== ORIGINAL INCIDENT DATA ===

{base_prompt.split('===')[-1] if '===' in base_prompt else base_prompt}

Provide your refined hypotheses in the same JSON format as before.
Focus on quality over quantity - 2-4 strong hypotheses are better than many weak ones.
"""
        
        return refinement_prompt
    
    def _format_previous_hypotheses(
        self,
        hypotheses: List[Dict[str, Any]],
        feedback: List[Dict[str, Any]]
    ) -> str:
        """Format previous hypotheses with judge feedback."""
        if not hypotheses:
            return "No previous hypotheses"
        
        formatted = []
        for i, hyp in enumerate(hypotheses[:3], 1):  # Top 3
            # Find matching feedback
            feedback_item = next(
                (f for f in feedback if f.get("hypothesis", "").startswith(hyp.get("hypothesis", "")[:50])),
                {}
            )
            
            formatted.append(
                f"Hypothesis {i}:\n"
                f"  Statement: {hyp.get('hypothesis', 'N/A')}\n"
                f"  Your Confidence: {hyp.get('confidence', 0):.2f}\n"
                f"  Judge Score: {feedback_item.get('score', 'N/A')}/100\n"
                f"  \n"
                f"  Strengths:\n"
            )
            
            for strength in feedback_item.get('strengths', ['No strengths noted']):
                formatted.append(f"    ✓ {strength}\n")
            
            formatted.append(f"  \n  Weaknesses:\n")
            for weakness in feedback_item.get('weaknesses', ['No weaknesses noted']):
                formatted.append(f"    ✗ {weakness}\n")
            
            if feedback_item.get('feedback'):
                formatted.append(f"  \n  Judge Feedback: {feedback_item['feedback'][:200]}...\n")
            
            formatted.append("\n")
        
        return ''.join(formatted)
    
    def _format_other_hypotheses(self, other_hypotheses: List[Dict[str, Any]]) -> str:
        """Format other reasoners' top hypotheses."""
        if not other_hypotheses:
            return "No hypotheses from other reasoners"
        
        formatted = []
        for i, hyp in enumerate(other_hypotheses[:3], 1):  # Top 3
            formatted.append(
                f"{i}. [{hyp.get('source', 'unknown')}] "
                f"Score: {hyp.get('judge_score', hyp.get('score', 'N/A'))}/100\n"
                f"   {hyp.get('hypothesis', 'N/A')[:100]}...\n"
                f"   Confidence: {hyp.get('confidence', 0):.2f}\n\n"
            )
        
        return ''.join(formatted)
    
    @abstractmethod
    def _build_reasoning_prompt(self, input_data: Dict[str, Any]) -> str:
        """
        Build reasoning prompt based on input data.
        
        Must be implemented by subclasses to provide specialized prompts.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Formatted prompt string
        """
        raise NotImplementedError("Subclasses must implement _build_reasoning_prompt")
    
    def _parse_hypotheses(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured hypotheses.
        
        Args:
            response: LLM response text
            
        Returns:
            List of hypothesis dictionaries
        """
        logger.debug("Parsing hypotheses from LLM response")
        
        try:
            # Try to extract JSON array from response
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                json_str = json_match.group(0)
                # Clean up common JSON issues
                json_str = self._clean_json_string(json_str)
                hypotheses = json.loads(json_str)
                
                # Validate and normalize hypotheses
                validated_hypotheses = []
                for h in hypotheses:
                    if isinstance(h, dict) and "hypothesis" in h:
                        validated_hypotheses.append(self._normalize_hypothesis(h))
                
                logger.info(f"Successfully parsed {len(validated_hypotheses)} hypotheses")
                return validated_hypotheses
            else:
                logger.warning("No JSON array found in response")
                return self._fallback_parse(response)
        
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse hypotheses as JSON: {e}")
            return self._fallback_parse(response)
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        Clean up common JSON formatting issues.
        
        Args:
            json_str: Raw JSON string
            
        Returns:
            Cleaned JSON string
        """
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix incomplete strings at end
        json_str = json_str.strip()
        if not json_str.endswith(']'):
            open_brackets = json_str.count('[')
            close_brackets = json_str.count(']')
            json_str += ']' * (open_brackets - close_brackets)
        
        return json_str
    
    def _normalize_hypothesis(self, hypothesis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize hypothesis to ensure all required fields exist.
        
        Args:
            hypothesis: Raw hypothesis dictionary
            
        Returns:
            Normalized hypothesis dictionary
        """
        return {
            "hypothesis": hypothesis.get("hypothesis", "Unknown root cause"),
            "confidence": float(hypothesis.get("confidence", 0.5)),
            "reasoning": hypothesis.get("reasoning", "No reasoning provided"),
            "evidence": hypothesis.get("evidence", []),
            "category": hypothesis.get("category", "unknown"),
            "affected_components": hypothesis.get("affected_components", []),
            "suggested_resolution": hypothesis.get("suggested_resolution", "No resolution suggested")
        }
    
    def _fallback_parse(self, response: str) -> List[Dict[str, Any]]:
        """
        Fallback parsing when JSON extraction fails.
        
        Attempts to extract basic hypothesis information from text.
        
        Args:
            response: LLM response text
            
        Returns:
            List with single basic hypothesis
        """
        logger.info("Using fallback parsing")
        
        # Try to extract key information from text
        lines = response.split('\n')
        hypothesis_text = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('{') and not line.startswith('['):
                hypothesis_text.append(line)
        
        if hypothesis_text:
            return [{
                "hypothesis": ' '.join(hypothesis_text[:3]),  # First 3 lines
                "confidence": 0.5,
                "reasoning": "Extracted from text response",
                "evidence": hypothesis_text,
                "category": "unknown",
                "affected_components": [],
                "suggested_resolution": "Manual investigation required"
            }]
        
        return []
    
    def _rank_hypotheses(self, hypotheses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank hypotheses by confidence score.
        
        Args:
            hypotheses: List of hypotheses
            
        Returns:
            Sorted list of hypotheses (highest confidence first)
        """
        return sorted(hypotheses, key=lambda x: x.get("confidence", 0), reverse=True)
    
    def _format_events(self, events: List[Dict[str, Any]]) -> str:
        """
        Format events for prompt.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Formatted string
        """
        if not events:
            return "No events available"
        
        formatted = []
        for i, event in enumerate(events[:20], 1):  # Limit to 20 events
            formatted.append(
                f"{i}. [{event.get('timestamp', 'N/A')}] "
                f"{event.get('component', 'Unknown')}: "
                f"{event.get('message', event.get('action', 'No message'))}"
            )
        
        return '\n'.join(formatted)
    
    def _format_errors(self, errors: List[Dict[str, Any]]) -> str:
        """
        Format error messages for prompt.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            Formatted string
        """
        if not errors:
            return "No error messages available"
        
        formatted = []
        for i, error in enumerate(errors, 1):
            formatted.append(
                f"{i}. {error.get('error_type', 'Unknown')}: "
                f"{error.get('message', 'No message')} "
                f"(Component: {error.get('component', 'Unknown')})"
            )
        
        return '\n'.join(formatted)
    
    def _format_timeline(self, timeline: List[Dict[str, Any]]) -> str:
        """
        Format timeline for prompt.
        
        Args:
            timeline: List of events in temporal order
            
        Returns:
            Formatted string
        """
        if not timeline:
            return "No timeline available"
        
        return self._format_events(timeline)
