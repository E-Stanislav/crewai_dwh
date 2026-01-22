"""ProjectAnalyzerCrew - main crew for DWH project analysis."""

import time
from typing import Any
from crewai import Crew, Task

from schemas.config import LLMConfig
from schemas.messages import CrewRequest, CrewResponse, AnalysisMode, ToolUsage
from config.llm_config import get_llm
from utils.sandbox import set_sandbox
from agents import (
    create_code_reviewer_agent,
    create_documentation_agent,
    create_architecture_agent,
    create_qa_expert_agent,
)


class ProjectAnalyzerCrew:
    """
    Main crew for analyzing DWH projects.
    
    Provides methods for code analysis, documentation generation,
    architecture analysis, and Q&A about the project.
    """
    
    def __init__(self, project_path: str, llm_config: LLMConfig):
        """
        Initialize the ProjectAnalyzerCrew.
        
        Args:
            project_path: Path to the DWH project to analyze.
            llm_config: Configuration for the LLM provider.
        """
        self.project_path = project_path
        self.llm_config = llm_config
        
        # Set up sandbox
        set_sandbox(project_path)
        
        # Initialize LLM
        self.llm = get_llm(llm_config)
        
        # Create agents
        self.code_reviewer = create_code_reviewer_agent(self.llm)
        self.documentation = create_documentation_agent(self.llm)
        self.architecture = create_architecture_agent(self.llm)
        self.qa_expert = create_qa_expert_agent(self.llm)
    
    def analyze_code(self, query: str) -> CrewResponse:
        """
        Analyze code quality, find bugs, and suggest improvements.
        
        Args:
            query: What to analyze (e.g., "Review the staging models for performance issues")
            
        Returns:
            CrewResponse with analysis results.
        """
        start_time = time.time()
        
        task = Task(
            description=f"""
            Analyze the DWH code based on this request: {query}
            
            Your analysis should cover:
            1. Code quality issues (naming, structure, readability)
            2. Performance concerns (inefficient queries, missing optimizations)
            3. Best practices violations (dbt conventions, SQL standards)
            4. Potential bugs or data quality issues
            5. Specific recommendations with code examples
            
            Use the available tools to read files, search code, and analyze SQL.
            Provide your response in well-formatted Markdown.
            """,
            expected_output="A detailed code review report in Markdown format with specific issues found and recommendations.",
            agent=self.code_reviewer,
        )
        
        crew = Crew(
            agents=[self.code_reviewer],
            tasks=[task],
            verbose=True,
        )
        
        try:
            result = crew.kickoff()
            return CrewResponse(
                result=str(result),
                agents_used=["Code Reviewer"],
                tools_used=[],
                execution_time=time.time() - start_time,
                success=True,
            )
        except Exception as e:
            return CrewResponse(
                result="",
                agents_used=["Code Reviewer"],
                tools_used=[],
                execution_time=time.time() - start_time,
                success=False,
                error=str(e),
            )
    
    def generate_docs(self, query: str) -> CrewResponse:
        """
        Generate or update documentation for the project.
        
        Args:
            query: What to document (e.g., "Document all staging models" or "Create schema.yml for orders model")
            
        Returns:
            CrewResponse with generated documentation.
        """
        start_time = time.time()
        
        task = Task(
            description=f"""
            Generate documentation based on this request: {query}
            
            Documentation should include:
            1. Clear model descriptions explaining business purpose
            2. Column definitions with data types and descriptions
            3. Notes about data sources and transformations
            4. Any important caveats or data quality notes
            
            Follow dbt documentation best practices.
            Use the available tools to understand the models before documenting them.
            Provide your response in well-formatted Markdown or YAML as appropriate.
            """,
            expected_output="Documentation in Markdown or YAML format that can be directly used in the project.",
            agent=self.documentation,
        )
        
        crew = Crew(
            agents=[self.documentation],
            tasks=[task],
            verbose=True,
        )
        
        try:
            result = crew.kickoff()
            return CrewResponse(
                result=str(result),
                agents_used=["Documentation"],
                tools_used=[],
                execution_time=time.time() - start_time,
                success=True,
            )
        except Exception as e:
            return CrewResponse(
                result="",
                agents_used=["Documentation"],
                tools_used=[],
                execution_time=time.time() - start_time,
                success=False,
                error=str(e),
            )
    
    def analyze_arch(self, query: str) -> CrewResponse:
        """
        Analyze the architecture and data lineage of the project.
        
        Args:
            query: What to analyze (e.g., "Show the lineage for orders_mart" or "Review the overall architecture")
            
        Returns:
            CrewResponse with architecture analysis.
        """
        start_time = time.time()
        
        task = Task(
            description=f"""
            Analyze the DWH architecture based on this request: {query}
            
            Your analysis should cover:
            1. Overall project structure and organization
            2. Data lineage and dependencies between models
            3. Architectural patterns used (medallion, dimensional, etc.)
            4. Layer boundaries and potential violations
            5. Recommendations for architectural improvements
            
            Use the lineage tracer, project structure, and other tools to understand the architecture.
            Provide your response in well-formatted Markdown with diagrams where helpful.
            """,
            expected_output="An architecture analysis report in Markdown format with lineage information and recommendations.",
            agent=self.architecture,
        )
        
        crew = Crew(
            agents=[self.architecture],
            tasks=[task],
            verbose=True,
        )
        
        try:
            result = crew.kickoff()
            return CrewResponse(
                result=str(result),
                agents_used=["Architecture"],
                tools_used=[],
                execution_time=time.time() - start_time,
                success=True,
            )
        except Exception as e:
            return CrewResponse(
                result="",
                agents_used=["Architecture"],
                tools_used=[],
                execution_time=time.time() - start_time,
                success=False,
                error=str(e),
            )
    
    def ask_question(self, question: str) -> CrewResponse:
        """
        Answer a question about the DWH project.
        
        Args:
            question: Any question about the project.
            
        Returns:
            CrewResponse with the answer.
        """
        start_time = time.time()
        
        task = Task(
            description=f"""
            Answer this question about the DWH project: {question}
            
            Guidelines:
            1. Always look at the actual code before answering
            2. Provide specific file references and code examples
            3. Explain complex concepts in clear, simple terms
            4. If you're not sure, say so and suggest where to look
            5. Use web search if you need documentation references
            
            Provide your response in well-formatted Markdown.
            """,
            expected_output="A clear, helpful answer in Markdown format with code references where appropriate.",
            agent=self.qa_expert,
        )
        
        crew = Crew(
            agents=[self.qa_expert],
            tasks=[task],
            verbose=True,
        )
        
        try:
            result = crew.kickoff()
            return CrewResponse(
                result=str(result),
                agents_used=["Q&A Expert"],
                tools_used=[],
                execution_time=time.time() - start_time,
                success=True,
            )
        except Exception as e:
            return CrewResponse(
                result="",
                agents_used=["Q&A Expert"],
                tools_used=[],
                execution_time=time.time() - start_time,
                success=False,
                error=str(e),
            )
    
    def run(self, request: CrewRequest) -> CrewResponse:
        """
        Run the crew based on the request mode.
        
        Args:
            request: CrewRequest with query and mode.
            
        Returns:
            CrewResponse with results.
        """
        mode = request.mode
        query = request.query
        
        if mode == AnalysisMode.ANALYZE or mode == "analyze":
            return self.analyze_code(query)
        elif mode == AnalysisMode.DOCS or mode == "docs":
            return self.generate_docs(query)
        elif mode == AnalysisMode.ARCH or mode == "arch":
            return self.analyze_arch(query)
        else:  # ASK mode is default
            return self.ask_question(query)
