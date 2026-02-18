# Mapping the Shadow Economy: Informal Markets in Brazil

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)

## Project Overview
This repository contains the source code for my Master's Thesis in Public Policy (University of Chicago). The project develops a computer vision pipeline to detect, map, and analyze the spatial distribution of informal markets ("camelôs") in São Paulo, Brazil.

By integrating **Google Street View (GSV)** imagery, **Roboflow** object detection, and **VIIRS** satellite nighttime lights, this tool quantifies the "Shadow Economy" at a granular street level, offering new insights for urban planning and economic policy.

## Methodology
The pipeline operates in three stages:
1.  **Data Collection (`sp_real_shape_scan.py`):**
    * Automates the retrieval of geolocated street-level imagery using the Google Maps Static API.
    * Scans coordinates based on official shapefiles of São Paulo's urban grid.
2.  **Object Detection:**
    * Utilizes a custom-trained YOLOv8 model (via Roboflow) to identify street vendors, stalls, and informal commerce markers.
3.  **Analysis & Visualization (`visualize_map.py`):**
    * Correlates vendor density with socio-economic indicators.
    * Generates interactive heatmaps (`sp_hexbin_map.html`) to visualize commercial hotspots.

## Key Files
* `sp_real_shape_scan.py`: Main script for the scanning algorithm.
* `visualize_map.py`: Generates hexbin maps and spatial statistics.
* `build_thesis_dataset.py`: Aggregates raw detection data into a structured dataset for regression analysis.
* `Shadow_Economy_Report.xlsx`: Preliminary findings and data exports.

## Usage
To run the scanning tool locally:

```bash
# Clone the repository
git clone [https://github.com/CarolBraga9/Informal-Markets-Brazil.git](https://github.com/CarolBraga9/Informal-Markets-Brazil.git)

# Install dependencies
pip install -r requirements.txt

# Run the scanner
python sp_real_shape_scan.py
