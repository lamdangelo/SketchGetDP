"""
Refines SVG paths by resampling, merging, and cleaning point sequences.
Post-processes SVG geometry for optimal representation.
"""

import math
from typing import Dict, List

from svg_to_getdp.core.entities.point import Point
from svg_to_getdp.core.entities.color import Color

from svg_to_getdp.infrastructure.svg_processing.raw_outline_assembler import RawOutline


class SvgPathRefiner:
    """
    Refines SVG paths through resampling, deduplication, and merging operations.
    """
    
    def __init__(self, points_per_unit_length: int = 1000):
        self.points_per_unit_length = points_per_unit_length
    
    def resample_all_raw_outlines(self, raw_outlines_by_color: Dict[Color, List[RawOutline]]) -> Dict[Color, List[RawOutline]]:
        """
        Apply uniform resampling to all raw_outlines except red dots.
        """
        resampled_raw_outlines = {}
        
        for color, raw_outlines in raw_outlines_by_color.items():
            resampled_raw_outlines[color] = []
            for raw_outline in raw_outlines:
                if color == Color.RED:
                    # Don't resample red dots (single points)
                    resampled_raw_outlines[color].append(raw_outline)
                else:
                    # Resample polylines for even point distribution
                    resampled_points = self._resample_polyline_uniform(raw_outline.points)
                    resampled_raw_outline = RawOutline(
                        points=resampled_points,
                        color=raw_outline.color,
                        is_closed=raw_outline.is_closed
                    )
                    resampled_raw_outlines[color].append(resampled_raw_outline)
        
        return resampled_raw_outlines
    
    def _resample_polyline_uniform(self, points: List[Point]) -> List[Point]:
        """
        Resample polyline to have evenly spaced points.
        
        Args:
            points: Original unevenly distributed points
            
        Returns:
            List of evenly spaced points
        """
        if len(points) < 2:
            return points
        
        # Calculate total length and segment lengths
        total_length = 0.0
        segment_lengths = []
        for i in range(len(points) - 1):
            segment_length = math.sqrt(
                (points[i+1].x - points[i].x)**2 + 
                (points[i+1].y - points[i].y)**2
            )
            segment_lengths.append(segment_length)
            total_length += segment_length
        
        if total_length <= 0:
            return points
        
        spacing = 1.0 / self.points_per_unit_length
        
        # Calculate how many points we need for each segment
        resampled_points = [points[0]]
        
        for segment_idx in range(len(segment_lengths)):
            segment_length = segment_lengths[segment_idx]
            segment_start = points[segment_idx]
            segment_end = points[segment_idx + 1]
            
            # Calculate how many points to place on this segment (excluding the start point)
            num_points_on_segment = max(1, int(segment_length / spacing))
            actual_spacing = segment_length / num_points_on_segment
            
            # Add points along this segment
            for i in range(1, num_points_on_segment):
                t = i * actual_spacing / segment_length
                new_x = segment_start.x + t * (segment_end.x - segment_start.x)
                new_y = segment_start.y + t * (segment_end.y - segment_start.y)
                resampled_points.append(Point(new_x, new_y))
            
            # Add the segment end point (unless it's the very last point of the polyline)
            if segment_idx < len(segment_lengths) - 1:
                resampled_points.append(segment_end)
        
        # Always include the very last point of the polyline
        if resampled_points[-1] != points[-1]:
            resampled_points.append(points[-1])
        
        return resampled_points
    
    def remove_consecutive_duplicate_points(self, points: List[Point]) -> List[Point]:
        """Remove consecutive duplicate points while preserving order."""
        if not points:
            return points
        
        unique_points = [points[0]]
        for current_point in points[1:]:
            if current_point != unique_points[-1]:
                unique_points.append(current_point)
        
        return unique_points
    
    def _remove_duplicate_end_point(self, points: List[Point]) -> List[Point]:
        """Remove closing duplicate point for closed paths."""
        if not points:
            return points

        # Check if path is closed (first and last points are the same)
        if len(points) > 1 and points[0] == points[-1]:
            # Remove the last point since it's a duplicate of the first
            points = points[:-1]
        
        return points
    
    def remove_duplicates_from_all_raw_outlines(self, raw_outlines_by_color: Dict[Color, List[RawOutline]]) -> Dict[Color, List[RawOutline]]:
        """
        Remove duplicate points from all raw_outlines after resampling.
        """
        cleaned_raw_outlines = {}
        
        for color, raw_outlines in raw_outlines_by_color.items():
            cleaned_raw_outlines[color] = []
            for raw_outline in raw_outlines:
                if color == Color.RED:
                    # For red dots (single points), no need to remove duplicates
                    cleaned_raw_outlines[color].append(raw_outline)
                else:
                    # Remove duplicate points from polyline raw_outlines
                    no_consecutive_duplicate_points = self.remove_consecutive_duplicate_points(raw_outline.points)
                    cleaned_points = self._remove_duplicate_end_point(no_consecutive_duplicate_points)
                    cleaned_raw_outline = RawOutline(
                        points=cleaned_points,
                        color=raw_outline.color,
                        is_closed=raw_outline.is_closed
                    )
                    cleaned_raw_outlines[color].append(cleaned_raw_outline)
        
        return cleaned_raw_outlines
    
    def merge_nearby_raw_outlines(self, raw_outlines_by_color: Dict[Color, List[RawOutline]], 
                                distance_threshold: float = 0.02) -> Dict[Color, List[RawOutline]]:
        """
        Merge raw_outlines of the same color that are close to each other and not already closed.
        
        Args:
            raw_outlines_by_color: Dictionary of raw_outlines grouped by color
            distance_threshold: Maximum distance between endpoints to consider for merging (in unit coordinates)
            
        Returns:
            Dictionary with merged raw_outlines
        """
        merged_raw_outlines = {}
        for color, raw_outlines in raw_outlines_by_color.items():
            if color == Color.RED:
                # Don't merge red dots (they're single points)
                merged_raw_outlines[color] = raw_outlines
                continue
            
            # Skip if only one raw_outline or all raw_outline are already closed
            if len(raw_outlines) <= 1 or all(o.is_closed for o in raw_outlines):
                merged_raw_outlines[color] = raw_outlines
                continue
            
            # Create a list of open raw_outlines to process
            open_raw_outlines = [o for o in raw_outlines if not o.is_closed]
            closed_raw_outlines = [o for o in raw_outlines if o.is_closed]
            
            # Try to merge open raw_outlines
            merged = self._merge_open_raw_outlines(open_raw_outlines, distance_threshold)
            
            # Combine merged raw_outlines with closed ones
            merged_raw_outlines[color] = closed_raw_outlines + merged
        
        return merged_raw_outlines
    
    def _merge_open_raw_outlines(self, open_raw_outlines: List[RawOutline], 
                              distance_threshold: float) -> List[RawOutline]:
        """
        Merge open raw_outlines by connecting endpoints that are close together.
        """
        if not open_raw_outlines:
            return []
        
        merged_raw_outlines = []
        processed = [False] * len(open_raw_outlines)
        
        for i, raw_outline in enumerate(open_raw_outlines):
            if processed[i]:
                continue
            
            # Start a new merged raw_outline with this one
            current_points = raw_outline.points.copy()
            start_point = current_points[0]
            end_point = current_points[-1]
            
            processed[i] = True
            merged_with_something = True
            
            # Keep trying to merge until no more merges are possible
            while merged_with_something:
                merged_with_something = False
                
                for j, other_raw_outline in enumerate(open_raw_outlines):
                    if processed[j]:
                        continue
                    
                    other_start = other_raw_outline.points[0]
                    other_end = other_raw_outline.points[-1]
                    
                    # Check for possible connections
                    start_to_start = self._distance_between_points(start_point, other_start)
                    start_to_end = self._distance_between_points(start_point, other_end)
                    end_to_start = self._distance_between_points(end_point, other_start)
                    end_to_end = self._distance_between_points(end_point, other_end)
                    
                    min_distance = min(start_to_start, start_to_end, end_to_start, end_to_end)
                    
                    if min_distance <= distance_threshold:
                        # Merge the raw_outlines
                        if min_distance == start_to_start:
                            # Reverse other raw_outline and prepend to current
                            other_points_reversed = other_raw_outline.points[::-1]
                            current_points = other_points_reversed + current_points[1:]
                            start_point = other_end  # After reversal, start becomes end
                        elif min_distance == start_to_end:
                            # Prepend other raw_outline to current
                            current_points = other_raw_outline.points[:-1] + current_points
                            start_point = other_start
                        elif min_distance == end_to_start:
                            # Append other raw_outline to current
                            current_points = current_points[:-1] + other_raw_outline.points
                            end_point = other_end
                        elif min_distance == end_to_end:
                            # Reverse other raw_outline and append to current
                            other_points_reversed = other_raw_outline.points[::-1]
                            current_points = current_points[:-1] + other_points_reversed
                            end_point = other_start  # After reversal, end becomes start
                        
                        processed[j] = True
                        merged_with_something = True
                        break
            
            # Check if the merged raw_outline is now closed
            is_closed = self._distance_between_points(start_point, end_point) <= distance_threshold
            
            if is_closed:
                # Ensure proper closure
                if self._distance_between_points(current_points[0], current_points[-1]) > distance_threshold:
                    current_points.append(current_points[0])
            
            merged_raw_outline = RawOutline(
                points=current_points,
                color=raw_outline.color,
                is_closed=is_closed
            )
            merged_raw_outlines.append(merged_raw_outline)
        
        return merged_raw_outlines
    
    def _distance_between_points(self, p1: Point, p2: Point) -> float:
        """Calculate Euclidean distance between two points."""
        return math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
    