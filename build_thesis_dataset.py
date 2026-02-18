import pandas as pd
import numpy as np
import rasterio
from rasterio.windows import Window
import reverse_geocoder as rg
import os
import multiprocessing

# --- CONFIGURATION ---
INPUT_SCAN = "sp_real_shape_map.csv"
INPUT_SATELLITE = "sp_nighttime_lights.tif"
OUTPUT_DB = "Final_Results/final_thesis_dataset.csv"

# BASELINE from PNAD (The "Average" Informal Worker)
BASE_INCOME_R = 2750.00  
WORKERS_PER_STALL = 1.5 

# --- THE "WEALTH INDEX" DICTIONARY ---
# Based on 'Mapa da Desigualdade' & Commercial Geography
DISTRICT_WEIGHTS = {
    # TIER 1: THE ELITE (High Markup / Wealthy Clients)
    'Pinheiros': 1.8, 'Jardim Paulista': 1.8, 'Itaim Bibi': 1.8, 'Moema': 1.8,
    'Alto de Pinheiros': 1.8, 'Morumbi': 1.6, 'Perdizes': 1.5, 'Vila Mariana': 1.4,
    'Consolacao': 1.4, 'Bela Vista': 1.3, 'Saude': 1.2,
    
    # TIER 2: THE SHADOW GIANTS (The "Feira da Madrugada" Effect)
    # Residents might be poor, but trade volume is INSANE. 
    # We manually boost these above the residential income proxy.
    'Bras': 1.5, 'Pari': 1.5, 'Bom Retiro': 1.4, 'Se': 1.3, 'Republica': 1.3,
    'Santa Efigenia': 1.3, 'Barra Funda': 1.2,
    
    # TIER 3: ESTABLISHED MIDDLE CLASS (Baseline 1.0)
    'Mooca': 1.1, 'Tatuape': 1.1, 'Ipiranga': 1.0, 'Santana': 1.0,
    'Lapa': 1.0, 'Cambuci': 1.0, 'Liberdade': 1.0, 'Barra Funda': 1.0,
    'Sao Caetano do Sul': 1.1, # Nearby Formal City
    
    # TIER 4: TRANSITION / MIXED
    'Agua Rasa': 0.9, 'Belem': 0.9, 'Casa Verde': 0.9, 'Jabaquara': 0.9,
    
    # TIER 5: PERIPHERY / SURVIVAL (Lower Markup)
    'Default': 0.75
}

def get_wealth_index(district_name):
    # 1. Clean the name
    if not isinstance(district_name, str): return DISTRICT_WEIGHTS['Default']
    
    # 2. Direct Lookup
    # We check if the dictionary key is INSIDE the geocoded name 
    # (e.g. "Distrito de Pinheiros" contains "Pinheiros")
    for key, weight in DISTRICT_WEIGHTS.items():
        if key in district_name:
            return weight
            
    # 3. Fallback
    return DISTRICT_WEIGHTS['Default']

def main():
    print("--- BUILDING THESIS DATABASE (WITH WEALTH INDEX) ---")

    if not os.path.exists(INPUT_SCAN):
        print(f"Error: {INPUT_SCAN} not found.")
        return

    df = pd.read_csv(INPUT_SCAN)
    print(f"Loaded {len(df)} rows.")

    # 1. Satellite Extraction
    print("Extracting Satellite Light...")
    radiance_values = []
    try:
        with rasterio.open(INPUT_SATELLITE) as src:
            for index, row in df.iterrows():
                try:
                    py, px = src.index(row['Lon'], row['Lat'])
                    window = Window(px, py, 1, 1)
                    val = src.read(1, window=window)[0, 0]
                    radiance_values.append(val)
                except:
                    radiance_values.append(0)
        df['Nighttime_Radiance'] = radiance_values
    except:
        df['Nighttime_Radiance'] = 0

    # 2. Geolocation
    print("Reverse Geocoding...")
    try:
        coords_geo = list(zip(df['Lat'], df['Lon']))
        results = rg.search(coords_geo, mode=1)
        df['District'] = [x['name'] for x in results]
    except:
        df['District'] = "Unknown"

    # 3. APPLY WEALTH INDEX
    print("Applying Socio-Economic Weights...")
    
    # Get the index (Multiplier)
    df['Wealth_Index'] = df['District'].apply(get_wealth_index)
    
    # Adjust Income: Baseline * Index
    df['Local_Avg_Income'] = BASE_INCOME_R * df['Wealth_Index']
    
    # Total Activity
    df['Total_Activity'] = df['Structure_Count']
    
    # Final Revenue Calculation
    df['Est_Monthly_Revenue_R$'] = df['Total_Activity'] * WORKERS_PER_STALL * df['Local_Avg_Income']

    # Shadow Index (Activity / Light)
    df['Shadow_Index'] = df['Total_Activity'] / np.log1p(df['Nighttime_Radiance'])

    # Dates
    df['Date_Obj'] = pd.to_datetime(df['Date'], format='%Y-%m', errors='coerce')
    df['Year'] = df['Date_Obj'].dt.year

    # 4. Export
    out_cols = [
        'Lat', 'Lon', 'District', 'Date', 
        'Total_Activity', 'Wealth_Index', 'Local_Avg_Income',
        'Est_Monthly_Revenue_R$', 'Nighttime_Radiance', 'Shadow_Index', 'Image_File'
    ]
    df[out_cols].to_csv(OUTPUT_DB, index=False)

    print("-" * 30)
    print(f"DONE! Saved to {OUTPUT_DB}")
    print("-" * 30)
    print("SAMPLE OF ECONOMIC DIVERSITY:")
    print(df[df['Total_Activity'] > 0][['District', 'Wealth_Index', 'Local_Avg_Income', 'Est_Monthly_Revenue_R$']].head(10))

if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()