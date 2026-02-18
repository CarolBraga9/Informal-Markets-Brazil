import requests
import os
import time
import csv
import numpy as np
from roboflow import Roboflow
from shapely.geometry import Point, Polygon

# --- 1. CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyBMMzyleMtj3XgPgBlEhNvQMrZbH8XSQgw"
ROBOFLOW_API_KEY = "t2jq94gHItiL5ZSLhwMG"
PROJECT_NAME = "camelo-detection-v1"
VERSION = 1

# WALLET GUARD: Limit points to prevent overspending
MAX_POINTS_LIMIT = 6000 

# GRID SETTINGS (High Resolution)
STEP_SIZE = 0.0055  # ~600 meters

OUTPUT_FOLDER = "sp_polygon_images"
CSV_FILE = "sp_polygon_map.csv"

# --- 2. DEFINE THE "URBAN POLYGON" (The Cookie Cutter) ---
# This shape traces the URBAN area, excluding the forests (North) and Dams (South).
# It looks like a rough diamond/star shape.
SP_URBAN_COORDS = [
    (-23.400, -46.750), # NW: Perus / Anhanguera
    (-23.400, -46.600), # N: Tremembé (Forest Edge)
    (-23.460, -46.450), # NE: Ermelino Matarazzo
    (-23.550, -46.360), # E: Itaquera / Guaianases Limit
    (-23.630, -46.420), # SE: São Mateus
    (-23.720, -46.600), # S: Grajaú (Urban Limit, before the dense reservoir)
    (-23.720, -46.750), # SW: M'Boi Mirim / Jardim Ângela
    (-23.600, -46.800), # W: Campo Limpo / Butantã
    (-23.500, -46.830), # W: Pirituba / Jaraguá
    (-23.400, -46.750)  # Close the loop
]
urban_polygon = Polygon(SP_URBAN_COORDS)

# --- 3. SETUP ---
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Resume Capability
processed_coords = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row:
                processed_coords.add(f"{float(row[0]):.4f},{float(row[1]):.4f}")

# --- 4. GENERATE SMART GRID ---
# We create a big box first, then throw away points outside the polygon
lat_min, lon_min, lat_max, lon_max = urban_polygon.bounds
lat_points = np.arange(lat_min, lat_max, STEP_SIZE)
lon_points = np.arange(lon_min, lon_max, STEP_SIZE)

valid_points = []
for lat in lat_points:
    for lon in lon_points:
        if urban_polygon.contains(Point(lat, lon)):
            valid_points.append((lat, lon))

print("-" * 40)
print(f"   SAO PAULO SMART SCAN (POLYGON FILTER)")
print("-" * 40)
print(f"Polygon Area Defined: ~900 km² (Urban Only)")
print(f"Grid Resolution: ~600m")
print(f"Points Inside Urban Shape: {len(valid_points)}")
print(f"Already Scanned: {len(processed_coords)}")
print("-" * 40)

if len(processed_coords) >= MAX_POINTS_LIMIT:
    print("⚠️ Limit reached. Increase MAX_POINTS_LIMIT or delete CSV to restart.")
    exit()

user_input = input(f"Start Smart Scan of {len(valid_points)} points? (yes/no): ")
if user_input.lower() != 'yes': exit()

# --- 5. INITIALIZE AI ---
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project(PROJECT_NAME)
model = project.version(VERSION).model

f = open(CSV_FILE, 'a', newline='')
writer = csv.writer(f)
if os.path.getsize(CSV_FILE) == 0:
    writer.writerow(["Lat", "Lon", "Date", "Vendor_Count", "Stall_Count", "Image_File"])

# --- 6. RUN LOOP ---
points_scanned = 0
credits_used = 0

for lat, lon in valid_points:
    # 1. Check Resume
    if f"{lat:.4f},{lon:.4f}" in processed_coords:
        continue
    
    # 2. Check Limit
    if (len(processed_coords) + points_scanned) >= MAX_POINTS_LIMIT:
        print(f"\nLimit reached ({MAX_POINTS_LIMIT}). Saving...")
        break
        
    print(f"Scanning... {points_scanned+1}/{len(valid_points) - len(processed_coords)} | Hits: {credits_used}", end='\r')

    # 3. Google Metadata Check (Free)
    try:
        meta_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={GOOGLE_API_KEY}"
        meta = requests.get(meta_url, timeout=3).json()
        
        if meta.get('status') == 'OK' and meta.get('date'):
            year = int(meta['date'].split('-')[0])
            
            # 4. Only Spend Money on 2022+ Data
            if year >= 2022:
                img_url = f"https://maps.googleapis.com/maps/api/streetview?size=640x640&location={lat},{lon}&fov=90&key={GOOGLE_API_KEY}"
                img_data = requests.get(img_url).content
                credits_used += 1
                
                filename = f"{OUTPUT_FOLDER}/poly_{lat:.5f}_{lon:.5f}_{meta['date']}.jpg"
                with open(filename, 'wb') as h:
                    h.write(img_data)
                
                # 5. Roboflow AI
                res = model.predict(filename, confidence=40, overlap=30).json()
                vendors = 0
                stalls = 0
                for p in res['predictions']:
                    if p['class'] in ["vendor", "street_vendor"]: vendors += 1
                    if p['class'] in ["stall", "vendor_stall"]: stalls += 1
                
                writer.writerow([lat, lon, meta['date'], vendors, stalls, filename])
                f.flush()
                points_scanned += 1
                
                if vendors > 0:
                    print(f" HIT! {vendors} vendors found at {lat:.4f}, {lon:.4f}")
                    
        time.sleep(0.05)

    except Exception as e:
        print(f"Error: {e}")
        continue

f.close()
print(f"\nDONE! Smart Scan saved to {CSV_FILE}")