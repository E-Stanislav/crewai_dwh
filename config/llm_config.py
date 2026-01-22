"""LLM configuration and provider setup."""

from typing import Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from schemas.config import LLMProvider, LLMConfig
from config.settings import settings


# Available models per provider (using string keys for compatibility)
LLM_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-4o",
        "gpt-4o-mini", 
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
    ],
    "anthropic": [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ],
    "ollama": [
        "llama3",
        "llama3:70b",
        "mistral",
        "codellama",
        "deepseek-coder",
    ],
    "openrouter": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o",
        "google/gemini-pro",
        "meta-llama/llama-3-70b-instruct",
    ],
    "zai": [
        "glm-4.7",
    ],
}


def get_llm(config: LLMConfig) -> Any:
    """
    Create an LLM instance based on configuration.
    
    Args:
        config: LLM configuration with provider, model, and credentials.
        
    Returns:
        LLM instance compatible with CrewAI.
        
    Raises:
        ValueError: If provider is not supported or configuration is invalid.
    """
    provider = config.provider
    
    if provider == LLMProvider.OPENAI:
        api_key = config.api_key or settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OpenAI API key not provided")
        
        return ChatOpenAI(
            model=config.model,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    
    elif provider == LLMProvider.ANTHROPIC:
        api_key = config.api_key or settings.ANTHROPIC_API_KEY
        if not api_key:
            raise ValueError("Anthropic API key not provided")
        
        return ChatAnthropic(
            model=config.model,
            api_key=api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens or 4096,
        )
    
    elif provider == LLMProvider.OLLAMA:
        base_url = config.base_url or settings.OLLAMA_BASE_URL
        
        # Use OpenAI-compatible endpoint for Ollama
        return ChatOpenAI(
            model=config.model,
            base_url=f"{base_url}/v1",
            api_key="ollama",  # Ollama doesn't require a real key
            temperature=config.temperature,
        )
    
    elif provider == LLMProvider.OPENROUTER:
        api_key = config.api_key or settings.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError("OpenRouter API key not provided")
        
        return ChatOpenAI(
            model=config.model,
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            temperature=config.temperature,
            default_headers={
                "HTTP-Referer": "https://github.com/crewai-dwh",
                "X-Title": "DWH Project Analyzer"
            }
        )
    
    elif provider == LLMProvider.ZAI:
        api_key = config.api_key or settings.ZAI_API_KEY
        base_url = config.base_url or settings.ZAI_BASE_URL
        
        if not api_key:
            raise ValueError("z.ai API key not provided")
        if not base_url:
            raise ValueError("z.ai base URL not provided")
        
        return ChatOpenAI(
            model=config.model,
            base_url=base_url,
            api_key=api_key,
            temperature=config.temperature,
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_default_llm() -> Any:
    """
    Get the default LLM based on settings.
    
    Returns:
        Default LLM instance.
    """
    config = LLMConfig(
        provider=LLMProvider(settings.DEFAULT_PROVIDER),
        model=settings.DEFAULT_MODEL,
        temperature=settings.DEFAULT_TEMPERATURE,
    )
    return get_llm(config)
