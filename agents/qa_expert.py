"""Q&A Expert Agent for answering questions about the DWH project."""

from typing import Any
from crewai import Agent

from tools.file import ReadFileTool, SearchCodeTool, ProjectStructureTool, ListDirectoryTool
from tools.dwh import DBTParserTool, SQLAnalyzeTool, LineageTracerTool
from tools.web_search import WebSearchTool


def create_qa_expert_agent(llm: Any) -> Agent:
    """
    Create a Q&A Expert agent for answering questions about the DWH project.
    
    Args:
        llm: Language model instance to use.
        
    Returns:
        Configured Q&A Expert agent.
    """
    return Agent(
        role="DWH Q&A Expert",
        goal=(
            "Answer questions about the DWH project clearly and accurately. "
            "Explain how data flows through the system, what specific models do, "
            "and help users understand the codebase."
        ),
        backstory=(
            "You are a helpful data engineering expert who knows this DWH project inside and out. "
            "You can explain complex SQL transformations in simple terms, trace where data comes from, "
            "and help team members understand unfamiliar parts of the codebase. "
            "You're patient and thorough - you always look at the actual code before answering, "
            "and you provide specific file references and code examples in your explanations. "
            "If you don't know something, you say so honestly and suggest where to look. "
            "You can also search the web for dbt/SQL documentation when needed."
        ),
        tools=[
            ReadFileTool(),
            SearchCodeTool(),
            ProjectStructureTool(),
            ListDirectoryTool(),
            DBTParserTool(),
            SQLAnalyzeTool(),
            LineageTracerTool(),
            WebSearchTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )
