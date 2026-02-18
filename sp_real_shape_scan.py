import requests
import os
import time
import csv
import shutil  # <--- FIXED TYPO (was shutilit)
import numpy as np
from roboflow import Roboflow
from shapely.geometry import Point, shape

# --- 1. CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyBMMzyleMtj3XgPgBlEhNvQMrZbH8XSQgw"
ROBOFLOW_API_KEY = "t2jq94gHItiL5ZSLhwMG"
PROJECT_NAME = "camelo-detection-v1"

# VERSION: Keep at 3
VERSION = 3

# WALLET GUARD
MAX_POINTS_LIMIT = 10000
STEP_SIZE = 0.004

# FOLDER SETUP 
MAIN_IMAGE_FOLDER = "Image_Banks/sp_real_shape_images"
TRAINING_FOLDER = "Image_Banks/For_Roboflow_Training" 
CSV_FILE = "sp_real_shape_map.csv"

# --- 2. FETCH OFFICIAL BOUNDARY ---
print("Downloading Official São Paulo Boundary...")
try:
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json"
    data = requests.get(url).json()
    sp_feature = next(f for f in data['features'] if f['properties']['id'] == '3550308')
    sp_polygon = shape(sp_feature['geometry'])
except Exception as e:
    print(f"Error loading map: {e}")
    exit()

# --- 3. SETUP ---
if not os.path.exists(MAIN_IMAGE_FOLDER):
    os.makedirs(MAIN_IMAGE_FOLDER)
if not os.path.exists(TRAINING_FOLDER):
    os.makedirs(TRAINING_FOLDER)

# Resume Capability
processed_coords = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f)
        try:
            next(reader, None) # Skip header
            for row in reader:
                if row:
                    processed_coords.add(f"{float(row[0]):.4f},{float(row[1]):.4f}")
        except csv.Error:
            pass 

# --- 4. GRID GENERATION ---
minx, miny, maxx, maxy = sp_polygon.bounds
lat_points = np.arange(miny, maxy, STEP_SIZE)
lon_points = np.arange(minx, maxx, STEP_SIZE)

valid_points = []
for lat in lat_points:
    for lon in lon_points:
        if sp_polygon.contains(Point(lon, lat)):
            valid_points.append((lat, lon))

print(f"OFFICIAL SHAPE SCAN: {len(valid_points)} points target.")

# --- 5. INITIALIZE AI ---
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project(PROJECT_NAME)
model = project.version(VERSION).model

# Open CSV for appending
f = open(CSV_FILE, 'a', newline='')
writer = csv.writer(f)

if os.path.getsize(CSV_FILE) == 0:
    writer.writerow(["Lat", "Lon", "Date", "Structure_Count", "Image_File"])

# --- 6. RUN LOOP ---
points_scanned = 0
credits_used = 0
TARGET_CLASSES = ["vendor_stall", "merchandise_display", "umbrella"]

for lat, lon in valid_points:
    if f"{lat:.4f},{lon:.4f}" in processed_coords: continue
    if (len(processed_coords) + points_scanned) >= MAX_POINTS_LIMIT: break
        
    print(f"Scanning... {points_scanned+1} | Hits: {credits_used}", end='\r')

    try:
        # 1. Check Metadata (Timeout increased to 15s)
        meta_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={GOOGLE_API_KEY}"
        meta = requests.get(meta_url, timeout=15).json()
        
        if meta.get('status') == 'OK' and meta.get('date'):
            year = int(meta['date'].split('-')[0])
            
            # 2. Download Image (Timeout increased to 20s)
            if year >= 2022:
                img_url = f"https://maps.googleapis.com/maps/api/streetview?size=640x640&location={lat},{lon}&fov=90&key={GOOGLE_API_KEY}"
                img_data = requests.get(img_url, timeout=20).content
                credits_used += 1
                
                filename = f"{MAIN_IMAGE_FOLDER}/real_{lat:.5f}_{lon:.5f}_{meta['date']}.jpg"
                with open(filename, 'wb') as h:
                    h.write(img_data)
                
                # 3. Predict (70% Confidence)
                try:
                    res = model.predict(filename, confidence=70, overlap=30).json()
                except Exception as model_error:
                    print(f"\nModel Error: {model_error}")
                    continue

                structure_count = 0
                for p in res['predictions']:
                    if p['class'] in TARGET_CLASSES:
                        structure_count += 1
                
                # Write to CSV
                writer.writerow([lat, lon, meta['date'], structure_count, filename])
                f.flush()
                points_scanned += 1
                
                if structure_count > 0:
                    training_filename = f"{TRAINING_FOLDER}/TRAIN_{lat:.5f}_{lon:.5f}.jpg"
                    shutil.copy(filename, training_filename)
                    print(f" HIT! Copied to training folder: {lat:.4f}, {lon:.4f}   ")
                    
        # Healthy Sleep: Wait 1 second between checks to be nice to the API
        time.sleep(1.0)
        
    except Exception as e:
        # If the internet fails, we print the error and WAIT 20 SECONDS.
        print(f"\n[Network Error] Pausing for 20 seconds to let WiFi recover... ({e})")
        time.sleep(20)
        continue

f.close()
print(f"\nDONE! Images with vendors are in {TRAINING_FOLDER}")