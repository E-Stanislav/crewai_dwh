"""DWH-specific Pydantic schemas for SQL, dbt, and lineage analysis."""

from pydantic import BaseModel, Field


# ============== SQL Analysis ==============

class JoinInfo(BaseModel):
    """Information about a SQL JOIN."""
    left_table: str = Field(..., description="Left table in join")
    right_table: str = Field(..., description="Right table in join")
    join_type: str = Field(..., description="Type of join (INNER, LEFT, RIGHT, FULL)")
    condition: str = Field(..., description="Join condition")


class SQLAnalyzeInput(BaseModel):
    """Input schema for SQL analysis."""
    sql_content: str = Field(..., description="SQL query to analyze")


class SQLAnalyzeOutput(BaseModel):
    """Output schema for SQL analysis."""
    tables: list[str] = Field(default_factory=list, description="Tables referenced in query")
    columns: list[str] = Field(default_factory=list, description="Columns referenced")
    joins: list[JoinInfo] = Field(default_factory=list, description="Join information")
    ctes: list[str] = Field(default_factory=list, description="Common Table Expressions")
    subqueries: int = Field(default=0, description="Number of subqueries")
    complexity_score: int = Field(default=0, description="Query complexity score (1-10)")
    query_type: str = Field(default="SELECT", description="Type of query (SELECT, INSERT, etc.)")


# ============== DBT Model ==============

class ColumnInfo(BaseModel):
    """Information about a dbt model column."""
    name: str = Field(..., description="Column name")
    description: str | None = Field(default=None, description="Column description")
    data_type: str | None = Field(default=None, description="Column data type")
    tests: list[str] = Field(default_factory=list, description="Tests applied to column")


class DBTModelInput(BaseModel):
    """Input schema for dbt model parsing."""
    model_path: str = Field(..., description="Path to dbt model file")


class DBTModelOutput(BaseModel):
    """Output schema for dbt model parsing."""
    name: str = Field(..., description="Model name")
    description: str | None = Field(default=None, description="Model description")
    columns: list[ColumnInfo] = Field(default_factory=list, description="Column definitions")
    refs: list[str] = Field(default_factory=list, description="Referenced models (ref())")
    sources: list[str] = Field(default_factory=list, description="Source tables (source())")
    materialization: str = Field(default="view", description="Materialization type")
    tags: list[str] = Field(default_factory=list, description="Model tags")
    config: dict = Field(default_factory=dict, description="Model configuration")


# ============== Lineage ==============

class LineageNode(BaseModel):
    """A node in the lineage graph."""
    name: str = Field(..., description="Node name (model/source)")
    node_type: str = Field(..., description="Type: model, source, seed, etc.")
    path: str | None = Field(default=None, description="File path if applicable")


class LineageInput(BaseModel):
    """Input schema for lineage tracing."""
    model_name: str = Field(..., description="Model name to trace lineage for")
    depth: int = Field(default=3, description="How many levels up/downstream to trace")


class LineageOutput(BaseModel):
    """Output schema for lineage tracing."""
    model: str = Field(..., description="Central model name")
    upstream: list[LineageNode] = Field(default_factory=list, description="Upstream dependencies")
    downstream: list[LineageNode] = Field(default_factory=list, description="Downstream dependents")
    lineage_graph: dict = Field(default_factory=dict, description="Graph representation")
    total_nodes: int = Field(default=0, description="Total nodes in lineage")
