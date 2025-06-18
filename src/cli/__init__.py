"""
CLI layer - Command-line interface and user interaction.

Provides command-line tools for:
- Monitoring creature populations
- Managing simulation state
- Network diagnostics
"""

from .interface import ThrongletCLI

__all__ = [
    "ThrongletCLI"
]
