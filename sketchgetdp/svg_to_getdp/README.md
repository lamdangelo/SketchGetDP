# SVG to GetDP

A sophisticated electromagnetic simulation pipeline that converts SVG sketches into Gmsh meshes and solves them using GetDP, with configurable physical properties and intelligent geometry processing.

## 🎯 Overview

SVG to GetDP is a Python-based electromagnetic simulation pipeline that processes SVG files containing electromagnetic structures and generates simulation results through a multi-stage workflow. It features:

- **Three operation modes**: SVG→Gmsh, SVG→Gmsh→GetDP, or Mesh→GetDP
- **Configurable physical properties** via YAML configuration
- **Intelligent SVG parsing** with Bézier curve fitting and corner detection
- **Fixed color mapping** for physical group identification
- **Automatic wire grouping** and boundary curve meshing

## 🏗️ Architecture

The project follows Clean Architecture principles with clear separation of concerns:

### Core Layers

- **`core/`** - Enterprise business rules
  - `entities/` - Domain models (Point, Color, BezierSegment, BoundaryCurve, PhysicalGroup)
  - `use_cases/` - Application logic (SVG-to-Geometry conversion, Geometry-to-Gmsh conversion, GetDP simulation execution)

- **`infrastructure/`** - Frameworks & drivers
  - `svg_parser/` - SVG parsing and path extraction
  - `corner_detector/` - Corner detection for curve segmentation
  - `bezier_fitter/` - Bézier curve fitting
  - `boundary_curve_grouper/` - Wire grouping logic
  - `boundary_curve_mesher/` - Boundary curve meshing
  - `wire_preprocessor/` - Wire preprocessing for meshing

- **`interfaces/`** - Interface adapters
  - `controllers/` - Application flow control
  - `arg_parser/` - Command line argument parsing
  - `abstractions/` - Interfaces for dependency inversion
  - `debug/` - Internal visualization and debug output

## 🚀 Key Features

### Three Operation Modes
1. **SVG → Gmsh**: Convert SVG sketches to Gmsh meshes
2. **SVG → Gmsh → GetDP**: Full pipeline from SVG to simulation results
3. **Mesh → GetDP**: Run GetDP simulation on existing meshes

### Intelligent SVG Processing
- **Bézier curve fitting** for accurate shape representation
- **Corner detection** for optimal curve segmentation
- **Fixed color mapping** for physical group identification
- **Automatic wire grouping** based on spatial relationships

### Configurable Physical Properties
- Customizable coil current directions and magnitudes
- Adjustable mesh sizing parameters
- Configurable physical values for simulation

### Visualization & Debug
- Interactive visualization of Bézier curves and control points
- Debug output of intermediate processing steps
- Plot export for documentation and analysis

## 📁 Project Structure
```
svg_to_getdp/
├── core/ # Business logic
│ ├── entities/ # Domain models
│ └── use_cases/ # Application services
├── infrastructure/ # External concerns
│ ├── svg_parser.py # SVG parsing
│ ├── corner_detector.py # Corner detection
│ ├── bezier_fitter.py # Bézier fitting
│ ├── boundary_curve_grouper.py # Wire grouping
│ ├── boundary_curve_mesher.py # Boundary meshing
│ └── wire_preprocessor # Wire preprocessing
├── interfaces/ # Adapters
│ ├── arg_parser.py # Command line interface
│ ├── abstractions/ # Dependency interfaces
│ └── debug/ # Debug tools
├── tests/ # Unit tests
│ ├── core/ # Core layer tests
│ └── infrastructure/ # Infrastructure tests
├── __main__.py # Package entry point
├── config.yaml # Configuration file
└── rmvp_formulation.pro # GetDP configuration file
```

## ⚙️ Configuration

Configure wire currents, mesh settings, and simulation parameters in `config.yaml`:

```yaml
## Wire cluster configuration
# Clusters are identified from top to bottom, left to right
# Each cluster has: number of wires and current direction (1 for positive, -1 for negative)
# Positive current flows out of the page.
wire_clusters:
  cluster_1:
    wire_count: 3
    current_sign: 1
  cluster_2:
    wire_count: 3
    current_sign: -1
    
# Mesh settings
mesh_size: 0.1

# GetDP simulation settings
physical_values:
  Isource: 10000 # Current source in Amperes [A]
  nu_iron_linear: 1/(1000 * 4e-7 * pi)  # Iron reluctivity
```

## 🛠️ Usage

### Mode 1: SVG to Gmsh Mesh

Convert an SVG file to a Gmsh mesh:

```bash
python -m svg_to_getdp drawing.svg --config config.yaml
```

### Mode 2: Full Pipeline (SVG to Simulation)

Convert SVG to mesh and run GetDP simulation:

```bash
python -m svg_to_getdp drawing.svg --run-simulation --config config.yaml
```

### Mode 3: Simulation Only (Existing Mesh)

Run GetDP simulation on an existing mesh file:

```bash
python -m svg_to_getdp --simulation-only existing_mesh.msh --config config.yaml
```

### Additional Options
- `--mesh-name my_mesh`: Specify output mesh name
- `--no-gui`: Run in batch mode without GUI
- `--visualize`: Display interactive visualization of internal datastructures
- `--output-plot curves.png`: Save visualization to file
- `--debug`: Enable debug output

### Examples
```bash
# Generate mesh with custom name and no GUI
python -m svg_to_getdp sketch.svg --mesh-name my_design --no-gui

# Full pipeline with custom config
python -m svg_to_getdp circuit.svg --config custom_config.yaml --run-simulation

# Save visualization to file
python -m svg_to_getdp layout.svg --output-plot analysis.png
```

## 📊 Output

The pipeline generates the following outputs depending on the mode:

### Mode 1(SVG → Gmsh)

- **`.msh` file**: Gmsh mesh file with physical groups
- **Conversion statistics**: Number of boundary curves, wires and bezier segments

### Mode 2(SVG → Gmsh → GetDP)

- **`.msh` file**: Gmsh mesh file
- **`.pro` file**: GetDP problem definition
- **`results/` directory**: GetDP simulation results
- **Visualization plots** (if requested)

### Mode 3(Mesh → GetDP)

- **`.pro` file**: GetDP problem definition
- **`results/` directory**: GetDP simulation results

## 🔧 Dependencies

- **NumPy** - Numerical computations
- **svgpathtools** - SVG parsing and path manipulation
- **PyYAML** - Configuration parsing
- **Gmsh** - Meshing engine (external dependency)
- **GetDP** - Finite element solver (external dependency)
- **matplotlib** - Visualization (optional)

## 🎨 Use Cases

- **Rapid prototyping**: Get first estimates of electromagnetic poperties from SVG sketches
- **Educational Tool**: Visualize electromagnetic field distributions from simple drawings
- **Design validation**: Quickly test electromagnetic structures before detailed CAD modeling
- **Mesh generation**: Create quality meshes from vector graphics for various Finite Element Analysis applications

The SVG to GetDP pipeline excels at transforming intuitive SVG sketches into detailed electromagnetic simulations, bridging the gap between conceptual design and numerical analysis while maintaining configurability and reproducability.