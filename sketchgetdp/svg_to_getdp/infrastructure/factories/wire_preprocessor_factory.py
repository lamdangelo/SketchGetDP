"""
Factory for creating wire preprocessor instances.
Implements the Factory pattern for dependency injection.
"""

from svg_to_getdp.infrastructure.wire_preprocessor import WirePreprocessor
from svg_to_getdp.interfaces.abstractions.wire_preprocessor_interface import WirePreprocessorInterface


class WirePreprocessorFactory:
    """
    Factory for creating WirePreprocessor instances.
    
    Follows the Factory pattern to decouple object creation from usage.
    """
    
    @staticmethod
    def create_default() -> WirePreprocessorInterface:
        """
        Create a default WirePreprocessor with standard settings.
        
        Returns:
            WirePreprocessorInterface: A preprocessor instance with default parameters
        """
        return WirePreprocessor()
    