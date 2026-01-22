"""Tool for reading file contents."""

from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.tools import ReadFileInput, ReadFileOutput
from utils.sandbox import get_sandbox


class ReadFileTool(BaseTool):
    """Tool to read the contents of a file."""
    
    name: str = "read_file"
    description: str = (
        "Read the contents of a file. Provide the file path relative to the project root. "
        "Returns the file content, size, and line count. "
        "Use this to examine source code, SQL files, configuration files, etc."
    )
    args_schema: type[BaseModel] = ReadFileInput
    
    def _run(self, file_path: str) -> str:
        """Execute the tool to read a file."""
        try:
            # Validate path within sandbox
            sandbox = get_sandbox()
            validated_path = sandbox.validate_path(file_path)
            
            # Check if file exists
            if not validated_path.exists():
                return f"Error: File not found: {file_path}"
            
            if not validated_path.is_file():
                return f"Error: Path is not a file: {file_path}"
            
            # Read file content
            try:
                content = validated_path.read_text(encoding="utf-8")
                encoding = "utf-8"
            except UnicodeDecodeError:
                # Try latin-1 as fallback
                content = validated_path.read_text(encoding="latin-1")
                encoding = "latin-1"
            
            # Create output
            output = ReadFileOutput(
                content=content,
                file_path=str(validated_path),
                size_bytes=validated_path.stat().st_size,
                encoding=encoding,
                line_count=len(content.splitlines())
            )
            
            # Return formatted response for LLM
            return (
                f"**File:** {sandbox.get_relative_path(validated_path)}\n"
                f"**Size:** {output.size_bytes} bytes | **Lines:** {output.line_count}\n"
                f"**Encoding:** {output.encoding}\n\n"
                f"```\n{output.content}\n```"
            )
            
        except Exception as e:
            return f"Error reading file: {str(e)}"
