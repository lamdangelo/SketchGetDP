"""
Debug data recording functionality for corner detection.
"""

import numpy as np
from typing import List, Dict
from svg_to_getdp.core.entities.point import Point


class DebugRecorder:
    """Handles debug data recording for corner detection."""
    
    def __init__(self, debug_enabled: bool = True):
        self.debug_enabled = debug_enabled
    
    def initialize_debug_data(self) -> Dict:
        """Initialize the debug data structure."""
        return {
            'shape_analysis': {},
            'candidate_detection': {},
            'strength_calculations': {},
            'clustering': {},
            'refinement_details': [],
            'final_decisions': {},
            'all_steps': []
        }
    
    def record_debug_step(self, debug_data: Dict, message: str) -> None:
        """Record a debug step if debugging is enabled."""
        if self.debug_enabled:
            debug_data['all_steps'].append(message)
    
    def record_bounding_box_info(
        self, 
        x_coordinates: np.ndarray, 
        y_coordinates: np.ndarray, 
        debug_data: Dict
    ) -> None:
        """Record bounding box information for debugging."""
        debug_data['shape_analysis']['bounding_box'] = {
            'x_min': float(np.min(x_coordinates)),
            'x_max': float(np.max(x_coordinates)),
            'y_min': float(np.min(y_coordinates)),
            'y_max': float(np.max(y_coordinates)),
            'width': float(np.max(x_coordinates) - np.min(x_coordinates)),
            'height': float(np.max(y_coordinates) - np.min(y_coordinates))
        }
    
    def record_final_results(
        self, 
        outline_points: List[Point], 
        final_corners: List[int], 
        debug_data: Dict,
        candidate_strengths: Dict[int, float]
    ) -> None:
        """Record final corner detection results for debugging."""
        debug_data['final_decisions']['final_corners'] = final_corners
        debug_data['final_decisions']['corner_coordinates'] = {
            idx: outline_points[idx] for idx in final_corners
        }
        debug_data['final_decisions']['corner_strengths'] = {
            idx: candidate_strengths.get(idx, 0) for idx in final_corners
        }
        