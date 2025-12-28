import earthaccess
import os
from dotenv import load_dotenv

# 1. Login
load_dotenv()
if not os.getenv("EARTHDATA_TOKEN"):
    print("👉 Key missing. I will ask for your NASA login now...")
    auth = earthaccess.login(strategy="interactive", persist=True)
else:
    auth = earthaccess.login(strategy="environment")

# 2. Define the Target Dataset Directly
# This is the standard ID for "MODIS Aqua Chlorophyll (Monthly 4km)"
dataset_id = "MODISA_L3m_CHL"

print(f"\n⬇️ Searching for files in dataset: {dataset_id}...")

# 3. Find and Download ONE file
files = earthaccess.search_data(
    short_name=dataset_id,
    temporal=("2023-10-01", "2023-10-31"),
    count=1
)

if files:
    print(f"✅ Found file: {files[0]['meta']['concept-id']}")
    os.makedirs("downloads/chlorophyll", exist_ok=True)
    earthaccess.download(files, "downloads/chlorophyll")
    print("\n🎉 SUCCESS! Data saved to 'downloads/chlorophyll'")
    print("👉 NOW you can run your notebook.")
else:
    print("❌ No files found. The dataset ID might have changed or the date is out of range.")