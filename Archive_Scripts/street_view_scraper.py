import requests
import os
import time

# --- PASTE YOUR KEY BELOW ---
GOOGLE_API_KEY = "AIzaSyBMMzyleMtj3XgPgBlEhNvQMrZbH8XSQgw"
# ----------------------------

OUTPUT_FOLDER = "street_view_images"

LOCATIONS_TO_CHECK = [
    (-23.543167, -46.629333, "25_de_Marco_SP"), 
    (-22.9694, -43.1868, "Rio_Copacabana"), # Tourist area = Frequent updates
]

def get_street_view_image(lat, lon, name):
    metadata_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat},{lon}&key={GOOGLE_API_KEY}"
    try:
        meta_response = requests.get(metadata_url).json()
    except:
        return

    if meta_response.get('status') == 'OK':
        date = meta_response.get('date', '')
        if not date: return

        year = int(date.split('-')[0])
        
        # Only download if 2023 or later
        if year >= 2023:
            print(f"Found valid image for {name}: {date}")
            image_url = f"https://maps.googleapis.com/maps/api/streetview?size=640x640&location={lat},{lon}&fov=90&key={GOOGLE_API_KEY}"
            img_data = requests.get(image_url).content
            
            filename = f"{OUTPUT_FOLDER}/{name}_{date}.jpg"
            with open(filename, 'wb') as handler:
                handler.write(img_data)
        else:
            print(f"Skipping {name}: Too old ({year})")

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print("Starting...")
for place in LOCATIONS_TO_CHECK:
    get_street_view_image(place[0], place[1], place[2])
    time.sleep(0.1)
print("Done.")