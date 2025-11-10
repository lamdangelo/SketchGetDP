"""
Presentation layer service for visualizing Bézier curves and boundary curves.
"""

import matplotlib.pyplot as plt
from typing import List
from ...core.entities.boundary_curve import BoundaryCurve
from ...core.entities.point import Point


class CurveVisualizer:
    """Presentation service for visualizing boundary curves and Bézier segments."""
    
    @staticmethod
    def display_boundary_curves(boundary_curves: List[BoundaryCurve], 
                              point_electrodes: List[tuple] = None,
                              show_control_points: bool = True, 
                              show_corners: bool = True) -> None:
        """
        Display boundary curves in an interactive plot.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to plot
            point_electrodes: List of (Point, Color) tuples for point electrodes
            show_control_points: Whether to show Bézier control points
            show_corners: Whether to show detected corners
        """
        plt.figure(figsize=(12, 10))
        
        # Plot each boundary curve
        for i, curve in enumerate(boundary_curves):
            CurveVisualizer._plot_single_curve(curve, i, show_control_points, show_corners)
        
        # Plot point electrodes
        if point_electrodes:
            CurveVisualizer._plot_point_electrodes(point_electrodes)
        
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.title('Bézier Curves from SVG Conversion')
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
                        filename: str = 'bezier_curves_plot.png', **kwargs):
        """
        Save the plot to a file instead of displaying it.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to plot
            point_electrodes: List of (Point, Color) tuples for point electrodes  
            filename: Output filename
            **kwargs: Additional arguments for plot_boundary_curves
        """
        plt.figure(figsize=(12, 10))
        
        # Plot each boundary curve
        for i, curve in enumerate(boundary_curves):
            CurveVisualizer._plot_single_curve(curve, i, 
                                            kwargs.get('show_control_points', True),
                                            kwargs.get('show_corners', True))
        
        # Plot point electrodes
        if point_electrodes:
            CurveVisualizer._plot_point_electrodes(point_electrodes)
        
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.title('Bézier Curves from SVG Conversion')
        plt.xlabel('X coordinate')
        plt.ylabel('Y coordinate')
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Plot saved to {filename}")