"""
Local LLM Client: Interface for local open-source models via Ollama or vLLM.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from loguru import logger


class LocalLLMClient:
    """
    Client for interacting with local LLMs via Ollama or vLLM.
    Supports multiple models running simultaneously.
    """
    
    def __init__(
        self,
        backend: str = "ollama",  # "ollama" or "vllm"
        base_url: str = "http://localhost:11434",
        model: str = "qwen2:7b"
    ):
        """
        Initialize local LLM client.
        
        Args:
            backend: Backend to use (ollama or vllm)
            base_url: Base URL for the LLM server
            model: Model name/identifier
        """
        self.backend = backend
        self.base_url = base_url
        self.model = model
        
        logger.info(f"Initialized LocalLLMClient: {backend}/{model}")
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Generate text from prompt using local LLM.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        if self.backend == "ollama":
            return self._generate_ollama(prompt, temperature, max_tokens, **kwargs)
        elif self.backend == "vllm":
            return self._generate_vllm(prompt, temperature, max_tokens, **kwargs)
        else:
            raise ValueError(f"Unknown backend: {self.backend}")
    
    def _generate_ollama(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Generate using Ollama API."""
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    def _generate_vllm(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Generate using vLLM OpenAI-compatible API."""
        try:
            url = f"{self.base_url}/v1/completions"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["text"]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"vLLM API error: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Chat-style generation (for instruction-tuned models).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            
        Returns:
            Generated response
        """
        if self.backend == "ollama":
            return self._chat_ollama(messages, temperature, max_tokens, **kwargs)
        elif self.backend == "vllm":
            return self._chat_vllm(messages, temperature, max_tokens, **kwargs)
    
    def _chat_ollama(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Chat using Ollama API."""
        try:
            url = f"{self.base_url}/api/chat"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama chat error: {e}")
            raise
    
    def _chat_vllm(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Chat using vLLM OpenAI-compatible API."""
        try:
            url = f"{self.base_url}/v1/chat/completions"
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"vLLM chat error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if the LLM server is available."""
        try:
            if self.backend == "ollama":
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            else:
                response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False


class MultiModelManager:
    """
    Manages multiple local LLMs for different agent roles.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize multi-model manager.
        
        Args:
            config: Configuration with model assignments
        """
        self.config = config
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all configured models."""
        model_config = self.config.get("local_models", {})
        
        for role, settings in model_config.items():
            self.models[role] = LocalLLMClient(
                backend=settings.get("backend", "ollama"),
                base_url=settings.get("base_url", "http://localhost:11434"),
                model=settings.get("model", "qwen2:7b")
            )
            logger.info(f"Initialized model for {role}: {settings.get('model')}")
    
    def get_client(self, role: str) -> LocalLLMClient:
        """
        Get LLM client for a specific role.
        
        Args:
            role: Agent role (e.g., 'log_parser', 'rca_reasoner_log')
            
        Returns:
            LocalLLMClient instance
        """
        if role not in self.models:
            logger.warning(f"No model configured for {role}, using default")
            return self.models.get("default", list(self.models.values())[0])
        
        return self.models[role]
    
    def check_availability(self) -> Dict[str, bool]:
        """Check availability of all models."""
        status = {}
        for role, client in self.models.items():
            status[role] = client.is_available()
        return status
