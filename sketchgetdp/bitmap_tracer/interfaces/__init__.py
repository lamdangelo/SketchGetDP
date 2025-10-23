"""
Interface Adapters Layer

This layer contains adapters that convert data between the form most convenient 
for external agencies (e.g., web, UI, devices) and the form most convenient 
for use cases and entities.

The interfaces layer depends on the enterprise business rules in the core layer,
but external agencies (like databases and web frameworks) depend on this layer.

Components:
- Controllers: Handle input from external sources and convert it to use case input
- Presenters: Format output from use cases for external presentation
- Gateways: Interface with external resources while abstracting their implementation
"""

from .controllers import *
from .presenters import *
from .gateways import *

__all__ = [
    # Controllers
    "TracingController",  # Handles image tracing requests and coordinates use cases
    
    # Presenters  
    "SVGPresenter",      # Formats tracing results as SVG documents
    
    # Gateways
    "ImageLoader",       # Abstracts image loading from various sources
    "ConfigRepository",  # Abstracts configuration storage and retrieval
]