import earthaccess
import os
from dotenv import load_dotenv

load_dotenv()
auth = earthaccess.login(strategy="environment")

# 1. We want the SAME month as the sharks (Oct 2023)
# ID: MODIS Aqua Sea Surface Temperature (4km Monthly)
dataset_id = "MODISA_L3m_SST" 

print(f"\n⬇️ Searching for SST (Temperature) data: {dataset_id}...")

files = earthaccess.search_data(
    short_name=dataset_id,
    temporal=("2023-10-01", "2023-10-31"),
    count=1
)

if files:
    print(f"✅ Found file: {files[0]['meta']['concept-id']}")
    os.makedirs("downloads/sst", exist_ok=True)
    earthaccess.download(files, "downloads/sst")
    print("\n🎉 SUCCESS! Data saved to 'downloads/sst'")
else:
    print("❌ No files found. Check your date range or internet.")