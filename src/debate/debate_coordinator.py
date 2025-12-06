"""
Debate Coordinator for Multi-Agent RCA.

This module orchestrates multi-round debates between RCA reasoners
to refine hypotheses and converge to the best root cause.
"""

from typing import Dict, Any, List
from loguru import logger


class DebateCoordinator:
    """
    Coordinates multi-round debate between RCA reasoners.
    
    The debate protocol:
    1. Round 1: Initial hypotheses from all reasoners
    2. Judge evaluates and provides feedback
    3. Round 2+: Reasoners refine based on feedback
    4. Convergence: Stop when scores plateau or max rounds reached
    5. Selection: Choose best hypothesis across all rounds
    """
    
    def __init__(
        self,
        log_reasoner,
        kg_reasoner,
        hybrid_reasoner,
        judge,
        max_rounds: int = 3,
        convergence_threshold: float = 5.0
    ):
        """
        Initialize Debate Coordinator.
        
        Args:
            log_reasoner: Log-focused reasoner agent
            kg_reasoner: KG-focused reasoner agent
            hybrid_reasoner: Hybrid reasoner agent
            judge: Judge agent for evaluation
            max_rounds: Maximum number of debate rounds
            convergence_threshold: Min improvement to continue (points)
        """
        self.reasoners = {
            "log_focused": log_reasoner,
            "kg_focused": kg_reasoner,
            "hybrid": hybrid_reasoner
        }
        self.judge = judge
        self.max_rounds = max_rounds
        self.convergence_threshold = convergence_threshold
        
        logger.info(f"Initialized Debate Coordinator (max_rounds={max_rounds})")
    
    def run_debate(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run multi-round debate protocol.
        
        Args:
            input_data: Incident data with events, errors, KG facts
            
        Returns:
            Dictionary with:
                - rounds: List of round results
                - final_hypothesis: Best hypothesis selected
                - total_rounds: Number of rounds executed
                - convergence_achieved: Whether early convergence occurred
                - improvement_trajectory: Score progression
        """
        logger.info("="*70)
        logger.info("STARTING DEBATE PROTOCOL")
        logger.info("="*70)
        
        rounds_results = []
        previous_top_score = 0
        improvement_trajectory = []
        
        for round_num in range(1, self.max_rounds + 1):
            logger.info(f"\n{'='*70}")
            logger.info(f"ROUND {round_num}")
            logger.info(f"{'='*70}")
            
            # Get feedback from previous round
            feedback = self._get_feedback(rounds_results) if round_num > 1 else {}
            
            # Run round
            round_result = self.run_round(
                round_num,
                input_data,
                feedback,
                rounds_results
            )
            
            rounds_results.append(round_result)
            
            # Track improvement
            current_top_score = round_result["top_hypothesis"]["judge_score"]
            improvement = current_top_score - previous_top_score
            improvement_trajectory.append(current_top_score)
            
            logger.info(f"\nRound {round_num} Complete:")
            logger.info(f"  Top Score: {current_top_score}/100")
            if round_num > 1:
                logger.info(f"  Improvement: +{improvement:.1f} points")
            
            # Check convergence
            if round_num > 1 and self.check_convergence(improvement, round_num):
                logger.info(f"\n✓ Convergence achieved at round {round_num}")
                break
            
            previous_top_score = current_top_score
        
        # Select final best hypothesis
        final_hypothesis = self.select_best_hypothesis(rounds_results)
        
        logger.info(f"\n{'='*70}")
        logger.info("DEBATE COMPLETE")
        logger.info(f"{'='*70}")
        logger.info(f"Total Rounds: {len(rounds_results)}")
        logger.info(f"Final Score: {final_hypothesis['judge_score']}/100")
        logger.info(f"Improvement: {improvement_trajectory}")
        
        return {
            "rounds": rounds_results,
            "final_hypothesis": final_hypothesis,
            "total_rounds": len(rounds_results),
            "convergence_achieved": len(rounds_results) < self.max_rounds,
            "improvement_trajectory": improvement_trajectory
        }
    
    def run_round(
        self,
        round_num: int,
        input_data: Dict[str, Any],
        feedback: Dict[str, Any],
        rounds_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute single debate round.
        
        Args:
            round_num: Current round number
            input_data: Incident data
            feedback: Feedback from previous round (empty for round 1)
            rounds_results: Previous rounds results
            
        Returns:
            Round results with hypotheses and evaluation
        """
        logger.info(f"\nGenerating hypotheses from reasoners...")
        
        # Generate/refine hypotheses from each reasoner
        all_hypotheses = {}
        previous_round = rounds_results[-1] if rounds_results else None
        
        for name, reasoner in self.reasoners.items():
            logger.info(f"  - {name}...")
            
            if round_num == 1:
                # Round 1: Initial hypotheses
                result = reasoner.process(input_data)
            else:
                # Round 2+: Refined hypotheses with feedback
                # Get this reasoner's previous hypotheses
                prev_hyp_key = f"{name}_hypotheses"
                previous_hypotheses = previous_round["hypotheses"].get(prev_hyp_key, [])
                
                # Get feedback for this reasoner
                reasoner_feedback = feedback.get(name, [])
                
                # Get other reasoners' top hypotheses
                other_top = self._get_other_top_hypotheses(
                    previous_round["evaluation"]["evaluated_hypotheses"],
                    name
                )
                
                # Refine hypotheses
                logger.info(f"    Refining with {len(reasoner_feedback)} feedback items...")
                result = reasoner.refine_hypotheses(
                    input_data,
                    previous_hypotheses,
                    reasoner_feedback,
                    other_top
                )
            
            all_hypotheses[f"{name}_hypotheses"] = result["hypotheses"]
            refined_tag = " (refined)" if result.get("refined", False) else ""
            logger.info(f"    ✓ Generated {len(result['hypotheses'])} hypotheses{refined_tag}")
        
        # Judge evaluates all hypotheses
        logger.info(f"\nJudge evaluating hypotheses...")
        
        judge_input = {
            **all_hypotheses,
            "events": input_data.get("events", []),
            "errors": input_data.get("error_messages", []),
            "similar_incidents": input_data.get("similar_incidents", [])
        }
        
        evaluation = self.judge.process(judge_input)
        
        logger.info(f"  ✓ Evaluated {evaluation['num_evaluated']} hypotheses")
        logger.info(f"  ✓ Top score: {evaluation['top_hypothesis']['judge_score']}/100")
        
        return {
            "round_number": round_num,
            "hypotheses": all_hypotheses,
            "evaluation": evaluation,
            "top_hypothesis": evaluation["top_hypothesis"],
            "all_evaluated": evaluation["evaluated_hypotheses"]
        }
    
    def _get_feedback(self, rounds_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract feedback from previous round for each reasoner.
        
        Args:
            rounds_results: List of previous round results
            
        Returns:
            Dictionary with feedback for each reasoner
        """
        if not rounds_results:
            return {}
        
        last_round = rounds_results[-1]
        evaluation = last_round["evaluation"]
        
        feedback = {}
        
        # Get feedback for each reasoner's hypotheses
        for hyp in evaluation["evaluated_hypotheses"]:
            source = hyp.get("source", "unknown")
            if source not in feedback:
                feedback[source] = []
            
            feedback[source].append({
                "hypothesis": hyp.get("hypothesis", ""),
                "score": hyp.get("judge_score", 0),
                "strengths": hyp.get("strengths", []),
                "weaknesses": hyp.get("weaknesses", []),
                "feedback": hyp.get("feedback", "")
            })
        
        return feedback
    
    def _get_other_top_hypotheses(
        self,
        all_evaluated: List[Dict[str, Any]],
        exclude_source: str,
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get top hypotheses from other reasoners.
        
        Args:
            all_evaluated: All evaluated hypotheses
            exclude_source: Source to exclude (this reasoner)
            top_n: Number of top hypotheses to get
            
        Returns:
            List of top hypotheses from other reasoners
        """
        # Filter out this reasoner's hypotheses
        other_hypotheses = [
            h for h in all_evaluated
            if h.get("source", "") != exclude_source
        ]
        
        # Sort by score and take top N
        other_hypotheses.sort(key=lambda x: x.get("judge_score", 0), reverse=True)
        
        return other_hypotheses[:top_n]
    
    def check_convergence(
        self,
        improvement: float,
        round_num: int
    ) -> bool:
        """
        Check if debate should stop.
        
        Args:
            improvement: Score improvement from previous round
            round_num: Current round number
            
        Returns:
            True if convergence achieved, False otherwise
        """
        # Max rounds reached
        if round_num >= self.max_rounds:
            logger.info("  Max rounds reached")
            return True
        
        # Score plateau (improvement below threshold)
        if improvement < self.convergence_threshold:
            logger.info(f"  Score plateau detected (improvement: {improvement:.1f} < {self.convergence_threshold})")
            return True
        
        return False
    
    def select_best_hypothesis(
        self,
        rounds_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Select best hypothesis across all rounds.
        
        Args:
            rounds_results: List of all round results
            
        Returns:
            Best hypothesis with metadata
        """
        # Collect all top hypotheses from each round
        all_top_hypotheses = []
        
        for round_result in rounds_results:
            top_hyp = round_result["top_hypothesis"]
            all_top_hypotheses.append({
                **top_hyp,
                "round": round_result["round_number"]
            })
        
        # Select highest scoring
        best = max(all_top_hypotheses, key=lambda x: x.get("judge_score", 0))
        
        # Add metadata
        best["rounds_refined"] = len(rounds_results)
        best["final_round"] = best.get("round", len(rounds_results))
        
        return best
    
    def get_debate_summary(self, debate_result: Dict[str, Any]) -> str:
        """
        Generate human-readable debate summary.
        
        Args:
            debate_result: Result from run_debate()
            
        Returns:
            Formatted summary string
        """
        final = debate_result["final_hypothesis"]
        trajectory = debate_result["improvement_trajectory"]
        
        summary = f"""
DEBATE SUMMARY
{'='*70}

Rounds: {debate_result['total_rounds']}
Convergence: {'Yes' if debate_result['convergence_achieved'] else 'No'}
Score Trajectory: {' → '.join(map(str, trajectory))}
Total Improvement: +{trajectory[-1] - trajectory[0]} points

FINAL HYPOTHESIS (Score: {final['judge_score']}/100)
{'='*70}

Hypothesis: {final.get('hypothesis', 'N/A')}
Source: {final.get('source', 'unknown')}
Confidence: {final.get('confidence', 0):.2f}
Category: {final.get('category', 'unknown')}

Reasoning:
{final.get('reasoning', 'No reasoning provided')[:300]}...

Resolution:
{final.get('suggested_resolution', 'No resolution provided')[:300]}...

Refined over {final.get('rounds_refined', 0)} rounds
"""
        
        return summary
