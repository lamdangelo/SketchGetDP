"""
Configuration infrastructure module.

This module provides services for loading and managing application configuration.
It follows the dependency inversion principle by implementing gateway interfaces
defined in the interfaces layer.
"""

from .config_loader import ConfigLoader

__all__ = ['ConfigLoader']