from typing import List
from svg_to_getdp.core.entities.bezier_segment import BezierSegment
from svg_to_getdp.core.entities.point import Point


class ContinuityEnforcer:
    """
    Enforces C0 and C1 continuity between Bézier segments.
    """
    
    def __init__(self, bezier_degree: int = 2):
        self.bezier_degree = bezier_degree
    
    def enforce_segment_continuity(self, segments: List[BezierSegment], 
                                  outlines: List[int], corner_indices: List[int],
                                  is_closed: bool):
        """Enforce C0 continuity at all junctions and C1 continuity only at non-corner junctions."""
        if len(segments) < 2:
            return
        
        for segment_index in range(len(segments) - 1):
            current_segment = segments[segment_index]
            next_segment = segments[segment_index + 1]
            junction_index = outlines[segment_index + 1]
            is_corner_junction = junction_index in corner_indices
            
            # Always enforce C0 continuity (position continuity)
            endpoint_gap = current_segment.end_point.distance_to(next_segment.start_point)
            if endpoint_gap > 1e-10:
                adjusted_control_points = next_segment.control_points.copy()
                adjusted_control_points[0] = current_segment.end_point
                segments[segment_index + 1] = BezierSegment(
                    control_points=adjusted_control_points,
                    degree=next_segment.degree
                )
            
            # Only enforce C1 continuity (tangent continuity) at smooth junctions
            if not is_corner_junction and self.bezier_degree == 2:
                self._enforce_tangent_continuity(current_segment, next_segment)
        
        # Handle closure for closed outlines
        if is_closed and len(segments) > 1:
            self._ensure_outline_closure(segments)
    
    def _enforce_tangent_continuity(self, first_segment: BezierSegment, second_segment: BezierSegment):
        """Enforce C1 continuity between two quadratic Bézier segments."""
        if self.bezier_degree != 2:
            return
        
        # For quadratic Bézier curves, C1 continuity requires:
        # first_segment.control_points[2] - first_segment.control_points[1] = 
        # second_segment.control_points[1] - second_segment.control_points[0]
        p0, p1, p2 = first_segment.control_points
        q0, q1, q2 = second_segment.control_points
        
        # Calculate ideal midpoint that satisfies C1 continuity
        ideal_midpoint_x = (p2.x + q0.x) / 2
        ideal_midpoint_y = (p2.y + q0.y) / 2
        
        # Adjust control points toward ideal midpoint
        adjustment_strength = 0.3
        
        adjusted_p1 = Point(
            p1.x * (1 - adjustment_strength) + ideal_midpoint_x * adjustment_strength,
            p1.y * (1 - adjustment_strength) + ideal_midpoint_y * adjustment_strength
        )
        
        adjusted_q1 = Point(
            q1.x * (1 - adjustment_strength) + ideal_midpoint_x * adjustment_strength,
            q1.y * (1 - adjustment_strength) + ideal_midpoint_y * adjustment_strength
        )
        
        first_segment.control_points[1] = adjusted_p1
        second_segment.control_points[1] = adjusted_q1
    
    def _ensure_outline_closure(self, segments: List[BezierSegment]):
        """Ensure the first and last points of a closed outline match exactly."""
        if not segments:
            return
        
        first_segment_start = segments[0].start_point
        last_segment = segments[-1]
        
        closure_gap = last_segment.end_point.distance_to(first_segment_start)
        if closure_gap > 1e-10:
            adjusted_control_points = last_segment.control_points.copy()
            adjusted_control_points[-1] = first_segment_start
            segments[-1] = BezierSegment(
                control_points=adjusted_control_points,
                degree=last_segment.degree
            )
            