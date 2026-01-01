import streamlit as st
import ee
import geemap.foliumap as geemap
import folium
import pandas as pd
from shark_network import fetch_global_fleet, fetch_historical_track

# --- THE GEE CORE ---
# This block is now designed to be "Bulletproof"
PROJECT_ID = 'practical-bebop-477117-a5'

def initialize_gee():
    try:
        # Modern check for initialization
        if not ee.data.is_initialized():
            ee.Initialize(project=PROJECT_ID)
        return True
    except Exception as e:
        st.sidebar.error(f"🛰️ GEE Auth Error: {e}")
        return False

GEE_READY = initialize_gee()

st.set_page_config(page_title="Global Shark AI", layout="wide")

# --- DATA LOAD ---
df = fetch_global_fleet()
if df.empty:
    st.error("📡 Connecting to Global Satellite Backbone...")
    st.stop()

tab1, tab2 = st.tabs(["🌍 Global Fleet", "🔬 Habitat Analysis"])

with tab1:
    m = geemap.Map(center=[0, 0], zoom=2)
    m.add_basemap('HYBRID')
    m.add_points_from_xy(df, x="lon", y="lat", color_column="category")
    # ... (Popup loop logic) ...
    m.to_streamlit(height=700)

with tab2:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### 🔬 Mission Parameters")
        selected = st.selectbox("Select Target:", df['name'].tolist())
        tgt = df[df['name'] == selected].iloc[0]

        # Locked Calendar Logic
        min_r, max_r = tgt['min_date'].date(), tgt['max_date'].date()
        date_start = st.date_input("Start Date", value=min_r, min_value=min_r, max_value=max_r)
        date_end = st.date_input("End Date", value=max_r, min_value=min_r, max_value=max_r)

        if st.button("📡 Generate Journey Analysis", type="primary"):
            hist_df, journey_km = fetch_historical_track(tgt['species'], date_start, date_end)
            if not hist_df.empty:
                st.session_state['active_path'] = hist_df
                st.session_state['total_km'] = journey_km
                st.session_state['active_tgt'] = tgt
            else:
                st.error("No movement found for this period.")

    with col2:
        if 'active_path' in st.session_state and st.session_state.get('active_tgt')['id'] == tgt['id']:
            path, km = st.session_state['active_path'], st.session_state['total_km']
            st.metric(label=f"Journey Distance", value=f"{km} KM")
            
            m2 = geemap.Map(center=[path.iloc[0]['lat'], path.iloc[0]['lon']], zoom=4)
            m2.add_basemap('SATELLITE')
            
            # Draw Path
            folium.PolyLine(path[['lat', 'lon']].values.tolist(), color="#00ffff", weight=4).add_to(m2)
            
            # Start/End Markers
            folium.Marker(path[['lat', 'lon']].iloc[0].tolist(), icon=folium.Icon(color='green')).add_to(m2)
            folium.Marker(path[['lat', 'lon']].iloc[-1].tolist(), icon=folium.Icon(color='red')).add_to(m2)

            # --- DYNAMIC GEE LAYER ---
            if GEE_READY:
                try:
                    # Pulling real-time Chlorophyll data via your Project ID
                    # MODIS Aqua is a high-bandwidth dataset
                    chl = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").select('chlor_a').median()
                    m2.add_layer(chl, {'min': 0, 'max': 5, 'palette': ['blue', 'green', 'yellow', 'red']}, 'NASA Chlorophyll')
                except:
                    st.warning("⚠️ Environmental layer failed to load. Check IAM Roles.")

            m2.to_streamlit(height=600)
            st.dataframe(path.tail(5))