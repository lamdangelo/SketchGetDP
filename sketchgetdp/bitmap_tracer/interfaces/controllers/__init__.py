"""
Interface adapters that handle user input and coordinate use cases.

Controllers are responsible for:
- Accepting input from the outside world
- Coordinating the execution of use cases
- Transforming data between external and internal representations
- Handling presentation concerns

This package follows the Interface Adapter layer in Clean Architecture.
"""

from .tracing_controller import TracingController

__all__ = ["TracingController"]