"""
Bitmap Tracer Application - Clean Architecture Entry Point

This module provides a clean command-line interface to the bitmap tracing
functionality using the clean architecture implementation.

The application converts bitmap images to SVG vector graphics through a structured
process of contour detection, color analysis, and vector path generation.
"""

import sys
import os
import argparse

from interfaces.controllers.tracing_controller import TracingController


def validate_input_file_exists(file_path: str) -> None:
    """
    Validates that the specified file exists and is readable.
    
    This validation prevents the application from attempting to process
    non-existent files and provides clear error messages to the user.
    
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
    
    return argument_parser.parse_args()


def execute_tracing_pipeline(input_path: str, output_path: str, config_path: str) -> bool:
    """
    Executes the complete bitmap-to-SVG tracing pipeline using clean architecture.
    
    This function uses the TracingController to orchestrate the workflow
    through the clean architecture layers.
    
    Args:
        input_path: Path to source bitmap image.
        output_path: Path where SVG output will be saved.
        config_path: Path to YAML configuration file.
        
    Returns:
        True if SVG was generated successfully, False otherwise.
    """
    try:
        # Create the tracing controller - this is the entry point to clean architecture
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
    
    Clear startup logging helps users verify that the application
    is processing the correct files with the intended configuration.
    
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
    
    Clear success/failure messaging provides immediate feedback
    to users about the outcome of the operation.
    
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
    Main entry point for the Bitmap Tracer command-line application.
    
    This function orchestrates the complete application workflow using
    the clean architecture implementation:
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