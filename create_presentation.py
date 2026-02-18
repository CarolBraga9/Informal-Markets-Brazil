import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- CONFIGURATION ---
INPUT_FILE = "Final_Results/final_thesis_dataset.csv"
EXCEL_OUTPUT = "Shadow_Economy_Report.xlsx"
CHART_OUTPUT = "thesis_visuals.png"

# We still need this just for the "Workers" constant, 
# but Income is now dynamic from the CSV.
WORKERS_PER_STALL = 1.5 

print("--- GENERATING FINAL THESIS REPORT (WITH WEALTH INDEX) ---")

if not os.path.exists(INPUT_FILE):
    print(f"Error: {INPUT_FILE} not found. Run 'build_thesis_dataset.py' first.")
    exit()

df = pd.read_csv(INPUT_FILE)
print(f"Loaded {len(df)} rows.")

# 1. Filter & Rename
# We only want rows with activity
active_df = df[df['Total_Activity'] > 0].copy()

# Rename columns for the Professor (Clear, Academic Terms)
active_df.rename(columns={
    'District': 'Neighborhood',
    'Total_Activity': 'Activity Count (Vendors+Stalls)',
    'Nighttime_Radiance': 'Nighttime Light (Infrastructure)',
    'Est_Monthly_Revenue_R$': 'Est. Monthly Revenue (R$)',
    'Shadow_Index': 'Shadow Intensity Index',
    'Wealth_Index': 'Socio-Economic Weight (Index)',
    'Local_Avg_Income': 'Local Est. Income per Vendor (R$)'
}, inplace=True)

# 2. Add The "Math" Columns (Transparency)
# Add the Workers constant so the formula is complete:
# Count * Workers * Local_Income = Revenue
active_df['Est. Workers per Unit'] = WORKERS_PER_STALL

# Reorder columns for logical flow (The "Audit Trail")
cols = [
    'Neighborhood', 'Lat', 'Lon', 'Date',
    'Activity Count (Vendors+Stalls)',       # A
    'Est. Workers per Unit',                 # B
    'Socio-Economic Weight (Index)',         # C (The New Variable)
    'Local Est. Income per Vendor (R$)',     # D (Adjusted by C)
    'Est. Monthly Revenue (R$)',             # = A * B * D
    'Nighttime Light (Infrastructure)',
    'Shadow Intensity Index'
]

# Keep only valid columns (handle cases where geocoding might have missed some)
valid_cols = [c for c in cols if c in active_df.columns]
active_df = active_df[valid_cols]

# 3. Create Summaries
# Summary A: Top Neighborhoods by Revenue
district_summary = active_df.groupby('Neighborhood')[['Activity Count (Vendors+Stalls)', 'Est. Monthly Revenue (R$)']].sum()
district_summary = district_summary.sort_values(by='Est. Monthly Revenue (R$)', ascending=False)

# Summary B: Top 50 Specific Hotspots
top_spots = active_df.sort_values(by='Est. Monthly Revenue (R$)', ascending=False).head(50)

# 4. Export to Excel
print(f"Writing to {EXCEL_OUTPUT}...")
try:
    with pd.ExcelWriter(EXCEL_OUTPUT, engine='openpyxl') as writer:
        # Sheet 1: The "Executive Summary"
        district_summary.to_excel(writer, sheet_name="District Leaderboard")
        
        # Sheet 2: The "Red List" (Actionable Intelligence)
        top_spots.to_excel(writer, sheet_name="Top 50 Hotspots", index=False)
        
        # Sheet 3: The "Proof" (Full Data)
        active_df.to_excel(writer, sheet_name="Full Dataset", index=False)
        
    print("Excel file created successfully.")
except Exception as e:
    print(f"Excel Error: {e}")

# 5. Generate Charts
print(f"Generating charts to {CHART_OUTPUT}...")
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(15, 6))

# Chart 1: Scatter (The Shadow Frontier)
# Note: We size the bubbles by REVENUE now, which includes your Wealth Index
sns.scatterplot(
    data=active_df, 
    x='Nighttime Light (Infrastructure)', 
    y='Activity Count (Vendors+Stalls)', 
    hue='Socio-Economic Weight (Index)', # Color by Wealth to show the disparity!
    palette='viridis', 
    size='Est. Monthly Revenue (R$)',
    sizes=(20, 300),
    alpha=0.7,
    ax=axes[0]
)
axes[0].set_title("The Shadow Frontier: Activity vs. Infrastructure")
axes[0].set_xlabel("Nighttime Light (Infrastructure)")
axes[0].set_ylabel("Informal Activity Count")
axes[0].axvline(x=100, color='gray', linestyle='--')
axes[0].text(105, active_df['Activity Count (Vendors+Stalls)'].max()*0.9, "Formal\n(High Light)", color='gray')

# Chart 2: Top Districts Bar Chart
top_10 = district_summary.head(10)
sns.barplot(
    x=top_10['Est. Monthly Revenue (R$)'], 
    y=top_10.index, 
    palette="flare", 
    ax=axes[1]
)
axes[1].set_title("Est. Monthly Shadow Volume (R$)")
axes[1].set_xlabel("Revenue (R$)")
axes[1].set_ylabel("")

plt.tight_layout()
plt.savefig(CHART_OUTPUT, dpi=150)
print("Charts saved.")

print("-" * 30)
print("PRESENTATION READY.")
print("Check 'Shadow_Economy_Report.xlsx' -> 'Full Dataset' tab.")
print("You will now see the 'Socio-Economic Weight' column.")
print("-" * 30)