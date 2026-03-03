#!/usr/bin/env python

import argparse
import glob
import os
import re
import sys
import cv2
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import datetime
from scipy.spatial import distance as dist
import pandas as pd


def keep_hsv_range(img, hsv_thresh_tuple):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    hmin, hmax = hsv_thresh_tuple[0]
    smin, smax = hsv_thresh_tuple[1]
    vmin, vmax = hsv_thresh_tuple[2]

    lower = np.array([hmin, smin, vmin])
    upper = np.array([hmax, smax, vmax])
    mask = cv2.inRange(hsv, lower, upper)

    only_thresh = cv2.bitwise_and(img, img, mask=mask)

    return only_thresh


def threshold_leaves(img):
    lab_img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    lab_img = cv2.medianBlur(lab_img, 5)

    # Green Channel
    a_channel = lab_img[:, :, 1]

    # Select only for green ~ 115 LAB
    _, thresh = cv2.threshold(a_channel, 115, 255, cv2.THRESH_BINARY_INV)

    masked = cv2.bitwise_and(img, img, mask=thresh)

    return masked


def green_distribution(img):
    coords = cv2.findNonZero(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))

    if coords is not None:
        rows = coords[:, :, 0]
        cols = coords[:, :, 1]
        greens = img[cols, rows, 1]
    else:
        greens = np.array([])

    return greens


def calibrate_pixel_area(img, plant_height, CAMERA_HEIGHT):
    image = img.copy()
    clone = img.copy()

    points = []
    pixel_distance = 0

    def click_event(event, x, y, flags, params):
        nonlocal points
        nonlocal image
        nonlocal pixel_distance

        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            cv2.circle(image, (x, y), 5, (0, 0, 255), -1)  # Draw a red circle
            cv2.imshow("Image", image)

        if len(points) == 2:
            # Draw the line connecting the two points
            cv2.line(image, points[0], points[1], (255, 0, 0), 2)  # Draw a blue line
            cv2.imshow("Image", image)

            # Calculate Euclidean distance
            pixel_distance = dist.euclidean(points[0], points[1])
            print(f"Selected distance in pixels: {pixel_distance:.2f}")

            # Put the distance text on the image
            midpoint_x, midpoint_y = int((points[0][0] + points[1][0]) / 2), int(
                (points[0][1] + points[1][1]) / 2
            )
            cv2.putText(
                image,
                f"{pixel_distance:.0f} px",
                (midpoint_x, midpoint_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 0),
                2,
            )
            cv2.imshow("Image", image)

            # Reset points for the next measurement
            points = []

    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Image", cv2.WND_PROP_FULLSCREEN, cv2.WND_PROP_FULLSCREEN)
    cv2.setMouseCallback("Image", click_event)

    while True:
        cv2.imshow("Image", image)
        key = cv2.waitKey(1) & 0xFF

        # If the 'q' key is pressed, break the loop
        if key == ord("q"):
            break
        # If the 'r' key is pressed, reset the image
        if key == ord("r"):
            image = clone.copy()
            points = []

    cv2.destroyAllWindows()

    if pixel_distance == 0:
        print("No measurement taken.")
        return 0

    # 1. Physical width of one pixel at the base (ground) in cm
    pixel_width_base_cm = 1.0 / pixel_distance

    # 2. Distance from camera to base and to plant
    dist_to_base = CAMERA_HEIGHT
    dist_to_plant = CAMERA_HEIGHT - plant_height

    # 3. Physical width of one pixel at the plant height in cm
    pixel_width_plant_cm = pixel_width_base_cm * (dist_to_plant / dist_to_base)

    # 4. Area of a single pixel at the plant height in cm^2
    area_cm2 = pixel_width_plant_cm**2

    return area_cm2


def calculate_leaf_area(img, pixel_area):
    total_green_pixels = cv2.countNonZero(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    return total_green_pixels * pixel_area


def parse_tuple(s):
    try:
        # Split the string by comma and convert elements to integers
        return tuple(map(int, s.split(",")))
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"'{s}' is not a valid tuple format (e.g., '1,2')"
        )


def graph_data(green_df, leaf_df, output_dir):
    plt.figure(figsize=(12, 8))
    greens_plot = sns.boxplot(
        green_df, x="Days", y="value", hue="Condition", palette="pastel"
    )
    plt.title("Leaf Green Color Distribution")
    plt.xlabel("Days Post Seed")
    plt.ylabel("Green Pixel Value")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "greens_plot.svg"))
    plt.clf()

    plt.figure(figsize=(12, 8))
    avg_leaf_plot = sns.boxplot(
        leaf_df, x="Days", y="value", hue="Condition", palette="pastel"
    )
    plt.title("Average Leaf Area")
    plt.xlabel("Days Post Seed")
    plt.ylabel("Leaf Area (cm^2)")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "avg_leaf_plot.svg"))
    plt.clf()


