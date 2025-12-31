import streamlit as st
import ee
import geemap.foliumap as geemap
import folium
import pandas as pd
from shark_network import fetch_global_fleet, fetch_shark_path

# --- GEE PERMISSION CHECK ---
GEE_READY = False
try:
    if not ee.data._initialized:
        ee.Initialize(project='practical-bebop-477117-a5')
    GEE_READY = True
except: pass

st.set_page_config(page_title="Global Shark AI", layout="wide")

# --- DATA LOAD ---
df = fetch_global_fleet()

if df.empty:
    st.error("📡 Connecting to Global Satellite Backbone...")
    if st.button("Re-attempt Handshake"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# --- SIDEBAR SPECIES BREAKDOWN ---
with st.sidebar:
    st.title("🛰️ Satellite Control")
    if st.button("🔄 Force Real-Time Sync", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    st.title("🦈 Species Intelligence")
    st.write(f"Total Active Tags: **{len(df)}**")
    species_counts = df['species'].value_counts().head(10)
    st.bar_chart(species_counts)

# --- MAIN UI ---
st.title("🛰️ Global Shark Habitat AI")
tab1, tab2 = st.tabs(["🌍 Global Fleet", "🔬 Habitat Analysis"])

with tab1:
    st.subheader("Global Distribution: Grouped by Family")
    m = geemap.Map(center=[0, 0], zoom=2)
    m.add_basemap('HYBRID')
    m.add_points_from_xy(df, x="lon", y="lat", color_column="category")
    
    # --- FIXED POPUP LOOP ---
    for _, shark in df.iterrows():
        popup_info = f"""
        <div style="font-family: Arial; font-size: 12px; width: 220px;">
            <b style="color: #00ffff;">Target:</b> {shark['name']}<br>
            <b>Species:</b> {shark['species']}<br>
            <b style="color: #ff6600;">Verified Ping:</b> {shark['ping_time']}
        </div>
        """
        folium.CircleMarker(
            location=[shark['lat'], shark['lon']],
            radius=5,
            popup=folium.Popup(popup_info, max_width=300),
            color="#00ffff" if "Great White" in shark['category'] else "#ff6600",
            fill=True,
            fill_opacity=0.7
        ).add_to(m)
    
    m.to_streamlit(height=700)

with tab2:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown("### 🎯 Mission Target")
        selected = st.selectbox("Select Target:", df['name'].tolist())
        tgt = df[df['name'] == selected].iloc[0]
        
        if st.button("📡 Start Analysis", type="primary"):
            st.session_state['active_path'] = fetch_shark_path(tgt['lat'], tgt['lon'])
            st.session_state['active_tgt'] = tgt

    with col2:
        if 'active_tgt' in st.session_state and st.session_state.get('active_tgt')['id'] == tgt['id']:
            path = st.session_state['active_path']
            t = st.session_state['active_tgt']
            
            m2 = geemap.Map(center=[t['lat'], t['lon']], zoom=7)
            m2.add_basemap('SATELLITE')
            folium.PolyLine(path[['lat', 'lon']].values.tolist(), color="cyan", weight=4).add_to(m2)
            
            icon_html = f'<div style="width:40px;height:40px;background-color:cyan;border-radius:50%;box-shadow:0 0 20px cyan;animation:blink 1.2s infinite;"></div><style>@keyframes blink{{50%{{opacity:0.2;}}}}</style>'
            folium.Marker([t['lat'], t['lon']], icon=folium.DivIcon(html=icon_html)).add_to(m2)
            
            if GEE_READY:
                chl_img = ee.ImageCollection("NASA/OCEANDATA/MODIS-Aqua/L3SMI").select('chlor_a').median()
                m2.add_layer(chl_img, {'min': 0, 'max': 5, 'palette': ['blue', 'green', 'yellow', 'red']}, 'NASA Chlorophyll')
            
            m2.to_streamlit(height=550)
            st.info(f"Analyzing {t['species']} | Last Ping: {t['ping_time']}")