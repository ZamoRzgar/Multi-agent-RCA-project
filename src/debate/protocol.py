"""
Debate Protocol: Orchestrates multi-agent debate and consensus.
"""

from typing import List, Dict, Any
from loguru import logger


class DebateProtocol:
    """
    Orchestrates the debate process between RCA reasoner agents:
    1. Initial hypothesis generation
    2. Critique and rebuttal rounds
    3. Hypothesis refinement
    4. Judge evaluation and selection
    """
    
    def __init__(
        self,
        reasoners: List[Any],
        judge: Any,
        max_rounds: int = 2,
        consensus_threshold: float = 0.8
    ):
        """
        Initialize debate protocol.
        
        Args:
            reasoners: List of RCA reasoner agents
            judge: Judge agent
            max_rounds: Maximum debate rounds
            consensus_threshold: Threshold for early consensus
        """
        self.reasoners = reasoners
        self.judge = judge
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold
        
        logger.info(
            f"Initialized debate with {len(reasoners)} reasoners, "
            f"max {max_rounds} rounds"
        )
    
    def run(
        self,
        parsed_logs: Dict[str, Any],
        kg_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run the complete debate protocol.
        
        Args:
            parsed_logs: Parsed log data
            kg_facts: Retrieved KG facts
            
        Returns:
            Final result with selected hypothesis and debate transcript
        """
        logger.info("Starting debate protocol")
        
        # Phase 1: Initial hypothesis generation
        hypotheses = self._generate_initial_hypotheses(parsed_logs, kg_facts)
        
        debate_transcript = {
            "rounds": [],
            "initial_hypotheses": hypotheses
        }
        
        # Phase 2: Debate rounds
        for round_num in range(self.max_rounds):
            logger.info(f"Debate round {round_num + 1}/{self.max_rounds}")
            
            round_result = self._run_debate_round(
                hypotheses, parsed_logs, kg_facts
            )
            
            debate_transcript["rounds"].append(round_result)
            hypotheses = round_result["refined_hypotheses"]
            
            # Check for early consensus
            if self._check_consensus(hypotheses):
                logger.info("Early consensus reached")
                break
        
        # Phase 3: Judge evaluation
        judgment = self._judge_hypotheses(hypotheses, parsed_logs, kg_facts)
        
        result = {
            "root_cause": judgment["selected_hypothesis"]["root_cause"],
            "explanation": judgment["selected_hypothesis"]["explanation"],
            "confidence": judgment["confidence"],
            "debate_transcript": debate_transcript,
            "judgment": judgment
        }
        
        logger.info(f"Debate complete. Root cause: {result['root_cause']}")
        
        return result
    
    def _generate_initial_hypotheses(
        self,
        parsed_logs: Dict[str, Any],
        kg_facts: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate initial hypotheses from all reasoners.
        
        Args:
            parsed_logs: Parsed log data
            kg_facts: KG facts
            
        Returns:
            List of initial hypotheses
        """
        hypotheses = []
        
        for reasoner in self.reasoners:
            input_data = {
                "parsed_logs": parsed_logs,
                "kg_facts": kg_facts
            }
            
            hypothesis = reasoner.process(input_data)
            hypothesis["agent"] = reasoner.name
            hypotheses.append(hypothesis)
        
        logger.info(f"Generated {len(hypotheses)} initial hypotheses")
        
        return hypotheses
    
    def _run_debate_round(
        self,
        hypotheses: List[Dict[str, Any]],
        parsed_logs: Dict[str, Any],
        kg_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run one round of debate: critique and refinement.
        
        Args:
            hypotheses: Current hypotheses
            parsed_logs: Log data
            kg_facts: KG facts
            
        Returns:
            Round results with critiques and refined hypotheses
        """
        critiques = []
        
        # Each agent critiques other hypotheses
        for i, reasoner in enumerate(self.reasoners):
            own_hypothesis = hypotheses[i]
            other_hypotheses = [h for j, h in enumerate(hypotheses) if j != i]
            
            for other_hyp in other_hypotheses:
                critique = reasoner.critique_hypothesis(
                    other_hyp, [own_hypothesis]
                )
                critique["critic"] = reasoner.name
                critique["target"] = other_hyp["agent"]
                critiques.append(critique)
        
        # Each agent refines their hypothesis based on critiques
        refined_hypotheses = []
        for i, reasoner in enumerate(self.reasoners):
            relevant_critiques = [
                c for c in critiques if c["target"] == reasoner.name
            ]
            
            refined = reasoner.refine_hypothesis(
                hypotheses[i], relevant_critiques
            )
            refined["agent"] = reasoner.name
            refined_hypotheses.append(refined)
        
        return {
            "critiques": critiques,
            "refined_hypotheses": refined_hypotheses
        }
    
    def _check_consensus(self, hypotheses: List[Dict[str, Any]]) -> bool:
        """
        Check if agents have reached consensus.
        
        Args:
            hypotheses: Current hypotheses
            
        Returns:
            True if consensus reached
        """
        # TODO: Implement consensus checking
        # Compare root causes and confidence levels
        return False
    
    def _judge_hypotheses(
        self,
        hypotheses: List[Dict[str, Any]],
        parsed_logs: Dict[str, Any],
        kg_facts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Have judge evaluate and select best hypothesis.
        
        Args:
            hypotheses: Final hypotheses
            parsed_logs: Log data
            kg_facts: KG facts
            
        Returns:
            Judgment result
        """
        input_data = {
            "hypotheses": hypotheses,
            "parsed_logs": parsed_logs,
            "kg_facts": kg_facts
        }
        
        return self.judge.process(input_data)
