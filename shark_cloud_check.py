import ee
import geemap

# 1. Initialize the Cloud Connection
# This is where your token gets used!
try:
    ee.Initialize(project='practical-bebop-477117-a5')
    print("✅ Success! You are now connected to the Google Earth Engine.")
except Exception as e:
    print(f"❌ Initialization failed: {e}")

# 2. Test the 'Major Fix' (The 5km Buffer)
# Let's check a point in the ocean
shark_point = ee.Geometry.Point([-80.0, 28.0])
buffer = shark_point.buffer(5000) # 5km circle created in the cloud

# 3. Pull a quick piece of data (Global Elevation/Depth)
# This replaces your old 'get_depth.py' script!
topo = ee.Image("NOAA/NGDC/ETOPO1").select('bedrock')

# Calculate mean depth in that 5km circle
mean_depth = topo.reduceRegion(
    reducer=ee.Reducer.mean(),
    geometry=buffer,
    scale=1000
).get('bedrock')

print(f"📊 5km Buffer Analysis: Mean Depth is {mean_depth.getInfo()}m")