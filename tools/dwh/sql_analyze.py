"""Tool for analyzing SQL queries."""

import re
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Parenthesis
from sqlparse.tokens import Keyword, DML
from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.dwh import SQLAnalyzeInput, SQLAnalyzeOutput, JoinInfo


class SQLAnalyzeTool(BaseTool):
    """Tool to analyze SQL queries and extract metadata."""
    
    name: str = "analyze_sql"
    description: str = (
        "Analyze a SQL query to extract tables, columns, joins, CTEs, and complexity. "
        "Provide the SQL content and get structured information about the query. "
        "Use this to understand complex queries, identify dependencies, and assess complexity."
    )
    args_schema: type[BaseModel] = SQLAnalyzeInput
    
    def _run(self, sql_content: str) -> str:
        """Execute the tool to analyze SQL."""
        try:
            # Parse SQL
            parsed = sqlparse.parse(sql_content)
            if not parsed:
                return "Error: Could not parse SQL"
            
            statement = parsed[0]
            
            # Extract components
            tables = self._extract_tables(sql_content)
            columns = self._extract_columns(sql_content)
            joins = self._extract_joins(sql_content)
            ctes = self._extract_ctes(sql_content)
            subqueries = self._count_subqueries(sql_content)
            query_type = self._get_query_type(statement)
            complexity = self._calculate_complexity(sql_content, tables, joins, ctes, subqueries)
            
            # Create output
            output = SQLAnalyzeOutput(
                tables=tables,
                columns=columns,
                joins=joins,
                ctes=ctes,
                subqueries=subqueries,
                complexity_score=complexity,
                query_type=query_type
            )
            
            # Format response
            result_lines = [
                "## SQL Analysis",
                f"**Query Type:** {output.query_type}",
                f"**Complexity Score:** {output.complexity_score}/10",
                ""
            ]
            
            if ctes:
                result_lines.append(f"**CTEs ({len(ctes)}):** {', '.join(ctes)}")
            
            if tables:
                result_lines.append(f"**Tables ({len(tables)}):** {', '.join(tables)}")
            
            if columns:
                result_lines.append(f"**Columns ({len(columns)}):** {', '.join(columns[:20])}")
                if len(columns) > 20:
                    result_lines.append(f"  ... and {len(columns) - 20} more columns")
            
            if joins:
                result_lines.append(f"\n**Joins ({len(joins)}):**")
                for j in joins:
                    result_lines.append(f"  - {j.join_type}: {j.left_table} ↔ {j.right_table}")
            
            if subqueries > 0:
                result_lines.append(f"\n**Subqueries:** {subqueries}")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            return f"Error analyzing SQL: {str(e)}"
    
    def _extract_tables(self, sql: str) -> list[str]:
        """Extract table names from SQL."""
        tables = set()
        
        # Pattern for FROM and JOIN clauses
        patterns = [
            r'\bFROM\s+([`"\[]?\w+[`"\]]?(?:\.[`"\[]?\w+[`"\]]?)?)',
            r'\bJOIN\s+([`"\[]?\w+[`"\]]?(?:\.[`"\[]?\w+[`"\]]?)?)',
            r'\bINTO\s+([`"\[]?\w+[`"\]]?(?:\.[`"\[]?\w+[`"\]]?)?)',
            r'\bUPDATE\s+([`"\[]?\w+[`"\]]?(?:\.[`"\[]?\w+[`"\]]?)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                # Clean up table name
                table = match.strip('`"[]')
                tables.add(table)
        
        return sorted(list(tables))
    
    def _extract_columns(self, sql: str) -> list[str]:
        """Extract column references from SQL."""
        columns = set()
        
        # Simple pattern for column references
        # Matches: table.column, alias.column, or just column in SELECT
        pattern = r'(?:SELECT|WHERE|AND|OR|ON|GROUP BY|ORDER BY|SET)\s+(?:DISTINCT\s+)?([^,\n;]+)'
        
        # Get SELECT columns
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql, re.IGNORECASE | re.DOTALL)
        if select_match:
            select_part = select_match.group(1)
            # Split by comma and clean
            for col in select_part.split(','):
                col = col.strip()
                if col and col != '*':
                    # Remove alias
                    col = re.sub(r'\s+AS\s+\w+', '', col, flags=re.IGNORECASE)
                    col = col.strip()
                    if col and not col.startswith('('):
                        columns.add(col[:50])  # Limit length
        
        return sorted(list(columns))[:30]  # Limit total
    
    def _extract_joins(self, sql: str) -> list[JoinInfo]:
        """Extract JOIN information from SQL."""
        joins = []
        
        # Pattern for JOINs
        pattern = r'(LEFT|RIGHT|INNER|OUTER|FULL|CROSS)?\s*JOIN\s+([`"\[]?\w+[`"\]]?(?:\.[`"\[]?\w+[`"\]]?)?)\s+(?:AS\s+)?(\w+)?\s*ON\s+([^WHERE;]+?)(?=LEFT|RIGHT|INNER|OUTER|FULL|CROSS|JOIN|WHERE|GROUP|ORDER|LIMIT|$)'
        
        matches = re.findall(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            join_type = match[0].upper() if match[0] else "INNER"
            right_table = match[1].strip('`"[]')
            condition = match[3].strip()
            
            # Try to extract left table from condition
            left_table = "unknown"
            cond_parts = re.findall(r'(\w+)\.\w+\s*=\s*(\w+)\.\w+', condition)
            if cond_parts:
                for part in cond_parts:
                    if part[0].lower() != right_table.lower() and part[0].lower() != match[2].lower():
                        left_table = part[0]
                        break
                    elif part[1].lower() != right_table.lower() and part[1].lower() != match[2].lower():
                        left_table = part[1]
                        break
            
            joins.append(JoinInfo(
                left_table=left_table,
                right_table=right_table,
                join_type=f"{join_type} JOIN",
                condition=condition[:100]
            ))
        
        return joins
    
    def _extract_ctes(self, sql: str) -> list[str]:
        """Extract CTE names from SQL."""
        ctes = []
        
        # Pattern for WITH ... AS
        pattern = r'WITH\s+(?:RECURSIVE\s+)?(\w+)\s+AS\s*\('
        matches = re.findall(pattern, sql, re.IGNORECASE)
        ctes.extend(matches)
        
        # Pattern for additional CTEs after comma
        pattern = r',\s*(\w+)\s+AS\s*\('
        matches = re.findall(pattern, sql, re.IGNORECASE)
        ctes.extend(matches)
        
        return ctes
    
    def _count_subqueries(self, sql: str) -> int:
        """Count subqueries in SQL."""
        # Count SELECT within parentheses (excluding CTEs)
        # Remove CTEs first
        sql_no_cte = re.sub(r'WITH\s+.*?(?=SELECT)', '', sql, flags=re.IGNORECASE | re.DOTALL)
        
        # Count nested SELECTs
        count = len(re.findall(r'\(\s*SELECT', sql_no_cte, re.IGNORECASE))
        return count
    
    def _get_query_type(self, statement) -> str:
        """Get the type of SQL query."""
        for token in statement.tokens:
            if token.ttype is DML:
                return token.value.upper()
        return "UNKNOWN"
    
    def _calculate_complexity(
        self, 
        sql: str, 
        tables: list, 
        joins: list, 
        ctes: list, 
        subqueries: int
    ) -> int:
        """Calculate complexity score (1-10)."""
        score = 1
        
        # Tables
        score += min(len(tables) - 1, 2)  # +0-2 for tables
        
        # Joins
        score += min(len(joins), 3)  # +0-3 for joins
        
        # CTEs
        score += min(len(ctes), 2)  # +0-2 for CTEs
        
        # Subqueries
        score += min(subqueries, 2)  # +0-2 for subqueries
        
        # Additional complexity indicators
        if re.search(r'\bUNION\b', sql, re.IGNORECASE):
            score += 1
        if re.search(r'\bCASE\s+WHEN\b', sql, re.IGNORECASE):
            score += 1
        if re.search(r'\bWINDOW\b|\bOVER\s*\(', sql, re.IGNORECASE):
            score += 1
        
        return min(score, 10)
