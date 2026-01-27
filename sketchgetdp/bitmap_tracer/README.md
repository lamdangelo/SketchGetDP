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
└── config.yaml            # Configuration
```

## ⚙️ Configuration

Configure the tracing behavior in `config.yaml`:

```yaml
## Structure Limits
# Maximum number of structures to keep for each color category after filtering.
# Structures are sorted by area (largest first) and only the top N are kept.
red_dots: 1    # Maximum red points to preserve
blue_paths: 1   # Maximum blue paths to preserve  
green_paths: 1  # Maximum green paths to preserve

## Contour Detection Parameters
# Control how contours are detected and filtered from the source image.
point_max_area: 2000     # Maximum area for a contour to be classified as a point
point_max_perimeter: 1000 # Maximum perimeter for point classification

## Color Detection Parameters
# Define thresholds for categorizing colors in the source image.
blue_hue_range: [100, 140]         # HSV hue range for blue color detection
red_hue_range: [[0, 10], [170, 180]] # HSV hue ranges for red color detection
green_hue_range: [35, 85]          # HSV hue range for green color detection
min_saturation: 50                 # Minimum saturation to avoid classifying as white
max_value_white: 200               # Maximum value above which colors are considered white
min_value_black: 50                # Minimum value below which colors are considered black
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