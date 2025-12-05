"""
Use case for running GetDP magnetostatic simulations.
This follows clean architecture principles by separating business logic from external dependencies.
"""

import yaml
from typing import Optional
import numpy as np
from sketchgetdp.solver.getdp_toolbox import (
    print_data_to_pro,
    run_magnetostatic_simulation,
    physical_identifiers
)

# Add Gmsh import
try:
    import gmsh
    GMSH_AVAILABLE = True
except ImportError:
    GMSH_AVAILABLE = False
    gmsh = None


class RunGetDPSimulation:
    """
    Use case for running GetDP magnetostatic simulations.
    
    This class encapsulates the business logic for configuring and running
    GetDP simulations following the specified steps.
    """
    
    def __init__(self):
        """Initialize the use case with default values."""
        self.physical_values = None
        
    def execute(
        self,
        mesh_name: str,
        use_config_yaml: bool = False,
        config_yaml_path: Optional[str] = None,
        show_simulation_result: bool = True
    ) -> None:
        """
        Execute the GetDP simulation use case.
        
        Parameters:
        -----------
        mesh_name : str
            Name of the mesh model (without .msh extension)
        use_config_yaml : bool
            Whether to use config.yaml to update rmvp_formulation.pro file
        config_yaml_path : Optional[str]
            Path to the config.yaml file (optional, defaults to 'config.yaml')
        show_simulation_result : bool
            Whether to show the simulation result in Gmsh GUI
        """
        # Step 0: Initialize Gmsh if needed
        self._initialize_gmsh()
        
        # Step 1: Handle mesh name
        if not mesh_name.endswith('.msh'):
            mesh_name = f"{mesh_name}.msh"
        
        # Step 2: Handle config.yaml if requested
        config_data = {}
        if use_config_yaml:
            config_path = config_yaml_path if config_yaml_path else 'config.yaml'
            config_data = self._load_config_yaml(config_path)
        
        # Step 3: Define physical values
        self._define_physical_values(config_data if use_config_yaml else None)
        
        # Step 4: Set physical identifiers
        phys_ids = physical_identifiers()
        print_data_to_pro("physical_identifiers", phys_ids)
        
        # Step 5: Set physical values
        print_data_to_pro("physical_values", self.physical_values)
        
        # Step 6: Run simulation (always uses rmvp_formulation.pro)
        self._run_simulation(mesh_name, show_simulation_result)
        
        # Step 7: Finalize Gmsh if we initialized it
        if hasattr(self, '_gmsh_initialized_by_us') and self._gmsh_initialized_by_us:
            if GMSH_AVAILABLE and gmsh.isInitialized():
                gmsh.finalize()
    
    def _initialize_gmsh(self) -> None:
        """
        Initialize Gmsh if it's not already initialized.
        """
        if not GMSH_AVAILABLE:
            raise ImportError("Gmsh is not available. Please install python-gmsh package.")
        
        if not gmsh.isInitialized():
            gmsh.initialize()
            self._gmsh_initialized_by_us = True
            print("Gmsh initialized for GetDP simulation")
        else:
            self._gmsh_initialized_by_us = False
    
    def _load_config_yaml(self, config_path: str) -> dict:
        """
        Load configuration from YAML file.
        
        Parameters:
        -----------
        config_path : str
            Path to the config.yaml file
            
        Returns:
        --------
        dict: Configuration data
        """
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Warning: Config file {config_path} not found. Using default values.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            return {}
    
    def _define_physical_values(self, config_data: Optional[dict] = None) -> None:
        """
        Define physical values for the simulation.
        
        Parameters:
        -----------
        config_data : Optional[dict]
            Configuration data from YAML file
        """
        mu0 = 4e-7 * np.pi  # Vacuum permeability
        
        self.physical_values = {
            "Isource": 1,  # Default current source [A]
            "mu0": mu0,  # Vacuum permeability [H/m]
            "nu0": 1/mu0,  # Vacuum reluctivity [m/H]
            "nu_iron_linear": 1/(4000 * mu0)  # Iron reluctivity (relative permeability = 4000) [m/H]
        }
        
        # Update with config data if provided
        if config_data and 'physical_values' in config_data:
            config_phys_vals = config_data['physical_values']
            for key, value in config_phys_vals.items():
                # Handle special case where expressions contain pi
                if isinstance(value, str):
                    # Replace pi with numpy pi for evaluation
                    if 'pi' in value.lower():
                        value = value.replace('pi', str(np.pi))
                        value = value.replace('Pi', str(np.pi))
                        value = value.replace('PI', str(np.pi))
                    try:
                        # Safe evaluation of mathematical expressions
                        value = eval(value, {"__builtins__": {}}, {"pi": np.pi})
                    except:
                        # If evaluation fails, keep as string
                        pass
                self.physical_values[key] = value
    
    def _run_simulation(self, mesh_name: str, show_result: bool) -> None:
        """
        Run the magnetostatic simulation.
        
        Parameters:
        -----------
        mesh_name : str
            Name of the mesh file
        show_result : bool
            Whether to show the simulation result
        """
        run_magnetostatic_simulation(mesh_name, show_simulation_result=show_result)
    
    def get_physical_values(self) -> dict:
        """
        Get the current physical values.
        
        Returns:
        --------
        dict: Current physical values
        """
        return self.physical_values.copy() if self.physical_values else {}