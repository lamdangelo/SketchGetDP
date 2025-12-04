"""
Usecase to convert geometry to Gmsh format.
Integrates boundary curves, point electrodes, and configuration to create a complete Gmsh model.
"""

import yaml
from typing import List, Tuple, Dict, Any
from pathlib import Path

from ...core.entities.boundary_curve import BoundaryCurve
from ...core.entities.point import Point
from ...core.entities.color import Color

from sketchgetdp.geometry.gmsh_toolbox import (
    initialize_gmsh,
    set_characteristic_mesh_length,
    mesh_and_save,
    show_model,
    finalize_gmsh
)
from ...interfaces.abstractions.boundary_curve_grouper_interface import BoundaryCurveGrouperInterface as BoundaryCurveGrouper
from ...interfaces.abstractions.boundary_curve_mesher_interface import BoundaryCurveMesherInterface as BoundaryCurveMesher
from ...interfaces.abstractions.point_electrode_mesher_interface import PointElectrodeMesherInterface as PointElectrodeMesher


class ConvertGeometryToGmsh:
    """
    Use case for converting geometry to Gmsh format.
    
    Follows the same dependency injection pattern as ConvertSVGToGeometry.
    """
    
    def __init__(
        self,
        boundary_curve_grouper: BoundaryCurveGrouper,
        boundary_curve_mesher: BoundaryCurveMesher,
        point_electrode_mesher: PointElectrodeMesher
    ):
        """
        Initialize the use case with required dependencies.
        
        Args:
            boundary_curve_grouper: Interface for grouping boundary curves by containment
            boundary_curve_mesher: Interface for meshing boundary curves
            point_electrode_mesher: Interface for meshing point electrodes
        """
        self.boundary_curve_grouper = boundary_curve_grouper
        self.boundary_curve_mesher = boundary_curve_mesher
        self.point_electrode_mesher = point_electrode_mesher
    
    def execute(
        self,
        boundary_curves: List[BoundaryCurve],
        point_electrodes: List[Tuple[Point, Color]],
        config_file_path: str,
        model_name: str = "geometry_model",
        output_filename: str = "geometry_mesh",
        dimension: int = 2,
        show_gui: bool = True
    ) -> dict:
        """
        Main use case to convert geometry to Gmsh format.
        
        Steps:
        1. Load configuration and extract mesh size
        2. Initialize Gmsh
        3. Set the mesh size from config
        4. Process point electrodes
        5. Group boundary curves with containment hierarchy
        6. Mesh boundary curves
        7. Synchronize before meshing
        8. Mesh and save
        9. Optionally show Gmsh GUI
        
        Args:
            boundary_curves: List of BoundaryCurve objects representing domain boundaries
            point_electrodes: List of (Point, Color) tuples representing electrodes
            config_file_path: Path to YAML configuration file for coil currents and mesh settings
            model_name: Name for the Gmsh model (default: "geometry_model")
            output_filename: Base filename for output mesh (without extension)
            dimension: Dimension of mesh (default: 2 for 2D)
            show_gui: Whether to open Gmsh GUI after meshing (default: True)
            
        Returns:
            Dictionary containing results from all processing steps
            
        Raises:
            ValueError: If input parameters are invalid
            FileNotFoundError: If config file doesn't exist
            KeyError: If required configuration is missing
        """
        # Input validation
        if not isinstance(boundary_curves, list):
            raise ValueError("boundary_curves must be a list")
        
        if not isinstance(point_electrodes, list):
            raise ValueError("point_electrodes must be a list")
        
        config_path = Path(config_file_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file_path}")
        
        if not boundary_curves:
            print("Warning: No boundary curves provided")
        
        # Step 1: Load configuration
        print(f"Loading configuration from: {config_file_path}")
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Extract mesh size from config (default to 0.1 if not specified)
        mesh_size = config.get('mesh_size', 0.1)
        print(f"Using mesh size from config: {mesh_size}")
        
        # Results dictionary to store outputs from each step
        results: Dict[str, Any] = {
            "model_name": model_name,
            "output_filename": output_filename,
            "mesh_size": mesh_size,
            "dimension": dimension,
            "config_file": config_file_path
        }
        
        try:
            # Step 2: Initialize Gmsh
            print(f"Initializing Gmsh with model name: {model_name}")
            factory = initialize_gmsh(model_name)
            results["factory_initialized"] = True
            
            # Step 3: Set mesh size from config
            print(f"Setting characteristic mesh length factor to: {mesh_size}")
            set_characteristic_mesh_length(mesh_size)
            results["mesh_size_set"] = True
            
            # Step 4: Process point electrodes
            print(f"Processing {len(point_electrodes)} point electrodes...")
            electrode_results = self.point_electrode_mesher.mesh_electrodes(
                factory,
                config_file_path,
                point_electrodes,
                point_size=mesh_size
            )
            results["electrode_results"] = electrode_results
            
            # Step 5: Group boundary curves with containment hierarchy
            print(f"Grouping {len(boundary_curves)} boundary curves...")
            grouping_result = self.boundary_curve_grouper.group_boundary_curves(boundary_curves)
            results["grouping_result"] = grouping_result
            
            # Step 6: Mesh boundary curves
            print("Meshing boundary curves...")
            self.boundary_curve_mesher.mesh_boundary_curves(factory, boundary_curves, grouping_result)
            results["boundary_mesher"] = self.boundary_curve_mesher
            
            # Step 7: Synchronize before meshing
            factory.synchronize()
            print("Geometry synchronized in Gmsh")
            results["geometry_synchronized"] = True
            
            # Step 8: Mesh and save
            print(f"Generating {dimension}D mesh...")
            mesh_and_save(output_filename, dimension)
            results["mesh_generated"] = True
            print(f"Mesh saved to: {output_filename}.msh")
            
            # Step 9: Show Gmsh GUI if requested
            if show_gui:
                print("Opening Gmsh GUI...")
                show_model()
                results["gui_shown"] = True
            
            return results
            
        except Exception as e:
            print(f"Error during geometry conversion: {e}")
            raise
            
        finally:
            # Clean up Gmsh resources
            finalize_gmsh()
            print("Gmsh finalized")