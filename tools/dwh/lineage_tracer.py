"""Tool for tracing data lineage in dbt projects."""

import re
from pathlib import Path
from collections import defaultdict
from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.dwh import LineageInput, LineageOutput, LineageNode
from utils.sandbox import get_sandbox


class LineageTracerTool(BaseTool):
    """Tool to trace data lineage in dbt projects."""
    
    name: str = "trace_lineage"
    description: str = (
        "Trace data lineage for a dbt model. "
        "Shows upstream dependencies (what this model depends on) and downstream dependents "
        "(what depends on this model). "
        "Use this to understand data flow and impact analysis."
    )
    args_schema: type[BaseModel] = LineageInput
    
    def _run(self, model_name: str, depth: int = 3) -> str:
        """Execute the tool to trace lineage."""
        try:
            sandbox = get_sandbox()
            root_path = sandbox.root_path
            
            # Build dependency graph
            graph = self._build_dependency_graph(root_path)
            
            if model_name not in graph["models"]:
                # Try to find model by partial name
                matches = [m for m in graph["models"] if model_name.lower() in m.lower()]
                if matches:
                    return f"Model '{model_name}' not found. Did you mean: {', '.join(matches[:5])}?"
                return f"Model '{model_name}' not found in project"
            
            # Trace upstream (what this model depends on)
            upstream = self._trace_upstream(model_name, graph, depth)
            
            # Trace downstream (what depends on this model)
            downstream = self._trace_downstream(model_name, graph, depth)
            
            # Build lineage graph for visualization
            lineage_graph = {
                "nodes": [model_name] + [n.name for n in upstream] + [n.name for n in downstream],
                "edges": []
            }
            
            for node in upstream:
                lineage_graph["edges"].append({"from": node.name, "to": model_name})
            for node in downstream:
                lineage_graph["edges"].append({"from": model_name, "to": node.name})
            
            # Create output
            output = LineageOutput(
                model=model_name,
                upstream=upstream,
                downstream=downstream,
                lineage_graph=lineage_graph,
                total_nodes=len(upstream) + len(downstream) + 1
            )
            
            # Format response
            result_lines = [
                f"## Lineage: {model_name}",
                f"**Total nodes:** {output.total_nodes}",
                ""
            ]
            
            # Upstream visualization
            result_lines.append("### Upstream Dependencies (what this model needs)")
            if upstream:
                result_lines.append("```")
                self._format_upstream_tree(model_name, graph, result_lines, depth)
                result_lines.append("```")
            else:
                result_lines.append("*No upstream dependencies (this is a source)*")
            
            result_lines.append("")
            
            # Downstream visualization  
            result_lines.append("### Downstream Dependents (what uses this model)")
            if downstream:
                result_lines.append("```")
                self._format_downstream_tree(model_name, graph, result_lines, depth)
                result_lines.append("```")
            else:
                result_lines.append("*No downstream dependents*")
            
            # Summary
            result_lines.append("\n### Summary")
            if upstream:
                sources = [n for n in upstream if n.node_type == "source"]
                models = [n for n in upstream if n.node_type == "model"]
                result_lines.append(f"- **Upstream:** {len(models)} models, {len(sources)} sources")
            
            if downstream:
                result_lines.append(f"- **Downstream:** {len(downstream)} models depend on this")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            return f"Error tracing lineage: {str(e)}"
    
    def _build_dependency_graph(self, root_path: Path) -> dict:
        """Build a dependency graph from dbt project files."""
        graph = {
            "models": {},  # model_name -> {"refs": [], "sources": [], "path": str}
            "reverse": defaultdict(list),  # model_name -> [models that depend on it]
        }
        
        # Find all SQL files
        for sql_file in root_path.rglob("*.sql"):
            # Skip if in target or dbt_packages
            if any(part in sql_file.parts for part in ["target", "dbt_packages", "logs"]):
                continue
            
            model_name = sql_file.stem
            content = sql_file.read_text(encoding="utf-8", errors="ignore")
            
            # Extract refs
            refs = re.findall(r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", content)
            
            # Extract sources
            sources = []
            source_matches = re.findall(
                r"\{\{\s*source\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", 
                content
            )
            for match in source_matches:
                sources.append(f"{match[0]}.{match[1]}")
            
            graph["models"][model_name] = {
                "refs": list(set(refs)),
                "sources": list(set(sources)),
                "path": str(sql_file.relative_to(root_path))
            }
            
            # Build reverse graph
            for ref in refs:
                graph["reverse"][ref].append(model_name)
        
        return graph
    
    def _trace_upstream(
        self, 
        model_name: str, 
        graph: dict, 
        depth: int, 
        visited: set = None
    ) -> list[LineageNode]:
        """Trace upstream dependencies."""
        if visited is None:
            visited = set()
        
        if depth <= 0 or model_name in visited:
            return []
        
        visited.add(model_name)
        upstream = []
        
        if model_name in graph["models"]:
            model_info = graph["models"][model_name]
            
            # Add direct refs
            for ref in model_info["refs"]:
                path = graph["models"].get(ref, {}).get("path")
                upstream.append(LineageNode(
                    name=ref,
                    node_type="model",
                    path=path
                ))
                
                # Recurse
                upstream.extend(self._trace_upstream(ref, graph, depth - 1, visited))
            
            # Add sources
            for source in model_info["sources"]:
                upstream.append(LineageNode(
                    name=source,
                    node_type="source",
                    path=None
                ))
        
        return upstream
    
    def _trace_downstream(
        self, 
        model_name: str, 
        graph: dict, 
        depth: int, 
        visited: set = None
    ) -> list[LineageNode]:
        """Trace downstream dependents."""
        if visited is None:
            visited = set()
        
        if depth <= 0 or model_name in visited:
            return []
        
        visited.add(model_name)
        downstream = []
        
        # Find models that reference this one
        for dependent in graph["reverse"].get(model_name, []):
            path = graph["models"].get(dependent, {}).get("path")
            downstream.append(LineageNode(
                name=dependent,
                node_type="model",
                path=path
            ))
            
            # Recurse
            downstream.extend(self._trace_downstream(dependent, graph, depth - 1, visited))
        
        return downstream
    
    def _format_upstream_tree(
        self, 
        model_name: str, 
        graph: dict, 
        lines: list, 
        depth: int, 
        prefix: str = "",
        visited: set = None
    ):
        """Format upstream as ASCII tree."""
        if visited is None:
            visited = set()
        
        if depth <= 0 or model_name in visited:
            return
        
        visited.add(model_name)
        
        if model_name in graph["models"]:
            model_info = graph["models"][model_name]
            deps = model_info["refs"] + model_info["sources"]
            
            for i, dep in enumerate(deps):
                is_last = i == len(deps) - 1
                connector = "└── " if is_last else "├── "
                
                node_type = "📊" if dep in model_info["sources"] else "📁"
                lines.append(f"{prefix}{connector}{node_type} {dep}")
                
                if dep not in model_info["sources"]:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    self._format_upstream_tree(dep, graph, lines, depth - 1, new_prefix, visited)
    
    def _format_downstream_tree(
        self, 
        model_name: str, 
        graph: dict, 
        lines: list, 
        depth: int, 
        prefix: str = "",
        visited: set = None
    ):
        """Format downstream as ASCII tree."""
        if visited is None:
            visited = set()
        
        if depth <= 0 or model_name in visited:
            return
        
        visited.add(model_name)
        
        dependents = graph["reverse"].get(model_name, [])
        
        for i, dep in enumerate(dependents):
            is_last = i == len(dependents) - 1
            connector = "└── " if is_last else "├── "
            
            lines.append(f"{prefix}{connector}📁 {dep}")
            
            new_prefix = prefix + ("    " if is_last else "│   ")
            self._format_downstream_tree(dep, graph, lines, depth - 1, new_prefix, visited)
