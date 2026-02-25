# SVG to GetDP

A sophisticated electromagnetic simulation pipeline that converts SVG sketches into Gmsh meshes and solves them using GetDP, with configurable physical properties and intelligent geometry processing.

## 🎯 Overview

SVG to GetDP is a Python-based electromagnetic simulation pipeline that processes non-freehand drawn SVG files containing electromagnetic structures and generates simulation results through a multi-stage workflow. It features:

- **Three operation modes**: SVG→Gmsh, SVG→Gmsh→GetDP, or Gmsh→GetDP
- **Configurable physical properties** via YAML configuration
- **Intelligent SVG parsing** with Bézier curve fitting and corner detection
- **Fixed color mapping** for physical group identification
- **Automatic wire grouping** and boundary curve meshing

## 🚀 Key Features

### Three Operation Modes
1. **SVG → Gmsh**: Convert SVG sketches to Gmsh meshes
2. **SVG → Gmsh → GetDP**: Full pipeline from SVG to simulation results
3. **Gmsh → GetDP**: Run GetDP simulation on existing meshes

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
- Visualization of internal geometry
- Debug output of intermediate processing steps via .txt files

## How It Works

1. **Parse SVG** – Reads paths and identifies colors (Blue = wires, Green = iron, Red = boundaries)
2. **Detect corners** – Breaks paths at sharp angles for better curve fitting
3. **Fit Bézier curves** – Creates smooth mathematical representations
4. **Preprocess wires and outlines** – Preprocesses wires and outlines for meshing with Gmsh
5. **Generate mesh** – Creates a Gmsh mesh with physical groups
6. **Run simulation** – Executes GetDP to solve the electromagnetic problem

## 📁 Project Structure
```
svg_to_getdp/
├── core/                         # Core logic
│ ├── entities/                   # Point, color, outline, etc.
│ └── use_cases/                  # Conversion workflows
├── infrastructure/               # Technical Implementations
│ ├── factories/                  # Creates objects
│ ├── svg_processing/             # Parses SVG files
│ ├── corner_detection/           # Finds path corners
│ ├── bezier_fitting/             # Fits curves to paths
│ ├── outline_grouper.py          # Groups outlines for preprocessing
│ ├── outline_preprocessor.py     # Preprocesses outlines for Gmsh
│ ├── wire_preprocessor.py        # Preprocesses wires for Gmsh
├── interfaces/                   # Connectors
│ ├── arg_parser.py               # Command-line interface
│ ├── abstractions/               # Dependency interfaces
│ ├── debug/                      # Debugging tools
│ ├── mesher/                     # Gmsh integration
│ └── solver/                     # GetDP integration
├── tests/                        # pytests
├── __main__.py                   # Entry point
├── config.yaml                   # Your settings
├── pytest.ini                    # Pytest initialization
└── README.md                     # This documentation
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
    wire_count: 6
    current_sign: 1
  cluster_2:
    wire_count: 6
    current_sign: -1

## mesh settings
# Set the mesh size for Gmsh
mesh_size: 0.1

## GetDP simulation settings
# Physical values for the simulation
physical_values:
  Isource: 9000  # Current source in Amperes [A]
  nu_iron_linear: 1/(1000 * 4e-7 * pi)  # Iron reluctivity
```

## 🛠️ Usage

### Mode 1: SVG to Gmsh Mesh

Convert an SVG file to a Gmsh mesh file:

```bash
python -m svg_to_getdp <path_to_svg> --config <path_to_config>
```

### Mode 2: Full Pipeline (SVG to Simulation)

Convert SVG file to mesh file and run GetDP simulation:

```bash
python -m svg_to_getdp <path_to_svg> --run-simulation --config <path_to_config>
```

### Mode 3: Simulation Only (Existing Mesh)

Run GetDP simulation on an existing mesh file:

```bash
python -m svg_to_getdp --simulation-only <path_to_msh> --config <path_to_config>
```

### Additional Options
- `--mesh-name my_mesh`: Specify output mesh name
- `--no-gui`: Run in batch mode without GUI
- `--debug`: Enable debug output

### Examples
```bash
# Generate mesh with custom name and no GUI
python -m svg_to_getdp <path_to_svg> --mesh-name my_design --no-gui

# Full pipeline with custom config
python -m svg_to_getdp <path_to_svg> --config custom_config.yaml --run-simulation

# Get debug output
python -m svg_to_getdp <path_to_svg> --debug
```

## 📊 Output

The pipeline generates the following outputs depending on the mode:

### Mode 1 (SVG → Gmsh)

Inside the sketchgetdp directory inside SketchGetDP:

- **`.msh` file**: Gmsh mesh file with physical groups

### Mode 2 (SVG → Gmsh → GetDP)

Inside the sketchgetdp directory inside SketchGetDP:

- **`.msh` file**: Gmsh mesh file
- **`.pro` file**: GetDP problem definition
- **`results/` directory**: GetDP simulation results

### Mode 3 (Gmsh Mesh → GetDP)

Inside the sketchgetdp directory inside SketchGetDP:

- **`.pro` file**: GetDP problem definition
- **`results/` directory**: GetDP simulation results

### Debug Output

Inside the debug subdirectory of the sketchgetdp directory inside SketchGetDP:

- **`svg_parser_debug_[filename]_[timestamp].txt` file**: SVG Processing Debug output
- **`corner_detection_debug_[filename]_[timestamp].txt` file**: Corner Detection Debug output
- **`geometry_debug_[filename]_[timestamp].txt` file**: Internal Geometry Representation Debug output
- **`geometry_plot_[filename]_[timestamp].png` file**: Internal Geometry Representation Plot
- **`wire_preprocessor_debug_[filename]_[timestamp].txt` file**: Wire Preprocessing Debug output
- **`outline_grouping_debug_[filename]_[timestamp].txt` file**: Outline Grouping Debug output
- **`outline_preprocessing_debug_[filename]_[timestamp].txt` file**: Outline Preprocessing Debug output


## 🔧 Dependencies

- **NumPy** - Numerical calculations
- **svgpathtools** - SVG parsing
- **PyYAML** - Configuration
- **Gmsh** - Meshing engine (external)
- **GetDP** - Finite element solver (external)
- **matplotlib** - Visualization (optional, for debugging)

## 🎨 Use Cases

- **Rapid prototyping**: Get first estimates of electromagnetic poperties from SVG sketches
- **Educational Tool**: Visualize electromagnetic field distributions from simple drawings
- **Design validation**: Quickly test electromagnetic structures before detailed CAD modeling
- **Mesh generation**: Create quality meshes from vector graphics for various Finite Element Analysis applications
