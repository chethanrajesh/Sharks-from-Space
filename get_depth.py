import os
import requests

# URL for ETOPO1 (Ice Surface) - 0.5 degree resolution (Small & Fast)
# This is a standard low-res version perfect for this project
url = "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/bedrock/grid_registered/netcdf/ETOPO1_Bed_g_gmt4.grd.gz"

# NOTE: This file is GZIPPED (.gz), so we need to unzip it after downloading.
import gzip
import shutil

save_dir = "downloads/bathymetry"
os.makedirs(save_dir, exist_ok=True)
gz_filename = os.path.join(save_dir, "etopo1.nc.gz")
final_filename = os.path.join(save_dir, "global_depth.nc")

print("⬇️ Downloading Bathymetry (Depth) Data from NOAA...")

try:
    # 1. Download
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(gz_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("✅ Download complete. Unzipping...")

        # 2. Unzip
        with gzip.open(gz_filename, 'rb') as f_in:
            with open(final_filename, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Cleanup
        os.remove(gz_filename)
        print(f"🎉 Success! Depth map saved to: {final_filename}")
        
    else:
        print(f"❌ Server Error: {response.status_code}")

except Exception as e:
    print(f"❌ Download failed: {e}")