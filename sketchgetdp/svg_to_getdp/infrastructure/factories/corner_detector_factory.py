"""
Factory for creating corner detector instances.
"""

from svg_to_getdp.interfaces.abstractions.corner_detector_interface import CornerDetectorInterface
from svg_to_getdp.infrastructure.corner_detection.corner_detector import CornerDetector


class CornerDetectorFactory:
    """Factory for creating corner detector instances."""
    
    @staticmethod
    def create_default() -> CornerDetectorInterface:
        """
        Create a corner detector with default parameters.
        
        Returns:
            CornerDetectorInterface instance
        """
        return CornerDetector(
            window_size=15,
            direction_change_threshold=0.8,
            angle_threshold=0.5,  # radians (~30 degrees)
            minimum_corner_distance=5,
            smoothness_threshold=0.72,
            corner_strength_threshold=0.45,
            ellipse_aspect_ratio_threshold=1.2,
            debug_enabled=True
        )
        