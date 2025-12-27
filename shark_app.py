import streamlit as st
import numpy as np
import pandas as pd
import joblib
import plotly.express as px
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shark Habitat AI - NASA Edition", layout="wide", page_icon="🦈")

# --- 1. LOAD DATA & MODELS ---
@st.cache_data
def load_data():
    model = joblib.load("models/shark_ai_model.pkl")
    try:
        imputer = joblib.load("models/shark_imputer.pkl")
    except:
        imputer = None 
    
    # Load Maps & Replace NaNs (Land) with 0 or Mean immediately
    # We use np.nan_to_num to turn "Empty Space" into "Zero" so math doesn't crash
    map_sst = np.nan_to_num(np.load("models/map_sst.npy"), nan=0.0)
    map_chlor = np.nan_to_num(np.load("models/map_chlor.npy"), nan=0.0)
    map_depth = np.nan_to_num(np.load("models/map_depth.npy"), nan=0.0)
    
    df = pd.read_csv("models/shark_data.csv")
    
    return model, imputer, map_sst, map_chlor, map_depth, df

try:
    model, imputer, map_sst, map_chlor, map_depth, df_sharks = load_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# --- 2. DEFINE GEOFENCES ---
zones = {
    "⚠️ Commercial Fishing Zone": {
        "coords": [[10, 10], [10, 30], [30, 30], [30, 10], [10, 10]], 
        "color": "yellow"
    },
    "🚢 Shipping Lane": {
        "coords": [[60, 60], [60, 80], [90, 80], [90, 60], [60, 60]], 
        "color": "red"
    }
}

# --- SIDEBAR CONTROL ---
st.sidebar.title("🛰️ Shark-AI Control Deck")
st.sidebar.markdown("---")

st.sidebar.subheader("🔧 Map Calibration")
# THE FIX: Default value is now False, so it loads standard by default.
flip_map = st.sidebar.checkbox("↩️ Flip Map Vertical", value=False, help="Toggle this if land masses look upside down.")

st.sidebar.subheader("🛡️ Conservation Tools")
show_geofences = st.sidebar.checkbox("Show Geofences & Alerts", value=True)

st.sidebar.subheader("🌡️ Ocean Dynamics")
temp_adjust = st.sidebar.slider("Ocean Warming (°C)", 0.0, 4.0, 0.0, 0.5)
eddy_boost = st.sidebar.slider("Eddy Strength (Vorticity)", 0.5, 2.0, 1.0, 0.1)

st.sidebar.subheader("⏳ Biological History")
lag_strength = st.sidebar.slider("Trophic Cascade Lag", 0.5, 1.5, 1.0, 0.1)

layer = st.sidebar.radio("Select Satellite Layer:", 
                         ["🦈 AI Habitat Prediction", "🌀 Okubo-Weiss (Eddies)", "🌡️ Temperature (SST)", "🌿 Chlorophyll (Food)", "🌪️ Thermal Fronts"])

# --- MAIN ENGINE ---
st.title("🦈 Global Shark Habitat Monitor (NASA-Grade)")
st.markdown("**Status:** Online | **Model:** Random Forest (Physics-Aware)")

# 1. APPLY SIMULATIONS
current_sst = map_sst + temp_adjust
current_chlor = map_chlor * lag_strength

# 2. REAL-TIME PHYSICS ENGINE
# A. Gradients
dy, dx = np.gradient(current_sst)
map_gradient = np.sqrt(dx**2 + dy**2)
map_gradient = np.nan_to_num(map_gradient) 
map_gradient = np.clip(map_gradient, 0, 0.1) 

# B. Okubo-Weiss
u_sim = -dy * eddy_boost 
v_sim = dx * eddy_boost 

du_dy, du_dx = np.gradient(u_sim)
dv_dy, dv_dx = np.gradient(v_sim)

sn = du_dx - dv_dy
ss = du_dy + dv_dx
omega = dv_dx - du_dy

w_param = (sn**2 + ss**2) - omega**2
w_param = np.nan_to_num(w_param) 

w_min, w_max = w_param.min(), w_param.max()
if w_max - w_min == 0:
    w_param = np.zeros_like(w_param) 
