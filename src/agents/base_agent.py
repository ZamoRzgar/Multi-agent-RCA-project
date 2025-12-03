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
