"""
Multi-Provider LLM Service with Automatic Failover

This module provides a unified interface for multiple LLM providers with automatic
failover capabilities. Currently supports:

1. Ollama Cloud (Primary) - Free tier with gpt-oss:20b
2. Google Gemini (Fallback) - When Ollama is unavailable

Usage:
    from app.services.llm_provider import get_llm_service
    
    llm_service = get_llm_service()
    response = await llm_service.generate(
        prompt="Extract skills from this resume...",
        options={
            "temperature": 0.7,
            "max_tokens": 2000,
            "response_format": "json"
        }
    )

Architecture:
    LLMProvider (ABC)
        ├── OllamaCloudProvider
        └── GeminiProvider
    
    LLMService (Orchestrator)
        - Manages providers
        - Handles automatic failover
        - Tracks provider health
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging
import aiohttp
import time
from functools import lru_cache
import google.generativeai as genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMOptions:
    """Options for LLM generation."""
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    response_format: Optional[str] = None  # "json" for JSON output
    system_prompt: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, name: str):
        self.name = name
        self.status = ProviderStatus.HEALTHY
        self.last_error: Optional[str] = None
        self.last_error_time: Optional[float] = None
        self.request_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def generate(self, prompt: str, options: LLMOptions) -> LLMResponse:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is available."""
        pass
    
    def mark_error(self, error: str):
        """Mark provider as having an error."""
        self.last_error = error
        self.last_error_time = time.time()
        self.error_count += 1
        
        # Mark as degraded after 3 errors, unavailable after 5
        if self.error_count >= 5:
            self.status = ProviderStatus.UNAVAILABLE
        elif self.error_count >= 3:
            self.status = ProviderStatus.DEGRADED
        
        logger.warning(f"{self.name} error #{self.error_count}: {error}")
    
    def mark_success(self):
        """Mark provider as successful."""
        self.request_count += 1
        
        # Reset error count after successful request
        if self.status != ProviderStatus.HEALTHY:
            logger.info(f"{self.name} recovered, marking as healthy")
            self.status = ProviderStatus.HEALTHY
            self.error_count = 0
            self.last_error = None
    
    def get_health_info(self) -> Dict[str, Any]:
        """Get provider health information."""
        return {
            "name": self.name,
            "status": self.status.value,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "last_error_time": self.last_error_time
        }


