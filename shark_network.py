import requests
import pandas as pd
import datetime
import streamlit as st
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# THE OFFICIAL ENDPOINT
OCEARCH_URL = "https://www.ocearch.org/tracker/ajax/filter-sharks"

def get_robust_session():
    """Creates a session with built-in retry logic for unstable connections."""
    session = requests.Session()
    # Retry strategy: 3 attempts, waiting longer each time
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://www.ocearch.org/tracker/",
        "X-Requested-With": "XMLHttpRequest"
    })
    return session

@st.cache_data(ttl=300)
def fetch_live_sharks():
    """Fetches real sharks from OCEARCH with high-timeout protection."""
    shark_list = []
    session = get_robust_session()

    try:
        # Increase timeout to 30 seconds for slow servers
        response = session.get(OCEARCH_URL, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            for shark_id, info in data.items():
                latest = info.get('latest_activity')
                if latest:
                    shark_list.append({
                        "id": info.get('id'),
                        "name": info.get('name', 'Unknown'),
                        "species": info.get('species', 'Unknown'),
                        "gender": info.get('gender', 'Unknown'),
                        "length": info.get('length', 'Unknown'),
                        "weight": info.get('weight', 'Unknown'),
                        "last_seen": datetime.datetime.fromtimestamp(int(latest)),
                        "lat": float(info.get('geo', {}).get('lat', 0)),
                        "lon": float(info.get('geo', {}).get('long', 0)),
                        "image_url": info.get('profile_image', None)
                    })
        else:
            st.warning(f"OCEARCH is busy. Received Code {response.status_code}. Using cache.")

    except Exception as e:
        st.error(f"📡 Connection Issue: {e}")
        # Return empty list if everything fails so the app doesn't crash
        return pd.DataFrame()

    df = pd.DataFrame(shark_list)
    if not df.empty:
        df = df.sort_values(by='last_seen', ascending=False)
    return df

def fetch_shark_path(shark_id):
    """Fetches official path history."""
    HISTORY_URL = f"https://www.ocearch.org/tracker/detail/{shark_id}/json"
    session = get_robust_session()

    try:
        response = session.get(HISTORY_URL, timeout=30)
        if response.status_code == 200:
            data = response.json()
            pings = data.get('pings', [])
            path_data = []
            for p in pings:
                path_data.append({
                    "datetime": datetime.datetime.fromtimestamp(int(p['tz'])),
                    "lat": float(p['latitude']),
                    "lon": float(p['longitude']),
                    "active": p['active'] == "1"
                })
            return pd.DataFrame(path_data)
    except:
        return pd.DataFrame()
    return pd.DataFrame()