from dataclasses import dataclass
from typing import List, Tuple
from ...core.entities.bezier_segment import BezierSegment
from ...core.entities.color import Color
from ...core.entities.point import Point


@dataclass
class BoundaryCurve:
    """
    Represents a complete boundary curve composed of multiple Bézier segments.
    Corresponds to the piecewise Bézier curve representation 𝒞(t) from the paper.
    Color property is preserved from SVG parsing for later potential assignment.
    """
    
    bezier_segments: List[BezierSegment]
    corners: List[Point]  # Coordinates identified as corners
    color: Color  # Used for potential assignment in simulation
    is_closed: bool = True
    
    def __post_init__(self):
        """Validate that the curve is properly constructed with tolerance."""
        if len(self.bezier_segments) < 1:
            raise ValueError("Boundary curve must have at least one Bézier segment")
        
        # Very tolerant check - only warn for significant gaps
        for i in range(len(self.bezier_segments) - 1):
            current_segment = self.bezier_segments[i]
            next_segment = self.bezier_segments[i + 1]
            
            distance = current_segment.end_point.distance_to(next_segment.start_point)
            if distance > 1e-5:  # Only warn for gaps > 0.00001
                print(f"WARNING: Small discontinuity between segments {i} and {i+1}: {distance:.6f}")
                
    @property
    def control_points(self) -> List[Point]:
        """Get all control points from all Bézier segments (including duplicates at interfaces)."""
        all_points = []
        for segment in self.bezier_segments:
            all_points.extend(segment.control_points)
        return all_points
    
    @property
    def unique_control_points(self) -> List[Point]:
        """Get all unique control points (removing duplicates at interfaces)."""
        if not self.bezier_segments:
            return []
        
        unique_points = []
        for i, segment in enumerate(self.bezier_segments):
            if i == 0:
                # For first segment, take all control points
                unique_points.extend(segment.control_points)
            else:
                # For subsequent segments, skip first control point (duplicate of previous segment's last point)
                unique_points.extend(segment.control_points[1:])
        return unique_points
    
    def evaluate(self, t: float) -> Point:
        """
        Evaluate the boundary curve at parameter t ∈ [0,1].
        Implements the piecewise evaluation from equation (5) in the paper.
        """
        if not 0 <= t <= 1:
            raise ValueError("Parameter t must be in [0,1]")
        
        num_segments = len(self.bezier_segments)
        segment_index = int(t * num_segments)
        segment_index = min(segment_index, num_segments - 1)  # Handle t=1.0
        
        # Map global t to local t̃ ∈ [0,1] for the specific segment
        local_t = (t * num_segments) - segment_index
        
        return self.bezier_segments[segment_index].evaluate(local_t)
    
    def derivative(self, t: float) -> Point:
        """
        Compute the derivative of the boundary curve at parameter t ∈ [0,1].
        Implements the derivative calculation from equations (8) and (31).
        """
        if not 0 <= t <= 1:
            raise ValueError("Parameter t must be in [0,1]")
        
        num_segments = len(self.bezier_segments)
        segment_index = int(t * num_segments)
        segment_index = min(segment_index, num_segments - 1)
        
        local_t = (t * num_segments) - segment_index
        
        # Apply chain rule: d𝒞/dt = N_C * dC/dṫ
        derivative = self.bezier_segments[segment_index].derivative(local_t)
        return Point(derivative.x * num_segments, derivative.y * num_segments)
    
    def is_corner_at_parameter(self, t: float, tolerance: float = 1e-6) -> bool:
        """
        Check if the given parameter t corresponds to a corner point.
        """
        evaluated_point = self.evaluate(t)
        for corner in self.corners:
            if (abs(evaluated_point.x - corner.x) < tolerance and 
                abs(evaluated_point.y - corner.y) < tolerance):
                return True
        return False
    
    def is_corner_at_segment_interface(self, segment_index: int) -> bool:
        """
        Check if the interface between segments is a corner.
        
        Args:
            segment_index: Index of the segment (0 to len(segments)-2)
                          Represents the interface between segments[segment_index] 
                          and segments[segment_index + 1]
        """
        if segment_index < 0 or segment_index >= len(self.bezier_segments) - 1:
            raise ValueError("Invalid segment index for interface check")
        
        interface_point = self.bezier_segments[segment_index].end_point
        for corner in self.corners:
            if (abs(interface_point.x - corner.x) < 1e-6 and 
                abs(interface_point.y - corner.y) < 1e-6):
                return True
        return False
    
    def get_segment_at_parameter(self, t: float) -> Tuple[BezierSegment, float]:
        """
        Get the Bézier segment and local parameter for a given global parameter t.
        
        Returns:
            Tuple of (segment, local_t) where local_t ∈ [0,1]
        """
        if not 0 <= t <= 1:
            raise ValueError("Parameter t must be in [0,1]")
        
        num_segments = len(self.bezier_segments)
        segment_index = int(t * num_segments)
        segment_index = min(segment_index, num_segments - 1)
        
        local_t = (t * num_segments) - segment_index
        
        return self.bezier_segments[segment_index], local_t
    
    def get_curve_points(self, num_points: int = 100) -> List[Point]:
        """
        Sample the entire boundary curve at multiple parameter values.
        
        Args:
            num_points: Number of points to sample along the entire curve
            
        Returns:
            List of points along the complete boundary curve
        """
        if num_points < 2:
            raise ValueError("Number of points must be at least 2")
        
        points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            points.append(self.evaluate(t))
        return points
    
    def get_boundary_length_approximation(self, num_samples: int = 1000) -> float:
        """
        Approximate the length of the boundary curve by sampling.
        
        Args:
            num_samples: Number of sample points for length approximation
            
        Returns:
            Approximate length of the boundary curve
        """
        points = self.get_curve_points(num_samples)
        length = 0.0
        for i in range(len(points) - 1):
            length += points[i].distance_to(points[i + 1])
        return length
    
    def __len__(self) -> int:
        """Return the number of Bézier segments in this boundary curve."""
        return len(self.bezier_segments)
    
    def __iter__(self):
        """Iterate over Bézier segments."""
        return iter(self.bezier_segments)
    
    def __repr__(self) -> str:
        return (f"BoundaryCurve(segments={len(self.bezier_segments)}, "
                f"corners={len(self.corners)}, color={self.color.name}, "
                f"closed={self.is_closed})")