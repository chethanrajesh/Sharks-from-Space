import requests
import pandas as pd
import streamlit as st
import numpy as np

# OBIS API - Global Sharks & Rays. 'order=eventDate' ensures 2025 pings are first.
OBIS_URL = "https://api.obis.org/v3/occurrence?taxonid=10194&size=5000&order=eventDate"

@st.cache_data(ttl=600)
def fetch_global_fleet():
    """Fetches real-time shark data from the global OBIS backbone."""
    try:
        response = requests.get(OBIS_URL, timeout=20)
        data = response.json()
        results = data.get('results', [])
        
        fleet = []
        for r in results:
            if r.get('decimalLatitude') and r.get('decimalLongitude'):
                species_name = r.get('scientificName', 'Unknown Shark')
                
                # Category logic for Legend
                category = "Other Sharks"
                if "Carcharodon" in species_name: category = "Great White"
                elif "Galeocerdo" in species_name: category = "Tiger Shark"
                
                # --- FIXED: Capturing the Accurate Timestamp ---
                # We prioritize eventDate (YYYY-MM-DD HH:MM:SS)
                accurate_time = r.get('eventDate') or r.get('date_year') or "N/A"

                fleet.append({
                    "id": str(r.get('id')),
                    "name": f"{species_name.split()[-1]}-{str(r.get('id'))[:4]}",
                    "species": species_name,
                    "category": category,
                    "lat": float(r['decimalLatitude']),
                    "lon": float(r['decimalLongitude']),
                    "ping_time": str(accurate_time) 
                })
        return pd.DataFrame(fleet)
    except Exception as e:
        print(f"Connection Error: {e}")
        return pd.DataFrame()

def fetch_shark_path(lat, lon):
    """Generates a mission trail for the Analysis tab."""
    path = [{"lat": lat - (np.random.uniform(-0.02, 0.02) * i), 
             "lon": lon - (np.random.uniform(-0.02, 0.02) * i)} for i in range(6)]
    return pd.DataFrame(path).iloc[::-1]