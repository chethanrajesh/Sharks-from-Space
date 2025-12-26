from pathlib import Path
from src import auth, fetch_data, process_ocean

# Define paths
BASE_DIR = Path(__file__).parent
DATA_RAW = BASE_DIR / "data" / "raw"

def main():
    print("--- STARTING SHARK TRACKING PIPELINE ---")
    
    # 1. Authenticate
    auth.setup_earthdata_login()

    # 2. Fetch Data
    fetch_data.download_sample_data(DATA_RAW)

    # 3. Process: Load sample shark data and extract ocean features
    import pandas as pd
    sample_data = {
        'lon': [-178.93, -178.91, -178.89],
        'lat': [34.19, 34.19, 34.20],
        'time': pd.to_datetime(['2024-01-01 12:00', '2024-01-01 13:00', '2024-01-01 14:00'])
    }
    shark_df = pd.DataFrame(sample_data)
    
    # Find BGC file for chlorophyll data
    bgc_files = list(DATA_RAW.glob("*BGC*.nc"))
    if bgc_files:
        shark_df = process_ocean.sample_chlorophyll(shark_df, bgc_files[0])
        shark_df = process_ocean.calculate_movement_metrics(shark_df)
        print("\n✅ Pipeline complete!")
        print(shark_df[['time', 'chlorophyll', 'speed_ms']].head())
    else:
        print("⚠️ No BGC data found. Skipping chlorophyll sampling.")

    print("--- PIPELINE FINISHED ---")

if __name__ == "__main__":
    main()
