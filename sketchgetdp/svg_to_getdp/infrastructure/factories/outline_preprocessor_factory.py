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
    
    @staticmethod  
    def create_with_precision(bezier_precision: float = 0.001) -> OutlinePreprocessorInterface:
        """
        Create an OutlinePreprocessor with custom precision settings.
        
        Args:
            bezier_precision: Precision for Bézier curve discretization
            
        Returns:
            OutlinePreprocessorInterface: A configured preprocessor instance
        """
        return OutlinePreprocessor(
            bezier_precision=bezier_precision
        )
    
    @staticmethod
    def from_config_dict(config: Optional[dict] = None) -> OutlinePreprocessorInterface:
        """
        Create a preprocessor from a configuration dictionary.
        
        Args:
            config: Dictionary with preprocessor configuration. If None, uses defaults.
                   Expected key: 'bezier_precision'
                   
        Returns:
            OutlinePreprocessorInterface: A configured preprocessor instance
        """
        if config is None:
            config = {}
        
        precision = config.get('bezier_precision', 0.001)
        
        return OutlinePreprocessorFactory.create_with_precision(precision)
    