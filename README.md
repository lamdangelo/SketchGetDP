# SketchGetDP
**From Hand-Drawn Sketches to Electromagnetic Simulations**

SketchGetDP translates photographed hand-drawn shapes and SVG files into Gmsh geometries ready for GetDP simulation. It's designed for engineers, researchers, and students working with accelerator magnet cross-sections.

## 🎯 Overview

SketchGetDP provides two complementary tools that turn your drawings into simulation results:

- **Bitmap Tracer** – Converts photos of hand-drawn sketches (JPEG, PNG) into SVG vector graphics
- **SVG to GetDP** – Analyzes SVG sketches to create meshes and run electromagnetic simulations

> ⚠️ **Note**: The Bitmap Tracer and SVG to GetDP components are still being integrated. Currently, corner detection for freehand lines and color mapping between the two tools require further development.


## 📁 Project Structure

```
SketchGetDP/
├── sketchgetdp/                # Core Implementation
│   ├── bitmap_tracer/          # Converts Images to SVG
│   ├── svg_to_getdp/           # Converts SVG to simulations
│   └── rmvp_formulation.pro    # GetDP configuration template
├── tests/                      # Example inputs for testing
├── README.md                   # This documentation
├── getdp_path.txt              # Path to your GetDP installation
└── requirements.txt            # Python package dependencies
```

For detailed information, check the README files in each subdirectory.

## Getting started 

1. **Install the SketchGetDP module**
    ```bash
    pip install -e .
    ```

2) **Install the SketchGetDP module**
    ```bash
    pip install -r requirements.txt
    ```

3) **Install GetDP**
    - Download GetDP from [getdp.info](https://getdp.info/)
    - Add the path to GetDP in `getdp_path.txt`

## 🛠️ Usage

### Bitmap Tracer

Convert a photo of a hand-drawn sketch to SVG by running the following from the sketchgetdp subdirectory:
```bash
python -m bitmap_tracer <path_to_image>
```

### SVG to GetDP

Three ways to use it from the sketchgetdp subdirectory:

```bash
# Mode 1: SVG to mesh only
python -m svg_to_getdp <path_to_svg> --config <path_to_config>

# Mode 2: Full pipeline (SVG → mesh → simulation)
python -m svg_to_getdp <path_to_svg> --run-simulation --config <path_to_config>

# Mode 3: Simulation only (existing mesh)
python -m svg_to_getdp --simulation-only <path_to_msh> --config <path_to_config>
```
