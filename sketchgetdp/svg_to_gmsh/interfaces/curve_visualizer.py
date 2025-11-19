"""
Presentation layer service for visualizing Bézier curves and boundary curves.
"""

import matplotlib.pyplot as plt
from typing import List
from ..core.entities.boundary_curve import BoundaryCurve
from ..infrastructure.svg_parser import RawBoundary 


class CurveVisualizer:
    """Presentation service for visualizing boundary curves, Bézier segments, and raw polylines."""
    
    @staticmethod
    def display_boundary_curves(boundary_curves: List[BoundaryCurve], 
                              point_electrodes: List[tuple] = None,
                              raw_boundaries: List[RawBoundary] = None,
                              show_control_points: bool = True, 
                              show_corners: bool = True,
                              show_raw_boundaries: bool = True) -> None:
        """
        Display boundary curves in an interactive plot.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to plot
            point_electrodes: List of (Point, Color) tuples for point electrodes
            raw_boundaries: List of RawBoundary objects (polylines) to plot
            show_control_points: Whether to show Bézier control points
            show_corners: Whether to show detected corners
            show_raw_boundaries: Whether to show raw polyline boundaries
        """
        plt.figure(figsize=(12, 10))
        
        # Plot each boundary curve
        for i, curve in enumerate(boundary_curves):
            CurveVisualizer._plot_single_curve(curve, i, show_control_points, show_corners)
        
        # Plot raw boundaries (polylines) if requested
        if raw_boundaries and show_raw_boundaries:
            CurveVisualizer._plot_raw_boundaries(raw_boundaries)
        
        # Plot point electrodes
        if point_electrodes:
            CurveVisualizer._plot_point_electrodes(point_electrodes)
        
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.title('Bézier Curves and Polylines from SVG Conversion')
        plt.xlabel('X coordinate')
        plt.ylabel('Y coordinate')
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def _plot_single_curve(curve: BoundaryCurve, curve_index: int, 
                        show_control_points: bool, show_corners: bool):
        """Plot a single boundary curve."""
        # Use the actual RGB values from the Color object
        rgb = curve.color.rgb
        plot_color = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)  # Normalize to 0-1 for matplotlib
        
        # Sample points along the entire curve
        t_values = [i/200 for i in range(201)]  # High resolution for smooth curves
        curve_points = [curve.evaluate(t) for t in t_values]
        
        x_curve = [p.x for p in curve_points]
        y_curve = [p.y for p in curve_points]
        
        # Plot the curve itself
        plt.plot(x_curve, y_curve, color=plot_color, linewidth=2, 
                label=f'{curve.color.name} Curve {curve_index+1}')
        
        # Plot control points if requested
        if show_control_points:
            for seg_idx, segment in enumerate(curve.bezier_segments):
                cp_x = [p.x for p in segment.control_points]
                cp_y = [p.y for p in segment.control_points]
                
                # Plot control points
                plt.plot(cp_x, cp_y, 'o--', color=plot_color, alpha=0.7, 
                        linewidth=1, markersize=4)
                
                # Annotate control points
                for cp_idx, (x, y) in enumerate(zip(cp_x, cp_y)):
                    plt.annotate(f'S{seg_idx}P{cp_idx}', (x, y), 
                            xytext=(5, 5), textcoords='offset points', 
                            fontsize=8, alpha=0.7)
        
        # Plot corners if requested
        if show_corners and curve.corners:
            corner_x = [c.x for c in curve.corners]
            corner_y = [c.y for c in curve.corners]
            plt.plot(corner_x, corner_y, 's', color=plot_color, 
                    markersize=10, markerfacecolor='none', markeredgewidth=2,
                    label=f'{curve.color.name} Corners')
    
    @staticmethod
    def _plot_raw_boundaries(raw_boundaries: List[RawBoundary]):
        """Plot raw polyline boundaries with lighter colors."""
        for i, raw_boundary in enumerate(raw_boundaries):
            rgb = raw_boundary.color.rgb
            
            # Create lighter colors by blending with white
            light_factor = 0.6  # 0.0 = original color, 1.0 = white
            plot_color = (
                (1 - light_factor) * (rgb[0] / 255.0) + light_factor,
                (1 - light_factor) * (rgb[1] / 255.0) + light_factor,
                (1 - light_factor) * (rgb[2] / 255.0) + light_factor
            )
            
            x_points = [p.x for p in raw_boundary.points]
            y_points = [p.y for p in raw_boundary.points]
            
            if raw_boundary.is_closed and len(raw_boundary.points) > 1:
                x_points.append(raw_boundary.points[0].x)
                y_points.append(raw_boundary.points[0].y)
            
            # Plot the polyline with lighter styling
            linestyle = '-' if raw_boundary.is_closed else '--'
            
            # Special handling for red dots (point electrodes in raw form)
            if raw_boundary.color.name == 'RED' and len(raw_boundary.points) == 1:
                # Use light red for single red points
                light_red = (1.0, 0.7, 0.7)  # Light red
                plt.plot(x_points, y_points, 'x', color=light_red, markersize=8,
                        markeredgewidth=1.5, alpha=0.7, 
                        label=f'Raw {raw_boundary.color.name} Point')
            else:
                # For polylines, use lighter colors and thinner lines
                plt.plot(x_points, y_points, linestyle, color=plot_color, 
                        linewidth=1.0, alpha=0.6, marker='.', markersize=4,
                        label=f'Raw {raw_boundary.color.name} Polyline {i+1}')
                
    @staticmethod
    def _plot_point_electrodes(point_electrodes: List[tuple]):
        """Plot point electrodes."""        
        for point, color in point_electrodes:
            # Use the actual RGB values from the Color object
            rgb = color.rgb
            plot_color = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)  # Normalize to 0-1 for matplotlib
    
            plt.plot(point.x, point.y, 'X', color=plot_color, markersize=12,
                    markeredgewidth=3, label=f'{color.name} Electrode')
    
    @staticmethod
    def save_plot_to_file(boundary_curves: List[BoundaryCurve], point_electrodes: List[tuple] = None,
                        raw_boundaries: List[RawBoundary] = None,
                        filename: str = 'bezier_curves_plot.png', **kwargs):
        """
        Save the plot to a file instead of displaying it.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to plot
            point_electrodes: List of (Point, Color) tuples for point electrodes  
            raw_boundaries: List of RawBoundary objects (polylines) to plot
            filename: Output filename
            **kwargs: Additional arguments for plot_boundary_curves
        """
        plt.figure(figsize=(12, 10))
        
        # Plot each boundary curve
        for i, curve in enumerate(boundary_curves):
            CurveVisualizer._plot_single_curve(curve, i, 
                                            kwargs.get('show_control_points', True),
                                            kwargs.get('show_corners', True))
        
        # Plot raw boundaries (polylines) if requested
        if raw_boundaries and kwargs.get('show_raw_boundaries', True):
            CurveVisualizer._plot_raw_boundaries(raw_boundaries)
        
        # Plot point electrodes
        if point_electrodes:
            CurveVisualizer._plot_point_electrodes(point_electrodes)
        
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.title('Bézier Curves and Polylines from SVG Conversion')
        plt.xlabel('X coordinate')
        plt.ylabel('Y coordinate')
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {filename}")