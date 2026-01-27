"""
Gateways Package

Exports abstract gateway interfaces that define the boundaries between
the application core and external infrastructure. These abstractions
enable testability and flexibility in choosing implementations.
"""

from .image_loader import ImageLoader
from .config_repository import ConfigRepository

__all__ = [
    "ImageLoader",
    "ConfigRepository",
]