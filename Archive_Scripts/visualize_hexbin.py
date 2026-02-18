import pandas as pd
import folium
from folium.plugins import HeatMap
import json

# --- CONFIGURATION ---
INPUT_CSV = "sp_macro_map.csv"  # Use your City-Wide scan
OUTPUT_MAP = "sp_hexbin_map.html"

# 1. Load Data
df = pd.read_csv(INPUT_CSV)

# Filter for locations with ANY activity
df_active = df[(df['Vendor_Count'] > 0) | (df['Stall_Count'] > 0)]

print(f"Generating Hexbin map from {len(df_active)} active locations...")

# 2. Create Base Map (Dark Mode for contrast)
m = folium.Map(location=[-23.543167, -46.629333], zoom_start=13, tiles="CartoDB dark_matter")

# 3. Create the Hexbin Layer
# This automatically aggregates points into hexagons
# gridsize=20 controls the size of the hexagons (Higher = Smaller hexagons)
from folium.plugins import DualMap

# We use a standard GeoJSON grid approach for flexibility, 
# but Folium's 'FastMarkerCluster' or simple Circle markers are often clearer.
# Let's stick to a high-quality Heatmap with 'gradient' for that "Economic Intensity" look.
# (Hexbins are complex to render purely in Folium without GeoJSON libraries, 
# so a high-gradient Heatmap is the closest instant alternative).

# Let's try a "Weighted" Heatmap which is better than dots.
heat_data = []
for index, row in df_active.iterrows():
    # Weight = Total Activity (Vendors + Stalls)
    weight = row['Vendor_Count'] + row['Stall_Count']
    # Add the point multiple times or use weight if supported
    heat_data.append([row['Lat'], row['Lon'], weight])

# Add Heatmap with specific gradient for "Shadow Economy"
HeatMap(
    heat_data, 
    radius=15, 
    blur=10, 
    gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'},
    min_opacity=0.4
).add_to(m)

# 4. Save
m.save(OUTPUT_MAP)
print(f"Map saved to {OUTPUT_MAP}")