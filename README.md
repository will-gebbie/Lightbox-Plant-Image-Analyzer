# Lightbox Plant Image Analyzer

* This software aims to provide distribution of average leaf areas and "greenness" distributions for plants taken in a study where a lightbox is employed
* The lightbox should have a reference ruler on the base for pixel area calibration and each picture should be taken at a constant height
* In order for this to work, the height of each plant must be taken from the base and each leaf counted. If leaves are severly overlapping, then this
  will return inaccurate results in terms of leaf area; however, if all plants have overlapping leaves, then the relative inaccurate leaf areas will still
  have merit.

## Create conda environemnt with dependencies
`conda create -n lightbox -c conda-forge opencv seaborn scipy pandas`

`conda activate lightbox`

## Data and directories setup
* Image data has to be structured in nested directories such as the example below
* The nested directories structure has 1 parent directory and each subdirectory name represents the condition from which that plant was growing in
* In each condition directory should exist all of the images and the associated leaf_counts.csv and plant_heights.csv that have the associated metadata for each image
* In this repo are templates for leaf_counts.csv and plant_heights.csv with the appropriate column headers
### Directory Structure Example
* pictures
   * day_21
     * 100_H2O
       * IMG_5557.tiff
       * IMG_5558.tiff
       * leaf_counts.csv
       * plant_heights.csv
     * 50_H2O
       * IMG_5581.tiff
       * IMG_5582.tiff
       * leaf_counts.csv
       * plant_heights.csv
   * day_28
     * 100_H2O
       * IMG_6753.tiff
       * IMG_6754.tiff
       * leaf_counts.csv
       * plant_heights.csv
     * 50_H2O
       * IMG_6843.tiff
       * IMG_6844.tiff
       * leaf_counts.csv
       * plant_heights.csv



## Usage
1. Use hsv_thresholder.py on a couple of images to isolate leaves as much as possible using the Hue/Saturation/Value (HSV) min and max sliders. Press ctrl-c in terminal to exit the program

`python hsv_thresholder.py -i path/to/image`

2. Keep note of the min and max values used to make your thresholds
3. Use process_plant_images.py to perform an analysis on the leaf sizes and greenness distributions between conditions over the course of a study

`python process_plant_images.py -d path/to/parent_dir -c CAMERA_HEIGHT_IN_CM -t HMIN,HMAX SMIN,SMAX VMIN,VMAX -o path/to/output_dir`

For more detailed usage information: `python process_plant_images.py -h`

