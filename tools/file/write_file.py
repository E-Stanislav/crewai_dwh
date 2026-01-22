"""Tool for writing files."""

from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.tools import WriteFileInput, WriteFileOutput
from utils.sandbox import get_sandbox


class WriteFileTool(BaseTool):
    """Tool to write/create a file."""
    
    name: str = "write_file"
    description: str = (
        "Write content to a file. Can create new files or overwrite existing ones. "
        "Use this to create new SQL files, dbt models, configuration files, documentation, etc. "
        "Set overwrite=True to replace existing files."
    )
    args_schema: type[BaseModel] = WriteFileInput
    
    def _run(
        self,
        file_path: str,
        content: str,
        create_dirs: bool = True,
        overwrite: bool = False
    ) -> str:
        """Execute the tool to write a file."""
        try:
            sandbox = get_sandbox()
            validated_path = sandbox.validate_path(file_path)
            
            # Check if file exists
            file_exists = validated_path.exists()
            
            if file_exists and not overwrite:
                return (
                    f"Error: File already exists: {file_path}\n"
                    f"Set overwrite=True to replace it."
                )
            
            # Create parent directories if needed
            if create_dirs:
                validated_path.parent.mkdir(parents=True, exist_ok=True)
            elif not validated_path.parent.exists():
                return f"Error: Parent directory does not exist: {validated_path.parent}"
            
            # Write content
            validated_path.write_text(content, encoding="utf-8")
            
            # Create output
            output = WriteFileOutput(
                file_path=str(validated_path),
                size_bytes=len(content.encode("utf-8")),
                created=not file_exists
            )
            
            # Format response
            action = "Created" if output.created else "Updated"
            return (
                f"✅ **{action}:** {sandbox.get_relative_path(validated_path)}\n"
                f"**Size:** {output.size_bytes} bytes"
            )
            
        except Exception as e:
            return f"Error writing file: {str(e)}"
