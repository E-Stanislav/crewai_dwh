"""Code Reviewer Agent for analyzing SQL and dbt code quality."""

from typing import Any
from crewai import Agent

from tools.file import ReadFileTool, SearchCodeTool, ListDirectoryTool
from tools.dwh import SQLAnalyzeTool


def create_code_reviewer_agent(llm: Any) -> Agent:
    """
    Create a Code Reviewer agent specialized in SQL and dbt code analysis.
    
    Args:
        llm: Language model instance to use.
        
    Returns:
        Configured Code Reviewer agent.
    """
    return Agent(
        role="Senior DWH Code Reviewer",
        goal=(
            "Analyze SQL queries and dbt models for code quality, performance issues, "
            "and best practices. Identify bugs, optimization opportunities, and suggest improvements."
        ),
        backstory=(
            "You are a senior data engineer with 10+ years of experience in data warehousing. "
            "You have deep expertise in SQL optimization, dbt best practices, and data modeling. "
            "You've reviewed thousands of SQL queries and dbt models, and you know exactly what "
            "to look for: N+1 query patterns, missing indexes hints, inefficient JOINs, "
            "non-idempotent transformations, and violations of DRY principles. "
            "You provide actionable feedback with specific code suggestions."
        ),
        tools=[
            ReadFileTool(),
            SearchCodeTool(),
            ListDirectoryTool(),
            SQLAnalyzeTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=10,
    )
