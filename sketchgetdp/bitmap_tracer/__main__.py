"""
Bitmap Tracer Application - Entry Point

The application converts bitmap images to SVG vector graphics through a structured
process of contour detection, color analysis, and vector path generation.
"""

import sys
import os
import argparse

from interfaces.controllers.tracing_controller import TracingController


def find_config_file(config_path: str) -> str:
    """
    Find configuration file, checking multiple possible locations.
    
    Priority order:
    1. User-specified path (absolute or relative to cwd)
    2. Relative to current working directory  
    3. In the package directory (for default config)
    
    Returns:
        Path to the first found config file, or original path if none found.
    """
    from pathlib import Path
    
    search_paths = [
        Path(config_path),                      # User-specified path
        Path.cwd() / config_path,               # Current working directory
        Path(__file__).parent / config_path,    # Package directory (where main.py lives)
    ]
    
    for path in search_paths:
        if path.exists():
            print(f"✅ Found configuration file: {path}")
            return str(path)
    
    print(f"⚠️  Configuration file not found: {config_path}, using defaults")
    return config_path                          # Return original if not found anywhere


def validate_input_file_exists(file_path: str) -> None:
    """
    Validates that the specified file exists and is readable.
        
    Args:
        file_path: Absolute or relative path to the file to validate.
        
    Raises:
        FileNotFoundError: When the specified file does not exist.
        PermissionError: When the file exists but cannot be read.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Input image not found: {file_path}")
    
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read input image: {file_path}")


def parse_command_line_arguments() -> argparse.Namespace:
    """
    Parses and validates command-line arguments provided by the user.
    
    Returns:
        Parsed arguments object containing:
        - input_image: Path to source bitmap file
        - output: Path for generated SVG file  
        - config: Path to configuration file
        
    Raises:
        SystemExit: When help is requested or arguments are invalid.
    """
    argument_parser = argparse.ArgumentParser(
        description=(
            'Convert bitmap images to SVG vector graphics using '
            'advanced computer vision techniques. The tracer detects '
            'contours, analyzes colors, and generates optimized vector paths.'
        ),
        epilog=(
            'Example usage:\n'
            '  python main.py drawing.jpg\n'
            '  python main.py sketch.png -o output.svg -c settings.yaml\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    argument_parser.add_argument(
        'input_image',
        help='Path to input bitmap image (supports JPEG, PNG, BMP formats)'
    )
    
    argument_parser.add_argument(
        '-o', '--output',
        default='output.svg',
        help='Output SVG file path (default: output.svg)'
    )
    
    argument_parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Configuration file controlling tracing behavior (default: config.yaml)'
    )
    
    arguments = argument_parser.parse_args()
    
    # Find the actual config file location
    arguments.config = find_config_file(arguments.config)
    
    return arguments


def execute_tracing_pipeline(input_path: str, output_path: str, config_path: str) -> bool:
    """
    Executes the complete bitmap-to-SVG tracing pipeline.
    
    Args:
        input_path: Path to source bitmap image.
        output_path: Path where SVG output will be saved.
        config_path: Path to YAML configuration file.
        
    Returns:
        True if SVG was generated successfully, False otherwise.
    """
    try:
        controller = TracingController()
        
        # Execute the tracing workflow
        result = controller.trace_image(
            image_path=input_path,
            output_svg_path=output_path,
            config_path=config_path
        )
        
        # Return success status
        return result.get('success', False)
        
    except Exception as processing_error:
        print(f"❌ Tracing pipeline error: {processing_error}")
        return False


def log_application_startup(arguments: argparse.Namespace) -> None:
    """
    Logs application startup parameters for user verification.
    
    Args:
        arguments: Parsed command-line arguments containing execution parameters.
    """
    print("🖼️  Bitmap Tracer Application Starting - Clean Architecture")
    print("=" * 50)
    print(f"📁 Input Image: {arguments.input_image}")
    print(f"📁 Output SVG: {arguments.output}")
    print(f"⚙️  Configuration: {arguments.config}")
    print("=" * 50)


def log_application_result(success: bool, output_path: str = "") -> None:
    """
    Logs the final result of the tracing operation.
    
    Args:
        success: True if tracing completed successfully, False otherwise.
        output_path: Path to the generated SVG file (on success).
    """
    if success:
        print(f"✅ Tracing completed successfully - SVG file generated: {output_path}")
    else:
        print("❌ Tracing failed - check error messages above for details.")


def main() -> None:
    """
    Entry point for the Bitmap Tracer.
    
    This function orchestrates the complete application workflow:
    1. Parse and validate command-line arguments
    2. Verify input file existence and accessibility
    3. Execute the tracing pipeline via TracingController
    4. Provide clear success/failure feedback
    5. Return appropriate exit codes
    
    System Exit Codes:
        0: Success - SVG file generated successfully
        1: Failure - Invalid input, processing error, or file issues
        2: System error - Unexpected application failure
    """
    try:
        arguments = parse_command_line_arguments()
        validate_input_file_exists(arguments.input_image)
        log_application_startup(arguments)
        
        tracing_success = execute_tracing_pipeline(
            input_path=arguments.input_image,
            output_path=arguments.output,
            config_path=arguments.config
        )
        
        log_application_result(tracing_success, arguments.output)
        exit_code = 0 if tracing_success else 1
        sys.exit(exit_code)
        
    except FileNotFoundError as file_error:
        print(f"❌ File error: {file_error}")
        sys.exit(1)
    except PermissionError as permission_error:
        print(f"❌ Permission error: {permission_error}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as unexpected_error:
        print(f"💥 Unexpected application error: {unexpected_error}")
        sys.exit(2)


if __name__ == "__main__":
    main()