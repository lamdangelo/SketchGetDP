from datetime import datetime
from typing import List
from sketchgetdp.svg_to_getdp.core.entities.outline import Outline
from svg_to_getdp.interfaces.debug.debug_coordinator import DebugCoordinator


class CornerDetectorDebugWriter(DebugCoordinator):
    """Handles writing debug information for corner detection."""
    
    def __init__(self):
        super().__init__()
    
    def write_corner_detection_debug_info(self, svg_file_path: str, 
                                          corner_debug_data: dict,
                                          outlines: List[Outline] = None):
        """
        Write detailed corner detection debug information.
        """
        self.set_svg_file(svg_file_path)
        debug_filename = self.get_debug_filename("corner_detection_debug", ".txt")
        
        with open(debug_filename, 'w') as f:
            self._write_corner_detection_header(f, svg_file_path, corner_debug_data)
            
            # Check if we have data
            if not corner_debug_data:
                f.write("\nNO CORNER DEBUG DATA AVAILABLE\n")
                return
            
            # Process each outline
            for key, data in corner_debug_data.items():
                self._write_outline_corner_analysis(f, key, data, outlines)
        
        print(f"Corner detection debug information written to: {debug_filename}")
    
    def write_detailed_decision_process(self, svg_file_path: str, corner_debug_data: dict):
        """
        Write even more detailed decision process for advanced debugging.
        """
        detailed_filename = self.get_debug_filename(svg_file_path, "corner_decisions_detailed", ".txt")
        
        with open(detailed_filename, 'w') as f:
            f.write("DETAILED CORNER DETECTION DECISION PROCESS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Input SVG: {svg_file_path}\n")
            f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Debug run timestamp: {self.get_shared_timestamp()}\n")
            f.write(f"Total outlines analyzed: {len(corner_debug_data)}\n\n")
            
            for key, data in corner_debug_data.items():
                f.write(f"\n{'='*100}\n")
                f.write(f"DETAILED PROCESS FOR: {key}\n")
                f.write(f"{'='*100}\n\n")
                
                # Write extremely detailed information
                self._write_extremely_detailed_analysis(f, data)
        
        print(f"Detailed decision process written to: {detailed_filename}")
    
    def _write_corner_detection_header(self, f, svg_file_path: str, corner_debug_data: dict):
        """Write header for corner detection debug file."""
        f.write("CORNER DETECTION DEBUG INFORMATION\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Input SVG: {svg_file_path}\n")
        f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Debug run timestamp: {self.get_shared_timestamp()}\n")
        f.write(f"Total outlines analyzed: {len(corner_debug_data) if corner_debug_data else 0}\n\n")
    
    def _write_outline_corner_analysis(self, f, key: str, data: dict, outlines: List[Outline]):
        """Write detailed analysis for a single outline."""
        f.write(f"\n{'='*80}\n")
        f.write(f"OUTLINE ANALYSIS: {key}\n")
        f.write(f"{'='*80}\n\n")
        
        # Basic info - with safety checks
        f.write(f"Basic Information:\n")
        f.write(f"  Color: {data.get('color', 'N/A')}\n")
        f.write(f"  Outline Index: {data.get('outline_index', 'N/A')}\n")
        f.write(f"  Total Points: {data.get('points_count', 'N/A')}\n")
        f.write(f"  Is Closed: {data.get('is_closed', 'N/A')}\n")
        f.write(f"  Final Corners: {len(data.get('corner_indices', []))}\n\n")
        
        debug_info = data.get('debug', {})
        
        if not debug_info:
            f.write("NO DEBUG INFO AVAILABLE FOR THIS OUTLINE\n\n")
            return
        
        # Shape analysis
        self._write_shape_analysis(f, debug_info.get('shape_analysis', {}))
        
        # Candidate detection
        self._write_candidate_detection(f, debug_info.get('candidate_detection', {}))
        
        # Strength calculations
        self._write_strength_calculations(f, debug_info.get('strength_calculations', {}))
        
        # Clustering
        self._write_clustering_info(f, debug_info.get('clustering', {}))
        
        # Refinement - handle the new structure
        refinement_details = debug_info.get('refinement_details', [])
        clustering_info = debug_info.get('clustering', {})
        self._write_refinement_info(f, refinement_details, clustering_info)
        
        # Final decisions
        self._write_final_decisions(f, debug_info.get('final_decisions', {}))
        
        # Process steps
        self._write_process_steps(f, debug_info.get('all_steps', []))
    
    def _write_shape_analysis(self, f, shape_info: dict):
        """Write shape analysis section."""
        f.write("SHAPE ANALYSIS:\n")
        
        if 'early_ellipse_detection' in shape_info and shape_info['early_ellipse_detection']:
            f.write(f"  ❌ EARLY REJECTION: {shape_info.get('ellipse_reason', 'Ellipse detected')}\n")
            return
        
        if 'too_smooth' in shape_info and shape_info['too_smooth']:
            f.write(f"  ❌ REJECTION: Shape too smooth (score={shape_info.get('smoothness_score', 0):.3f})\n")
            return
        
        if 'too_small' in shape_info and shape_info['too_small']:
            f.write(f"  ❌ REJECTION: Shape too small for analysis\n")
            return
        
        if 'small_ellipse' in shape_info and shape_info['small_ellipse']:
            f.write(f"  ❌ REJECTION: Small ellipse detected\n")
            return
        
        f.write(f"  Smoothness Score: {shape_info.get('smoothness_score', 'N/A')}\n")
        f.write(f"  Is Ellipse: {shape_info.get('is_ellipse', 'N/A')}\n")
        
        if 'bounding_box' in shape_info:
            bbox = shape_info['bounding_box']
            f.write(f"  Bounding Box:\n")
            f.write(f"    X: [{bbox['x_min']:.6f}, {bbox['x_max']:.6f}] (width: {bbox['width']:.6f})\n")
            f.write(f"    Y: [{bbox['y_min']:.6f}, {bbox['y_max']:.6f}] (height: {bbox['height']:.6f})\n")
        
        f.write("\n")
    
    def _write_candidate_detection(self, f, cand_info: dict):
        """Write candidate detection section."""
        f.write("CANDIDATE DETECTION:\n")
        
        angle_corners = cand_info.get('angle_method', [])
        direction_corners = cand_info.get('direction_method', [])
        curvature_corners = cand_info.get('curvature_method', [])
        all_candidates = cand_info.get('all_candidates', [])
        
        f.write(f"  Method Results:\n")
        f.write(f"    Angle Method:      {len(angle_corners):3d} candidates\n")
        f.write(f"    Direction Method:  {len(direction_corners):3d} candidates\n")
        f.write(f"    Curvature Method:  {len(curvature_corners):3d} candidates\n")
        f.write(f"    Total Unique:      {len(all_candidates):3d} candidates\n\n")
        
        # Show combined votes if available
        if 'combined_votes' in cand_info:
            combined = cand_info['combined_votes']
            if combined:
                f.write(f"  Combined Votes (Top 20):\n")
                sorted_votes = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:20]
                for idx, votes in sorted_votes:
                    f.write(f"    Point {idx:4d}: {votes:.2f} votes\n")
                f.write("\n")
        
        # Show coarse corners
        coarse_corners = cand_info.get('coarse_corners', [])
        if coarse_corners:
            f.write(f"  Coarse Corners (after initial filtering): {len(coarse_corners)}\n")
            f.write(f"    Indices: {sorted(coarse_corners)}\n")
        f.write("\n")
    
    def _write_strength_calculations(self, f, strengths: dict):
        """Write strength calculations section."""
        if not strengths:
            return
        
        f.write("CORNER STRENGTH CALCULATIONS:\n")
        
        # Show top strengths
        if len(strengths) <= 30:
            f.write(f"  All Candidate Strengths:\n")
            sorted_strengths = sorted(strengths.items(), key=lambda x: x[1], reverse=True)
            for idx, strength in sorted_strengths:
                f.write(f"    Point {idx:4d}: strength={strength:.3f}\n")
        else:
            f.write(f"  Top 30 Candidate Strengths:\n")
            sorted_strengths = sorted(strengths.items(), key=lambda x: x[1], reverse=True)[:30]
            for idx, strength in sorted_strengths:
                f.write(f"    Point {idx:4d}: strength={strength:.3f}\n")
        
        f.write("\n")
    
    def _write_clustering_info(self, f, clustering_info: dict):
        """Write clustering information section."""
        clusters = clustering_info.get('clusters', [])
        if not clusters:
            return
        
        f.write("CLUSTERING RESULTS:\n")
        f.write(f"  Number of clusters: {len(clusters)}\n")
        
        for i, cluster in enumerate(clusters):
            f.write(f"  Cluster {i}: {cluster}\n")
            if len(cluster) > 1:
                f.write(f"    Size: {len(cluster)} candidates\n")
                f.write(f"    Range: {min(cluster)} to {max(cluster)} "
                       f"(span: {max(cluster) - min(cluster)} points)\n")
        
        f.write("\n")
    
    def _write_refinement_info(self, f, refinement_details: list, clustering_info: dict):
        """Write refinement information section."""
        if not refinement_details:
            f.write("REFINEMENT PROCESS:\n")
            f.write("  No refinement details available\n\n")
            return
        
        f.write("REFINEMENT PROCESS:\n")
        
        for i, cluster_info in enumerate(refinement_details):
            f.write(f"  Cluster {i}:\n")
            f.write(f"    Candidates: {cluster_info.get('cluster', [])}\n")
            f.write(f"    Best Candidate: {cluster_info.get('best_candidate', 'N/A')}\n")
            f.write(f"    Refined To: {cluster_info.get('refined_candidate', 'N/A')}\n")
            if 'refined_strength' in cluster_info:
                f.write(f"    Refined Strength: {cluster_info['refined_strength']:.3f}\n")
            if 'accepted' in cluster_info:
                f.write(f"    Accepted: {cluster_info['accepted']}\n")
        
        if 'refined_corners' in clustering_info:
            refined = clustering_info.get('refined_corners', [])
            f.write(f"\n  Refinement Results:\n")
            f.write(f"    Refined Corners: {refined}\n")
            f.write(f"    Count: {len(refined)}\n")
        
        if 'quality_corners' in clustering_info:
            quality = clustering_info.get('quality_corners', [])
            f.write(f"    Quality Corners: {quality}\n")
            f.write(f"    Count: {len(quality)}\n")
        
        f.write("\n")
    
    def _write_final_decisions(self, f, final_info: dict):
        """Write final decisions section."""
        final_corners = final_info.get('final_corners', [])
        corner_coords = final_info.get('corner_coordinates', {})
        corner_strengths = final_info.get('corner_strengths', {})
        
        f.write("FINAL DECISIONS:\n")
        f.write(f"  Total Final Corners: {len(final_corners)}\n")
        
        if final_corners:
            f.write(f"  Final Corner Indices: {sorted(final_corners)}\n\n")
            
            f.write(f"  Corner Details:\n")
            for idx in sorted(final_corners):
                point = corner_coords.get(idx)
                strength = corner_strengths.get(idx, 0)
                if point:
                    f.write(f"    Point {idx:4d}: ({point.x:.6f}, {point.y:.6f}) "
                           f"[strength={strength:.3f}]\n")
        
        f.write("\n")
    
    def _write_process_steps(self, f, steps: list):
        """Write process steps section."""
        if not steps:
            return
        
        f.write("PROCESS STEPS:\n")
        for i, step in enumerate(steps, 1):
            f.write(f"  {i:3d}. {step}\n")
        f.write("\n")
    
    def _write_extremely_detailed_analysis(self, f, data: dict):
        """Write extremely detailed analysis for a outline."""
        debug_info = data['debug']
        
        # Write complete shape analysis
        shape_info = debug_info.get('shape_analysis', {})
        f.write("COMPLETE SHAPE ANALYSIS:\n")
        for key, value in shape_info.items():
            if key != 'bounding_box':
                f.write(f"  {key}: {value}\n")
        
        if 'bounding_box' in shape_info:
            bbox = shape_info['bounding_box']
            f.write(f"  bounding_box:\n")
            for bkey, bvalue in bbox.items():
                f.write(f"    {bkey}: {bvalue}\n")
        f.write("\n")
        
        # Write complete candidate information
        cand_info = debug_info.get('candidate_detection', {})
        if 'angle_method' in cand_info:
            f.write(f"Angle Method Candidates ({len(cand_info['angle_method'])}):\n")
            f.write(f"  {cand_info['angle_method']}\n")
        
        if 'direction_method' in cand_info:
            f.write(f"\nDirection Method Candidates ({len(cand_info['direction_method'])}):\n")
            f.write(f"  {cand_info['direction_method']}\n")
        
        if 'curvature_method' in cand_info:
            f.write(f"\nCurvature Method Candidates ({len(cand_info['curvature_method'])}):\n")
            f.write(f"  {cand_info['curvature_method']}\n")
        
        if 'all_candidates' in cand_info:
            f.write(f"\nAll Unique Candidates ({len(cand_info['all_candidates'])}):\n")
            f.write(f"  {sorted(cand_info['all_candidates'])}\n")
        
        f.write("\n")
        
        # Write all strength calculations
        strengths = debug_info.get('strength_calculations', {})
        if strengths:
            f.write("ALL STRENGTH CALCULATIONS:\n")
            for idx, strength in sorted(strengths.items()):
                f.write(f"  Point {idx:4d}: {strength:.6f}\n")
            f.write("\n")
        
        # Write decision steps
        steps = debug_info.get('all_steps', [])
        if steps:
            f.write("DECISION STEPS:\n")
            for step in steps:
                f.write(f"  {step}\n")
            f.write("\n")
            