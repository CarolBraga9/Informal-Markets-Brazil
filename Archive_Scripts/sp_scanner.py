import requests
import os
import time
import csv
from roboflow import Roboflow

# --- CONFIGURATION ---
GOOGLE_API_KEY = "AIzaSyBMMzyleMtj3XgPgBlEhNvQMrZbH8XSQgw"
ROBOFLOW_API_KEY = "t2jq94gHItiL5ZSLhwMG" 
PROJECT_NAME = "camelo-detection-v1" 
VERSION = 1

# --- SCAN SETTINGS (Rua 25 de Marco, SP) ---
START_LAT = -23.543167
START_LON = -46.629333

# 3x3 Grid = 9 total points to check (Small test)
GRID_SIZE = 3 
STEP_SIZE = 0.0005 # Approx 50 meters apart

OUTPUT_FOLDER = "sp_scan_images"
CSV_FILE = "sp_market_map.csv"

# --- SETUP ---
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print("Connecting to Roboflow...")
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project(PROJECT_NAME)
model = project.version(VERSION).model

# Create the CSV file
f = open(CSV_FILE, 'w', newline='')
writer = csv.writer(f)
writer.writerow(["Lat", "Lon", "Date", "Vendor_Count", "Stall_Count", "Merch_Count", "Image_File"])

# --- THE SCANNER ---
def scan_location(lat, lon):
    # 1. CHECK GOOGLE METADATA (Is there a photo? Is it new?)
    meta_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={GOOGLE_API_KEY}"
    try:
        meta = requests.get(meta_url).json()
    except:
        return

    if meta.get('status') != 'OK':
        print(f"No street view at {lat:.5f}, {lon:.5f}")
        return

    date = meta.get('date', '') # Returns "YYYY-MM"
    if not date: return
    
    year = int(date.split('-')[0])

    # 2. FILTER: Only 2023, 2024, 2025, 2026
    if year >= 2023:
        print(f"Found {date} data! Downloading image...")
        
        # 3. DOWNLOAD IMAGE
        img_url = f"https://maps.googleapis.com/maps/api/streetview?size=640x640&location={lat},{lon}&fov=90&key={GOOGLE_API_KEY}"
        img_data = requests.get(img_url).content
        
        filename = f"{OUTPUT_FOLDER}/sp_{lat}_{lon}_{date}.jpg"
        with open(filename, 'wb') as handler:
            handler.write(img_data)
        
        # 4. DETECT VENDORS
        # confidence=15 means "count it if 15% sure"
        results = model.predict(filename, confidence=15, overlap=30).json()
        predictions = results['predictions']
        
        vendors = 0
        stalls = 0
        merch = 0
        
        # Loop through found objects
        for p in predictions:
            c = p['class']
            # Check for ALL variations of names you might have used
            if c == "vendor" or c == "street_vendor": vendors += 1
            if c == "stall" or c == "vendor_stall": stalls += 1
            if c == "merchandise" or c == "merchandise_display": merch += 1

        print(f"   -> Result: {vendors} Vendors, {stalls} Stalls, {merch} Merch.")

        # 5. SAVE TO CSV
        writer.writerow([lat, lon, date, vendors, stalls, merch, filename])
        
    else:
        print(f"Skipping: Data too old ({year})")

# --- RUN GRID ---
print(f"Starting Grid Scan...")
offset = range(-(GRID_SIZE//2), (GRID_SIZE//2) + 1)

for i in offset:
    for j in offset:
        lat = START_LAT + (i * STEP_SIZE)
        lon = START_LON + (j * STEP_SIZE)
        scan_location(lat, lon)
        time.sleep(0.1)

f.close()
print(f"DONE! Open {CSV_FILE} to see your map data.")