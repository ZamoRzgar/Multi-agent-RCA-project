"""
Base agent class for all agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the multi-agent RCA system.
    """
    
    def __init__(
        self,
        name: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name/identifier
            model: LLM model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            config: Additional configuration parameters
        """
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.config = config or {}
        
        # Get agent-specific model from config if available
        agent_type_map = {
            "LogParserAgent": "log_parser",
            "KGRetrievalAgent": "kg_retrieval",
            "HybridReasoner": "rca_reasoner_hybrid",
            "LogReasoner": "rca_reasoner_log",
            "KGReasoner": "rca_reasoner_kg",
            "JudgeAgent": "judge"
        }
        
        agent_config_key = agent_type_map.get(name)
        if agent_config_key and "local_models" in self.config:
            agent_config = self.config["local_models"].get(agent_config_key, {})
            self.model = agent_config.get("model", model)
            self.temperature = agent_config.get("temperature", temperature)
        else:
            # Fallback to default LLM config or provided values
            llm_config = self.config.get("llm", {})
            self.model = llm_config.get("model", model)
            self.temperature = llm_config.get("temperature", temperature)
        
        self.max_tokens = max_tokens
        
        logger.info(f"Initialized {self.name} with model {self.model}")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Processing results dictionary
        """
        pass
    
    def _build_prompt(self, **kwargs) -> str:
        """
        Build prompt for LLM based on agent-specific template.
        
        Returns:
            Formatted prompt string
        """
        raise NotImplementedError("Subclasses must implement _build_prompt")
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM API with the given prompt.
        
        Args:
            prompt: Prompt string
            
        Returns:
            LLM response
        """
        from src.utils.local_llm_client import LocalLLMClient
        
        # Initialize client if not already done
        if not hasattr(self, '_llm_client'):
            self._llm_client = LocalLLMClient(
                backend="ollama",
                model=self.model
            )
        
        try:
            response = self._llm_client.generate(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', model='{self.model}')"
