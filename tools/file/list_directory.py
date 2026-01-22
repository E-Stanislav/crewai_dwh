"""Tool for listing directory contents."""

import fnmatch
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.tools import ListDirectoryInput, ListDirectoryOutput
from utils.sandbox import get_sandbox


class ListDirectoryTool(BaseTool):
    """Tool to list contents of a directory."""
    
    name: str = "list_directory"
    description: str = (
        "List files and directories in a given path. "
        "Can filter by pattern (e.g., '*.sql', '*.py') and optionally list recursively. "
        "Use this to explore project structure and find files."
    )
    args_schema: type[BaseModel] = ListDirectoryInput
    
    def _run(
        self, 
        directory_path: str = ".", 
        pattern: str = "*", 
        recursive: bool = False
    ) -> str:
        """Execute the tool to list directory contents."""
        try:
            # Validate path within sandbox
            sandbox = get_sandbox()
            validated_path = sandbox.validate_path(directory_path)
            
            # Check if directory exists
            if not validated_path.exists():
                return f"Error: Directory not found: {directory_path}"
            
            if not validated_path.is_dir():
                return f"Error: Path is not a directory: {directory_path}"
            
            files: list[str] = []
            directories: list[str] = []
            
            if recursive:
                # Recursive listing
                for item in validated_path.rglob(pattern):
                    if sandbox.is_valid_path(item):
                        rel_path = str(item.relative_to(validated_path))
                        if item.is_file():
                            files.append(rel_path)
                        elif item.is_dir():
                            directories.append(rel_path)
            else:
                # Non-recursive listing
                for item in validated_path.iterdir():
                    if sandbox.is_valid_path(item):
                        if fnmatch.fnmatch(item.name, pattern):
                            if item.is_file():
                                files.append(item.name)
                            elif item.is_dir():
                                directories.append(item.name)
            
            # Sort results
            files.sort()
            directories.sort()
            
            # Create output
            output = ListDirectoryOutput(
                files=files,
                directories=directories,
                total_count=len(files) + len(directories),
                directory_path=str(validated_path)
            )
            
            # Format response
            result_lines = [
                f"**Directory:** {sandbox.get_relative_path(validated_path)}",
                f"**Pattern:** {pattern} | **Recursive:** {recursive}",
                f"**Total:** {output.total_count} items ({len(files)} files, {len(directories)} directories)",
                ""
            ]
            
            if directories:
                result_lines.append("**Directories:**")
                for d in directories[:50]:  # Limit output
                    result_lines.append(f"  📁 {d}")
                if len(directories) > 50:
                    result_lines.append(f"  ... and {len(directories) - 50} more directories")
                result_lines.append("")
            
            if files:
                result_lines.append("**Files:**")
                for f in files[:100]:  # Limit output
                    result_lines.append(f"  📄 {f}")
                if len(files) > 100:
                    result_lines.append(f"  ... and {len(files) - 100} more files")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            return f"Error listing directory: {str(e)}"
