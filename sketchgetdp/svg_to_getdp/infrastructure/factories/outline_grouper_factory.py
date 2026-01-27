"""
Factory for creating outline grouper instances.
Implements the Factory pattern for dependency injection.
"""

from svg_to_getdp.infrastructure.outline_grouper import OutlineGrouper
from svg_to_getdp.interfaces.abstractions.outline_grouper_interface import OutlineGrouperInterface


class OutlineGrouperFactory:
    """
    Factory for creating OutlineGrouper instances.
    
    Follows the Factory pattern to decouple object creation from usage.
    """
    
    @staticmethod
    def create_default() -> OutlineGrouperInterface:
        """
        Create a default OutlineGrouper with standard settings.
        
        Returns:
            OutlineGrouperInterface: A grouper instance with default parameters
        """
        return OutlineGrouper()
    