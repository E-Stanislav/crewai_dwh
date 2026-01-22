"""Tool for parsing dbt models."""

import re
import yaml
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.dwh import DBTModelInput, DBTModelOutput, ColumnInfo
from utils.sandbox import get_sandbox


class DBTParserTool(BaseTool):
    """Tool to parse dbt model files and extract metadata."""
    
    name: str = "parse_dbt_model"
    description: str = (
        "Parse a dbt model file (.sql) and its associated schema (.yml) to extract metadata. "
        "Returns model name, description, columns, refs, sources, and configuration. "
        "Use this to understand dbt model structure and dependencies."
    )
    args_schema: type[BaseModel] = DBTModelInput
    
    def _run(self, model_path: str) -> str:
        """Execute the tool to parse a dbt model."""
        try:
            sandbox = get_sandbox()
            validated_path = sandbox.validate_path(model_path)
            
            if not validated_path.exists():
                return f"Error: Model file not found: {model_path}"
            
            # Read model SQL
            sql_content = validated_path.read_text(encoding="utf-8")
            
            # Extract model name
            model_name = validated_path.stem
            
            # Extract refs and sources from SQL
            refs = self._extract_refs(sql_content)
            sources = self._extract_sources(sql_content)
            
            # Extract config from SQL
            config = self._extract_config(sql_content)
            materialization = config.get("materialized", "view")
            tags = config.get("tags", [])
            
            # Try to find schema.yml
            schema_info = self._find_schema_info(validated_path, model_name)
            
            description = schema_info.get("description")
            columns = schema_info.get("columns", [])
            
            # Create output
            output = DBTModelOutput(
                name=model_name,
                description=description,
                columns=columns,
                refs=refs,
                sources=sources,
                materialization=materialization,
                tags=tags,
                config=config
            )
            
            # Format response
            result_lines = [
                f"## dbt Model: {output.name}",
                f"**Materialization:** {output.materialization}",
            ]
            
            if output.description:
                result_lines.append(f"**Description:** {output.description}")
            
            if output.tags:
                result_lines.append(f"**Tags:** {', '.join(output.tags)}")
            
            result_lines.append("")
            
            if sources:
                result_lines.append(f"**Sources ({len(sources)}):**")
                for src in sources:
                    result_lines.append(f"  - `{src}`")
                result_lines.append("")
            
            if refs:
                result_lines.append(f"**References ({len(refs)}):**")
                for ref in refs:
                    result_lines.append(f"  - `{ref}`")
                result_lines.append("")
            
            if columns:
                result_lines.append(f"**Columns ({len(columns)}):**")
                for col in columns[:20]:
                    desc = f" - {col.description}" if col.description else ""
                    tests = f" [{', '.join(col.tests)}]" if col.tests else ""
                    result_lines.append(f"  - `{col.name}`{desc}{tests}")
                if len(columns) > 20:
                    result_lines.append(f"  ... and {len(columns) - 20} more columns")
            
            if config:
                result_lines.append(f"\n**Config:** `{config}`")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            return f"Error parsing dbt model: {str(e)}"
    
    def _extract_refs(self, sql: str) -> list[str]:
        """Extract ref() calls from SQL."""
        refs = []
        pattern = r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
        matches = re.findall(pattern, sql)
        refs.extend(matches)
        return list(set(refs))
    
    def _extract_sources(self, sql: str) -> list[str]:
        """Extract source() calls from SQL."""
        sources = []
        pattern = r"\{\{\s*source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}"
        matches = re.findall(pattern, sql)
        for match in matches:
            sources.append(f"{match[0]}.{match[1]}")
        return list(set(sources))
    
    def _extract_config(self, sql: str) -> dict:
        """Extract config block from SQL."""
        config = {}
        
        # Pattern for config block
        pattern = r"\{\{\s*config\s*\((.*?)\)\s*\}\}"
        match = re.search(pattern, sql, re.DOTALL)
        
        if match:
            config_str = match.group(1)
            
            # Extract key-value pairs
            # materialized
            mat_match = re.search(r"materialized\s*=\s*['\"](\w+)['\"]", config_str)
            if mat_match:
                config["materialized"] = mat_match.group(1)
            
            # tags
            tags_match = re.search(r"tags\s*=\s*\[(.*?)\]", config_str)
            if tags_match:
                tags = re.findall(r"['\"]([^'\"]+)['\"]", tags_match.group(1))
                config["tags"] = tags
            
            # schema
            schema_match = re.search(r"schema\s*=\s*['\"](\w+)['\"]", config_str)
            if schema_match:
                config["schema"] = schema_match.group(1)
            
            # alias
            alias_match = re.search(r"alias\s*=\s*['\"](\w+)['\"]", config_str)
            if alias_match:
                config["alias"] = alias_match.group(1)
        
        return config
    
    def _find_schema_info(self, model_path: Path, model_name: str) -> dict:
        """Find and parse schema.yml for model metadata."""
        result = {"description": None, "columns": []}
        
        # Look for schema.yml in same directory or parent directories
        search_dirs = [model_path.parent]
        if model_path.parent.name == "models":
            search_dirs.append(model_path.parent.parent)
        
        schema_files = ["schema.yml", "_schema.yml", "schema.yaml", "_models.yml"]
        
        for search_dir in search_dirs:
            for schema_name in schema_files:
                schema_path = search_dir / schema_name
                if schema_path.exists():
                    try:
                        content = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
                        if content and "models" in content:
                            for model in content["models"]:
                                if model.get("name") == model_name:
                                    result["description"] = model.get("description")
                                    
                                    # Parse columns
                                    for col in model.get("columns", []):
                                        result["columns"].append(ColumnInfo(
                                            name=col.get("name", ""),
                                            description=col.get("description"),
                                            data_type=col.get("data_type"),
                                            tests=[t if isinstance(t, str) else list(t.keys())[0] 
                                                   for t in col.get("tests", [])]
                                        ))
                                    return result
                    except Exception:
                        continue
        
        return result
