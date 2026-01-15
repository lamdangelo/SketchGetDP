"""
Presentation layer service for visualizing Bézier curves and boundary curves.
"""

import matplotlib.pyplot as plt
import os
from datetime import datetime
from typing import List
from svg_to_getdp.core.entities.boundary_curve import BoundaryCurve
from svg_to_getdp.interfaces.debug.debug_coordinator import DebugCoordinator


class CurveVisualizer:
    """Presentation service for visualizing boundary curves, Bézier segments, and raw polylines."""
    
    @staticmethod
    def _plot_single_curve(curve: BoundaryCurve, curve_index: int, 
                        show_control_points: bool, show_corners: bool,
                        color_in_legend: dict, corner_color_in_legend: dict):
        """Plot a single boundary curve."""
        # Use the actual RGB values from the Color object
        rgb = curve.color.rgb
        plot_color = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)  # Normalize to 0-1 for matplotlib
        
        # Sample points along the entire curve
        t_values = [i/200 for i in range(201)]  # High resolution for smooth curves
        curve_points = [curve.evaluate(t) for t in t_values]
        
        x_curve = [p.x for p in curve_points]
        y_curve = [p.y for p in curve_points]
        
        # Determine label for the curve (only add to legend if not already added for this color)
        if curve.color.name not in color_in_legend:
            label = f'{curve.color.name} Curves'
            color_in_legend[curve.color.name] = True
        else:
            label = None
        
        # Plot the curve itself
        plt.plot(x_curve, y_curve, color=plot_color, linewidth=2, label=label)
        
        # Plot control points if requested
        if show_control_points:
            for seg_idx, segment in enumerate(curve.bezier_segments):
                cp_x = [p.x for p in segment.control_points]
                cp_y = [p.y for p in segment.control_points]
                
                # Plot control points without adding to legend
                plt.plot(cp_x, cp_y, 'o--', color=plot_color, alpha=0.7, 
                        linewidth=1, markersize=4)
        
        # Plot corners if requested
        if show_corners and curve.corners:
            corner_x = [c.x for c in curve.corners]
            corner_y = [c.y for c in curve.corners]
            
            # Only add corner label to legend if not already added for this color
            if curve.color.name not in corner_color_in_legend:
                corner_label = f'{curve.color.name} Corners'
                corner_color_in_legend[curve.color.name] = True
            else:
                corner_label = None
            
            plt.plot(corner_x, corner_y, 's', color=plot_color, 
                    markersize=10, markerfacecolor='none', markeredgewidth=2,
                    label=corner_label)
    
    @staticmethod
    def _plot_colored_boundaries(colored_boundaries: dict):
        """Plot colored polyline boundaries with lighter colors."""
        # Track which colors we've already added to the legend for raw boundaries
        raw_color_in_legend = {}
        raw_point_color_in_legend = {}
        
        for color, raw_boundaries in colored_boundaries.items():
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
                
                # Special handling for red dots (wires in raw form)
                if raw_boundary.color.name == 'RED' and len(raw_boundary.points) == 1:
                    # Use light red for single red points
                    light_red = (1.0, 0.7, 0.7)  # Light red
                    
                    # Only add to legend once for red points
                    if raw_boundary.color.name not in raw_point_color_in_legend:
                        label = 'Raw RED Points'
                        raw_point_color_in_legend[raw_boundary.color.name] = True
                    else:
                        label = None
                        
                    plt.plot(x_points, y_points, 'x', color=light_red, markersize=8,
                            markeredgewidth=1.5, alpha=0.7, label=label)
                else:
                    # For polylines, use lighter colors and thinner lines
                    # Only add to legend once per color for raw polylines
                    if raw_boundary.color.name not in raw_color_in_legend:
                        label = f'Raw {raw_boundary.color.name} Polylines'
                        raw_color_in_legend[raw_boundary.color.name] = True
                    else:
                        label = None
                        
                    plt.plot(x_points, y_points, linestyle, color=plot_color, 
                            linewidth=1.0, alpha=0.6, marker='.', markersize=4,
                            label=label)
    
    @staticmethod
    def _plot_wires(wires: List[tuple]):
        """Plot point wires."""
        # Track which wire colors we've already added to the legend
        wire_color_in_legend = {}
        
        for point, color in wires:
            # Use the actual RGB values from the Color object
            rgb = color.rgb
            plot_color = (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)  # Normalize to 0-1 for matplotlib

            # Only add wire label to legend once per color
            if color.name not in wire_color_in_legend:
                label = f'{color.name} Wires'
                wire_color_in_legend[color.name] = True
            else:
                label = None
                
            plt.plot(point.x, point.y, 'X', color=plot_color, markersize=12,
                    markeredgewidth=3, label=label)
    
    @staticmethod
    def save_plot_to_file(boundary_curves: List[BoundaryCurve], wires: List[tuple] = None,
                        colored_boundaries: dict = None,
                        filename: str = 'bezier_curves_plot.png', **kwargs):
        """
        Save the plot to a file.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to plot
            wires: List of (Point, Color) tuples for wires  
            colored_boundaries: Dictionary of {color: List[RawBoundary]} objects to plot
            filename: Output filename
            **kwargs: Additional arguments for plot_boundary_curves
        """
        plt.figure(figsize=(12, 10))
        
        # Track which colors we've already added to the legend
        color_in_legend = {}
        corner_color_in_legend = {}
        
        # Plot each boundary curve
        for i, curve in enumerate(boundary_curves):
            CurveVisualizer._plot_single_curve(curve, i, 
                                            kwargs.get('show_control_points', True),
                                            kwargs.get('show_corners', True),
                                            color_in_legend, corner_color_in_legend)
        
        # Plot colored boundaries (polylines) if requested
        if colored_boundaries and kwargs.get('show_raw_boundaries', True):
            CurveVisualizer._plot_colored_boundaries(colored_boundaries)
        
        # Plot wires
        if wires:
            CurveVisualizer._plot_wires(wires)
        
        plt.grid(True, alpha=0.3)
        plt.axis('equal')
        plt.title('Bézier Curves and Polylines from SVG Conversion')
        plt.xlabel('X coordinate')
        plt.ylabel('Y coordinate')
        plt.legend()
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Geometry debug plot saved to: {filename}")
    
    @staticmethod
    def save_plot_to_debug_directory(boundary_curves: List[BoundaryCurve], svg_file_path: str, 
                                   wires: List[tuple] = None, colored_boundaries: dict = None,
                                   timestamp: str = None, **kwargs) -> str:
        """
        Save geometry plot to debug directory with timestamped filename.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to plot
            svg_file_path: Path to the original SVG file (for naming)
            wires: List of (Point, Color) tuples for wires
            colored_boundaries: Dictionary of {color: List[RawBoundary]} objects to plot
            timestamp: Optional timestamp string (if None, generates new)
            **kwargs: Additional arguments for the plot
            
        Returns:
            Path to the saved plot file
        """
        # Create debug directory if it doesn't exist
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        
        # Create debug filename based on input SVG filename and timestamp
        svg_filename = os.path.basename(svg_file_path)
        svg_name = os.path.splitext(svg_filename)[0]
        
        # Use provided timestamp or generate new one
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        debug_filename = f"{debug_dir}/geometry_plot_{svg_name}_{timestamp}.png"
        
        # Save the plot to the debug directory
        CurveVisualizer.save_plot_to_file(
            boundary_curves=boundary_curves,
            wires=wires,
            colored_boundaries=colored_boundaries,
            filename=debug_filename,
            **kwargs
        )
        
        return debug_filename
    
    @classmethod
    def save_plot_with_coordinator(cls, boundary_curves: List[BoundaryCurve], 
                                 coordinator: DebugCoordinator,
                                 wires: List[tuple] = None, 
                                 colored_boundaries: dict = None,
                                 **kwargs) -> str:
        """
        Save plot using a DebugCoordinator for consistent naming.
        
        Args:
            boundary_curves: List of BoundaryCurve objects to plot
            coordinator: DebugCoordinator instance
            wires: List of (Point, Color) tuples for wires
            colored_boundaries: Dictionary of {color: List[RawBoundary]} objects to plot
            **kwargs: Additional arguments for the plot
            
        Returns:
            Path to the saved plot file
        """
        plot_filename = coordinator.get_debug_plot_filename("geometry_plot", ".png")
        
        # Save the plot to the debug directory
        cls.save_plot_to_file(
            boundary_curves=boundary_curves,
            wires=wires,
            colored_boundaries=colored_boundaries,
            filename=plot_filename,
            **kwargs
        )
        
        return plot_filename
    