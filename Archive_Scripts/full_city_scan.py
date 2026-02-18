import requests
import os
import time
import csv
from roboflow import Roboflow

# --- 1. CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyBMMzyleMtj3XgPgBlEhNvQMrZbH8XSQgw"
ROBOFLOW_API_KEY = "t2jq94gHItiL5ZSLhwMG"
PROJECT_NAME = "camelo-detection-v1"
VERSION = 1

# --- 2. DEFINE THE SCAN AREA (Brás / 25 de Marco / Sé) ---
# Centered on the main market area
START_LAT = -23.543167
START_LON = -46.629333

# 20x20 Grid = 400 total checks
# This covers roughly a 1km x 1km block of the city center
GRID_SIZE = 20 
STEP_SIZE = 0.0005  # Approx 50 meters between points

OUTPUT_FOLDER = "sp_full_scan_images"
CSV_FILE = "full_city_market_map.csv"

# --- 3. SETUP ---
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print("Initializing AI Model...")
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project(PROJECT_NAME)
model = project.version(VERSION).model

# Create the CSV file
f = open(CSV_FILE, 'w', newline='')
writer = csv.writer(f)
writer.writerow(["Lat", "Lon", "Date", "Vendor_Count", "Stall_Count", "Merch_Count", "Image_File"])

# --- 4. THE SCANNER ENGINE ---
def scan_location(lat, lon):
    # A. Check if image exists & is new (2023-2026)
    meta_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={GOOGLE_API_KEY}"
    try:
        meta = requests.get(meta_url, timeout=5).json()
    except:
        return # Skip if network error

    if meta.get('status') != 'OK':
        return

    date = meta.get('date', '')
    if not date: return
    
    year = int(date.split('-')[0])

    # FILTER: Only keep fresh data (Post-Pandemic)
    if year >= 2023:
        # B. Download Image
        img_url = f"https://maps.googleapis.com/maps/api/streetview?size=640x640&location={lat},{lon}&fov=90&key={GOOGLE_API_KEY}"
        img_data = requests.get(img_url).content
        
        filename = f"{OUTPUT_FOLDER}/sp_{lat:.6f}_{lon:.6f}_{date}.jpg"
        with open(filename, 'wb') as handler:
            handler.write(img_data)
        
        # C. Run AI Detection
        # Using 40% confidence to reduce false positives (pedestrians)
        try:
            results = model.predict(filename, confidence=40, overlap=30).json()
            predictions = results['predictions']
        except:
            print(f"   [Error] AI failed on {filename}")
            return

        vendors = 0
        stalls = 0
        merch = 0
        
        for p in predictions:
            c = p['class']
            if c == "vendor" or c == "street_vendor": vendors += 1
            if c == "stall" or c == "vendor_stall": stalls += 1
            if c == "merchandise" or c == "merchandise_display": merch += 1

        # Only save to CSV if we actually found something interesting
        # (This keeps your map clean of empty streets)
        if vendors > 0 or stalls > 0 or merch > 0:
            print(f"[HIT] {date} @ {lat:.5f},{lon:.5f}: {vendors} Vendors, {stalls} Stalls")
            writer.writerow([lat, lon, date, vendors, stalls, merch, filename])
        else:
            print(f"[...] {date} @ {lat:.5f},{lon:.5f}: Empty street")
        
    else:
        # Optional: Print skipped old locations just to know it's working
        # print(f"[Skip] Old data ({year})")
        pass

# --- 5. RUN THE LOOP ---
print(f"Starting Massive Scan ({GRID_SIZE}x{GRID_SIZE} grid)...")
offset = range(-(GRID_SIZE//2), (GRID_SIZE//2) + 1)

total_checks = GRID_SIZE * GRID_SIZE
count = 0

for i in offset:
    for j in offset:
        count += 1
        lat = START_LAT + (i * STEP_SIZE)
        lon = START_LON + (j * STEP_SIZE)
        
        print(f"Scanning point {count}/{total_checks}...", end='\r')
        scan_location(lat, lon)
        
        # Sleep to prevent API rate limiting
        time.sleep(0.2)

f.close()
print(f"\nDONE! Full map data saved to {CSV_FILE}")