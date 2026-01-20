"""
Factory for creating wire preprocessor instances.
Implements the Factory pattern for dependency injection.
"""

from typing import Optional
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
    
    @staticmethod  
    def create_with_cluster_detection(
        cluster_distance_threshold: float = 0.05,
        min_cluster_size: int = 1
    ) -> WirePreprocessorInterface:
        """
        Create a WirePreprocessor with custom cluster detection settings.
        
        Args:
            cluster_distance_threshold: Maximum distance between wires to consider them as a cluster
            min_cluster_size: Minimum number of wires to form a cluster
            
        Returns:
            WirePreprocessorInterface: A configured preprocessor instance
        """
        return WirePreprocessor(
            cluster_distance_threshold=cluster_distance_threshold,
            min_cluster_size=min_cluster_size
        )
    
    @staticmethod
    def from_config_dict(config: Optional[dict] = None) -> WirePreprocessorInterface:
        """
        Create a preprocessor from a configuration dictionary.
        
        Args:
            config: Dictionary with preprocessor configuration. If None, uses defaults.
                   Expected keys: 'cluster_distance_threshold', 'min_cluster_size'
                   
        Returns:
            WirePreprocessorInterface: A configured preprocessor instance
        """
        if config is None:
            config = {}
        
        distance_threshold = config.get('cluster_distance_threshold', 0.05)
        min_size = config.get('min_cluster_size', 1)
        
        return WirePreprocessorFactory.create_with_cluster_detection(
            cluster_distance_threshold=distance_threshold,
            min_cluster_size=min_size
        )
        