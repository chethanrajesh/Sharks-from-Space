import xarray as xr
import numpy as np
import pandas as pd
from math import radians, sin, cos, asin, sqrt, atan2, degrees

def sample_chlorophyll(tag_df, satellite_file):
    """
    Takes a DataFrame of shark tags (lon, lat, time) and samples
    Chlorophyll-a from the given satellite NetCDF file.
    """
    print(f"Sampling Chlorophyll from {satellite_file}...")
    
    # Open the datasets
    try:
        ds_geo = xr.open_dataset(satellite_file, group='geophysical_data')
        try:
            ds_nav = xr.open_dataset(satellite_file, group='navigation_data')
        except (OSError, KeyError):
            ds_nav = None
    except (OSError, KeyError):
        try:
            ds_geo = xr.open_dataset(satellite_file)
            ds_nav = None
        except Exception as e:
            print(f"Error opening file: {e}")
            return tag_df

    # Find the chlorophyll variable
    var_name = None
    for v in ['chlor_a', 'chlorophyll', 'Rrs_443']:
        if v in ds_geo:
            var_name = v
            break
            
    if not var_name:
        print("Error: No chlorophyll variable found in file.")
        return tag_df

    # For PACE data, lat/lon are in navigation_data
    if ds_nav is not None and 'latitude' in ds_nav and 'longitude' in ds_nav:
        lat_2d = ds_nav['latitude'].values
        lon_2d = ds_nav['longitude'].values
    else:
        # Fallback: assume lat/lon are coordinates
        lat_2d = ds_geo['lat'].values if 'lat' in ds_geo else None
        lon_2d = ds_geo['lon'].values if 'lon' in ds_geo else None
        
    if lat_2d is None or lon_2d is None:
        print("Error: Could not find latitude/longitude data.")
        return tag_df

    # Sample values for each shark location
    sampled_values = []
    for _, row in tag_df.iterrows():
        shark_lat = row['lat']
        shark_lon = row['lon']
        
        # Calculate distances to all pixels
        distances = ((lat_2d - shark_lat)**2 + (lon_2d - shark_lon)**2)**0.5
        min_idx = np.unravel_index(np.argmin(distances), distances.shape)
        
        # Get the value at nearest pixel
        value = ds_geo[var_name].values[min_idx]
        sampled_values.append(value)

    # Add to DataFrame
    tag_df['chlorophyll'] = sampled_values
    return tag_df

def calculate_movement_metrics(df):
    """
    Calculates Step Length (meters), Speed (m/s), and Turning Angle.
    """
    print("Calculating movement metrics...")
    df = df.copy()
    
    # Shift columns to compare "Now" vs "Previous"
    df['lon_prev'] = df['lon'].shift(1)
    df['lat_prev'] = df['lat'].shift(1)
    df['time_prev'] = df['time'].shift(1)

    # Haversine Distance Function
    def get_dist(row):
        if pd.isna(row['lon_prev']): return np.nan
        lon1, lat1, lon2, lat2 = map(radians, [row['lon_prev'], row['lat_prev'], row['lon'], row['lat']])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return c * 6371000 # Earth radius in meters

    # Calculate Distance
    df['step_meters'] = df.apply(get_dist, axis=1)

    # Calculate Speed (Distance / Time)
    df['dt_seconds'] = (df['time'] - df['time_prev']).dt.total_seconds()
    df['speed_ms'] = df['step_meters'] / df['dt_seconds']

    return df