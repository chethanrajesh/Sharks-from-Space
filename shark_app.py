import streamlit as st
import ee
import geemap.foliumap as geemap
import pandas as pd
import numpy as np
import folium
import time
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

# --- 1. UTILITY: DISTANCE CALCULATION (Haversine Formula) ---
def calculate_total_distance(path_df):
    """Calculates total distance in miles for the provided path."""
    def haversine(lat1, lon1, lat2, lon2):
        R = 3958.8  # Radius of Earth in miles
        dLat = radians(lat2 - lat1)
        dLon = radians(lon2 - lon1)
        a = sin(dLat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2)**2
        return R * 2 * asin(sqrt(a))

    total = 0
    for i in range(len(path_df) - 1):
        total += haversine(path_df.iloc[i]['lat'], path_df.iloc[i]['lon'], 
                           path_df.iloc[i+1]['lat'], path_df.iloc[i+1]['lon'])
    return total

# --- 2. NETWORK & CLOUD LINK ---
try:
    from shark_network import fetch_live_sharks, fetch_shark_path
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False

try:
    ee.Initialize(project='practical-bebop-477117-a5') 
    GEE_AVAILABLE = True
except:
    GEE_AVAILABLE = False

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shark Habitat AI", layout="wide", page_icon="🦈")

# ==============================================================================
# 🛰️ HIGH-PRECISION ENVIRONMENTAL ENGINE
# ==============================================================================

@st.cache_data(ttl=3600)
def fetch_gee_env(lat, lon):
    point = ee.Geometry.Point([lon, lat])
    buffer = point.buffer(5000)
    end = datetime.now()
    start = end - timedelta(days=20)
    
    sst_img = ee.ImageCollection("HYCOM/GLBy0_08/latest").select('sea_surface_temperature').first()
    chl_img = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").select('chlor_a').filterDate(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')).median()
    topo = ee.Image("NOAA/NGDC/ETOPO1").select('bedrock')
    
    def safe_get(img, key, scale_factor=1.0):
        try:
            val = img.reduceRegion(ee.Reducer.mean(), buffer, 1000).get(key).getInfo()
            return val * scale_factor if val is not None else 0.0
        except: return 0.0

    return chl_img, {
        'chl': safe_get(chl_img, 'chlor_a'), 
        'sst': safe_get(sst_img, 'sea_surface_temperature', 0.001), 
        'depth': safe_get(topo, 'bedrock')
    }

# ==============================================================================
# 🌍 MAIN UI FLOW
# ==============================================================================

st.sidebar.title("🦈 Shark Command")
app_mode = st.sidebar.selectbox("Mission Profile", ["Live Global Tracker", "AI Simulation"])