class OllamaCloudProvider(LLMProvider):
    """Ollama Cloud provider (Primary)."""
    
    def __init__(self, config_settings=None):
        super().__init__("Ollama Cloud")
        self.settings = config_settings or settings
        self.api_key = self.settings.OLLAMA_API_KEY
        self.base_url = self.settings.OLLAMA_CLOUD_URL
        self.model = self.settings.OLLAMA_MODEL
        
        if not self.api_key:
            logger.warning("OLLAMA_API_KEY not set, Ollama Cloud provider unavailable")
            self.status = ProviderStatus.UNAVAILABLE
    
    async def generate(self, prompt: str, options: LLMOptions) -> LLMResponse:
        """Generate text using Ollama Cloud API."""
        if self.status == ProviderStatus.UNAVAILABLE:
            raise Exception(f"{self.name} is unavailable")
        
        try:
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Build payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": options.temperature,
                    "num_predict": options.max_tokens,
                    "top_p": options.top_p
                }
            }
            
            # Add system prompt if provided
            if options.system_prompt:
                payload["system"] = options.system_prompt
            
            # Add JSON format instruction if requested
            if options.response_format == "json":
                payload["format"] = "json"
            
            # Make request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                    
                    result = await response.json()
            
            # Extract response
            content = result.get("response", "")
            
            # Mark success
            self.mark_success()
            
            # Return standardized response
            return LLMResponse(
                content=content,
                provider=self.name,
                model=self.model,
                usage={
                    "prompt_tokens": result.get("prompt_eval_count", 0),
                    "completion_tokens": result.get("eval_count", 0),
                    "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                },
                metadata={
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "eval_duration": result.get("eval_duration")
                }
            )
            
        except Exception as e:
            self.mark_error(str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama Cloud is available."""
        if not self.api_key:
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.debug(f"Ollama health check failed: {e}")
            return False


class GeminiProvider(LLMProvider):
    """Google Gemini provider (Fallback)."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        super().__init__("Google Gemini")
        self.api_key = api_key
        # Remove 'models/' prefix if present for GenerativeModel constructor
        self.model = model.replace("models/", "")
        
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not set, Gemini provider unavailable")
            self.status = ProviderStatus.UNAVAILABLE
        else:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
    
    async def generate(self, prompt: str, options: LLMOptions) -> LLMResponse:
        """Generate text using Google Gemini API."""
        if self.status == ProviderStatus.UNAVAILABLE:
            raise Exception(f"{self.name} is unavailable")
        
        try:
            # Build full prompt with system prompt if provided
            full_prompt = prompt
            if options.system_prompt:
                full_prompt = f"{options.system_prompt}\n\n{prompt}"
            
            # Add JSON format instruction if requested
            if options.response_format == "json":
                full_prompt += "\n\nPlease respond with valid JSON only, no markdown formatting."
            
            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=options.temperature,
                max_output_tokens=options.max_tokens,
                top_p=options.top_p
            )
            
            # Generate (Gemini SDK is sync, we'll run in executor if needed)
            # For now, direct call (consider using asyncio.to_thread for true async)
            response = self.client.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Extract content
            content = response.text
            
            # Mark success
            self.mark_success()
            
            # Return standardized response
            return LLMResponse(
                content=content,
                provider=self.name,
                model=self.model,
                usage={
                    "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                    "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                    "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
                },
                metadata={
                    "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None
                }
            )
            
        except Exception as e:
            self.mark_error(str(e))
            raise
    
    async def health_check(self) -> bool:
        """Check if Gemini is available."""
        if not self.api_key:
            return False
        
        try:
            # Simple check: list models
            models = genai.list_models()
            return len(list(models)) > 0
        except Exception as e:
            logger.debug(f"Gemini health check failed: {e}")
            return False


class LLMService:
    """
    Multi-provider LLM service with automatic failover.
    
    Manages multiple LLM providers and automatically switches to fallback
    when primary provider fails.
    """
    
    def __init__(self):
        self.settings = settings
        self.providers: List[LLMProvider] = []
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup available LLM providers in priority order."""
        # Primary: Ollama Cloud
        ollama_provider = OllamaCloudProvider(self.settings)
        self.providers.append(ollama_provider)
        
        # Fallback: Google Gemini
        gemini_api_key = self.settings.GOOGLE_API_KEY if hasattr(self.settings, 'GOOGLE_API_KEY') else None
        if gemini_api_key:
            gemini_provider = GeminiProvider(
                api_key=gemini_api_key,
                model=self.settings.GEMINI_MODEL if hasattr(self.settings, 'GEMINI_MODEL') else "gemini-1.5-flash"
            )
            self.providers.append(gemini_provider)
        else:
            logger.warning("GOOGLE_API_KEY not configured, Gemini fallback unavailable")
        
        logger.info(f"LLM Service initialized with {len(self.providers)} providers: {[p.name for p in self.providers]}")
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
        response_format: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate text using available providers with automatic failover.
        
        Args:
            prompt: The prompt to generate from
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            response_format: "json" for JSON output
            system_prompt: System/instruction prompt
        
        Returns:
            LLMResponse with generated content
        
        Raises:
            Exception: If all providers fail
        """
        options = LLMOptions(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            response_format=response_format,
            system_prompt=system_prompt
        )
        
        errors = []
        
        # Try each provider in order
        for provider in self.providers:
            if provider.status == ProviderStatus.UNAVAILABLE:
                logger.debug(f"Skipping {provider.name} (unavailable)")
                continue
            
            try:
                logger.info(f"Attempting generation with {provider.name}")
                response = await provider.generate(prompt, options)
                logger.info(f"✓ Generated with {provider.name} ({response.usage.get('total_tokens', 0) if response.usage else 0} tokens)")
                return response
                
            except Exception as e:
                error_msg = f"{provider.name} failed: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                continue
        
        # All providers failed
        error_summary = "; ".join(errors)
        raise Exception(f"All LLM providers failed: {error_summary}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all providers."""
        health_info = {
            "providers": [],
            "available_count": 0,
            "total_count": len(self.providers)
        }
        
        for provider in self.providers:
            is_healthy = await provider.health_check()
            provider_info = provider.get_health_info()
            provider_info["is_healthy"] = is_healthy
            health_info["providers"].append(provider_info)
            
            if is_healthy:
                health_info["available_count"] += 1
        
        return health_info
    
    def get_provider_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all providers."""
        return [provider.get_health_info() for provider in self.providers]


# Singleton instance
_llm_service_instance: Optional[LLMService] = None


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """
    Get singleton LLM service instance.
    
    Returns:
        LLMService instance
    """
    global _llm_service_instance
    
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    
    return _llm_service_instance


# Convenience function for settings
def get_settings():
    """Get application settings."""
    return settings
