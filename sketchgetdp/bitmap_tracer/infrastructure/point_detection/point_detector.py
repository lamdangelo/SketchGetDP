import cv2
import numpy as np
from typing import Optional, Tuple
from ...core.entities.point import Point


class PointDetector:
    """
    Detects point-like contours and extracts their geometric properties.
    
    A point is defined as a small, compact contour that represents a discrete
    marker rather than a continuous path. This class encapsulates the logic
    for identifying such contours and calculating their center points.
    """
    
    def __init__(self, max_area: int = 100, max_perimeter: int = 80):
        """
        Initialize the point detector with size thresholds.
        
        Args:
            max_area: Maximum contour area to be considered a point (pixels²)
            max_perimeter: Maximum contour perimeter to be considered a point (pixels)
        """
        self.max_area = max_area
        self.max_perimeter = max_perimeter
    
    def is_point(self, contour: np.ndarray) -> bool:
        """
        Determine if a contour represents a point-like shape.
        
        Points are small, compact contours that meet both area and perimeter
        criteria. This prevents large or elongated shapes from being misclassified.
        
        Args:
            contour: OpenCV contour array to evaluate
            
        Returns:
            True if contour meets point criteria, False otherwise
        """
        if len(contour) < 3:
            return False
        
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        return area < self.max_area and perimeter < self.max_perimeter
    
    def get_center(self, contour: np.ndarray) -> Optional[Point]:
        """
        Calculate the centroid of a contour using moment analysis.
        
        The centroid represents the geometric center of the contour shape.
        This method uses OpenCV's moments calculation for accurate center detection.
        
        Args:
            contour: OpenCV contour array to analyze
            
        Returns:
            Point object representing the centroid, or None if calculation fails
        """
        if len(contour) < 3:
            return None
        
        moments = cv2.moments(contour)
        if moments["m00"] != 0:
            center_x = int(moments["m10"] / moments["m00"])
            center_y = int(moments["m01"] / moments["m00"])
            return Point(center_x, center_y)
        
        return None
    
    def detect_point(self, contour: np.ndarray) -> Optional[Point]:
        """
        Complete point detection pipeline: identification and center calculation.
        
        This method combines contour evaluation and center calculation into
        a single operation. It first verifies the contour meets point criteria,
        then calculates and returns its center if valid.
        
        Args:
            contour: OpenCV contour array to process
            
        Returns:
            Point object for valid point contours, None for non-point contours
        """
        if not self.is_point(contour):
            return None
        
        center = self.get_center(contour)
        if center:
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            print(f"  📍 Point detected: area={area:.1f}, perimeter={perimeter:.1f}, center=({center.x}, {center.y})")
        
        return center
    
    def get_contour_center(self, contour: np.ndarray) -> Optional[Point]:
        """
        Calculate center point for any contour, regardless of point classification.
        
        This is a utility method that provides centroid calculation without
        the point validation constraints. Useful for finding centers of
        larger shapes and paths.
        
        Args:
            contour: OpenCV contour array to analyze
            
        Returns:
            Point object representing the centroid, or None if calculation fails
        """
        return self.get_center(contour)
    
    def create_point_marker(self, center: Point, radius: int = 3) -> dict:
        """
        Generate SVG-compatible point marker data.
        
        Creates a simple circular marker representation suitable for
        SVG rendering. The marker is defined as a filled circle with
        no stroke for optimal visibility.
        
        Args:
            center: Point object specifying marker position
            radius: Radius of the circular marker in pixels
            
        Returns:
            Dictionary containing marker type and geometric properties
        """
        return {
            'type': 'circle',
            'cx': center.x,
            'cy': center.y,
            'r': radius
        }