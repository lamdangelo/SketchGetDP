"""
Factory for creating outline preprocessor instances.
Implements the Factory pattern for dependency injection.
"""

from typing import Optional
from svg_to_getdp.infrastructure.outline_preprocessor import OutlinePreprocessor
from svg_to_getdp.interfaces.abstractions.outline_preprocessor_interface import OutlinePreprocessorInterface


class OutlinePreprocessorFactory:
    """
    Factory for creating OutlinePreprocessor instances.
    
    Follows the Factory pattern to decouple object creation from usage.
    """
    
    @staticmethod
    def create_default() -> OutlinePreprocessorInterface:
        """
        Create a default OutlinePreprocessor with standard settings.
        
        Returns:
            OutlinePreprocessorInterface: A preprocessor instance with default parameters
        """
        return OutlinePreprocessor()
    