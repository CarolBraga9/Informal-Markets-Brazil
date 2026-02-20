# Mapping the Shadow Economy: Informal Markets in Brazil

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)

## Project Overview
This repository contains the source code for a research project completed during my Master of Public Policy at the University of Chicago. The project develops a computer vision pipeline to detect and map the spatial distribution of informal markets (*"camelôs"*) in São Paulo, Brazil.

Beyond visual mapping, the project integrates data from the **PNAD-C household survey** to estimate the informal income of these street vendors. By combining object detection with economic microdata, this tool quantifies the "Shadow Economy" at a granular street level, offering new insights for urban planning and economic policy.

## Methodology
The pipeline operates in three stages:
1.  **Data Collection (`sp_real_shape_scan.py`):**
    * Automates the retrieval of geolocated street-level imagery using the Google Maps Static API.
    * Scans coordinates based on official shapefiles of São Paulo's urban grid.
2.  **Object Detection:**
    * Utilizes a custom-trained YOLOv8 model (via Roboflow) to identify street vendors, stalls, and informal commerce markers.
3.  **Economic Analysis & Visualization (`visualize_map.py`):**
    * Constructs a synthetic dataset using **PNAD-C survey data** to map the estimated informal salaries of identified vendors.
    * Generates interactive heatmaps (`sp_hexbin_map.html`) to visualize commercial hotspots against socio-economic wealth indices.

## Key Files
* `sp_real_shape_scan.py`: Main script for the scanning algorithm.
* `visualize_map.py`: Generates hexbin maps and spatial statistics.
* `build_thesis_dataset.py`: Aggregates raw detection data into a structured dataset for regression analysis.
* `Shadow_Economy_Report.xlsx`: Preliminary findings and data exports.

## Project Structure

```text
Informal-Markets-Brazil/
├── .vscode/                   # VS Code workspace settings
├── Archive_Data/              # Sample detections and backup data
├── Archive_Scripts/           # Deprecated or old scraping scripts
├── Final_Results/             # Output maps, datasets, and figures
├── sp_real_shape_images/      # Raw Google Street View images (Excluded via .gitignore)
├── .env                       # API Keys (Local only, not tracked by Git)
├── .gitignore                 # Specifies which files Git should ignore
├── README.md                  # Project documentation
├── Shadow_Economy_Report.xlsx # Preliminary findings and data exports
├── build_thesis_dataset.py    # Aggregates raw data into structured dataset
├── create_presentation.py     # Script to generate final presentation visuals
├── organize_project.py        # Utility script for file management
├── sp_hexbin_map.html         # Interactive heatmap output
├── sp_real_shape_scan.py      # Main automated scanning script
└── visualize_map.py           # Generates spatial statistics and maps

## Usage
To run the scanning tool locally:

```bash
# Clone the repository
git clone [https://github.com/CarolBraga9/Informal-Markets-Brazil.git](https://github.com/CarolBraga9/Informal-Markets-Brazil.git)

# Install dependencies
pip install -r requirements.txt

# Run the scanner
python sp_real_shape_scan.py
