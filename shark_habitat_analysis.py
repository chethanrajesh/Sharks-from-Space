import ee
import geemap

# 1. Initialize with your Project ID
ee.Initialize(project='practical-bebop-477117-a5')

# 2. Parameters
lat, lon = 28.39, -80.60
# Use a slightly wider date range to ensure we find a cloud-free day
date_start = '2025-11-01'
date_end = '2025-12-01'
point = ee.Geometry.Point([lon, lat])
buffer = point.buffer(5000) 

# 3. Pull Data (Using standard MODIS for high stability, or PACE if available)
# NOTE: NASA PACE is often under 'NASA/OCEANDATA/PACE/L3/CHL'
# We use .filterBounds to make the search even faster
pace_chl = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI") \
            .filterDate(date_start, date_end) \
            .filterBounds(buffer) \
            .select('chlor_a') \
            .median()

sst = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI") \
        .filterDate(date_start, date_end) \
        .filterBounds(buffer) \
        .select('sst') \
        .median()

# 4. The Analysis (The Heart of the Major Fix)
def get_stats(image, region):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000,
        maxPixels=1e9
    ).getInfo()
    return stats

stats_chl = get_stats(pace_chl, buffer)
stats_sst = get_stats(sst, buffer)

print(f"--- 🛰️ 5km Buffer Environmental Report ---")
# Get the values safely
chl_val = stats_chl.get('chlor_a')
sst_val = stats_sst.get('sst')

if chl_val and sst_val:
    print(f"🍃 Avg Chlorophyll-a: {chl_val:.4f} mg/m³")
    print(f"🌡️ Avg Temperature: {sst_val:.2f} °C")
else:
    print("⚠️ Data found, but area might be covered by heavy clouds.")