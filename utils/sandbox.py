"""Sandbox validation for secure file operations."""

import os
from pathlib import Path
from functools import wraps
from typing import Callable, Any


class SandboxError(Exception):
    """Exception raised when sandbox validation fails."""
    pass


class SandboxValidator:
    """Validates that all file operations stay within the sandbox directory."""
    
    def __init__(self, root_path: str | Path):
        """
        Initialize sandbox with a root directory.
        
        Args:
            root_path: The root directory that serves as the sandbox boundary.
        """
        self.root_path = Path(root_path).resolve()
        if not self.root_path.exists():
            raise SandboxError(f"Sandbox root does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise SandboxError(f"Sandbox root is not a directory: {self.root_path}")
    
    def validate_path(self, path: str | Path) -> Path:
        """
        Validate that a path is within the sandbox.
        
        Args:
            path: The path to validate (can be relative or absolute).
            
        Returns:
            The resolved absolute path.
            
        Raises:
            SandboxError: If the path is outside the sandbox.
        """
        # Convert to Path object
        target_path = Path(path)
        
        # If relative, make it relative to sandbox root
        if not target_path.is_absolute():
            target_path = self.root_path / target_path
        
        # Resolve to absolute path (this handles .., symlinks, etc.)
        resolved_path = target_path.resolve()
        
        # Check if the resolved path is within the sandbox
        try:
            resolved_path.relative_to(self.root_path)
        except ValueError:
            raise SandboxError(
                f"Path '{path}' resolves to '{resolved_path}' which is outside sandbox '{self.root_path}'"
            )
        
        return resolved_path
    
    def is_valid_path(self, path: str | Path) -> bool:
        """
        Check if a path is valid without raising an exception.
        
        Args:
            path: The path to check.
            
        Returns:
            True if the path is within the sandbox, False otherwise.
        """
        try:
            self.validate_path(path)
            return True
        except SandboxError:
            return False
    
    def get_relative_path(self, path: str | Path) -> str:
        """
        Get the path relative to the sandbox root.
        
        Args:
            path: The path to convert.
            
        Returns:
            The path relative to the sandbox root.
        """
        resolved = self.validate_path(path)
        return str(resolved.relative_to(self.root_path))
    
    def join_path(self, *parts: str) -> Path:
        """
        Safely join path parts within the sandbox.
        
        Args:
            *parts: Path parts to join.
            
        Returns:
            The joined and validated path.
        """
        joined = Path(*parts)
        return self.validate_path(joined)


# Global sandbox instance (set when project is configured)
_sandbox: SandboxValidator | None = None


def set_sandbox(root_path: str | Path) -> SandboxValidator:
    """
    Set the global sandbox root.
    
    Args:
        root_path: The root directory for the sandbox.
        
    Returns:
        The SandboxValidator instance.
    """
    global _sandbox
    _sandbox = SandboxValidator(root_path)
    return _sandbox


def get_sandbox() -> SandboxValidator:
    """
    Get the global sandbox instance.
    
    Returns:
        The SandboxValidator instance.
        
    Raises:
        SandboxError: If sandbox has not been configured.
    """
    if _sandbox is None:
        raise SandboxError("Sandbox not configured. Call set_sandbox() first.")
    return _sandbox


def validate_path(path: str | Path) -> Path:
    """
    Validate a path using the global sandbox.
    
    Args:
        path: The path to validate.
        
    Returns:
        The validated absolute path.
    """
    return get_sandbox().validate_path(path)


def sandbox_protected(func: Callable) -> Callable:
    """
    Decorator to protect a function with sandbox validation.
    
    The decorated function must have a 'path' or 'file_path' or 'directory_path'
    parameter that will be validated.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Find path parameter
        path_params = ['path', 'file_path', 'directory_path', 'model_path']
        
        for param in path_params:
            if param in kwargs:
                kwargs[param] = str(validate_path(kwargs[param]))
                break
        
        return func(*args, **kwargs)
    
    return wrapper
