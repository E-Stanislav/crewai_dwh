"""Tool for getting project structure as a tree."""

from pathlib import Path
from collections import defaultdict
from typing import ClassVar
from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.tools import ProjectStructureInput, ProjectStructureOutput
from utils.sandbox import get_sandbox


class ProjectStructureTool(BaseTool):
    """Tool to get the project structure as a tree."""
    
    name: str = "get_project_structure"
    description: str = (
        "Get the project structure as an ASCII tree. "
        "Shows directories and files organized hierarchically. "
        "Use this to understand the project layout, find configuration files, "
        "identify dbt models structure, etc."
    )
    args_schema: type[BaseModel] = ProjectStructureInput
    
    # Directories to skip (ClassVar to exclude from Pydantic model fields)
    SKIP_DIRS: ClassVar[set[str]] = {
        '__pycache__', '.git', '.svn', '.hg',
        'node_modules', '.venv', 'venv', 'env',
        '.idea', '.vscode', '.mypy_cache', '.pytest_cache',
        'target', 'dbt_packages', 'logs'
    }
    
    def _run(
        self,
        directory_path: str = ".",
        max_depth: int = 5,
        include_files: bool = True
    ) -> str:
        """Execute the tool to get project structure."""
        try:
            sandbox = get_sandbox()
            root_path = sandbox.validate_path(directory_path)
            
            if not root_path.is_dir():
                return f"Error: Not a directory: {directory_path}"
            
            tree_lines: list[str] = []
            total_files = 0
            total_dirs = 0
            file_types: dict[str, int] = defaultdict(int)
            
            # Build tree recursively
            tree_lines.append(f"📁 {root_path.name}/")
            total_files, total_dirs = self._build_tree(
                root_path, 
                tree_lines, 
                "", 
                0, 
                max_depth, 
                include_files,
                file_types,
                sandbox
            )
            
            # Create output
            output = ProjectStructureOutput(
                tree="\n".join(tree_lines),
                total_files=total_files,
                total_directories=total_dirs,
                file_types=dict(file_types)
            )
            
            # Format response
            result_lines = [
                f"**Project Structure**",
                f"**Total:** {output.total_files} files, {output.total_directories} directories",
                ""
            ]
            
            # Add file type summary
            if file_types:
                result_lines.append("**File Types:**")
                sorted_types = sorted(file_types.items(), key=lambda x: -x[1])
                for ext, count in sorted_types[:10]:
                    result_lines.append(f"  {ext}: {count}")
                result_lines.append("")
            
            result_lines.append("**Tree:**")
            result_lines.append("```")
            result_lines.append(output.tree)
            result_lines.append("```")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            return f"Error getting project structure: {str(e)}"
    
    def _build_tree(
        self,
        path: Path,
        lines: list[str],
        prefix: str,
        depth: int,
        max_depth: int,
        include_files: bool,
        file_types: dict[str, int],
        sandbox
    ) -> tuple[int, int]:
        """Recursively build tree structure."""
        if depth >= max_depth:
            return 0, 0
        
        total_files = 0
        total_dirs = 0
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return 0, 0
        
        # Filter items
        filtered_items = []
        for item in items:
            if item.name.startswith('.'):
                continue
            if item.is_dir() and item.name in self.SKIP_DIRS:
                continue
            if not sandbox.is_valid_path(item):
                continue
            filtered_items.append(item)
        
        for i, item in enumerate(filtered_items):
            is_last = i == len(filtered_items) - 1
            connector = "└── " if is_last else "├── "
            new_prefix = prefix + ("    " if is_last else "│   ")
            
            if item.is_dir():
                total_dirs += 1
                lines.append(f"{prefix}{connector}📁 {item.name}/")
                sub_files, sub_dirs = self._build_tree(
                    item, lines, new_prefix, depth + 1, max_depth,
                    include_files, file_types, sandbox
                )
                total_files += sub_files
                total_dirs += sub_dirs
            elif include_files:
                total_files += 1
                ext = item.suffix.lower() if item.suffix else "(no ext)"
                file_types[ext] += 1
                icon = self._get_file_icon(item.suffix)
                lines.append(f"{prefix}{connector}{icon} {item.name}")
        
        return total_files, total_dirs
    
    def _get_file_icon(self, suffix: str) -> str:
        """Get an icon for a file type."""
        icons = {
            '.py': '🐍',
            '.sql': '📊',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.json': '📋',
            '.md': '📝',
            '.txt': '📄',
            '.sh': '🔧',
            '.csv': '📈',
        }
        return icons.get(suffix.lower(), '📄')
