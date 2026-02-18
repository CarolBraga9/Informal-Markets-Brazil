import pandas as pd
import folium
from folium.plugins import HeatMap
import os
import webbrowser

# --- CONFIGURATION ---
INPUT_FILE = "Final_Results/final_thesis_dataset.csv"
OUTPUT_VENDORS = "Final_Results/map_vendors.html"
OUTPUT_MONEY = "Final_Results/map_money.html"

# THESIS LOGIC:
# Light < 100 = Shadow Economy (Hidden/Dark) -> RED
# Light > 100 = Formal Infrastructure (Visible/Bright) -> GREEN
LIGHT_THRESHOLD = 100 

print("--- GENERATING DUAL THESIS MAPS ---")

# 1. Load Data
if not os.path.exists(INPUT_FILE):
    print(f"Error: {INPUT_FILE} not found. Run 'build_thesis_dataset.py' first.")
    exit()

df = pd.read_csv(INPUT_FILE)
print(f"Loaded {len(df)} total rows.")

# Filter: We only map locations where vendors were actually found
active_df = df[df['Total_Activity'] > 0].copy()
print(f"Mapping {len(active_df)} active locations.")

# --- SHARED FUNCTION TO BUILD MAPS ---
def create_map(data, metric_col, map_name, title_text, scale_factor, color_logic=True):
    print(f"Generating {map_name}...")
    
    # Base Map (Dark Mode for contrast)
    m = folium.Map(location=[-23.5505, -46.6333], zoom_start=11, tiles="CartoDB dark_matter")
    
    # Add Title
    title_html = f'''
             <h3 align="center" style="font-size:16px"><b>{title_text}</b></h3>
             '''
    m.get_root().html.add_child(folium.Element(title_html))

    # Add Circles (The Dots)
    for index, row in data.iterrows():
        
        # COLOR LOGIC (The "Shadow" Filter)
        if color_logic:
            # Check if Light column exists, otherwise default to Red
            light_val = row.get('Nighttime_Radiance', 0)
            color = "#00ff00" if light_val > LIGHT_THRESHOLD else "#ff0000"
        else:
            color = "#3388ff" # Default blue if no logic requested

        # SIZE LOGIC (Dynamic Radius)
        val = row[metric_col]
        # Calculate radius and cap it so it doesn't cover the whole map
        radius = 3 + (val / scale_factor)
        if radius > 30: radius = 30 

        # POPUP INFO (Clickable)
        popup_text = f"""
        <div style="font-family: sans-serif; width: 150px;">
            <b>{row['District']}</b><br><hr>
            <b>Light:</b> {row.get('Nighttime_Radiance', 0):.1f}<br>
            <b>Vendors:</b> {row['Total_Activity']}<br>
            <b>Revenue:</b> R$ {row['Est_Monthly_Revenue_R$']:,.0f}<br>
            <b>Wealth Index:</b> {row.get('Wealth_Index', 'N/A')}
        </div>
        """

        folium.CircleMarker(
            location=[row['Lat'], row['Lon']],
            radius=radius,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=popup_text
        ).add_to(m)

    # Add Heatmap Layer (Weighted by the specific metric)
    # This creates the "glowing" effect under the dots
    heat_data = [[row['Lat'], row['Lon'], row[metric_col]] for index, row in data.iterrows()]
    HeatMap(heat_data, radius=15, blur=20, min_opacity=0.3).add_to(m)

    # Save
    m.save(map_name)
    print(f"Saved: {map_name}")

# --- EXECUTION ---

# Map A: Vendor Density (Physical Presence)
# Metric: Total_Activity (Count)
# Scale: Divides count by 2 (e.g., 10 vendors = Radius 8)
create_map(
    active_df, 
    'Total_Activity', 
    OUTPUT_VENDORS, 
    "Map A: Physical Density (Vendor Count)", 
    scale_factor=2
)

# Map B: Economic Volume (Inequality)
# Metric: Est_Monthly_Revenue_R$ (Money)
# Scale: Divides money by 2000 (e.g., R$ 10k = Radius 8)
create_map(
    active_df, 
    'Est_Monthly_Revenue_R$', 
    OUTPUT_MONEY, 
    "Map B: Economic Volume (Est. Revenue)", 
    scale_factor=2000
)

print("-" * 30)
print("SUCCESS! Maps generated.")
print("Opening them in your browser now...")
webbrowser.open(OUTPUT_VENDORS)
webbrowser.open(OUTPUT_MONEY)