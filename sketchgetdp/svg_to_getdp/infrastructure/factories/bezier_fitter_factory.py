"""
Factory for creating bezier fitter instances.
"""

from svg_to_getdp.infrastructure.bezier_fitter import BezierFitter
from svg_to_getdp.interfaces.abstractions.bezier_fitter_interface import BezierFitterInterface


class BezierFitterFactory:
    """Factory for creating bezier fitter instances."""
    
    @staticmethod
    def create_default() -> BezierFitterInterface:
        """Create a default bezier fitter."""
        return BezierFitter()
    