import cv2
import numpy as np
from svgwrite import Drawing
from collections import defaultdict
import yaml
import os

def load_config(config_path="config.yaml"):
    """
    Load the number of structures to keep for each color from YAML config file
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                red_dots = config.get('red_dots', 0)
                blue_paths = config.get('blue_paths', 0)
                green_paths = config.get('green_paths', 0)
                print(f"📁 Loaded config: red_dots={red_dots}, blue_paths={blue_paths}, green_paths={green_paths}")
                return red_dots, blue_paths, green_paths
        else:
            print(f"❌ Config file not found: {config_path}")
            return 0, 0, 0
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return 0, 0, 0

def detect_points(contour, max_area=100, max_perimeter=80):
    """
    Detect if a contour represents a point (very small, compact shape)
    Returns center coordinates if it's a point, None otherwise
    """
    if len(contour) < 3:
        return None
    
    # Calculate contour properties
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    
    # More lenient criteria for points
    if area < max_area and perimeter < max_perimeter:
        # Calculate centroid
        M = cv2.moments(contour)
        if M["m00"] != 0:
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            print(f"  📍 Point detected: area={area:.1f}, perimeter={perimeter:.1f}, center=({center_x}, {center_y})")
            return (center_x, center_y)
    
    return None

def create_point_marker(center_x, center_y, radius=3):
    """
    Create a simple dot as a filled circle
    Returns SVG circle element for the point marker
    """
    # Simple dot - filled circle
    return {
        'type': 'circle',
        'cx': center_x,
        'cy': center_y,
        'r': radius
    }

def get_contour_center(contour):
    """
    Calculate the center point of any contour
    """
    M = cv2.moments(contour)
    if M["m00"] != 0:
        center_x = int(M["m10"] / M["m00"])
        center_y = int(M["m01"] / M["m00"])
        return (center_x, center_y)
    return None

def categorize_color(bgr_color):
    """
    Categorize BGR color into major color groups: blue, red, green
    Returns the category name and standardized hex color
    """
    b, g, r = bgr_color
    
    # Convert to HSV for better color segmentation
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    hue, saturation, value = hsv
    
    # Ignore white/light colors (high value, low saturation)
    if value > 200 and saturation < 50:
        return "white", None
    
    # Ignore black/dark colors
    if value < 50:
        return "black", None
    
    # Color categorization based on hue
    if (hue >= 100 and hue <= 140) or (b > g + 20 and b > r + 20):  # Blue range
        return "blue", "#0000FF"
    elif (hue >= 0 and hue <= 10) or (hue >= 170 and hue <= 180) or (r > g + 20 and r > b + 20):  # Red range
        return "red", "#FF0000"
    elif (hue >= 35 and hue <= 85) or (g > r + 20 and g > b + 20):  # Green range
        return "green", "#00FF00"
    else:
        return "other", None

def detect_dominant_stroke_color(contour, original_image):
    """
    Detect and categorize the dominant stroke color
    """
    # Create a mask for just the contour boundary (the actual stroke)
    boundary_mask = np.zeros(original_image.shape[:2], np.uint8)
    cv2.drawContours(boundary_mask, [contour], 0, 255, 2)  # Only draw the boundary
    
    boundary_pixels = original_image[boundary_mask == 255]
    
    if len(boundary_pixels) == 0:
        return None
    
    # Count colors by category
    color_categories = defaultdict(int)
    
    for pixel in boundary_pixels:
        b, g, r = pixel
        category, hex_color = categorize_color([b, g, r])
        if category not in ["white", "black", "other"]:
            color_categories[category] += 1
    
    # Return the most common non-white, non-black color category
    if color_categories:
        dominant_category = max(color_categories.items(), key=lambda x: x[1])[0]
        
        # Return standardized hex color for the category
        if dominant_category == "blue":
            return "#0000FF"
        elif dominant_category == "red":
            return "#FF0000"
        elif dominant_category == "green":
            return "#00FF00"
    
    return None

def ensure_contour_closure(contour, tolerance=5.0):
    """
    Ensure the contour forms a closed loop by checking if start and end points are close enough.
    Returns a closed contour.
    """
    if len(contour) < 3:
        return contour
    
    start_point = contour[0][0]
    end_point = contour[-1][0]
    
    # Calculate distance between start and end points
    distance = np.linalg.norm(start_point - end_point)
    
    # If points are not close enough, add the start point at the end to close the contour
    if distance > tolerance:
        # Reshape the start point to match contour dimensions: [[x, y]]
        start_point_reshaped = contour[0].reshape(1, 1, 2)
        closed_contour = np.vstack([contour, start_point_reshaped])
        print(f"  🔒 Closed contour: start-end distance was {distance:.2f} pixels")
        return closed_contour
    
    return contour

def is_contour_closed(contour, tolerance=5.0):
    """
    Check if a contour is closed by verifying start and end points are sufficiently close.
    """
    if len(contour) < 3:
        return False
    
    start_point = contour[0][0]
    end_point = contour[-1][0]
    distance = np.linalg.norm(start_point - end_point)
    
    return distance <= tolerance

def smart_curve_fitting(contour, angle_threshold=25, min_curve_angle=120):
    """
    Optimized hybrid approach: uses lines for straight segments, curves for curved segments
    Preserves the actual shape while smoothing where appropriate
    """
    if len(contour) < 3:
        return None
    
    # Ensure contour is closed before processing
    contour = ensure_contour_closure(contour)
    
    # Conservative simplification to remove noise but keep important features
    contour_length = cv2.arcLength(contour, True)
    epsilon = 0.0015 * contour_length  # Balanced simplification
    approx = cv2.approxPolyDP(contour, epsilon, True)
    
    if len(approx) < 3:
        return None
    
    points = [point[0] for point in approx]
    
    # Closure check and enforcement
    start_point = points[0]
    end_point = points[-1]
    distance_to_close = np.linalg.norm(np.array(start_point) - np.array(end_point))
    
    closure_threshold = 10.0  # pixels
    is_closed = distance_to_close <= closure_threshold
    
    if not is_closed:
        print(f"  ⚠️  Simplified contour not closed, distance: {distance_to_close:.2f}")
        # Force closure by adding start point at the end
        points.append(points[0])
        print("  🔒 Forced closure on simplified points")
        is_closed = True
    
    path_data = f"M {points[0][0]},{points[0][1]}"
    
    n = len(points)
    i = 1
    
    while i < n:
        # Handle wrap-around for closed paths
        current_point = points[i]
        prev_point = points[i-1]
        next_point = points[(i+1) % n]  # Wrap around for closed paths
        
        # For the last segment in a closed path, ensure we connect back to start
        if i == n-1 and is_closed:
            path_data += f" L {points[0][0]},{points[0][1]}"
            break
        
        # Check if we have enough points for curve analysis
        if i < n - 1 or (is_closed and n > 3):
            # Calculate vectors and angle
            vec1 = np.array([prev_point[0] - current_point[0], prev_point[1] - current_point[1]])
            vec2 = np.array([next_point[0] - current_point[0], next_point[1] - current_point[1]])
            
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 > 0 and norm2 > 0:
                # Normalize vectors
                vec1 = vec1 / norm1
                vec2 = vec2 / norm2
                
                # Calculate angle between segments
                dot_product = np.clip(np.dot(vec1, vec2), -1.0, 1.0)
                angle = np.degrees(np.arccos(dot_product))
                
                # Decision logic:
                # - Sharp angles (< threshold): use straight lines
                # - Gentle curves: use quadratic bezier
                if angle < angle_threshold:
                    # Sharp corner - use line
                    path_data += f" L {current_point[0]},{current_point[1]}"
                    i += 1
                else:
                    # Gentle curve - use quadratic bezier
                    # Use the next point as the end point, current as control
                    end_point = next_point
                    path_data += f" Q {current_point[0]},{current_point[1]} {end_point[0]},{end_point[1]}"
                    i += 2  # Skip the next point since we used it in the curve
            else:
                # Fallback to line
                path_data += f" L {current_point[0]},{current_point[1]}"
                i += 1
        else:
            # Last point or not enough points - use line
            path_data += f" L {current_point[0]},{current_point[1]}"
            i += 1
    
    # Always close the path with Z
    path_data += " Z"
    
    # Final closure verification
    print(f"  {'✅' if is_closed else '⚠️'} Path closure: {is_closed} (distance: {distance_to_close:.2f}px)")
    
    return path_data

def filter_structures_by_area(structures, max_count):
    """
    Filter structures by area, keeping only the largest max_count structures
    structures: list of tuples (area, data)
    max_count: maximum number of structures to keep
    Returns: filtered list
    """
    if max_count <= 0:
        return []
    
    # Sort by area in descending order (largest first)
    structures.sort(key=lambda x: x[0], reverse=True)
    
    # Keep only the largest max_count structures
    if max_count < len(structures):
        print(f"   Keeping only {max_count} largest structures (discarding {len(structures) - max_count})")
        return structures[:max_count]
    else:
        print(f"   Keeping all {len(structures)} structures")
        return structures

def create_final_svg_color_categories(image_path, output_svg="peanut_smart.svg", config_path="config.yaml"):
    """
    Create SVG with colors categorized into blue, red, green and white background ignored
    Using smart curve fitting for optimal shape preservation and smoothness
    RED IS RESERVED FOR POINTS ONLY - all red shapes become point markers at their center
    Number of structures for each color is controlled by YAML config file
    """
    print(f"⚡ Creating categorized color outline with smart curve fitting: {output_svg}")
    print("🎯 NOTE: Red is reserved exclusively for point markers - all red shapes become points")
    
    # Load configuration for all color categories
    max_red_dots, max_blue_paths, max_green_paths = load_config(config_path)
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not load image: {image_path}")
        return False
    
    height, width = img.shape[:2]
    print(f"Image size: {width}x{height}")
    
    # Convert to grayscale for contour detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Use multiple thresholding methods to capture all colored strokes
    binary1 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 5)
    
    _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Combine both methods
    combined = cv2.bitwise_or(binary1, binary2)
    
    # Conservative cleaning
    kernel = np.ones((3,3), np.uint8)
    cleaned = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel, iterations=1)
    
    # Find contours WITH hierarchy - this is key!
    contours, hierarchy = cv2.findContours(cleaned, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    
    print(f"Found {len(contours)} total contours")
    
    if contours:
        # Create SVG
        dwg = Drawing(output_svg, size=(width, height))
        
        # Storage for all structures by type
        all_red_points = []    # Will store tuples of (area, center, is_small_point)
        blue_structures = []   # Will store tuples of (area, contour)
        green_structures = []  # Will store tuples of (area, contour)
        
        # Calculate image area for relative sizing
        total_image_area = width * height
        
        kept_contours = 0
        skipped_contours = 0
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            perimeter = cv2.arcLength(contour, True)
            
            print(f"Contour {i}: area={area:.1f}, perimeter={perimeter:.1f}, points={len(contour)}")
            
            # First, check if this is a small point
            point_center = detect_points(contour)
            if point_center:
                # Store small points with their area for unified sorting
                all_red_points.append((area, point_center, True))
                kept_contours += 1
                print(f"  ✅ Small point found: area={area:.1f}")
                continue  # Skip further processing for small points
            
            # For non-points, apply regular filters
            min_area = 150
            max_area = total_image_area * 0.8
            
            if area < min_area or area > max_area:
                skipped_contours += 1
                continue
            
            # Filter 2: Hierarchy-based filtering - only keep top-level contours
            if hierarchy is not None and hierarchy[0][i][3] != -1:
                skipped_contours += 1
                continue
            
            # Filter 3: Solidarity check
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                if circularity < 0.01:  
                    skipped_contours += 1
                    continue
            
            # Detect and categorize the color
            stroke_color = detect_dominant_stroke_color(contour, img)
            
            if stroke_color:
                # ⭐ CRITICAL: If the color is red, store for unified sorting
                if stroke_color == "#FF0000":
                    center = get_contour_center(contour)
                    if center:
                        # Store red structure with area for unified sorting
                        all_red_points.append((area, center, False))
                        print(f"  🔴 Red structure found: area={area:.1f}, center=({center[0]}, {center[1]})")
                    else:
                        print(f"  ⚠️  Red shape has no center, skipping")
                
                # Store blue structures for filtering
                elif stroke_color == "#0000FF":
                    blue_structures.append((area, contour))
                    print(f"  🔵 Blue structure found: area={area:.1f}")
                
                # Store green structures for filtering  
                elif stroke_color == "#00FF00":
                    green_structures.append((area, contour))
                    print(f"  🟢 Green structure found: area={area:.1f}")
                    
                kept_contours += 1
            else:
                skipped_contours += 1
        
        # ⭐ FILTER ALL STRUCTURES BY CONFIGURED LIMITS
        
        # Filter red points
        if all_red_points:
            print(f"\n🔴 Found {len(all_red_points)} total red points/structures")
            print("   Sorting by area (largest to smallest):")
            for i, (area, center, is_small_point) in enumerate(all_red_points):
                point_type = "small point" if is_small_point else "red structure"
                print(f"   {i+1}. Area: {area:.1f}, Type: {point_type}, Center: ({center[0]}, {center[1]})")
            
            all_red_points = filter_structures_by_area(all_red_points, max_red_dots)
        
        # Filter blue paths
        if blue_structures:
            print(f"\n🔵 Found {len(blue_structures)} blue structures")
            print("   Sorting by area (largest to smallest):")
            for i, (area, contour) in enumerate(blue_structures):
                print(f"   {i+1}. Area: {area:.1f}")
            
            blue_structures = filter_structures_by_area(blue_structures, max_blue_paths)
        
        # Filter green paths  
        if green_structures:
            print(f"\n🟢 Found {len(green_structures)} green structures")
            print("   Sorting by area (largest to smallest):")
            for i, (area, contour) in enumerate(green_structures):
                print(f"   {i+1}. Area: {area:.1f}")
            
            green_structures = filter_structures_by_area(green_structures, max_green_paths)
        
        print(f"\n📊 Filtering results: {kept_contours} kept, {skipped_contours} skipped")
        print(f"📍 Final red points: {len(all_red_points)}")
        print(f"🔵 Final blue paths: {len(blue_structures)}") 
        print(f"🟢 Final green paths: {len(green_structures)}")
        
        # Process blue paths with smart curve fitting
        total_paths = 0
        print(f"\n🔵 Processing {len(blue_structures)} blue paths")
        for area, contour in blue_structures:
            path_data = smart_curve_fitting(contour)
            
            if path_data:
                dwg.add(dwg.path(
                    d=path_data,
                    fill="none",
                    stroke="#0000FF",
                    stroke_width=2,
                    stroke_linecap="round",
                    stroke_linejoin="round"
                ))
                total_paths += 1
        
        # Process green paths with smart curve fitting
        print(f"\n🟢 Processing {len(green_structures)} green paths")
        for area, contour in green_structures:
            path_data = smart_curve_fitting(contour)
            
            if path_data:
                dwg.add(dwg.path(
                    d=path_data,
                    fill="none",
                    stroke="#00FF00", 
                    stroke_width=2,
                    stroke_linecap="round",
                    stroke_linejoin="round"
                ))
                total_paths += 1
        
        # Process points with custom markers - ALWAYS USE RED FOR POINTS
        print(f"\n🔴 Processing {len(all_red_points)} final red points as simple dots")
        total_points_added = 0
        for area, center, is_small_point in all_red_points:
            x, y = center
            point_data = create_point_marker(x, y, radius=4)  # Simple dot with radius 4
            
            # Create a simple filled circle for the point
            dwg.add(dwg.circle(
                center=(point_data['cx'], point_data['cy']),
                r=point_data['r'],
                fill="#FF0000",  # Filled red
                stroke="none"    # No border
            ))
            total_points_added += 1
            point_type = "small point" if is_small_point else "red structure"
            print(f"    ✅ Added red dot at ({x}, {y}) - {point_type}, area={area:.1f}")
        
        dwg.save()
        print(f"✅ SVG saved: {output_svg}")
        print(f"🎨 Final breakdown:")
        print(f"   Blue paths: {len(blue_structures)}")
        print(f"   Green paths: {len(green_structures)}")
        print(f"   Red points: {total_points_added}")
        print(f"   Configuration: red_dots={max_red_dots}, blue_paths={max_blue_paths}, green_paths={max_green_paths}")
        
        if total_points_added == 0 and total_paths == 0:
            print("❕ No structures were detected.")
        
        return total_paths + total_points_added > 0
    else:
        print("❌ No contours found")
        return False

if __name__ == "__main__":
    input_image = "../../tests/inputs/colors.jpg"
    create_final_svg_color_categories(input_image, "colors.svg")