else:
    w_param = np.clip(w_param, -1e-5, 1e-5)
    w_param = (w_param - w_param.min()) / (w_param.max() - w_param.min())

# C. Trophic Lag
map_lag_21d = current_chlor 

# 3. PREPARE AI INPUT
target_shape = current_sst.shape
display_map = np.zeros(target_shape) 

# Select Layer Data
if layer == "🦈 AI Habitat Prediction":
    with st.spinner("🤖 AI is analyzing fluid dynamics & biological history..."):
        flat_sst = current_sst.flatten()
        flat_depth = map_depth.flatten()
        flat_lag = map_lag_21d.flatten()
        flat_grad = map_gradient.flatten()
        flat_ow = w_param.flatten()
        
        X_map = np.column_stack((flat_sst, flat_depth, flat_lag, flat_grad, flat_ow))
        
        if imputer:
            X_map = imputer.transform(X_map)
            
        probs = model.predict_proba(X_map)[:, 1]
        display_map = probs.reshape(target_shape)
elif layer == "🌀 Okubo-Weiss (Eddies)":
    display_map = w_param
elif layer == "🌡️ Temperature (SST)":
    display_map = current_sst
elif layer == "🌿 Chlorophyll (Food)":
    display_map = current_chlor
elif layer == "🌪️ Thermal Fronts":
    display_map = map_gradient
else:
    display_map = map_depth

# --- VISUALIZATION ---

# Apply Manual Flip if checked
if flip_map:
    display_map = np.flipud(display_map)

# Set Colors
if layer == "🌀 Okubo-Weiss (Eddies)":
    c_scale = 'RdBu'
    mid_point = 0.5
elif "AI" in layer:
    c_scale = 'inferno'
    mid_point = None
else:
    c_scale = 'viridis'
    mid_point = None

# Draw Plot
fig = px.imshow(
    display_map, 
    color_continuous_scale=c_scale,
    color_continuous_midpoint=mid_point,
    title=f"Global View: {layer}"
)

# 4. DRAW GEOFENCES
alert_messages = []

if show_geofences:
    for name, data in zones.items():
        xs = [p[0] for p in data['coords']]
        ys = [p[1] for p in data['coords']]
        
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            fill="toself",
            mode="lines",
            line=dict(color=data['color'], width=2),
            name=name,
            hoverinfo="name"
        ))
        
        # Geofence Alert Logic
        if layer == "🦈 AI Habitat Prediction":
            try:
                x_min, x_max = min(xs), max(xs)
                y_min, y_max = min(ys), max(ys)
                
                r_start, r_end = int(y_min), int(y_max)
                c_start, c_end = int(x_min), int(x_max)
                
                # Check for sharks
                if r_start >= 0 and r_end < target_shape[0] and c_start >= 0 and c_end < target_shape[1]:
                    # IMPORTANT: If map is flipped, we must check the flipped data
                    zone_pixels = display_map[r_start:r_end, c_start:c_end]
                    
                    risk_sum = np.sum(zone_pixels > 0.75)
                    if risk_sum > 10:
                        alert_messages.append(f"🚨 ALERT: High Shark Activity in {name} ({risk_sum} px).")
            except:
                pass 

fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0))
fig.update_xaxes(showticklabels=False)
fig.update_yaxes(showticklabels=False)

st.plotly_chart(fig, use_container_width=True)

# --- METRICS & REPORT ---
st.subheader("📋 Mission Status Report")

if len(alert_messages) > 0:
    for msg in alert_messages:
        st.error(msg)
else:
    if show_geofences:
        st.success("✅ Commercial Zones Clear.")

if layer == "🦈 AI Habitat Prediction":
    # Calculate average on non-zero pixels
    ocean_pixels = display_map[display_map > 0.01]
    avg_qual = np.mean(ocean_pixels) if len(ocean_pixels) > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Habitat Suitability", f"{avg_qual:.1%}")
    col2.metric("Eddy Activity", "High" if np.mean(w_param) > 0.4 else "Normal")
    col3.metric("Trophic Efficiency", f"{lag_strength * 100}%")