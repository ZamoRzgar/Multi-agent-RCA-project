"""
LLM Client: Unified interface for different LLM providers.
"""

import os
from typing import Optional, Dict, Any
from loguru import logger


class LLMClient:
    """
    Unified client for interacting with different LLM providers.
    Supports OpenAI, Anthropic, and local models.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4-turbo-preview",
        api_key: Optional[str] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            provider: LLM provider (openai, anthropic, local)
            model: Model name
            api_key: API key (if None, reads from environment)
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or self._get_api_key()
        
        self.client = self._initialize_client()
        
        logger.info(f"Initialized LLM client: {provider}/{model}")
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        if self.provider == "openai":
            return os.getenv("OPENAI_API_KEY")
        elif self.provider == "anthropic":
            return os.getenv("ANTHROPIC_API_KEY")
        return None
    
    def _initialize_client(self):
        """Initialize provider-specific client."""
        if self.provider == "openai":
            try:
                import openai
                return openai.OpenAI(api_key=self.api_key)
            except ImportError:
                logger.error("OpenAI package not installed")
                return None
        
        elif self.provider == "anthropic":
            try:
                import anthropic
                return anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                logger.error("Anthropic package not installed")
                return None
        
        return None
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text
        """
        if self.provider == "openai":
            return self._generate_openai(prompt, temperature, max_tokens, **kwargs)
        elif self.provider == "anthropic":
            return self._generate_anthropic(prompt, temperature, max_tokens, **kwargs)
        else:
            raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def _generate_openai(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Generate using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _generate_anthropic(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> str:
        """Generate using Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def generate_async(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Async version of generate.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        # TODO: Implement async generation
        raise NotImplementedError("Async generation not yet implemented")