def main():

    parser = argparse.ArgumentParser(
        description="""
        Plant Image Processor: Calculates green color distribution and leaf area.
        
        REQUIRED DIRECTORY STRUCTURE:
        The script expects a nested directory structure representing time and treatment:
        /Parent_Dir
            /Day_0
                /Control
                    pic1.jpg, leaf_counts.csv, plant_heights.csv
                /Treatment_A
                    pic2.jpg, leaf_counts.csv, plant_heights.csv
            /Day_7
                ...
        
        CSV REQUIREMENTS:
        1. leaf_counts.csv: Must contain 'pic_filename' and 'leaf_count' columns.
        2. plant_heights.csv: Must contain 'pic_filename' and 'height' columns.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        INTERACTIVE CALIBRATION MODE:
        When the program starts, it will open a window for pixel-to-cm calibration.
        
        1. Left-Click two points on the image representing a known distance 
           (e.g., a ruler or the width of a pot at the base).
        2. The distance in pixels will be displayed.
        3. Key Commands:
           - 'r' : Reset the points if you misclicked.
           - 'q' : Confirm the measurement and proceed to processing.
           
        The script uses the CAMERA_HEIGHT and the plant's height from the CSV to 
        adjust the pixel-to-cm ratio for the specific canopy level.
        """,
    )

    parser.add_argument(
        "-d",
        "--directory",
        help="Parent directory containing 'Day_X/Condition' subdirectories.",
        required=True,
    )

    parser.add_argument(
        "-c",
        "--camera-height",
        default=45,
        type=int,
        help="Height of the camera lens from the ground in cm (default: 45).",
        dest="cam_height",
    )

    parser.add_argument(
        "-t",
        "--thresholds",
        type=parse_tuple,
        nargs=3,
        help="""Three space-separated tuples for HSV: 'Hmin,Hmax' 'Smin,Smax' 'Vmin,Vmax'.
                Example: --thresholds 30,90 50,255 20,255""",
        required=True,
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output directory for SVG graphs and CSV data (default: current dir).",
        default=".",
    )

    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    greens_dflist = []
    leaves_dflist = []

    PIXEL_SAMPLE_SIZE = 10000
    pixel_area = 0

    CAMERA_HEIGHT = args.cam_height

    for root, dirs, files in os.walk(args.directory):
        if root.count("/") > 1:
            day_str, cond = root.split("/")[1:]

            # Extract number from day string
            pattern = r"-?\d*\.?\d+"
            matches = re.findall(pattern, day_str)
            day = int(matches[0])

            leaf_counts = pd.read_csv(os.path.join(root, "leaf_counts.csv"))
            plant_heights = pd.read_csv(os.path.join(root, "plant_heights.csv"))

            current_dir_greens = []
            current_dir_leaf_areas = []

            print(f"Processing: {root}")

            for pic in files:
                if pic.endswith((".tiff", ".jpeg", ".jpg")):
                    img = cv2.imread(os.path.join(root, pic))
                    plant_height = plant_heights.loc[
                        plant_heights["pic_filename"] == pic, "height"
                    ]

                    if plant_height.empty:
                        raise ValueError(
                            f"There is no plant height associated with {os.path.join(root, pic)} in the corresponding plant_heights.csv"
                        )

                    while pixel_area == 0:
                        pixel_area = calibrate_pixel_area(
                            img, plant_height.iloc[0], CAMERA_HEIGHT
                        )

                    no_hsv = keep_hsv_range(img, args.thresholds)
                    leaf_thresh = threshold_leaves(no_hsv)

                    # Green Distribution
                    greens = green_distribution(leaf_thresh).flatten()
                    if greens is not None and greens.any():
                        # Randomly sample pixels to save massive amounts of memory
                        if len(greens) > PIXEL_SAMPLE_SIZE:
                            greens = np.random.choice(
                                greens, size=PIXEL_SAMPLE_SIZE, replace=False
                            )
                        current_dir_greens.extend(greens)

                    # Leaf Area
                    num_leaves = leaf_counts.loc[
                        leaf_counts["pic_filename"] == pic, "leaf_count"
                    ]
                    total_leaf_area = calculate_leaf_area(leaf_thresh, pixel_area)

                    if num_leaves.iloc[0] > 0:
                        avg_leaf_area = total_leaf_area / num_leaves.iloc[0]
                    else:
                        avg_leaf_area = 0

                    current_dir_leaf_areas.append(avg_leaf_area)

            if current_dir_greens:
                temp_greens_df = pd.DataFrame(
                    {
                        "Days": day,
                        "DataType": "Green Value",
                        "Condition": cond,
                        "value": current_dir_greens,
                    }
                )
                greens_dflist.append(temp_greens_df)

            if current_dir_leaf_areas:
                temp_leaves_df = pd.DataFrame(
                    {
                        "Days": day,
                        "DataType": "Average Leaf Area",
                        "Condition": cond,
                        "value": current_dir_leaf_areas,
                    }
                )
                leaves_dflist.append(temp_leaves_df)

    if greens_dflist:
        greens_final_df = pd.concat(greens_dflist, ignore_index=True)
        greens_final_df.to_csv(os.path.join(args.output, "greens.csv"))
    else:
        greens_final_df = pd.DataFrame()

    if leaves_dflist:
        leaves_final_df = pd.concat(leaves_dflist, ignore_index=True)
        leaves_final_df.to_csv(os.path.join(args.output, "leaves.csv"))
    else:
        leaves_final_df = pd.DataFrame()

    if not greens_final_df.empty and not leaves_final_df.empty:
        graph_data(greens_final_df, leaves_final_df, args.output)
    else:
        print("No data was collected to graph.")


if __name__ == "__main__":
    main()
