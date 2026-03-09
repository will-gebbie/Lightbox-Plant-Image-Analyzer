# Lightbox Plant Image Analyzer

- This software aims to provide distribution of total leaf canopy area/average leaf areas and "greenness" distributions for plants taken in a study where a lightbox is employed
- The lightbox should have a reference ruler on the base for pixel area calibration and each picture should be taken at a constant height
- In order for this to work, the height of each plant must be taken from the base and each leaf counted (if average leaf area is desired). If leaves are severly overlapping, then this
  will return inaccurate results in terms of leaf area; however, if all plants have overlapping leaves, then the relative inaccurate leaf areas will still
  have merit although total canopy area may be of more use.
- If there are other plants in the soil or other green artifacts that you do not wish to include in this analysis, remove these from the image before analysis via AI eraser tool or other means.

## Create conda environemnt with dependencies

`conda create -n lightbox -c conda-forge opencv seaborn scipy pandas`

`conda activate lightbox`

## Data and directories setup

- Image data has to be structured in nested directories such as the example below
- The nested directories structure has 1 parent directory and each subdirectory name represents the condition from which that plant was growing in
- In each condition directory should exist all of the images and the associated pic_metadata.csv that has the associated metadata for each image.
  A pic_metadata.csv template is available in this repo for use

### Directory Structure Example

- pictures
  - day_21
    - 100_H2O
      - IMG_5557.tiff
      - IMG_5558.tiff
      - pic_metadata.csv
    - 50_H2O
      - IMG_5581.tiff
      - IMG_5582.tiff
      - pic_metadata.csv
  - day_28
    - 100_H2O
      - IMG_6753.tiff
      - IMG_6754.tiff
      - pic_metadata.csv
    - 50_H2O
      - IMG_6843.tiff
      - IMG_6844.tiff
      - pic_metadata.csv

## Usage

1. Use hsv_thresholder.py on a couple of images to isolate leaves from the background as much as possible using the Hue/Saturation/Value (HSV) min and max sliders. Press ctrl-c in terminal to exit the program

`python hsv_thresholder.py -i path/to/image`

2. Keep note of the min and max values used to make your thresholds
3. Use process_plant_images.py to perform an analysis on the leaf canopy/leaf area sizes and greenness distributions between conditions over the course of a study

`python process_plant_images.py -d path/to/parent_dir -c CAMERA_HEIGHT_IN_CM -t HMIN,HMAX SMIN,SMAX VMIN,VMAX -o path/to/output_dir -l`

For more detailed usage information: `python process_plant_images.py -h`
Note: the -l/--leaf-area argument is required for average leaf area calculation. Without this flag, only the total leaf area canopy will be calculated
