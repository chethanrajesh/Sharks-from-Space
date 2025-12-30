import os
import requests
import gzip
import shutil

# NEW URL: ETOPO 2022 (More stable and faster)
url = "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO1/data/bedrock/grid_registered/netcdf/ETOPO1_Bed_g_gmt4.grd.gz"

save_dir = "downloads/bathymetry"
os.makedirs(save_dir, exist_ok=True)
gz_filename = os.path.join(save_dir, "etopo.nc.gz")
final_filename = os.path.join(save_dir, "global_depth.nc")

print("⬇️ Connecting to NOAA ETOPO 2022 Servers...")

try:
    # 1. Download with a timeout and stream
    response = requests.get(url, stream=True, timeout=30)
    
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(gz_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024): # 1MB chunks for speed
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    # Print progress so you know it hasn't hung!
                    done = int(50 * downloaded / total_size)
                    print(f"\rProgress: [{'=' * done}{' ' * (50-done)}] {downloaded//(1024*1024)}MB", end="")
        
        print("\n✅ Download complete. Unzipping...")

        with gzip.open(gz_filename, 'rb') as f_in:
            with open(final_filename, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        os.remove(gz_filename)
        print(f"🎉 Success! Depth map saved to: {final_filename}")
        
    else:
        print(f"❌ Server Error: {response.status_code}. NOAA might be down.")

except Exception as e:
    print(f"❌ Download failed: {e}")