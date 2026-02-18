import os
import shutil

# --- CONFIGURATION ---
# These are the files we want to KEEP in the main folder (The "Active" Workflow)
KEEP_IN_ROOT = [
    "sp_real_shape_scan.py",      # The Official Scanner
    "build_thesis_dataset.py",    # The Database Builder
    "visualize_map.py",           # The Map Generator
    "create_presentation.py",     # The Excel Report Generator
    "harvest_training_images.py", # The Image Harvester
    "organize_project.py",        # This script
    "sp_real_shape_map.csv",      # Your latest scan data
    "sp_nighttime_lights.tif"     # Your satellite data
]

# Define the New Folder Structure
FOLDERS = {
    "Archive_Scripts": [
        "sp_scanner.py", "sp_macro_scan.py", "sp_polygon_scan.py", 
        "sp_full_city_scan.py", "full_city_scan.py", "audit_image.py", 
        "street_view_scraper.py", "fetch_economic_data.py", "merge_lights.py",
        "visualize_hexbin.py", "test.ipynb", "sp_macro_scanner.py"
    ],
    "Archive_Data": [
        "sp_macro_map.csv", "sp_polygon_map.csv", "sp_full_city_map.csv", 
        "sp_market_map.csv", "full_city_market_map.csv", 
        "final_shadow_economy_dataset.csv" # The old dataset
    ],
    "Image_Banks": [
        "sp_macro_images", "sp_polygon_images", "sp_full_scan_images", 
        "sp_scan_images", "street_view_images", "images_to_scan"
    ],
    "Final_Results": [
        "Shadow_Economy_Report.xlsx", 
        "map_money.html", "map_vendors.html", 
        "sp_shadow_economy_map.html", "final_thesis_dataset.csv"
    ]
}

print("--- ORGANIZING PROJECT FOLDERS ---")

for folder, files in FOLDERS.items():
    # 1. Create the folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created Folder: {folder}")
    
    # 2. Move the files
    for filename in files:
        if os.path.exists(filename):
            try:
                shutil.move(filename, f"{folder}/{filename}")
                print(f"Moved: {filename} -> {folder}/")
            except Exception as e:
                print(f"Error moving {filename}: {e}")

print("-" * 30)
print("CLEANUP COMPLETE!")
print("Your root folder now contains only your ACTIVE scripts.")
print("Check 'Final_Results' for your maps and reports.")
print("Check '99_Archive' for old experiments.")