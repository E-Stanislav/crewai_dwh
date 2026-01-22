"""Application settings and configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

from schemas.config import ProjectItem, ProjectsConfig

# Load environment variables
load_dotenv(override=True)

# Disable CrewAI telemetry
os.environ["CREWAI_TELEMETRY"] = "false"
os.environ["OTEL_SDK_DISABLED"] = "true"


class Settings:
    """Application settings loaded from environment variables."""
    
    # OpenAI
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    
    # Anthropic
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    
    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # OpenRouter
    OPENROUTER_API_KEY: str | None = os.getenv("OPENROUTER_API_KEY")
    
    # z.ai
    ZAI_API_KEY: str | None = os.getenv("ZAI_API_KEY")
    ZAI_BASE_URL: str | None = os.getenv("ZAI_BASE_URL")
    
    # Default LLM settings
    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "openai")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    
    # Project settings
    PROJECTS_FILE: str = os.getenv("PROJECTS_FILE", "projects.yaml")
    
    # Sandbox settings
    SANDBOX_ENABLED: bool = os.getenv("SANDBOX_ENABLED", "true").lower() == "true"
    
    @classmethod
    def load_projects(cls) -> list[ProjectItem]:
        """Load projects from YAML file."""
        projects_file = Path(cls.PROJECTS_FILE)
        
        # Try relative to current directory, then relative to this file
        if not projects_file.exists():
            projects_file = Path(__file__).parent.parent / cls.PROJECTS_FILE
        
        if not projects_file.exists():
            return []
        
        try:
            with open(projects_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if data and "projects" in data:
                config = ProjectsConfig(**data)
                return config.projects
        except Exception as e:
            print(f"Error loading projects: {e}")
        
        return []


settings = Settings()
