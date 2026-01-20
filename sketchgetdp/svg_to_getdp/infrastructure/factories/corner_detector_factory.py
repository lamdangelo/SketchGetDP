"""
Factory for creating corner detector instances.
"""

from svg_to_getdp.infrastructure.corner_detector import CornerDetector
from svg_to_getdp.interfaces.abstractions.corner_detector_interface import CornerDetectorInterface


class CornerDetectorFactory:
    """Factory for creating corner detector instances."""
    
    @staticmethod
    def create_default() -> CornerDetectorInterface:
        """Create a default corner detector."""
        return CornerDetector()
    
    @staticmethod
    def create_with_debug(debug_enabled: bool = True) -> CornerDetectorInterface:
        """Create a corner detector with debug mode."""
        return CornerDetector(debug_enabled=debug_enabled)
    