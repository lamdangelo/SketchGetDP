import cv2
import numpy as np
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class ClosedContour:
    """
    Represents a contour with closure verification and metrics.
    
    This immutable data structure provides a clean interface for contour
    information, ensuring closure status is explicitly tracked and available
    to downstream processing stages.
    
    Attributes:
        points: List of contour points as numpy arrays
        is_closed: Boolean indicating whether the contour forms a closed shape
        closure_gap: Distance between start and end points in pixels
    """
    points: List[np.ndarray]
    is_closed: bool
    closure_gap: float


class ContourClosureService:
    """
    Ensures contour closure and provides closure analysis utilities.
    
    Handles the important task of verifying and enforcing contour closure,
    which is essential for generating valid SVG paths and proper shape rendering.
    Open contours can cause rendering artifacts and incorrect shape interpretation.
    """

    def ensure_closure(self, contour: np.ndarray, tolerance: float = 5.0) -> np.ndarray:
        """
        Guarantees a contour forms a closed loop by connecting endpoints if necessary.
        
        Checks the distance between start and end points. If beyond tolerance,
        explicitly adds the start point to the end to create a mathematically
        closed contour. This prevents rendering issues in downstream SVG generation.
        
        Args:
            contour: numpy array of contour points to check and potentially close
            tolerance: Maximum allowed gap between start and end points in pixels
            
        Returns:
            Guaranteed closed contour as numpy array
        """
        # Contours with less than 3 points cannot form closed shapes
        if len(contour) < 3:
            return contour
        
        start_point = contour[0][0]
        end_point = contour[-1][0]
        
        # Calculate Euclidean distance between start and end points
        distance = np.linalg.norm(start_point - end_point)
        
        # Explicitly close the contour if endpoints are too far apart
        if distance > tolerance:
            # Reshape start point to match contour array structure
            start_point_reshaped = contour[0].reshape(1, 1, 2)
            closed_contour = np.vstack([contour, start_point_reshaped])
            print(f"  🔒 Closed contour: start-end distance was {distance:.2f} pixels")
            return closed_contour
        
        return contour
    
    def is_closed(self, contour: np.ndarray, tolerance: float = 5.0) -> bool:
        """
        Determines if a contour forms a mathematically closed shape.
        
        A contour is considered closed if the distance between its start
        and end points is within the specified tolerance. This is essential
        for validating contour integrity before further processing.
        
        Args:
            contour: numpy array of contour points to check
            tolerance: Maximum allowed gap for considering the contour closed
            
        Returns:
            True if contour is closed within tolerance, False otherwise
        """
        # Contours with insufficient points cannot be closed
        if len(contour) < 3:
            return False
        
        start_point = contour[0][0]
        end_point = contour[-1][0]
        distance = np.linalg.norm(start_point - end_point)
        
        return distance <= tolerance
    
    def calculate_closure_gap(self, contour: np.ndarray) -> float:
        """
        Calculates the precise gap distance between contour start and end points.
        
        This metric helps quantify how "open" a contour is and informs
        closure decisions. Larger gaps may indicate detection errors or
        intentionally open shapes.
        
        Args:
            contour: numpy array of contour points to measure
            
        Returns:
            Euclidean distance between start and end points in pixels,
            or infinity for invalid contours
        """
        if len(contour) < 3:
            return float('inf')
        
        start_point = contour[0][0]
        end_point = contour[-1][0]
        return np.linalg.norm(start_point - end_point)
    
    def create_closed_contour_object(self, contour: np.ndarray, tolerance: float = 5.0) -> ClosedContour:
        """
        Creates a ClosedContour object with comprehensive closure analysis.
        
        Factory method that bundles contour points with closure metadata
        in an immutable data structure. This provides a clean interface
        for passing contour information between system components.
        
        Args:
            contour: numpy array of contour points to analyze
            tolerance: Closure tolerance threshold in pixels
            
        Returns:
            ClosedContour instance containing points and closure metadata
        """
        closure_gap = self.calculate_closure_gap(contour)
        is_closed = closure_gap <= tolerance
        closed_points = self.ensure_closure(contour, tolerance)
        
        return ClosedContour(
            points=[point[0] for point in closed_points],
            is_closed=is_closed,
            closure_gap=closure_gap
        )
    
    def analyze_contour_closure(self, contour: np.ndarray) -> Dict:
        """
        Performs comprehensive closure analysis on a contour.
        
        Provides a complete set of metrics for contour quality assessment,
        useful for debugging, filtering, and quality control in the
        image processing pipeline.
        
        Args:
            contour: numpy array of contour points to analyze
            
        Returns:
            Dictionary containing comprehensive contour metrics:
            - is_closed: Closure status boolean
            - closure_gap: Distance between endpoints
            - area: Contour area in pixels
            - perimeter: Contour perimeter length
            - point_count: Number of points in contour
            - needs_closure: Whether explicit closure is recommended
        """
        closure_gap = self.calculate_closure_gap(contour)
        is_closed = self.is_closed(contour)
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        return {
            'is_closed': is_closed,
            'closure_gap': closure_gap,
            'area': area,
            'perimeter': perimeter,
            'point_count': len(contour),
            'needs_closure': closure_gap > 5.0 and not is_closed
        }