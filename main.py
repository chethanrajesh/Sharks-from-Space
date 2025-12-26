from pathlib import Path
from src import auth, fetch_data, process_ocean

# Define paths
BASE_DIR = Path(__file__).parent
project_root = BASE_DIR  # For compatibility with notebook
DATA_RAW = BASE_DIR / "data" / "raw"

def main():
    print("--- STARTING SHARK TRACKING PIPELINE ---")
    
    # 1. Authenticate
    auth.setup_earthdata_login()

    # 2. Fetch Data
    fetch_data.download_sample_data(DATA_RAW)

    # 3. Process: Load REAL shark tracking data
    import pandas as pd
    
    # Load real shark tracking data from CSV
    shark_tracks_file = BASE_DIR / "data" / "shark_tracks.csv"
    if shark_tracks_file.exists():
        shark_df = pd.read_csv(shark_tracks_file)
        shark_df['timestamp'] = pd.to_datetime(shark_df['timestamp'])
        shark_df = shark_df.rename(columns={'timestamp': 'time', 'lon': 'lon', 'lat': 'lat'})
        print(f"\n📊 Loaded {len(shark_df)} shark tracking records")
        print(f"🦈 Sharks tracked: {shark_df['shark_id'].unique()}")
    else:
        print(f"❌ Real shark data file not found at {shark_tracks_file}")
        return
    
    # Find BGC file for chlorophyll data
    bgc_files = list(DATA_RAW.glob("*BGC*.nc"))
    if bgc_files:
        # Sample chlorophyll at real shark locations
        shark_df = process_ocean.sample_chlorophyll(shark_df, bgc_files[0])
        shark_df = process_ocean.calculate_movement_metrics(shark_df)
        
        print("\n✅ Pipeline complete!")
        print("\n--- Shark Foraging Analysis Summary ---")
        print(shark_df[['time', 'shark_id', 'lat', 'lon', 'speed_ms', 'chlorophyll']].head(10))
        
        # Save results
        output_file = BASE_DIR / "data" / "processed" / "shark_analysis_results.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        shark_df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to {output_file}")
    else:
        print("⚠️ No BGC data found. Skipping chlorophyll sampling.")

    print("--- PIPELINE FINISHED ---")

if __name__ == "__main__":
    main()
