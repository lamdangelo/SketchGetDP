from core.entities.point import Point, PointData
from core.entities.contour import ClosedContour
from core.entities.color import Color


class PointStub:
    """
    Factory methods for creating Point entities with sensible test defaults.
    Supports both basic coordinate points and enriched PointData with metadata.
    """
    
    @staticmethod
    def create(x=0.0, y=0.0, radius=1.0, is_small_point=False):
        """Create PointData with geometric metadata for testing point detection algorithms."""
        return PointData(x=x, y=y, radius=radius, is_small_point=is_small_point)
    
    @staticmethod
    def create_basic(x=0.0, y=0.0):
        """Create minimal Point for testing coordinate-based operations and contour construction."""
        return Point(x=x, y=y)


class ContourStub:
    """
    Factory methods for creating ClosedContour entities with configurable geometric properties.
    Supports testing both perfect and imperfect (gapped) contour scenarios.
    """
    
    @staticmethod
    def create(points=None, is_closed=True, closure_gap=0.0):
        """Create contour from basic Points for testing geometric operations and closure detection."""
        if points is None:
            points = [PointStub.create_basic(), PointStub.create_basic(1.0, 1.0)]
        return ClosedContour(points=points, is_closed=is_closed, closure_gap=closure_gap)
    
    @staticmethod
    def create_with_point_data(points=None, is_closed=True, closure_gap=0.0):
        """Create contour from PointData objects for testing point metadata preservation in contours."""
        if points is None:
            points = [PointStub.create(), PointStub.create(1.0, 1.0)]
        # Convert PointData to Point for contour compatibility
        basic_points = [point_data.to_point() for point_data in points]
        return ClosedContour(points=basic_points, is_closed=is_closed, closure_gap=closure_gap)


class ColorStub:
    """
    Factory methods for creating Color entities using BGR format (OpenCV standard).
    Provides semantic color creation for testing color detection and categorization.
    """
    
    @staticmethod
    def create(b=255, g=255, r=255):
        """Create color with explicit BGR channels for testing specific color value handling."""
        return Color(b=b, g=g, r=r)
    
    @staticmethod
    def create_blue():
        """Pure blue for testing blue path detection in diagram processing."""
        return Color(b=255, g=0, r=0)
    
    @staticmethod
    def create_red():
        """Pure red for testing red dot detection in structural diagrams."""
        return Color(b=0, g=0, r=255)
    
    @staticmethod
    def create_green():
        """Pure green for testing green path detection in multi-color diagrams."""
        return Color(b=0, g=255, r=0)
    
    @staticmethod
    def create_white():
        """White for testing background detection and noise filtering."""
        return Color(b=255, g=255, r=255)
    
    @staticmethod
    def create_black():
        """Black for testing noise detection and minimum value thresholds."""
        return Color(b=0, g=0, r=0)