import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_mock_shark_data(num_sharks=3, points_per_shark=50):
    """
    Generates random walk data to simulate sharks swimming 
    in the Gulf Stream (North Atlantic).
    """
    data = []
    
    # Starting near Florida/Bahamas
    start_lat = 26.0
    start_lon = -79.0
    
    for shark_id in range(1, num_sharks + 1):
        current_lat = start_lat + np.random.uniform(-1, 1)
        current_lon = start_lon + np.random.uniform(-1, 1)
        current_time = datetime(2023, 10, 1) # Starting Oct 1, 2023
        
        for _ in range(points_per_shark):
            # Simulate movement: Sharks move ~0.1 degrees per time step
            # Bias them slightly North-East (following Gulf Stream)
            delta_lat = np.random.normal(0.05, 0.02) 
            delta_lon = np.random.normal(0.05, 0.02)
            
            current_lat += delta_lat
            current_lon += delta_lon
            current_time += timedelta(hours=6) # 4 points per day
            
            data.append({
                "shark_id": f"Shark_{shark_id}",
                "timestamp": current_time,
                "lat": round(current_lat, 4),
                "lon": round(current_lon, 4),
                "speed_knots": round(np.random.uniform(1.5, 4.0), 2)
            })

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    # Ensure data directory exists
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate and Save
    print("Generating mock shark tracks...")
    df_sharks = generate_mock_shark_data()
    
    output_path = os.path.join(output_dir, "shark_tracks.csv")
    df_sharks.to_csv(output_path, index=False)
    
    print(f"Success! Mock data saved to: {output_path}")
    print(df_sharks.head())