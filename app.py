import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
import streamlit.components.v1 as components # Import the HTML component renderer

# 1. Page Config
st.set_page_config(page_title="Shark Tracker", layout="wide")

# 2. Add a "Sanity Check" box
# If you don't see this blue box, you are editing the wrong file!
st.info("✅ If you can see this, the code has updated successfully.")

st.title("🦈 Shark Tracker: Embed Method")

# 3. Define the Map Generation Function
def generate_html_map():
    # --- Generate Dummy Data ---
    steps = 50
    t = np.linspace(0, 10, steps)
    lat = 25.0 + np.sin(t) * 0.5 + np.linspace(0, 1, steps) * 0.2
    lon = -80.0 + np.cos(t) * 0.5 + np.linspace(0, 0.5, steps)
    timestamps = [f"12:{i*15:02d}" for i in range(steps)]

    df = pd.DataFrame({
        "lat": lat,
        "lon": lon,
        "time": timestamps,
        "icon": ["🦈"] * steps, 
        "size": [30] * steps
    })

    # --- Build the Plotly Figure ---
    fig = px.scatter_mapbox(
        df,
        lat="lat",
        lon="lon",
        text="icon",
        size="size",
        animation_frame="time",
        zoom=8,
        height=600
    )

    # Add the path line
    trace_line = px.line_mapbox(df, lat="lat", lon="lon").data[0]
    trace_line.line.color = 'blue'
    fig.add_trace(trace_line)

    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":0,"l":0,"b":0}
    )

    # --- CRITICAL STEP: Convert to HTML String ---
    # We convert the entire map to a text string of HTML code
    return fig.to_html(include_plotlyjs='cdn')

# 4. Layout
col1, col2 = st.columns([1, 2])

with col1:
    st.write("### Controls")
    st.write("Target: Maverick-693")
    
    # We use a button to trigger the display
    if st.button("Load Map 🗺️", type="primary"):
        st.session_state['show_map'] = True

with col2:
    if st.session_state.get('show_map'):
        st.write("### 📍 Live Tracker")
        
        # Generate the HTML string
        map_html = generate_html_map()
        
        # RENDER IT: We use components.html to embed the raw code
        # This bypasses the standard st.plotly_chart which was failing for you
        components.html(map_html, height=600)
    else:
        st.write("Click 'Load Map' to generate the view.")