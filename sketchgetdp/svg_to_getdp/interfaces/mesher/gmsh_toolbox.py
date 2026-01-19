""" This module contains functions to initialize and work with Gmsh. 

To that end, a geometry factory is employed, which is used to build the geometry, manage physical identities of 
geometrical objects, and ultimately mesh the final geometry. 

Author: Laura D'Angelo
"""

import gmsh 
from typing import List
from typing import NewType

GeoFactory = NewType('GeoFactory', type[gmsh.model.geo])


def add_to_physical_group(factory: GeoFactory, dimension: int, entity_tags: List[int], physical_id: int) -> None:
    """ Adds a list of geometrical tags to a physical group.

    Parameters:
        factory (GeoFactory): a Gmsh factory object
        dimension (int): dimension of the geometrical entities
        entity_tags (List[int]): list of tags of the geometrical entities
        physical_id (int): physical identifier of the physical group
    """
    # Check if it is a single entity tag
    if isinstance(entity_tags, int):
        entity_tags = [entity_tags]

    # Synchronize
    factory.synchronize()

    # Add to physical region
    factory.addPhysicalGroup(dimension, entity_tags, physical_id)


def finalize_gmsh() -> None:
    """ Finalizes Gmsh.
    """
    gmsh.finalize()


def initialize_gmsh(model_name: str) -> GeoFactory:
    """ Initializes Gmsh.

    Parameters:
        model_name (str): name of the Gmsh model
    
    Returns: 
        GeoFactory: Gmsh model factory
    """
    gmsh.initialize()
    gmsh.model.add(model_name)
    return gmsh.model.geo


def mesh_and_save(filename: str, dim: int) -> None:
    """ Creates a 2D mesh and writes the Gmsh model.

    Parameters:
        filename (str): name under which Gmsh model mesh is to be saved
        dim (int): dimension of the mesh
    """
    gmsh.model.mesh.generate(dim)
    gmsh.write(filename + ".msh")


def set_characteristic_mesh_length(h_mesh: float) -> None:
    """ Sets the characteristic mesh length on a given value.

    Parameters:
        h_mesh (float): characteristic mesh length
    """
    gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", h_mesh)


def show_model() -> None: 
    """ Opens the Gmsh GUI to show the current state of the geometrical model.
    Note: This will stop the execution of further Python code until the GUI is closed.
    """
    gmsh.fltk.run()