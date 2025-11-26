# Bitmap Tracer

A sophisticated image-to-SVG tracing application that converts bitmap images into clean, scalable vector graphics with intelligent color categorization and structure filtering.

## 🎯 Overview

Bitmap Tracer is a Python-based tool that analyzes bitmap images and converts them into SVG vector graphics. It features:

- **Smart color categorization** (Red, Blue, Green)
- **Intelligent curve fitting** for optimal shape preservation
- **Configurable structure filtering** to keep only the most important elements
- **Point detection** for small, compact shapes
- **Automatic contour closure** ensuring all paths form complete loops

## 🏗️ Architecture

The project follows Clean Architecture principles with clear separation of concerns:

### Core Layers

- **`core/`** - Enterprise business rules
  - `entities/` - Domain models (Point, Contour, Color)
  - `use_cases/` - Application logic (Image Tracing, Structure Filtering)

- **`infrastructure/`** - Frameworks & drivers
  - `image_processing/` - Contour detection, color analysis, closure services
  - `svg_generation/` - SVG creation and shape processing
  - `configuration/` - Config loading and management
  - `point_detection/` - Point detection and curve fitting

- **`interfaces/`** - Interface adapters
  - `controllers/` - Application flow control
  - `presenters/` - Output formatting (SVG presentation)
  - `gateways/` - External interfaces (image loading, config access)

## 🚀 Key Features

### Color Categorization
- Automatically detects and categorizes strokes into Red, Blue, and Green
- Red shapes are reserved exclusively for point markers
- Ignores white/black background colors

### Smart Curve Fitting
- Hybrid approach using lines for straight segments and curves for curved segments
- Preserves actual shape while smoothing where appropriate
- Automatic contour closure with distance validation

### Configurable Filtering
- Control the number of structures kept for each color via YAML configuration
- Filters by area, keeping only the largest structures
- Hierarchical filtering to remove nested contours

### Point Detection
- Identifies small, compact shapes as points
- Creates simple dot markers at contour centers
- Unified sorting with larger red structures

## 📁 Project Structure

```
bitmap_tracer/
├── core/                    # Business logic
│   ├── entities/           # Domain models
│   └── use_cases/          # Application services
├── infrastructure/          # External concerns
│   ├── image_processing/   # Computer vision
│   ├── svg_generation/     # Vector output
│   ├── configuration/      # Config management
│   └── point_detection/    # Point analysis
├── interfaces/             # Adapters
│   ├── controllers/        # Flow control
│   ├── presenters/         # Output formatting
│   └── gateways/           # External interfaces
├── __main__.py             # Python module entry point
├── main.py                 # General entry point
└── config.yaml            # Configuration
```

## ⚙️ Configuration

Configure the number of structures to keep for each color in `config.yaml`:

```yaml
red_dots: 10      # Maximum number of red points to keep
blue_paths: 5     # Maximum number of blue paths to keep  
green_paths: 8    # Maximum number of green paths to keep
```

## 🛠️ Usage

The Bitmap Tracer can be run from the command line in two ways:

### From the sketchgetdp directory as a python module:
```bash
python -m bitmap_tracer <path_to_image>
```

### From the bitmap_tracer directory:
```bash
python main.py <path_to_image>
```

Where `<path_to_image>` is the path to the bitmap image you want to convert to SVG.

The application will automatically:
- Load configuration from `config.yaml`
- Process the input image
- Generate an SVG output file with the same name as the input image (changing extension to .svg)
- Apply color categorization and structure filtering based on your configuration

## 📊 Output

The tracer generates SVG files with:
- **Blue paths** - Curved and straight segments from blue strokes
- **Green paths** - Curved and straight segments from green strokes  
- **Red points** - Simple dot markers from red shapes and small points
- Clean, optimized vector paths suitable for scaling and further processing

## 🔧 Dependencies

- OpenCV - Image processing and contour detection
- NumPy - Numerical computations
- svgwrite - SVG generation
- PyYAML - Configuration parsing

## 🎨 Use Cases

- Converting hand-drawn sketches to vector graphics
- Processing technical diagrams and schematics
- Creating scalable versions of bitmap artwork
- Extracting structured information from images

The Bitmap Tracer excels at transforming complex bitmap images into clean, manageable vector representations while preserving the essential structure and color information.