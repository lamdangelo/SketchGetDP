"""
Demo: Basic usage of the Gmsh geometry construction functionalities

Author: Laura D'Angelo 
"""

from sketchgetdp.geometry import gmsh_toolbox as geo

def draw_rectangle(factory: geo.GeoFactory, x1: float, y1: float, x2: float, y2: float, 
                   hole_tags: list[int] = []) -> dict: 
    """ Draws a rectangle from two given corner points, possibly with a hole.

    Parameters:
        factory (GeoFactory): a Gmsh factory object
        x1 (float): x-coordinate of first corner point
        y1 (float): y-coordinate of first corner point
        x2 (float): x-coordinate of second corner point 
        y2 (float): y-coordinate of second corner point
        hole_tags (list[int]): list of surfaces within the rectangle which should be 
            treated as holes, optional
    
    Returns:
        dict: dictionary containing surface, curve loop and line tags of the drawn rectangle
    """
    # Draw the points
    p1 = factory.addPoint(x1, y1, 0)
    p2 = factory.addPoint(x2, y1, 0)
    p3 = factory.addPoint(x2, y2, 0)
    p4 = factory.addPoint(x1, y2, 0)

    # Draw the lines
    l1 = factory.addLine(p1, p2)
    l2 = factory.addLine(p2, p3)
    l3 = factory.addLine(p3, p4)
    l4 = factory.addLine(p4, p1)

    # Define curve loop and plane surface
    curve_loop = factory.addCurveLoop([l1, l2, l3, l4])
    curve_loop_list = [curve_loop] + hole_tags
    surface = factory.addPlaneSurface(curve_loop_list)

    # Return curve loop tag (for future holes) and surface tags for wires
    return {"hole": [curve_loop],
            "surface": surface, 
            "boundary": [l1, l2, l3, l4]}

def run_demo() -> None:
    """ Runs a demo script that draws a rectangular domain within a larger rectangular domain. 
    """
    model_name = "demo_rectangular_model"  # Define the model name 

    # Define geometrical parameters
    width_in = 0.7
    height_in = 0.3
    width_out = 1
    height_out = 0.5

    # Define physical region identifiers 
    domain_in = 1
    domain_out = 2
    boundary_in = 11
    boundary_out = 12

    # Define the mesh size 
    h_mesh = 0.1

    factory = geo.initialize_gmsh(model_name)  # Initialize Gmsh 
    geo.set_characteristic_mesh_length(h_mesh)  # Set the mesh size 

    # Draw the inner rectangle, and define its surface and boundary as physical regions
    inner_rectangle_tags = draw_rectangle(factory, -width_in/2, -height_in/2, 
                                          +width_in/2, +height_in/2)
    geo.add_to_physical_group(factory, 2, inner_rectangle_tags["surface"], domain_in)
    geo.add_to_physical_group(factory, 1, inner_rectangle_tags["boundary"], boundary_in)

    # Draw the outer rectangle, having the inner rectangle as hole, and define its surface and 
    # boundary as physical regions 
    outer_rectangle_tags = draw_rectangle(factory, -width_out/2, -height_out/2, 
                                          +width_out/2, +height_out/2, inner_rectangle_tags["hole"])
    geo.add_to_physical_group(factory, 2, outer_rectangle_tags["surface"], domain_out)
    geo.add_to_physical_group(factory, 1, outer_rectangle_tags["boundary"], boundary_out)

    # Synchronize before meshing 
    factory.synchronize() 

    # Mesh and save 
    geo.mesh_and_save(model_name, 2)

    # Open the Gmsh GUI to show the drawn and meshed geometry
    geo.show_model()


if __name__ == "__main__":
    run_demo()