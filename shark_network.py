import requests
import pandas as pd
import streamlit as st
import numpy as np

OBIS_GLOBAL_URL = "https://api.obis.org/v3/occurrence?taxonid=10194&size=5000&order=eventDate"

@st.cache_data(ttl=3600)
def fetch_global_fleet():
    try:
        response = requests.get(OBIS_GLOBAL_URL, timeout=25)
        data = response.json()
        results = data.get('results', [])
        
        fleet = []
        for r in results:
            if r.get('decimalLatitude') and r.get('decimalLongitude'):
                species_name = r.get('scientificName', 'Unknown')
                
                # --- CATEGORY LOGIC (Fixes the Color Error) ---
                category = "Other Sharks"
                if "Carcharodon carcharias" in species_name: category = "Great White"
                elif "Galeocerdo cuvier" in species_name: category = "Tiger Shark"
                elif "Sphyrna" in species_name: category = "Hammerhead"
                elif "Carcharhinus" in species_name: category = "Requiem Shark"
                
                fleet.append({
                    "id": str(r.get('id')),
                    "name": f"{species_name.split()[-1]}-{str(r.get('id'))[:4]}",
                    "species": species_name,
                    "category": category, # This is our new color column
                    "lat": float(r['decimalLatitude']),
                    "lon": float(r['decimalLongitude']),
                    "ping_time": r.get('eventDate', 'Recent')
                })
        return pd.DataFrame(fleet)
    except Exception as e:
        return pd.DataFrame()

def fetch_shark_path(lat, lon):
    path = []
    for i in range(8):
        path.append({
            "lat": lat - (np.random.uniform(-0.03, 0.03) * i),
            "lon": lon - (np.random.uniform(-0.03, 0.03) * i)
        })
    return pd.DataFrame(path).iloc[::-1]