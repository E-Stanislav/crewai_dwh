"""Pydantic schemas for file operation tools."""

from pydantic import BaseModel, Field


# ============== Read File ==============

class ReadFileInput(BaseModel):
    """Input schema for reading a file."""
    file_path: str = Field(..., description="Path to the file to read")


class ReadFileOutput(BaseModel):
    """Output schema for file read operation."""
    content: str = Field(..., description="Content of the file")
    file_path: str = Field(..., description="Absolute path to the file")
    size_bytes: int = Field(..., description="File size in bytes")
    encoding: str = Field(default="utf-8", description="File encoding")
    line_count: int = Field(..., description="Number of lines in the file")


# ============== List Directory ==============

class ListDirectoryInput(BaseModel):
    """Input schema for listing directory contents."""
    directory_path: str = Field(default=".", description="Path to directory to list")
    pattern: str = Field(default="*", description="Glob pattern to filter files")
    recursive: bool = Field(default=False, description="List subdirectories recursively")


class ListDirectoryOutput(BaseModel):
    """Output schema for directory listing."""
    files: list[str] = Field(default_factory=list, description="List of file paths")
    directories: list[str] = Field(default_factory=list, description="List of directory paths")
    total_count: int = Field(..., description="Total number of items")
    directory_path: str = Field(..., description="Listed directory path")


# ============== Search Code ==============

class SearchMatch(BaseModel):
    """A single search match result."""
    file_path: str = Field(..., description="Path to file containing match")
    line_number: int = Field(..., description="Line number of match")
    line_content: str = Field(..., description="Full line content")
    match_text: str = Field(..., description="Matched text")


class SearchCodeInput(BaseModel):
    """Input schema for code search."""
    pattern: str = Field(..., description="Search pattern (regex supported)")
    file_pattern: str = Field(default="*", description="Glob pattern for files to search")
    case_sensitive: bool = Field(default=False, description="Case-sensitive search")
    max_results: int = Field(default=100, description="Maximum number of results")


class SearchCodeOutput(BaseModel):
    """Output schema for code search."""
    matches: list[SearchMatch] = Field(default_factory=list, description="List of matches")
    total_matches: int = Field(..., description="Total number of matches found")
    files_searched: int = Field(..., description="Number of files searched")


# ============== Project Structure ==============

class ProjectStructureInput(BaseModel):
    """Input schema for getting project structure."""
    directory_path: str = Field(default=".", description="Root directory path")
    max_depth: int = Field(default=5, description="Maximum depth to traverse")
    include_files: bool = Field(default=True, description="Include files in output")


class ProjectStructureOutput(BaseModel):
    """Output schema for project structure."""
    tree: str = Field(..., description="ASCII tree representation")
    total_files: int = Field(..., description="Total number of files")
    total_directories: int = Field(..., description="Total number of directories")
    file_types: dict[str, int] = Field(default_factory=dict, description="Count of files by extension")


# ============== Write File ==============

class WriteFileInput(BaseModel):
    """Input schema for writing a file."""
    file_path: str = Field(..., description="Path where to write the file")
    content: str = Field(..., description="Content to write")
    create_dirs: bool = Field(default=True, description="Create parent directories if needed")
    overwrite: bool = Field(default=False, description="Overwrite existing file")


class WriteFileOutput(BaseModel):
    """Output schema for file write operation."""
    file_path: str = Field(..., description="Path to written file")
    size_bytes: int = Field(..., description="Size of written file")
    created: bool = Field(..., description="True if file was created, False if overwritten")


# ============== Edit File ==============

class EditFileInput(BaseModel):
    """Input schema for editing a file."""
    file_path: str = Field(..., description="Path to the file to edit")
    old_text: str = Field(..., description="Text to find and replace")
    new_text: str = Field(..., description="Replacement text")
    count: int = Field(default=1, description="Number of replacements (0 for all)")


class EditFileOutput(BaseModel):
    """Output schema for file edit operation."""
    file_path: str = Field(..., description="Path to edited file")
    replacements_made: int = Field(..., description="Number of replacements made")
    success: bool = Field(..., description="Whether edit was successful")
