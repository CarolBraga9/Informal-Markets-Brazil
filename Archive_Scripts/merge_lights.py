import pandas as pd
import rasterio
import os

# --- CONFIGURATION ---
INPUT_CSV = "sp_macro_map.csv"
SATELLITE_TIF = "sp_nighttime_lights.tif" 
OUTPUT_CSV = "final_shadow_economy_dataset.csv"

print("--- Starting SAFE MODE Data Fusion ---")

# 1. Load Data
if not os.path.exists(INPUT_CSV):
    print("Error: Input CSV not found.")
    exit()
    
df = pd.read_csv(INPUT_CSV)
print(f"Loaded {len(df)} rows.")

# 2. Open Satellite Image
# We use a 'try' block to catch any errors
try:
    with rasterio.open(SATELLITE_TIF) as src:
        print(f"Image Open: {src.width}x{src.height}")
        
        radiance_values = []
        
        print("Extracting values (showing progress every 20 rows)...")
        
        # Loop manually so we can see it working
        for index, row in df.iterrows():
            try:
                # Convert Lat/Lon to Row/Col
                r, c = src.index(row['Lon'], row['Lat'])
                
                # Read just that one pixel
                # window=... is safer for huge files than read()[r,c]
                window = rasterio.windows.Window(c, r, 1, 1)
                value = src.read(1, window=window)[0, 0]
                
                radiance_values.append(value)
                
                if index % 20 == 0:
                    print(f"   Processed row {index}/{len(df)} -> Value: {value:.2f}")
                    
            except Exception as e:
                print(f"   [Error on Row {index}] {e}")
                radiance_values.append(0) # Use 0 if error

        # Add to dataframe
        df['Nighttime_Radiance'] = radiance_values
        
        # Save
        df.to_csv(OUTPUT_CSV, index=False)
        print("-" * 30)
        print("SUCCESS! Script finished cleanly.")
        print("-" * 30)

except Exception as main_error:
    print(f"CRITICAL CRASH: {main_error}")