# Bitmap Tracer

A image-to-SVG tracing application that converts bitmap images into clean, scalable vector graphics with intelligent color categorization and structure filtering.

## 🎯 Overview

Bitmap Tracer is a Python-based tool that analyzes bitmap images and converts them into SVG vector graphics. It features:

- **Smart color categorization** (Red, Blue, Green)
- **Intelligent curve fitting** for optimal shape preservation
- **Configurable structure filtering** to keep only the most important elements
- **Point detection** for small, compact shapes
- **Automatic contour closure** ensuring all paths form complete loops

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
├── core/                   # Core logic
│   ├── entities/           # Point, Contour, Color models
│   └── use_cases/          # Tracing and filtering workflows
├── infrastructure/         # Technical Implementations
│   ├── image_processing/   # OpenCV contour detection
│   ├── svg_generation/     # Creates SVG output
│   ├── configuration/      # Loads config.yaml
│   └── point_detection/    # Identifies small shapes
├── interfaces/             # Connects components
│   ├── controllers/        # Orchestrates the workflow
│   ├── presenters/         # Formats output
│   └── gateways/           # Handles external input
├── tests/                  # Pytests
├── __main__.py             # Entry point
├── config.yaml             # Your settings
├── pytest.ini              # Pytest initialization
└── README.md               # This documentation
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

From the sketchgetdp directory:
```bash
python -m bitmap_tracer <path_to_image>
```

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
