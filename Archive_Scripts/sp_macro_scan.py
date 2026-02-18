import requests
import os
import time
import csv
import numpy as np
from roboflow import Roboflow

# --- 1. CONFIGURATION (Zero Cost Setup) ---
GOOGLE_API_KEY = "AIzaSyBMMzyleMtj3XgPgBlEhNvQMrZbH8XSQgw"
ROBOFLOW_API_KEY = "t2jq94gHItiL5ZSLhwMG"
PROJECT_NAME = "camelo-detection-v1"
VERSION = 1

# --- 2. DEFINE THE "MACRO" ZONE (Centro Expandido) ---
# This covers a huge box: Lapa to Mooca, Santana to Vila Mariana
LAT_MIN = -23.6000  # South 
LAT_MAX = -23.5000  # North
LON_MIN = -46.7000  # West
LON_MAX = -46.5500  # East

# STEP_SIZE: 0.004 degrees is approx 450 meters.
# This makes the grid "coarse" enough to be free, but fine enough to find hotspots.
STEP_SIZE = 0.004

OUTPUT_FOLDER = "sp_macro_images"
CSV_FILE = "sp_macro_map.csv"

# --- 3. SETUP ---
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# --- 4. SAFETY CHECK (The "Wallet Protector") ---
lat_points = np.arange(LAT_MIN, LAT_MAX, STEP_SIZE)
lon_points = np.arange(LON_MIN, LON_MAX, STEP_SIZE)
total_points = len(lat_points) * len(lon_points)

print("-" * 40)
print(f"   SAFE MODE CITY SCANNER")
print("-" * 40)
print(f"Scanning Area: {LAT_MIN} to {LAT_MAX} / {LON_MIN} to {LON_MAX}")
print(f"Grid Step: ~450 meters")
print(f"Total Points to Check: {total_points}")
print("-" * 40)
print(f"Estimated Cost: $0.00 (Uses ~{total_points/28000*100:.1f}% of free monthly quota)")
print("-" * 40)

user_input = input("Do you want to proceed? (type 'yes'): ")
if user_input.lower() != 'yes':
    print("Aborted.")
    exit()

# --- 5. INITIALIZE AI ---
print("Connecting to Roboflow...")
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project(PROJECT_NAME)
model = project.version(VERSION).model

f = open(CSV_FILE, 'w', newline='')
writer = csv.writer(f)
writer.writerow(["Lat", "Lon", "Date", "Vendor_Count", "Stall_Count", "Image_File"])

# --- 6. THE SCAN LOOP ---
def scan_location(lat, lon):
    # Free Check: Metadata
    meta_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={GOOGLE_API_KEY}"
    try:
        meta = requests.get(meta_url, timeout=3).json()
    except:
        return

    if meta.get('status') != 'OK':
        return 

    date = meta.get('date', '')
    if not date: return
    year = int(date.split('-')[0])

    # ONLY download if data is recent (2023+)
    if year >= 2023:
        img_url = f"https://maps.googleapis.com/maps/api/streetview?size=640x640&location={lat},{lon}&fov=90&key={GOOGLE_API_KEY}"
        img_data = requests.get(img_url).content
        
        filename = f"{OUTPUT_FOLDER}/macro_{lat:.5f}_{lon:.5f}_{date}.jpg"
        with open(filename, 'wb') as handler:
            handler.write(img_data)
        
        try:
            # AI Inference
            results = model.predict(filename, confidence=40, overlap=30).json()
            predictions = results['predictions']
            
            vendors = 0
            stalls = 0
            for p in predictions:
                if p['class'] in ["vendor", "street_vendor"]: vendors += 1
                if p['class'] in ["stall", "vendor_stall"]: stalls += 1

            # Save to CSV (Even if 0, to show we checked)
            if vendors > 0 or stalls > 0:
                print(f"[HIT] {date} @ {lat:.4f},{lon:.4f}: {vendors} Vendors")
            
            writer.writerow([lat, lon, date, vendors, stalls, filename])

        except Exception as e:
            print(f"AI Error: {e}")

count = 0
for lat in lat_points:
    for lon in lon_points:
        count += 1
        print(f"Scanning {count}/{total_points}...", end='\r')
        scan_location(lat, lon)
        time.sleep(0.1) 

f.close()
print(f"\nDONE! City-wide map saved to {CSV_FILE}")