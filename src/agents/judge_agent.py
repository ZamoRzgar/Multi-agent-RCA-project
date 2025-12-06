"""
Judge Agent for evaluating RCA hypotheses.

This agent evaluates hypotheses from all RCA reasoners and provides
scores, feedback, and rankings.
"""

from typing import Dict, Any, List
from loguru import logger
import json
import re

from src.agents.base_agent import BaseAgent


class JudgeAgent(BaseAgent):
    """
    Agent that evaluates and scores RCA hypotheses.
    
    Responsibilities:
    - Score hypotheses from all reasoners (0-100)
    - Provide feedback on strengths and weaknesses
    - Rank hypotheses by quality
    - Generate consensus analysis
    - Guide debate process
    """
    
    def __init__(self, **kwargs):
        """Initialize Judge Agent with Qwen2-7B."""
        super().__init__(
            name="JudgeAgent",
            model="qwen2:7b",  # Good at reasoning and evaluation
            temperature=0.2,   # Low temperature for consistent scoring
            max_tokens=3000,
            **kwargs
        )
        logger.info("Initialized Judge Agent")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate hypotheses from all reasoners.
        
        Args:
            input_data: Dictionary containing:
                - log_focused_hypotheses: List of hypotheses
                - kg_focused_hypotheses: List of hypotheses
                - hybrid_hypotheses: List of hypotheses
                - events: Original events (for context)
                - errors: Original errors (for context)
                - similar_incidents: From KG (optional)
                
        Returns:
            Dictionary with:
                - evaluated_hypotheses: List of scored hypotheses
                - top_hypothesis: Highest scoring hypothesis
                - consensus_analysis: Overall agreement analysis
                - debate_guidance: Suggestions for debate
        """
        logger.info("Starting hypothesis evaluation")
        
        # Collect all hypotheses
        all_hypotheses = self._collect_hypotheses(input_data)
        logger.info(f"Collected {len(all_hypotheses)} hypotheses for evaluation")
        
        if not all_hypotheses:
            logger.warning("No hypotheses to evaluate")
            return {
                "evaluated_hypotheses": [],
                "top_hypothesis": None,
                "consensus_analysis": "No hypotheses provided",
                "debate_guidance": "Generate hypotheses first"
            }
        
        # Build evaluation prompt
        prompt = self._build_evaluation_prompt(all_hypotheses, input_data)
        
        # Call LLM for evaluation
        logger.debug(f"Calling LLM with prompt length: {len(prompt)}")
        response = self._call_llm(prompt)
        
        # Parse evaluation
        evaluated = self._parse_evaluation(response, all_hypotheses)
        
        # Rank hypotheses
        ranked = self.rank_hypotheses(evaluated)
        
        # Generate consensus analysis
        consensus = self._analyze_consensus(ranked)
        
        # Generate debate guidance
        guidance = self._generate_debate_guidance(ranked)
        
        logger.info(f"Evaluation complete: {len(ranked)} hypotheses ranked")
        
        return {
            "evaluated_hypotheses": ranked,
            "top_hypothesis": ranked[0] if ranked else None,
            "num_evaluated": len(ranked),
            "consensus_analysis": consensus,
            "debate_guidance": guidance
        }
    
    def _collect_hypotheses(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Collect hypotheses from all reasoners.
        
        Args:
            input_data: Input data with hypotheses from reasoners
            
        Returns:
            List of all hypotheses with source labels
        """
        hypotheses = []
        
        # From log-focused reasoner
        for i, h in enumerate(input_data.get("log_focused_hypotheses", [])):
            hypotheses.append({
                **h,
                "source": "log_focused",
                "hypothesis_id": f"log_{i+1}"
            })
        
        # From KG-focused reasoner
        for i, h in enumerate(input_data.get("kg_focused_hypotheses", [])):
            hypotheses.append({
                **h,
                "source": "kg_focused",
                "hypothesis_id": f"kg_{i+1}"
            })
        
        # From hybrid reasoner
        for i, h in enumerate(input_data.get("hybrid_hypotheses", [])):
            hypotheses.append({
                **h,
                "source": "hybrid",
                "hypothesis_id": f"hybrid_{i+1}"
            })
        
        return hypotheses
    
    def _build_evaluation_prompt(
        self,
        hypotheses: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """
        Build evaluation prompt for LLM.
        
        Args:
            hypotheses: List of hypotheses to evaluate
            context: Original incident data for context
            
        Returns:
            Formatted prompt string
        """
        # Format context
        events_str = self._format_events(context.get("events", []))
        errors_str = self._format_errors(context.get("errors", []))
        
        # Format hypotheses
        hypotheses_str = self._format_hypotheses(hypotheses)
        
        prompt = f"""You are an expert judge evaluating root cause analysis hypotheses.

Your task is to objectively evaluate each hypothesis based on multiple criteria and assign scores.

=== INCIDENT CONTEXT ===

Events:
{events_str}

Errors:
{errors_str}

=== HYPOTHESES TO EVALUATE ===

{hypotheses_str}

=== EVALUATION CRITERIA ===

For each hypothesis, evaluate on these criteria:

1. **Evidence Quality (0-30 points)**:
   - Specificity and directness of evidence
   - Number of supporting facts
   - Evidence from logs vs historical data

2. **Reasoning Strength (0-25 points)**:
   - Logical coherence
   - Causal chain clarity
   - Explanation completeness

3. **Confidence Calibration (0-20 points)**:
   - Confidence matches evidence strength
   - Appropriate uncertainty acknowledgment
   - Not overconfident or underconfident

4. **Completeness (0-15 points)**:
   - Identifies affected components
   - Provides resolution steps
   - Considers side effects

5. **Consistency (0-10 points)**:
   - Aligns with other evidence
   - Doesn't contradict facts
   - Fits known patterns

**Total Score**: 0-100 points

=== OUTPUT FORMAT ===

Return a JSON array with evaluations for each hypothesis:

[
  {{
    "hypothesis_id": "log_1",
    "source": "log_focused",
    "hypothesis": "Original hypothesis text",
    "judge_score": 85,
    "evidence_quality": 25,
    "reasoning_strength": 22,
    "confidence_calibration": 18,
    "completeness": 12,
    "consistency": 8,
    "strengths": ["Strength 1", "Strength 2", "Strength 3"],
    "weaknesses": ["Weakness 1", "Weakness 2"],
    "feedback": "Detailed feedback explaining the scores"
  }}
]

**IMPORTANT**: 
- Be objective and fair
- Score based on evidence, not source
- Provide specific, actionable feedback
- Return ONLY the JSON array, no additional text

Evaluate the hypotheses now:"""

        return prompt
    
    def _format_events(self, events: List[Dict[str, Any]]) -> str:
        """Format events for prompt."""
        if not events:
            return "No events available"
        
        formatted = []
        for i, event in enumerate(events[:10], 1):
            formatted.append(
                f"{i}. [{event.get('timestamp', 'N/A')}] "
                f"{event.get('component', 'Unknown')}: "
                f"{event.get('message', event.get('action', 'No message'))}"
            )
        
        return '\n'.join(formatted)
    
    def _format_errors(self, errors: List[Dict[str, Any]]) -> str:
        """Format errors for prompt."""
        if not errors:
            return "No errors available"
        
        formatted = []
        for i, error in enumerate(errors, 1):
            formatted.append(
                f"{i}. {error.get('error_type', 'Unknown')}: "
                f"{error.get('message', 'No message')}"
            )
        
        return '\n'.join(formatted)
    
    def _format_hypotheses(self, hypotheses: List[Dict[str, Any]]) -> str:
        """Format hypotheses for prompt."""
        formatted = []
        
        for i, h in enumerate(hypotheses, 1):
            formatted.append(
                f"Hypothesis {i} (ID: {h.get('hypothesis_id', 'unknown')}, "
                f"Source: {h.get('source', 'unknown')}):\n"
                f"  - Hypothesis: {h.get('hypothesis', 'No hypothesis')}\n"
                f"  - Confidence: {h.get('confidence', 0):.2f}\n"
                f"  - Reasoning: {h.get('reasoning', 'No reasoning')[:200]}...\n"
                f"  - Evidence: {len(h.get('evidence', []))} items\n"
                f"  - Category: {h.get('category', 'unknown')}\n"
                f"  - Resolution: {h.get('suggested_resolution', 'None')[:100]}..."
            )
        
        return '\n\n'.join(formatted)
    
    def _parse_evaluation(
        self,
        response: str,
        original_hypotheses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Parse LLM evaluation response.
        
        Args:
            response: LLM response text
            original_hypotheses: Original hypotheses for fallback
            
        Returns:
            List of evaluated hypotheses with scores
        """
        logger.debug("Parsing evaluation response")
        
        try:
            # Extract JSON array
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                json_str = json_match.group(0)
                # Clean up
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                evaluations = json.loads(json_str)
                
                # Merge with original hypotheses
                evaluated = []
                for eval_item in evaluations:
                    # Find matching original hypothesis
                    hyp_id = eval_item.get("hypothesis_id", "")
                    original = next(
                        (h for h in original_hypotheses if h.get("hypothesis_id") == hyp_id),
                        {}
                    )
                    
                    # Merge
                    evaluated.append({
                        **original,
                        **eval_item,
                        "judge_score": int(eval_item.get("judge_score", 50))
                    })
                
                logger.info(f"Successfully parsed {len(evaluated)} evaluations")
                return evaluated
            else:
                logger.warning("No JSON array found in response")
                return self._fallback_evaluation(original_hypotheses)
        
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Failed to parse evaluation: {e}")
            return self._fallback_evaluation(original_hypotheses)
    
    def _fallback_evaluation(
        self,
        hypotheses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fallback evaluation when LLM parsing fails.
        
        Uses confidence scores as basis for judge scores.
        
        Args:
            hypotheses: Original hypotheses
            
        Returns:
            Hypotheses with basic scores
        """
        logger.info("Using fallback evaluation")
        
        evaluated = []
        for h in hypotheses:
            confidence = h.get("confidence", 0.5)
            # Convert confidence (0-1) to score (0-100)
            judge_score = int(confidence * 100)
            
            evaluated.append({
                **h,
                "judge_score": judge_score,
                "evidence_quality": int(confidence * 30),
                "reasoning_strength": int(confidence * 25),
                "confidence_calibration": int(confidence * 20),
                "completeness": int(confidence * 15),
                "consistency": int(confidence * 10),
                "strengths": ["Based on reasoner confidence"],
                "weaknesses": ["Evaluation incomplete - fallback mode"],
                "feedback": f"Fallback evaluation based on confidence: {confidence:.2f}"
            })
        
        return evaluated
    
    def rank_hypotheses(
        self,
        evaluated_hypotheses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank hypotheses by judge score.
        
        Args:
            evaluated_hypotheses: Hypotheses with scores
            
        Returns:
            Sorted list (highest score first) with rank numbers
        """
        # Sort by score
        ranked = sorted(
            evaluated_hypotheses,
            key=lambda x: x.get("judge_score", 0),
            reverse=True
        )
        
        # Add rank numbers
        for i, h in enumerate(ranked, 1):
            h["rank"] = i
        
        return ranked
    
    def _analyze_consensus(self, ranked_hypotheses: List[Dict[str, Any]]) -> str:
        """Generate consensus analysis."""
        if not ranked_hypotheses:
            return "No hypotheses to analyze"
        
        # Check for common themes
        categories = [h.get("category", "unknown") for h in ranked_hypotheses]
        most_common_category = max(set(categories), key=categories.count)
        
        # Check score distribution
        top_score = ranked_hypotheses[0].get("judge_score", 0)
        score_range = top_score - ranked_hypotheses[-1].get("judge_score", 0)
        
        if score_range < 20:
            agreement = "strong"
        elif score_range < 40:
            agreement = "moderate"
        else:
            agreement = "weak"
        
        return (
            f"{agreement.capitalize()} consensus among reasoners. "
            f"Most hypotheses point to '{most_common_category}' category. "
            f"Top hypothesis scored {top_score}/100."
        )
    
    def _generate_debate_guidance(self, ranked_hypotheses: List[Dict[str, Any]]) -> str:
        """Generate guidance for debate."""
        if not ranked_hypotheses:
            return "No guidance available"
        
        top_3 = ranked_hypotheses[:3]
        
        # Identify areas of disagreement
        categories = [h.get("category", "unknown") for h in top_3]
        sources = [h.get("source", "unknown") for h in top_3]
        
        if len(set(categories)) > 1:
            guidance = f"Debate should focus on distinguishing between {' vs '.join(set(categories))} categories. "
        else:
            guidance = f"Strong agreement on {categories[0]} category. "
        
        guidance += f"Top hypotheses from {', '.join(set(sources))} reasoners. "
        guidance += "Focus on evidence quality and resolution strategies."
        
        return guidance
