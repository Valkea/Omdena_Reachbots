"""
This script is for processing a video of laser-welding operations.
It uses computer vision techniques like Hough transform, Canny edge detection,
and coordinate transformations to create a trasformed images which is later
used by other models for inference.

Author: Raza Ahmad
"""
import cv2
import numpy as np
import math
from pathlib import Path


def rotate_point(x, y, angle_rad):
    """
    Rotates a point around the origin.

    Parameters:
        x (float): x-coordinate of the point
        y (float): y-coordinate of the point
        angle_rad (float): angle to rotate, in radians

    Returns:
        tuple: rotated coordinates as (new_x, new_y)
    """
    new_x = x * np.cos(angle_rad) - y * np.sin(angle_rad)
    new_y = x * np.sin(angle_rad) + y * np.cos(angle_rad)
    return int(new_x), int(new_y)


# Function to draw a triangle
def draw_triangle(img, vertices, color, thickness):
    """
    Draws a triangle on an image.

    Parameters:
        img (array-like): the image on which to draw
        vertices (list of tuples): the vertices of the triangle as (x, y) coordinates
        color (int): color of the triangle
        thickness (int): line thickness

    Returns:
        None
    """
    pts = np.array(vertices, np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(img, [pts], isClosed=True, color=color, thickness=thickness)


# Function to check if a point is inside a polygon
def is_near_polygon(pt, vertices, threshold):
    point = np.array(pt, dtype=np.float32)
    distance = cv2.pointPolygonTest(np.array([vertices], dtype=np.int32),
                                    (point[0], point[1]), True)

    if distance > 0:  # Point is inside the triangle
        return True
    elif abs(
            distance
    ) <= threshold:  # Point is outside but within the threshold distance
        return True

    return False  # Point is outside and beyond the threshold distance


def angle_difference(theta1, theta2):
    theta1 = theta1 % (2 * math.pi)
    theta2 = theta2 % (2 * math.pi)

    diff = abs(theta1 - theta2)

    if diff > math.pi:
        diff = 2 * math.pi - diff

    return diff


def extract_coordinates(binary_image):
    # After thresholding, the image is binary (0s and 255s).
    # The laser profile points will have the value 0 (black pixels)
    coords = np.column_stack(np.where(binary_image == 0))
    return coords[:, [1, 0]]  # Swap x and y


def transform_frame(frame,
                    bead_radius_threshold: float = 200.0,
                    lines_angular_threshold: float = 0.2,
                    polygon_threshold: float = 5.0):

    try:
        if frame is None:
            raise ValueError("Could not open or find the image.")
    except ValueError as e:
        print(e)
    if len(frame.shape) > 2 and frame.shape[2] == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresholded_image = cv2.threshold(frame, 0, 255,
                                         cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    edges = cv2.Canny(thresholded_image, 200, 255, apertureSize=7)
    # Define kernel for morphological operations

    coords = extract_coordinates(thresholded_image)

    # Probabilistic Hough Transform
    minLineLength = 100
    maxLineGap = 10
    lines = cv2.HoughLinesP(edges,
                            1,
                            np.pi / 180,
                            100,
                            minLineLength=minLineLength,
                            maxLineGap=maxLineGap)

    if lines is not None:
        lines = np.squeeze(lines)

        selected_lines = []
        line_params = [
        ]  # To store the parameters (slope and intercept) of each line

        if len(lines.shape) == 1:
            print('Only one hough line detected, Frame Passed')
            return None

        for x1, y1, x2, y2 in lines:
            # Calculate slope and intercept
            if x2 - x1 == 0:  # Vertical line
                continue
            m = (y2 - y1) / (x2 - x1)
            c = y1 - m * x1

            # Create an angle representation, note: arctan2 returns in the range [-π, π]
            theta = np.arctan2(y2 - y1, x2 - x1)

            # Check the new line against existing selected lines for similarity using angle difference
            # multiple hough lines will be detected so this is required to supress almost parallel lines
            if len(selected_lines) > 0:
                is_similar_to_existing_line = False
                for existing_theta in [params[1] for params in line_params]:
                    if angle_difference(
                            theta, existing_theta) < lines_angular_threshold:
                        is_similar_to_existing_line = True
                        break

                if is_similar_to_existing_line:
                    continue

            selected_lines.append((x1, y1, x2, y2))
            line_params.append((m, theta))

        # Initialize a blank image to store the final result
        # final_outliers_img = np.ones_like(
        #     frame) * 255  # Create a blank  images (with all white pixels)

        if len(line_params) == 2:
            m1, _ = line_params[0]
            m2, _ = line_params[1]
            c1 = selected_lines[0][1] - m1 * selected_lines[0][0]
            c2 = selected_lines[1][1] - m2 * selected_lines[1][0]

            # Calculate the intersection point
            xi = (c2 - c1) / (m1 - m2)
            yi = m1 * xi + c1

            # Filter out points that are not close to the intersection point
            distances_to_intersection = np.sqrt((coords[:, 0] - xi)**2 +
                                                (coords[:, 1] - yi)**2)
            coords = coords[distances_to_intersection < bead_radius_threshold]
            # cv2.circle(final_outliers_img, (int(xi), int(yi)), 5, 0, -1) #for visualization only
        else:
            # Handle the case where there is only one line
            print(
                'Only one line detected,cannot find Intersection, Frame Passed'
            )
            return None

        # Farthest point towards the lower left corner
        farthest_lower_left = coords[np.argmin(coords[:, 0] - coords[:, 1])]

        # Farthest point towards the lower right corner
        farthest_lower_right = coords[np.argmax(coords[:, 0] + coords[:, 1])]

        # final_outliers_img[coords[:, 1], coords[:, 0]] = 0

        # vertices (xi, yi), farthest_lower_left, and farthest_lower_right
        triangle_vertices = [(int(xi), int(yi)),
                             tuple(farthest_lower_left),
                             tuple(farthest_lower_right)]

        # # Draw the triangle used for visualization only
        # draw_triangle(final_outliers_img,
        #               triangle_vertices,
        #               color=0,
        #               thickness=1)

        #Using polygon_threshold (in pixels) to filter out points that are not close to the triangle

        # Filter out the coordinates based on the distance to the triangle
        coords_filtered = [
            pt for pt in coords
            if is_near_polygon(pt, triangle_vertices, polygon_threshold)
        ]

        # Reset the final_outliers_img_filtered to a blank image
        # final_outliers_img_filtered = np.ones_like(frame) * 255

        # # Redraw the remaining coordinates back to a binary image for visualization only
        # for x, y in coords_filtered:
        #     cv2.circle(final_outliers_img_filtered, (x, y), 3, 0, -1)
        # cv2.circle(final_outliers_img_filtered, farthest_lower_left, 8, 0, -1)
        # cv2.circle(final_outliers_img_filtered, farthest_lower_right, 18, 0,
        #            -1)

        # Define a new image for plotting the transformed points.qq
        transformed_image = np.ones((300, 300), np.uint8) * 255

        # Coordinates of the intersection point
        xi, yi = int(xi), int(yi)

        # Coordinates of the lower left corner
        llx, lly = farthest_lower_left

        # Translate the coordinates so the intersection point is the origin.
        translated_coords = [(x - xi, y - yi) for x, y in coords_filtered]
        translated_lower_left = (llx - xi, lly - yi)
        translated_lower_right = (farthest_lower_right[0] - xi,
                                  farthest_lower_right[1] - yi)

        # Calculate the angle to rotate all points so the line from the intersection to the lower left corner is parallel to the x-axis.
        angle_rad = np.arctan2(lly - yi, llx - xi)

        # Rotate and translate the coordinates.
        transformed_coords = [
            rotate_point(x, y, -angle_rad) for x, y in translated_coords
        ]

        transformed_lower_left = rotate_point(translated_lower_left[0],
                                              translated_lower_left[1],
                                              -angle_rad)

        transformed_lower_right = rotate_point(translated_lower_right[0],
                                               translated_lower_right[1],
                                               -angle_rad)

        # Translate points back to fit into 300x300 image by adding an offset to the points for visiblity on inside the transformed image
        offset_x = 50  # The new origin in the transformed image
        offset_y = 250  # The new origin in the transformed image

        for x, y in transformed_coords:
            # Translate the origin back to offset_x, offset_y
            translated_x, translated_y = x + offset_x, y + offset_y
            llp = transformed_lower_left[0] + offset_x, transformed_lower_left[
                1] + offset_y
            lrp = transformed_lower_right[
                0] + offset_x, transformed_lower_right[1] + offset_y
            if 0 <= translated_x < 500 and 0 <= translated_y < 500:
                transformed_image[translated_y, translated_x] = 0

        return transformed_image

    else:
        print('No hough lines detected, Frame Passed')
        return None


if __name__ == '__main__':

    #Video File path to be processed
    video_path = Path(
        'task-3-modeling/modelling_approaches/laser_profile_preprocess/data/Good Weld/nodefect2_microepsilon_profile_compressed.mp4'
    )
    #Required Threshold Values for laser profile extraction
    bead_radius_threshold = 200.0  # Radial distance of points from the intersection point
    lines_angular_threshold = 0.2  # Angular difference between two lines to supress parallel lines
    polygon_threshold = 5.0  # Distance threshold to filter out points that are not close to the triangle

    print(f'processing {video_path}')

    cap = cv2.VideoCapture(str(video_path))

    # Get the video FPS
    video_fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"The selected video frame rate is {video_fps} FPS")
    # Specify the desired FPS for frame sampling
    desired_fps = 25

    # Calculate the frame skipping rate
    skip_frames = int(video_fps / desired_fps)

    frame_count = 0

    is_paused = False
    # Loop through each frame in the video
    while cap.isOpened():
        if not is_paused:
            ret, frame = cap.read()

            if not ret:
                print("Can't receive frame. Exiting ...")
                break

            if frame_count % skip_frames == 0:
                idx = frame_count
                transformed_image = transform_frame(
                    frame,
                    bead_radius_threshold=bead_radius_threshold,
                    lines_angular_threshold=lines_angular_threshold,
                    polygon_threshold=polygon_threshold)
                if transformed_image is not None:

                    cv2.imshow('Transformed Image', transformed_image)
                else:
                    print('Frame Passed')
            key = cv2.waitKey(1)
            if key == ord('p'):  # Pause when 'p' is pressed
                is_paused = True
            elif key == ord('r'):  # Resume when 'r' is pressed
                is_paused = False
            elif key == ord('q'):  # Exit when 'q' is pressed
                break

            if not is_paused:
                frame_count += 1
