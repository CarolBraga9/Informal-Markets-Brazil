import requests
import os
import time
import csv
import numpy as np
from roboflow import Roboflow

# --- 1. CONFIGURATION (AGGRESSIVE MODE) ---
# 50% of Quota Strategy
GOOGLE_API_KEY = "AIzaSyBMMzyleMtj3XgPgBlEhNvQMrZbH8XSQgw"
ROBOFLOW_API_KEY = "t2jq94gHItiL5ZSLhwMG"
PROJECT_NAME = "camelo-detection-v1"
VERSION = 1

# THE WALLET GUARD (50% CAP)
# We set the limit to 5,000 unique points.
MAX_POINTS_LIMIT = 5000 

# --- 2. DEFINE THE "FULL CITY" ZONE ---
# Focusing on the massive Urban Sprawl of SP
LAT_MIN = -23.7500  # South (Interlagos)
LAT_MAX = -23.4000  # North (Cantareira Edge)
LON_MIN = -46.8300  # West (Osasco/Carapicuiba Border)
LON_MAX = -46.3600  # East (Itaquera)

# STEP_SIZE: 0.0055 degrees is approx ~600 meters.
# This is High Resolution for a city-wide scan.
STEP_SIZE = 0.0055

OUTPUT_FOLDER = "sp_full_scan_images"
CSV_FILE = "sp_full_city_map.csv"

# --- 3. SETUP ---
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Load existing points to enable RESUME capability
processed_coords = set()
if os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f)
        next(reader, None) # Skip header
        for row in reader:
            if row:
                # Store "Lat,Lon" string to skip duplicates
                processed_coords.add(f"{float(row[0]):.4f},{float(row[1]):.4f}")

print(f"RESUME MODE: Found {len(processed_coords)} points already scanned.")

# --- 4. CALCULATOR ---
lat_points = np.arange(LAT_MIN, LAT_MAX, STEP_SIZE)
lon_points = np.arange(LON_MIN, LON_MAX, STEP_SIZE)
total_potential = len(lat_points) * len(lon_points)

print("-" * 40)
print(f"   FULL CITY SCANNER (AGGRESSIVE 50%)")
print("-" * 40)
print(f"Grid Step: ~600 meters (High Res)")
print(f"Total Grid Points: {total_potential}")
print(f"Wallet Limit: {MAX_POINTS_LIMIT}")
print("-" * 40)

if len(processed_coords) >= MAX_POINTS_LIMIT:
    print("⚠️ LIMIT ALREADY REACHED. Delete the CSV if you want to restart.")
    exit()

user_input = input(f"Ready to scan up to {MAX_POINTS_LIMIT} points? (type 'yes'): ")
if user_input.lower() != 'yes':
    print("Aborted.")
    exit()

# --- 5. INITIALIZE AI ---
print("Connecting to Roboflow...")
rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project(PROJECT_NAME)
model = project.version(VERSION).model

# Open CSV in Append Mode
f = open(CSV_FILE, 'a', newline='')
writer = csv.writer(f)

# If file is empty, write header
if os.path.getsize(CSV_FILE) == 0:
    writer.writerow(["Lat", "Lon", "Date", "Vendor_Count", "Stall_Count", "Image_File"])

# --- 6. ENGINE ---
new_points_scanned = 0
total_credits_used_session = 0

def scan_location(lat, lon):
    global new_points_scanned, total_credits_used_session
    
    # Check Metadata first (Free)
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

    # Only spend credits on recent data (Post-Pandemic relevant)
    if year >= 2022:
        img_url = f"https://maps.googleapis.com/maps/api/streetview?size=640x640&location={lat},{lon}&fov=90&key={GOOGLE_API_KEY}"
        
        # This is where the money is spent
        img_data = requests.get(img_url).content
        total_credits_used_session += 1
        
        filename = f"{OUTPUT_FOLDER}/full_{lat:.5f}_{lon:.5f}_{date}.jpg"
        with open(filename, 'wb') as handler:
            handler.write(img_data)
        
        try:
            # Roboflow Inference
            results = model.predict(filename, confidence=40, overlap=30).json()
            predictions = results['predictions']
            
            vendors = 0
            stalls = 0
            for p in predictions:
                if p['class'] in ["vendor", "street_vendor"]: vendors += 1
                if p['class'] in ["stall", "vendor_stall"]: stalls += 1

            # Log it
            writer.writerow([lat, lon, date, vendors, stalls, filename])
            f.flush()
            
            new_points_scanned += 1
            if (vendors > 0 or stalls > 0):
                print(f"HIT! {date} | V:{vendors} S:{stalls} | {lat:.4f}, {lon:.4f}")

        except Exception as e:
            print(f"AI Error: {e}")

# --- 7. RUN LOOP ---
print("Starting Scan...")

for lat in lat_points:
    for lon in lon_points:
        # Check if we already did this point (Resume Check)
        coord_key = f"{lat:.4f},{lon:.4f}"
        if coord_key in processed_coords:
            continue
            
        # Check Limits
        if (len(processed_coords) + new_points_scanned) >= MAX_POINTS_LIMIT:
            print(f"\n🛑 HARD LIMIT REACHED ({MAX_POINTS_LIMIT}). Saving budget.")
            break
            
        print(f"Scanning... Total: {len(processed_coords) + new_points_scanned} | Session Hits: {total_credits_used_session}", end='\r')
        
        scan_location(lat, lon)
        
        # Important: Don't hammer the API too fast
        time.sleep(0.05) 
    
    if (len(processed_coords) + new_points_scanned) >= MAX_POINTS_LIMIT:
        break

f.close()
print("-" * 30)
print(f"SESSION COMPLETE.")
print(f"New Points Scanned: {new_points_scanned}")
print(f"Total Map Size: {len(processed_coords) + new_points_scanned}")
print(f"File: {CSV_FILE}")