if app_mode == "Live Global Tracker":
    if not NETWORK_AVAILABLE:
        st.error("Missing 'shark_network.py'.")
        st.stop()

    st.title("🛰️ Live Satellite Tracker (OCEARCH x GEE)")
    df_live = fetch_live_sharks()

    if df_live.empty:
        st.error("🚨 Major Sync Error: OCEARCH servers are blocking the connection.")
        st.info("Try refreshing the page or checking your internet connection.")
        if st.button("🔄 Force Re-Connect"):
            st.cache_data.clear()
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["📍 Fleet Map", "🔬 Habitat Analysis"])

        with tab1:
            st.subheader(f"Current Global Positions ({len(df_live)} Active Tags)")
            m_global = geemap.Map(center=[0, 0], zoom=2)
            m_global.add_basemap('SATELLITE')
            m_global.add_points_from_xy(df_live, x="lon", y="lat", color_column="species")
            m_global.to_streamlit(height=600)

        with tab2:
            col_list, col_main = st.columns([1, 3])
            
            with col_list:
                st.markdown("### 🎯 Target Selection")
                shark_names = sorted(df_live['name'].unique().tolist())
                selected_name = st.selectbox("Select Animal:", shark_names)
                
                tgt = df_live[df_live['name'] == selected_name].iloc[0]
                active_id = int(tgt['id'])
                
                # --- NEW UI BUTTONS ---
                analyze_btn = st.button("📡 Analyze Mission Path", type="primary")
                play_btn = st.button("▶️ Play Movement Simulation")
                
                if analyze_btn:
                    st.session_state['path_data'] = fetch_shark_path(active_id)
                    st.session_state['selected_shark_name'] = selected_name
                    st.session_state['run_animation'] = False

                if play_btn:
                    # Ensure data is loaded before playing
                    st.session_state['path_data'] = fetch_shark_path(active_id)
                    st.session_state['selected_shark_name'] = selected_name
                    st.session_state['run_animation'] = True

            with col_main:
                if 'path_data' in st.session_state and st.session_state.get('selected_shark_name') == selected_name:
                    path = st.session_state['path_data']
                    
                    if not path.empty:
                        # 1. DISTANCE CALCULATION
                        miles_covered = calculate_total_distance(path)
                        
                        current_pos = path.iloc[-1]
                        c_lat, c_lon = current_pos['lat'], current_pos['lon']
                        chl_img, env = fetch_gee_env(c_lat, c_lon)
                        
                        st.subheader(f"🗺️ Habitat Trajectory: {selected_name}")
                        shark_url = "https://getdrawings.com/free-icon-bw/shark-icon-11.png"

                        # 2. PLAY MOVEMENT ANIMATION
                        if st.session_state.get('run_animation', False):
                            placeholder = st.empty()
                            # Ensure chronological order for movement
                            p_sorted = path.copy()
                            if 'datetime' in p_sorted.columns:
                                p_sorted = p_sorted.sort_values(by='datetime')

                            for i in range(len(p_sorted)):
                                step = p_sorted.iloc[i]
                                m_anim = geemap.Map(center=[step['lat'], step['lon']], zoom=8)
                                m_anim.add_basemap('SATELLITE')
                                
                                # Trace path up to current point in loop
                                current_path_coords = p_sorted[['lat', 'lon']][:i+1].values.tolist()
                                folium.PolyLine(current_path_coords, color="#00ffff", weight=4).add_to(m_anim)
                                
                                icon_html = f'<div style="width:45px; height:45px; background-image:url(\'{shark_url}\'); background-size:contain; background-repeat:no-repeat; filter:invert(100%) drop-shadow(0 0 10px #00ffff);"></div>'
                                folium.Marker(location=[step['lat'], step['lon']], icon=folium.DivIcon(html=icon_html)).add_to(m_anim)
                                
                                with placeholder.container():
                                    m_anim.to_streamlit(height=500, key=f"anim_{selected_name}_{i}")
                                time.sleep(0.05)
                            st.session_state['run_animation'] = False
                        
                        else:
                            # Standard Static View
                            m = geemap.Map(center=[c_lat, c_lon], zoom=8)
                            m.add_basemap('SATELLITE')
                            m.add_layer(chl_img, {'min': 0, 'max': 5, 'palette': ['blue', 'green', 'yellow', 'red']}, 'NASA Chlorophyll', opacity=0.4)
                            folium.PolyLine(path[['lat', 'lon']].values.tolist(), color="#00ffff", weight=4, opacity=0.7).add_to(m)
                            
                            for _, p in path.iterrows():
                                folium.CircleMarker(location=[p['lat'], p['lon']], radius=2, color="white").add_to(m)
                            
                            icon_html = f'<div style="width:50px; height:50px; background-image:url(\'{shark_url}\'); background-size:contain; background-repeat:no-repeat; filter:invert(100%) drop-shadow(0 0 10px #00ffff); animation: blinker 1.5s infinite;"></div><style>@keyframes blinker {{50%{{opacity:0.3;}}}}</style>'
                            folium.Marker(location=[c_lat, c_lon], icon=folium.DivIcon(html=icon_html)).add_to(m)
                            m.to_streamlit(height=550)
                        
                        # 3. METRICS DISPLAY (Including new Distance)
                        st.markdown(f"### 📊 Mission Stats: {selected_name}")
                        m_dist, m1, m2, m3 = st.columns(4)
                        m_dist.metric("📏 Distance Covered", f"{miles_covered:.2f} Miles")
                        m1.metric("🌡️ Sea Temp", f"{env['sst']:.2f} °C")
                        m2.metric("🌿 Chlorophyll", f"{env['chl']:.3f} mg/m³")
                        m3.metric("📉 Depth", f"{env['depth']:.0f} m")
                else:
                    st.info("Select a shark and click 'Analyze Mission Path' to see the Trajectory.")

else:
    st.title("🧪 AI Simulation (Offline)")
    st.info("Legacy mode using static .npy files.")