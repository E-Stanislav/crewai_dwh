"""Tool for searching code in files."""

import re
import fnmatch
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel

from schemas.tools import SearchCodeInput, SearchCodeOutput, SearchMatch
from utils.sandbox import get_sandbox


class SearchCodeTool(BaseTool):
    """Tool to search for patterns in code files."""
    
    name: str = "search_code"
    description: str = (
        "Search for a pattern (text or regex) across files in the project. "
        "Can filter by file pattern (e.g., '*.sql', '*.py'). "
        "Returns matching lines with file paths and line numbers. "
        "Use this to find function definitions, table references, specific code patterns, etc."
    )
    args_schema: type[BaseModel] = SearchCodeInput
    
    def _run(
        self,
        pattern: str,
        file_pattern: str = "*",
        case_sensitive: bool = False,
        max_results: int = 100
    ) -> str:
        """Execute the tool to search for patterns in files."""
        try:
            sandbox = get_sandbox()
            root_path = sandbox.root_path
            
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                regex = re.compile(pattern, flags)
            except re.error as e:
                return f"Error: Invalid regex pattern: {e}"
            
            matches: list[SearchMatch] = []
            files_searched = 0
            
            # Search through files
            for file_path in root_path.rglob("*"):
                if not file_path.is_file():
                    continue
                
                if not sandbox.is_valid_path(file_path):
                    continue
                
                # Check file pattern
                if not fnmatch.fnmatch(file_path.name, file_pattern):
                    continue
                
                # Skip binary files
                if self._is_binary(file_path):
                    continue
                
                files_searched += 1
                
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        match = regex.search(line)
                        if match:
                            matches.append(SearchMatch(
                                file_path=str(file_path.relative_to(root_path)),
                                line_number=line_num,
                                line_content=line.strip(),
                                match_text=match.group()
                            ))
                            
                            if len(matches) >= max_results:
                                break
                    
                    if len(matches) >= max_results:
                        break
                        
                except Exception:
                    continue
            
            # Create output
            output = SearchCodeOutput(
                matches=matches,
                total_matches=len(matches),
                files_searched=files_searched
            )
            
            # Format response
            result_lines = [
                f"**Search pattern:** `{pattern}`",
                f"**File pattern:** {file_pattern} | **Case sensitive:** {case_sensitive}",
                f"**Found:** {output.total_matches} matches in {output.files_searched} files searched",
                ""
            ]
            
            if matches:
                # Group by file
                by_file: dict[str, list[SearchMatch]] = {}
                for m in matches:
                    if m.file_path not in by_file:
                        by_file[m.file_path] = []
                    by_file[m.file_path].append(m)
                
                for file_path, file_matches in by_file.items():
                    result_lines.append(f"**📄 {file_path}**")
                    for m in file_matches[:10]:  # Limit per file
                        result_lines.append(f"  Line {m.line_number}: `{m.line_content[:100]}`")
                    if len(file_matches) > 10:
                        result_lines.append(f"  ... and {len(file_matches) - 10} more matches")
                    result_lines.append("")
            else:
                result_lines.append("No matches found.")
            
            return "\n".join(result_lines)
            
        except Exception as e:
            return f"Error searching code: {str(e)}"
    
    def _is_binary(self, file_path: Path) -> bool:
        """Check if a file is binary."""
        binary_extensions = {
            '.pyc', '.pyo', '.so', '.dll', '.exe', '.bin',
            '.jpg', '.jpeg', '.png', '.gif', '.ico', '.pdf',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.db', '.sqlite', '.sqlite3'
        }
        return file_path.suffix.lower() in binary_extensions
