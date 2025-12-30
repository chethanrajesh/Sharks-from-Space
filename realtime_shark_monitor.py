import ee
from datetime import datetime, timedelta

# 1. Initialize with your Project ID
ee.Initialize(project='practical-bebop-477117-a5')

# 2. Get TODAY's Date
# We look back 3 days to account for any NASA server lag
now = datetime.now()
date_start = (now - timedelta(days=3)).strftime('%Y-%m-%d')
date_end = now.strftime('%Y-%m-%d')

# 3. Pull REAL-TIME Datasets
# 'NASA/OCEANDATA/MODIS-Aqua/L3SMI' is the NRT-capable collection
# We use the most recent image in the stack (.last())
# --- CORRECTED REAL-TIME LOGIC ---

# 1. Pull the collection and filter by date/location
chl_col = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI") \
            .filterDate(date_start, date_end) \
            .select('chlor_a') \
            .sort('system:time_start', False) # Sort by newest first

# 2. Grab the single most recent image correctly
# We use .first() after sorting by 'False' (Descending)
latest_chl = chl_col.first()

# 3. Do the same for Temperature (SST)
temp_col = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI") \
            .filterDate(date_start, date_end) \
            .select('sst') \
            .sort('system:time_start', False)

latest_sst = temp_col.first()

# 4. Define Shark Location (Use your latest OCEARCH ping)
lat, lon = 28.39, -80.60 
point = ee.Geometry.Point([lon, lat])
buffer = point.buffer(5000)

# 5. Extract Data
def get_realtime_val(image, band_name):
    try:
        val = image.reduceRegion(reducer=ee.Reducer.mean(), geometry=buffer, scale=1000).get(band_name)
        return val.getInfo()
    except:
        return None

chl_now = get_realtime_val(latest_chl, 'chlor_a')
sst_now = get_realtime_val(latest_sst, 'sst')

print(f"--- 🚨 REAL-TIME SHARK FEED (As of {date_end}) ---")
print(f"🍃 Current Chlorophyll: {chl_now if chl_now else '☁️ Cloudy - No Signal'} mg/m³")
print(f"🌡️ Current Temperature: {sst_now if sst_now else '☁️ Cloudy - No Signal'} °C")