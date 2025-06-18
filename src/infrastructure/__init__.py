"""
Infrastructure layer - External concerns and data persistence.

Handles interaction with external systems:
- File-based data storage
- Network communication protocols
- System integration
"""

from .repository import FileRepository

__all__ = [
    "FileRepository"
]
