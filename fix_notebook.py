import os
from dotenv import load_dotenv

# Test .env and Library setup
load_dotenv()
try:
    import earthaccess
    import xarray as xr
    print("✅ System Ready: NASA Data Access Active.")
    print(f"✅ Credentials loaded for: {os.getenv('EARTHDATA_USERNAME')}")
except Exception as e:
    print(f"❌ Error: {e}")