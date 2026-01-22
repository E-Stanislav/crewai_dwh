"""Configuration schemas for LLM and project settings."""

from enum import Enum
from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    ZAI = "zai"


class LLMConfig(BaseModel):
    """Configuration for LLM provider."""
    provider: LLMProvider = Field(..., description="LLM provider to use")
    model: str = Field(..., description="Model name/identifier")
    api_key: str | None = Field(default=None, description="API key for the provider")
    base_url: str | None = Field(default=None, description="Base URL for API (for Ollama, z.ai)")
    temperature: float = Field(default=0.7, ge=0, le=2, description="Sampling temperature")
    max_tokens: int | None = Field(default=None, description="Maximum tokens in response")
    
    class Config:
        use_enum_values = True


class ProjectItem(BaseModel):
    """A single project in the projects list."""
    name: str = Field(..., description="Project display name")
    path: str = Field(..., description="Path to the project directory")


class ProjectsConfig(BaseModel):
    """Configuration loaded from projects.yaml."""
    projects: list[ProjectItem] = Field(default_factory=list, description="List of projects")


class ProjectConfig(BaseModel):
    """Configuration for project analysis."""
    project_path: str = Field(..., description="Path to the project directory")
    sandbox_enabled: bool = Field(default=True, description="Enable sandbox restrictions")
    include_patterns: list[str] = Field(
        default=["*.py", "*.sql", "*.yml", "*.yaml", "*.json", "*.md"],
        description="File patterns to include in analysis"
    )
    exclude_patterns: list[str] = Field(
        default=["__pycache__", ".git", "node_modules", ".venv", "venv"],
        description="Patterns to exclude from analysis"
    )
