"""Documentation Agent for generating and updating documentation."""

from typing import Any
from crewai import Agent

from tools.file import ReadFileTool, WriteFileTool, ProjectStructureTool, SearchCodeTool
from tools.dwh import DBTParserTool


def create_documentation_agent(llm: Any) -> Agent:
    """
    Create a Documentation agent specialized in generating DWH documentation.
    
    Args:
        llm: Language model instance to use.
        
    Returns:
        Configured Documentation agent.
    """
    return Agent(
        role="DWH Documentation Specialist",
        goal=(
            "Generate clear, comprehensive documentation for dbt models, SQL transformations, "
            "and data pipelines. Create schema.yml files, model descriptions, and column documentation."
        ),
        backstory=(
            "You are a technical writer specialized in data documentation. "
            "You understand that good documentation is crucial for data governance and team productivity. "
            "You excel at writing clear descriptions that explain not just WHAT the data is, "
            "but WHY it exists and HOW it should be used. "
            "You follow dbt documentation best practices and ensure all models have "
            "proper descriptions, column definitions, and test documentation. "
            "You write in a clear, concise style that both technical and business users can understand."
        ),
        tools=[
            ReadFileTool(),
            WriteFileTool(),
            ProjectStructureTool(),
            SearchCodeTool(),
            DBTParserTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
    )
