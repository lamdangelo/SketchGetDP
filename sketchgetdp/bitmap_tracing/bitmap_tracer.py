import cv2
import numpy as np
from svgwrite import Drawing
from collections import defaultdict

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

def create_final_svg_color_categories(image_path, output_svg="peanut_smart.svg"):
    """
    Create SVG with colors categorized into blue, red, green and white background ignored
    Using smart curve fitting for optimal shape preservation and smoothness
    """
    print(f"⚡ Creating categorized color outline with smart curve fitting: {output_svg}")
    
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
        
        # Group contours by color category
        color_groups = defaultdict(list)
        
        # Calculate image area for relative sizing
        total_image_area = width * height
        
        kept_contours = 0
        skipped_contours = 0
        closed_contours = 0
        forced_closed_contours = 0
        
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            
            # Filter 1: Area-based filtering (moderate threshold)
            min_area = 150  # Balanced threshold
            max_area = total_image_area * 0.8
            
            if area < min_area or area > max_area:
                skipped_contours += 1
                continue
            
            # Filter 2: Hierarchy-based filtering - only keep top-level contours
            # hierarchy structure: [Next, Previous, First_Child, Parent]
            if hierarchy is not None and hierarchy[0][i][3] != -1:
                # This contour has a parent (it's nested inside another contour)
                # Often these are holes or internal details we don't want
                skipped_contours += 1
                continue
            
            # Filter 3: Solidarity check - contours should be reasonably solid
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                # Very low circularity often indicates fragmented/noisy contours
                if circularity < 0.01:  
                    skipped_contours += 1
                    continue
            
            # Check initial contour closure
            is_initially_closed = is_contour_closed(contour)
            if is_initially_closed:
                closed_contours += 1
            else:
                forced_closed_contours += 1
                print(f"  🔧 Contour {i} requires forced closure")
            
            # Detect and categorize the color
            stroke_color = detect_dominant_stroke_color(contour, img)
            
            if stroke_color:  # Only process if we found a valid color category
                color_groups[stroke_color].append(contour)
                kept_contours += 1
                print(f"✅ Keeping contour {i}: area {area:.0f}, Color: {stroke_color}, Closed: {is_initially_closed}")
            else:
                skipped_contours += 1
                print(f"❌ Skipping contour {i}: no valid color detected")
        
        print(f"\nFiltering results: {kept_contours} kept, {skipped_contours} skipped")
        print(f"Closure status: {closed_contours} naturally closed, {forced_closed_contours} forced closed")
        print(f"Color groups found after filtering:")
        for color, contours in color_groups.items():
            print(f"  {color}: {len(contours)} contours")
        
        # Process each color group with smart curve fitting
        total_paths = 0
        for color, contour_list in color_groups.items():
            for j, contour in enumerate(contour_list):
                print(f"🔄 Processing {color} contour {j+1}/{len(contour_list)}")
                path_data = smart_curve_fitting(contour)
                
                if path_data:
                    # Add smooth path with categorized color
                    dwg.add(dwg.path(
                        d=path_data,
                        fill="none",
                        stroke=color,
                        stroke_width=2,
                        stroke_linecap="round",
                        stroke_linejoin="round"
                    ))
                    total_paths += 1
                    print(f"  ✅ Successfully created path for {color} contour {j+1}")
                else:
                    print(f"❌ Failed to process {color} contour {j+1}")
        
        dwg.save()
        print(f"✅ Smart curve fitting SVG saved: {output_svg}")
        print(f"🎨 Final color breakdown:")
        for color, contours in color_groups.items():
            print(f"   {color}: {len(contours)} paths")
        print(f"📊 Total paths created: {total_paths}")
        
        if total_paths == 0:
            print("❌ WARNING: No paths were created in the SVG!")
            print("   Possible issues:")
            print("   - Color detection failing")
            print("   - Contours too complex for curve fitting")
            print("   - Image quality issues")
        
        print(f"\n✨ Smart curve fitting completed!")
        print(f"   - Lines used for sharp corners")
        print(f"   - Curves used for gentle bends") 
        print(f"   - Shape preservation optimized")
        print(f"   - Closure enforcement: {forced_closed_contours} contours were forced closed")
        return total_paths > 0
    else:
        print("❌ No contours found")
        return False

if __name__ == "__main__":
    input_image = "../../tests/inputs/colors.jpg"
    create_final_svg_color_categories(input_image, "colors.svg")