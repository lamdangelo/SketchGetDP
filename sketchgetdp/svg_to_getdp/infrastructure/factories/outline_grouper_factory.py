"""
Factory for creating outline grouper instances.
Implements the Factory pattern for dependency injection.
"""

from typing import Optional
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
    
    @staticmethod  
    def create_with_tolerance(point_in_polygon_tolerance: float = 1e-10) -> OutlineGrouperInterface:
        """
        Create an OutlineGrouper with custom tolerance settings.
        
        Args:
            point_in_polygon_tolerance: Tolerance for point-in-polygon tests
            
        Returns:
            OutlineGrouperInterface: A configured grouper instance
        """
        return OutlineGrouper(
            point_in_polygon_tolerance=point_in_polygon_tolerance
        )
    
    @staticmethod
    def from_config_dict(config: Optional[dict] = None) -> OutlineGrouperInterface:
        """
        Create a grouper from a configuration dictionary.
        
        Args:
            config: Dictionary with grouper configuration. If None, uses defaults.
                   Expected key: 'point_in_polygon_tolerance'
                   
        Returns:
            OutlineGrouperInterface: A configured grouper instance
        """
        if config is None:
            config = {}
        
        tolerance = config.get('point_in_polygon_tolerance', 1e-10)
        
        return OutlineGrouperFactory.create_with_tolerance(tolerance)
    