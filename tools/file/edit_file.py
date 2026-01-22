"""Tool for editing files with search and replace."""

from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.tools import EditFileInput, EditFileOutput
from utils.sandbox import get_sandbox


class EditFileTool(BaseTool):
    """Tool to edit a file using search and replace."""
    
    name: str = "edit_file"
    description: str = (
        "Edit a file by replacing specific text. "
        "Provide the exact text to find (old_text) and what to replace it with (new_text). "
        "Use count=0 to replace all occurrences, or specify a number to limit replacements. "
        "Use this to modify SQL queries, update dbt configurations, fix bugs, etc."
    )
    args_schema: type[BaseModel] = EditFileInput
    
    def _run(
        self,
        file_path: str,
        old_text: str,
        new_text: str,
        count: int = 1
    ) -> str:
        """Execute the tool to edit a file."""
        try:
            sandbox = get_sandbox()
            validated_path = sandbox.validate_path(file_path)
            
            # Check if file exists
            if not validated_path.exists():
                return f"Error: File not found: {file_path}"
            
            if not validated_path.is_file():
                return f"Error: Path is not a file: {file_path}"
            
            # Read current content
            try:
                content = validated_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return f"Error: Cannot edit binary file: {file_path}"
            
            # Check if old_text exists
            if old_text not in content:
                return (
                    f"Error: Text not found in file: {file_path}\n"
                    f"Searched for: `{old_text[:100]}{'...' if len(old_text) > 100 else ''}`"
                )
            
            # Count occurrences
            occurrences = content.count(old_text)
            
            # Perform replacement
            if count == 0:
                # Replace all
                new_content = content.replace(old_text, new_text)
                replacements_made = occurrences
            else:
                # Replace limited number
                new_content = content.replace(old_text, new_text, count)
                replacements_made = min(count, occurrences)
            
            # Write back
            validated_path.write_text(new_content, encoding="utf-8")
            
            # Create output
            output = EditFileOutput(
                file_path=str(validated_path),
                replacements_made=replacements_made,
                success=True
            )
            
            # Format response
            return (
                f"✅ **Edited:** {sandbox.get_relative_path(validated_path)}\n"
                f"**Replacements:** {output.replacements_made} of {occurrences} occurrences\n"
                f"**Replaced:** `{old_text[:50]}{'...' if len(old_text) > 50 else ''}`\n"
                f"**With:** `{new_text[:50]}{'...' if len(new_text) > 50 else ''}`"
            )
            
        except Exception as e:
            return f"Error editing file: {str(e)}"
