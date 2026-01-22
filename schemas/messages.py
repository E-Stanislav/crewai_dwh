"""Pydantic schemas for chat messages and crew requests/responses."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """A single chat message."""
    role: MessageRole = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content (supports Markdown)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    
    class Config:
        use_enum_values = True


class AnalysisMode(str, Enum):
    """Available analysis modes."""
    ANALYZE = "analyze"
    DOCS = "docs"
    ARCH = "arch"
    ASK = "ask"


class CrewRequest(BaseModel):
    """Request to the ProjectAnalyzerCrew."""
    query: str = Field(..., description="User query/request")
    mode: AnalysisMode = Field(default=AnalysisMode.ASK, description="Analysis mode")
    context: dict = Field(default_factory=dict, description="Additional context")
    
    class Config:
        use_enum_values = True


class ToolUsage(BaseModel):
    """Record of a tool being used during execution."""
    tool_name: str = Field(..., description="Name of the tool")
    input_data: dict = Field(default_factory=dict, description="Input provided to tool")
    output_summary: str = Field(default="", description="Brief summary of output")
    execution_time: float = Field(default=0.0, description="Tool execution time in seconds")


class CrewResponse(BaseModel):
    """Response from the ProjectAnalyzerCrew."""
    result: str = Field(..., description="Final result (Markdown formatted)")
    agents_used: list[str] = Field(default_factory=list, description="Agents that participated")
    tools_used: list[ToolUsage] = Field(default_factory=list, description="Tools used during execution")
    execution_time: float = Field(default=0.0, description="Total execution time in seconds")
    success: bool = Field(default=True, description="Whether execution was successful")
    error: str | None = Field(default=None, description="Error message if failed")
