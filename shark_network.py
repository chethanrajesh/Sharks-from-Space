import requests
import pandas as pd
import streamlit as st
import numpy as np
from math import radians, cos, sin, asin, sqrt

# --- ML FEATURE: DISTANCE CALCULATOR ---
def haversine_km(lat1, lon1, lat2, lon2):
    """Calculates real-world distance between GPS points in KM."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon, dlat = lon2 - lon1, lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * asin(sqrt(a)) * 6371

def clean_date(raw_val):
    """Handles OBIS messy formats like 2021_03 or intervals."""
    if not raw_val or raw_val == 'None': return pd.to_datetime("2025-12-31")
    clean_str = str(raw_val).split('/')[0].replace('_', '-')
    try: return pd.to_datetime(clean_str)
    except: return pd.to_datetime("2025-12-31")

OBIS_URL = "https://api.obis.org/v3/occurrence?taxonid=10194&size=5000&order=eventDate"

@st.cache_data(ttl=600)
def fetch_global_fleet():
    try:
        response = requests.get(OBIS_URL, timeout=30)
        results = response.json().get('results', [])
        fleet = []
        for r in results:
            if r.get('decimalLatitude'):
                ts = clean_date(r.get('eventDate'))
                fleet.append({
                    "id": str(r.get('id')),
                    "name": f"{str(r.get('scientificName')).split()[-1]}-{str(r.get('id'))[:4]}",
                    "species": r.get('scientificName'),
                    "category": "Great White" if "Carcharodon" in str(r.get('scientificName')) else "Other",
                    "lat": float(r['decimalLatitude']), "lon": float(r['decimalLongitude']),
                    "ping_time": ts.strftime('%Y-%m-%d'),
                    "min_date": pd.to_datetime(f"{r.get('date_year', 2022)}-01-01"),
                    "max_date": ts
                })
        return pd.DataFrame(fleet)
    except: return pd.DataFrame()

def fetch_historical_track(species_name, start_date, end_date):
    """Fetches movement and calculates distance for the chosen period."""
    s, e = start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    url = f"https://api.obis.org/v3/occurrence?scientificname={species_name}&startdate={s}&enddate={e}&size=500"
    try:
        response = requests.get(url, timeout=30)
        results = response.json().get('results', [])
        path_data = [{"lat": float(r['decimalLatitude']), "lon": float(r['decimalLongitude']), 
                      "timestamp": clean_date(r.get('eventDate'))} for r in results if r.get('decimalLatitude')]
        df = pd.DataFrame(path_data).sort_values('timestamp').drop_duplicates()
        
        total_km = 0
        if len(df) > 1:
            for i in range(1, len(df)):
                total_km += haversine_km(df.iloc[i-1]['lat'], df.iloc[i-1]['lon'], df.iloc[i]['lat'], df.iloc[i]['lon'])
        return df, round(total_km, 2)
    except: return pd.DataFrame(), 0