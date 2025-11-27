"""
This module contains functions to configure, run and evaluate numerical simulations using GetDP.

Author: Laura D'Angelo
"""

import gmsh 
import numpy as np
from sketchgetdp.geometry import gmsh_toolbox as geo


def get_getdp_path(filename: str) -> str:
    """
    Returns the path for running GetDP on the respective computer.

    Parameters:
        filename (str): file name
    
    Returns:
        str: path to GetDP executable
    """
    try:
        file = open(filename, 'r')
    except FileNotFoundError:
        message = 'Error: ' + filename + " not found. You have to create this file and give the path of your GetDP executable."
        exit(message)
    data = file.readlines()
    path = data[0].split('\n')
    file.close()
    return path[0]


def physical_identifiers() -> dict:
    """
    Returns fixed physical identifiers to be used for the SS-RMVP formulation.

    Returns: 
        dict: dictionary mapping physical identifier names to integers
    """
    return {"domain_coil_positive": 101, 
            "domain_coil_negative": 102,
            "boundary_gamma": 11, 
            "boundary_out": 12, 
            "domain_Va": 1, 
            "domain_Vi_iron": 2, 
            "domain_Vi_air": 3}


def print_data_to_pro(filename: str, data: dict) -> None:
    """
    Prints out the physical identifiers given in a dictionary to a .pro file that can be included into another .pro script.

    Parameters:
        filename (str): file name for the .pro file 
        data (dict): dictionary containing data 
    """
    f = open(filename + ".pro", "wt")
    f.write("DefineConstant [ \n")  # header 

    # Go through all physical-identifier names and integers and print them line by line
    counter = 1
    for key in data:
        if counter == len(data):
            f.write(key + " = " + str(data[key]) + " \n")
        else:
            f.write(key + " = " + str(data[key]) + ", \n")
        counter += 1
    
    f.write("]; \n")  # footer
    f.close()


def run_magnetostatic_simulation(msh_name: str, show_simulation_result: bool = True):
    """
    Runs a magnetostatic GetDP simulation using the RMVP formulation.

    Parameters:
        msh_name (str): name of the .msh file to be used
        show_simulation_result (bool): indicator whether the Gmsh GUI should be opened to view the results
    """
    pro_name = "rmvp_formulation.pro"
    resolution_name = "Magnetostatic_Resolution"
    gmsh.open(pro_name)
    getdp_path = get_getdp_path("./../../getdp_path.txt")
    onelab_command = getdp_path + " " + pro_name + " -msh " + msh_name + " -solve " + resolution_name + " -pos"
    gmsh.onelab.run("GetDP", onelab_command)
    if show_simulation_result:
        geo.show_model()
    gmsh.onelab.clear()
    geo.finalize_gmsh()


def demo_rmvp():
    """
    Runs a demonstrator: Two wires in an iron tube.
    """
    # Define properties of the geometric model
    model_name = "demo_model"
    physical_ids = physical_identifiers()
    print_data_to_pro("physical_identifiers", physical_ids)
    radius_wire = 0.1
    radius_tube_inner = 0.25
    radius_tube_outer = 0.3

    # Construct geometry
    cad = geo.initialize_gmsh(model_name)
    geo.set_characteristic_mesh_length(0.1)

    point_center = cad.addPoint(0, 0, 0)

    point_wire_left = cad.addPoint(-radius_wire, 0, 0)
    cad.addPhysicalGroup(0, [point_wire_left], physical_ids["domain_coil_positive"])
    point_wire_right = cad.addPoint(+radius_wire, 0, 0)
    cad.addPhysicalGroup(0, [point_wire_right], physical_ids["domain_coil_negative"])

    point_tube_inner_left = cad.addPoint(-radius_tube_inner, 0, 0)
    point_tube_inner_right = cad.addPoint(+radius_tube_inner, 0, 0)
    first_inner_arc = cad.addCircleArc(point_tube_inner_left, point_center, point_tube_inner_right)
    second_inner_arc = cad.addCircleArc(point_tube_inner_right, point_center, point_tube_inner_left)
    inner_curve_loop = cad.addCurveLoop([first_inner_arc, second_inner_arc])
    inner_surface = cad.addPlaneSurface([inner_curve_loop]) 
    cad.addPhysicalGroup(1, [first_inner_arc, second_inner_arc], physical_ids["boundary_gamma"])
    cad.addPhysicalGroup(2, [inner_surface], physical_ids["domain_Va"])

    point_tube_outer_left = cad.addPoint(-radius_tube_outer, 0, 0)
    point_tube_outer_right = cad.addPoint(+radius_tube_outer, 0, 0)
    first_outer_arc = cad.addCircleArc(point_tube_outer_left, point_center, point_tube_outer_right)
    second_outer_arc = cad.addCircleArc(point_tube_outer_right, point_center, point_tube_outer_left)
    outer_curve_loop = cad.addCurveLoop([first_outer_arc, second_outer_arc])
    outer_surface = cad.addPlaneSurface([outer_curve_loop, inner_curve_loop])
    cad.addPhysicalGroup(1, [first_outer_arc, second_outer_arc], physical_ids["boundary_out"])
    cad.addPhysicalGroup(2, [outer_surface], physical_ids["domain_Vi_iron"])

    # Synchronize
    cad.synchronize()

    # Mesh and visualize mesh
    geo.mesh_and_save(model_name, 2)
    geo.show_model()

    # Define additional data for simulation 
    mu0 = 4e-7 * np.pi
    physical_values = {"Isource": 1, 
                       "mu0": mu0, 
                       "nu0": 1/mu0, 
                       "nu_iron_linear": 1/(4000 * mu0)}
    print_data_to_pro("physical_values", physical_values) 
    other_data = {"des_dir": "results"}
    print_data_to_pro("other_data", other_data)

    # Run simulation
    run_magnetostatic_simulation(model_name + ".msh")


if __name__ == "__main__":
    demo_rmvp()