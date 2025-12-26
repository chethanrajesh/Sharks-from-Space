import streamlit as st
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import plotly.express as px

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shark Habitat AI", layout="wide", page_icon="🦈")

# --- 1. LOAD DATA (Cached for Speed) ---
@st.cache_data
def load_data():
    # Load Model & Scaler
    model = joblib.load("models/shark_ai_model.pkl")
    scaler = joblib.load("models/shark_scaler.pkl")
    
    # Load Maps
    map_sst = np.load("models/map_sst.npy")
    map_chlor = np.load("models/map_chlor.npy")
    map_depth = np.load("models/map_depth.npy")
    
    # Load Coords
    lat = np.load("models/lat_grid.npy")
    lon = np.load("models/lon_grid.npy")
    
    # Load Sharks
    df = pd.read_csv("models/shark_data.csv")
    
    return model, scaler, map_sst, map_chlor, map_depth, lat, lon, df

try:
    model, scaler, map_sst, map_chlor, map_depth, lat, lon, df_sharks = load_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("🦈 Shark-AI Control")
st.sidebar.markdown("Control the ocean parameters below.")

# FEATURE: Climate Change Simulator
temp_adjust = st.sidebar.slider("🌡️ Ocean Warming (°C)", min_value=0.0, max_value=5.0, step=0.5, value=0.0)
if temp_adjust > 0:
    st.sidebar.warning(f"⚠️ Simulating +{temp_adjust}°C warming scenario!")

# Layer Selection
layer = st.sidebar.radio("Select View:", ["AI Prediction", "Temperature", "Chlorophyll", "Depth"])

# --- MAIN LOGIC ---
st.title("🌊 Global Shark Habitat Monitor")
st.markdown(f"**Species:** *Tiger Shark* | **Data Points:** {len(df_sharks)}")

# 1. APPLY SIMULATION (Modify SST)
current_sst = map_sst + temp_adjust

# 2. PREPARE DATA FOR AI
target_shape = current_sst.shape

if layer == "AI Prediction":
    with st.spinner("🤖 AI is calculating new habitat probabilities..."):
        # Flatten
        flat_chlor = map_chlor.flatten()
        flat_sst = current_sst.flatten()
        flat_depth = map_depth.flatten()
        
        # Stack
        X_map = np.column_stack((flat_chlor, flat_sst, flat_depth))
        
        # Find valid pixels
        valid_idx = np.where(np.isfinite(X_map).all(axis=1))[0]
        valid_pixels = X_map[valid_idx]
        
        # Predict
        final_prediction = np.full(flat_chlor.shape, np.nan)
        if len(valid_pixels) > 0:
            valid_pixels_scaled = scaler.transform(valid_pixels)
            probs = model.predict_proba(valid_pixels_scaled)[:, 1]
            final_prediction[valid_idx] = probs
            
        # Reshape
        display_map = final_prediction.reshape(target_shape)
        
        # Stats
        avg_prob = np.nanmean(display_map)
        col1, col2 = st.columns(2)
        col1.metric("Avg Habitat Suitability", f"{avg_prob:.1%}", delta=f"{avg_prob - 0.5:.1%}")
        
elif layer == "Temperature":
    display_map = current_sst
elif layer == "Chlorophyll":
    display_map = map_chlor
elif layer == "Depth":
    display_map = map_depth

# --- VISUALIZATION (Plotly) ---
# We use Plotly because it's interactive and handles hovering nicely
# --- VISUALIZATION (Plotly) ---
# FIX: Removed np.flipud() because the map was appearing inverted
fig = px.imshow(
    display_map,  # <--- CHANGED: Removed np.flipud()
    color_continuous_scale='inferno' if layer == "AI Prediction" else 'viridis',
    labels={'color': 'Intensity'},
    title=f"Global View: {layer}"
)

# Remove axes for clean look
fig.update_xaxes(showticklabels=False)
fig.update_yaxes(showticklabels=False)
fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0))

st.plotly_chart(fig, use_container_width=True)