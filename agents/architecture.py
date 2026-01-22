"""Architecture Agent for analyzing DWH structure and data lineage."""

from typing import Any
from crewai import Agent

from tools.file import ReadFileTool, ProjectStructureTool, SearchCodeTool, ListDirectoryTool
from tools.dwh import DBTParserTool, LineageTracerTool, SQLAnalyzeTool


def create_architecture_agent(llm: Any) -> Agent:
    """
    Create an Architecture agent specialized in DWH structure analysis.
    
    Args:
        llm: Language model instance to use.
        
    Returns:
        Configured Architecture agent.
    """
    return Agent(
        role="DWH Architecture Analyst",
        goal=(
            "Analyze the data warehouse architecture, understand data lineage, "
            "identify architectural patterns and anti-patterns, and provide recommendations "
            "for improving the overall DWH structure."
        ),
        backstory=(
            "You are a data architect with extensive experience designing and reviewing "
            "data warehouse architectures. You understand medallion architecture (bronze/silver/gold), "
            "dimensional modeling, Data Vault, and modern dbt-based approaches. "
            "You can trace data lineage, identify circular dependencies, spot violations of "
            "layer boundaries, and recommend architectural improvements. "
            "You think holistically about data flow, from raw sources through transformations "
            "to final business-facing marts. You ensure the DWH is maintainable, scalable, and reliable."
        ),
        tools=[
            ReadFileTool(),
            ProjectStructureTool(),
            SearchCodeTool(),
            ListDirectoryTool(),
            DBTParserTool(),
            LineageTracerTool(),
            SQLAnalyzeTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=15,
    )
