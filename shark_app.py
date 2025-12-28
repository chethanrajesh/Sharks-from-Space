import streamlit as st
import numpy as np
import pandas as pd
import joblib
import plotly.express as px
import plotly.graph_objects as go
import random
from datetime import datetime
import streamlit.components.v1 as components
import requests

# Import Real-Time Engine (Must be in the same folder as shark_network.py)
try:
    from shark_network import fetch_live_sharks, fetch_shark_path
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shark Habitat AI - Global Uplink", layout="wide", page_icon="🦈")

# ==============================================================================
# 🧮 NEW: ADVANCED MATH ENGINE (Kalman, Buffers, Eddies)
# ==============================================================================

class SharkKalmanFilter:
    """
    Implements a 2D Constant Velocity Kalman Filter to smooth GPS jitters
    and estimate true swimming velocity vectors.
    """
    def __init__(self, dt=1.0, std_acc=1.0, x_std_meas=0.1, y_std_meas=0.1):
        # State Vector [x, y, vx, vy]
        self.x = np.matrix([[0], [0], [0], [0]]) 
        
        # State Transition Matrix
        self.A = np.matrix([[1, 0, dt, 0],
                            [0, 1, 0, dt],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1]])
        
        # Measurement Function
        self.H = np.matrix([[1, 0, 0, 0],
                            [0, 1, 0, 0]])
        
        # Process Noise Covariance
        self.Q = np.matrix([[(dt**4)/4, 0, (dt**3)/2, 0],
                            [0, (dt**4)/4, 0, (dt**3)/2],
                            [(dt**3)/2, 0, dt**2, 0],
                            [0, (dt**3)/2, 0, dt**2]]) * std_acc**2
        
        # Measurement Noise Covariance
        self.R = np.matrix([[x_std_meas**2, 0],
                            [0, y_std_meas**2]])
        
        # Covariance Matrix
        self.P = np.eye(self.A.shape[1])

    def predict(self):
        self.x = self.A * self.x
        self.P = self.A * self.P * self.A.T + self.Q
        return self.x[0:2]

    def update(self, z):
        # z is measurement [[x], [y]]
        S = self.H * self.P * self.H.T + self.R
        K = self.P * self.H.T * np.linalg.inv(S)
        self.x = self.x + K * (z - self.H * self.x)
        self.P = self.P - K * self.H * self.P
        return self.x[0:2]

def apply_kalman_smoothing(df):
    """Runs the Kalman Filter over the entire track history."""
    kf = SharkKalmanFilter(dt=1.0)
    smoothed_lat = []
    smoothed_lon = []
    
    # Initialize with first point
    if not df.empty:
        kf.x[0,0] = df.iloc[0]['lat']
        kf.x[1,0] = df.iloc[0]['lon']

    for i, row in df.iterrows():
        meas = np.matrix([[row['lat']], [row['lon']]])
        kf.predict()
        est = kf.update(meas)
        smoothed_lat.append(est[0,0])
        smoothed_lon.append(est[1,0])
        
    return smoothed_lat, smoothed_lon

def haversine_km(lat1, lon1, lat2, lon2):
    """Vectorized Haversine distance in kilometers."""
    R = 6371.0
    lat1r = np.radians(lat1)
    lat2r = np.radians(lat2)
    dlat = lat2r - lat1r
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2.0)**2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon/2.0)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c


def sample_spatial_buffer(lat, lon, map_chlor, lat_grid, lon_grid, radius_km=5):
    """Sample the chlorophyll and SST fields in a circular buffer around (lat, lon).
    Returns aggregated stats (mean, max, count) or None if fields unavailable.
    """
    try:
        # Ensure inputs are numpy arrays
        latg = np.array(lat_grid)
        long = np.array(lon_grid)
        chl = np.array(map_chlor)
        # compute distances (vectorized)
        dists = haversine_km(lat, lon, latg, long)
        mask = dists <= radius_km
        vals = chl[mask]
        if vals.size == 0:
            return None
        return {
            'mean_chl': float(np.nanmean(vals)),
            'max_chl': float(np.nanmax(vals)),
            'n_samples': int(vals.size)
        }
    except Exception:
        return None


def analyze_spatial_buffer(lat, lon, map_chlor=None, lat_grid=None, lon_grid=None):
    """
    Preferentially performs a real buffer analysis using available model grids; otherwise falls back to a simulated estimate.
    """
    if map_chlor is not None and lat_grid is not None and lon_grid is not None:
        stats = sample_spatial_buffer(lat, lon, map_chlor, lat_grid, lon_grid, radius_km=5)
        if stats is not None:
            feature = "Open Water"
            if stats['max_chl'] > 2.0:
                feature = "High Productivity Front"
            return {'feature': feature, 'stats': stats}

    # Fallback (simulate)
    local_seed = int(abs(lat*lon)*100)
    random.seed(local_seed)
    samples_chl = [random.uniform(0.1, 3.5) for _ in range(10)]
    samples_sst = [random.uniform(18.0, 24.0) for _ in range(10)]
    max_chl = max(samples_chl)
    feature = "Open Water"
    if max_chl > 2.0: feature = "High Productivity Front"
    if max(samples_sst) - min(samples_sst) > 1.5: feature = "Thermal Wall"
    return {'feature': feature, 'stats': {'mean_chl': float(np.mean(samples_chl)), 'max_chl': max_chl, 'n_samples': len(samples_chl)}}

def calculate_okubo_weiss(lat, lon, map_ssh=None, lat_grid=None, lon_grid=None):
    """
    Calculates the Okubo-Weiss parameter W at (lat, lon) using an SSH field when available.
    If SSH is not available, falls back to a simulated estimate.

    Returns (W, status) where status is a human-friendly string.
    """
    # If a real SSH field is available, use geostrophic relations
    if map_ssh is not None and lat_grid is not None and lon_grid is not None:
        try:
            ssh = np.array(map_ssh)
            latg = np.array(lat_grid)
            long = np.array(lon_grid)

            # find nearest grid point index
            idx = np.argmin(np.abs(latg - lat))
            jdx = np.argmin(np.abs(long - lon))

            # extract a local window for derivatives (5x5)
            w = 2
            i0, i1 = max(0, idx-w), min(ssh.shape[0], idx+w+1)
            j0, j1 = max(0, jdx-w), min(ssh.shape[1], jdx+w+1)
            local_ssh = ssh[i0:i1, j0:j1]
            local_lat = latg[i0:i1]
            local_lon = long[j0:j1]

            # compute distance arrays (meters)
            # Convert degree grid spacing to meters using haversine between grid points
            if local_ssh.size < 4:
                raise ValueError("SSH window too small")

            # gradients: dssh/dy (north-south) and dssh/dx (east-west)
            # Use numpy gradient with physical spacing in meters
            # Compute approximate dy/dx in meters using small deltas
            # compute dy spacing (meters) as haversine between lat grid rows at central lon
            lat_mid = latg[idx]
            dy = haversine_km(lat_mid, long[j0], lat_mid+0.01, long[j0]) * 1000.0 if len(local_lat) > 1 else 1000.0
            dx = haversine_km(local_lat[0], long[j0], local_lat[0], long[j0]+0.01) * 1000.0 if len(local_lon) > 1 else 1000.0

            dssh_dy, dssh_dx = np.gradient(local_ssh, dy, dx)

            # Use central cell indices
            ci = local_ssh.shape[0] // 2
            cj = local_ssh.shape[1] // 2
            dvdx = 0.0
            dudy = 0.0

            # geostrophic approximation: u = -g/f * dssh/dy, v = g/f * dssh/dx
            g = 9.81
            omega = 7.2921e-5
            f = 2 * omega * np.sin(np.radians(lat))
            if f == 0:
                f = 1e-5

            du_dy = -g/f * dssh_dy
            dv_dx = g/f * dssh_dx

            # spatial derivatives of u and v
            du_dx, du_dyy = np.gradient(du_dy, dx, dy)
            dv_dxx, dv_dy = np.gradient(dv_dx, dx, dy)

            # approximate components at center
            du_dx_c = du_dx[ci, cj] if du_dx.shape == local_ssh.shape else du_dx
            dv_dy_c = dv_dy[ci, cj] if dv_dy.shape == local_ssh.shape else dv_dy
            du_dy_c = du_dy[ci, cj] if du_dy.shape == local_ssh.shape else du_dy
            dv_dx_c = dv_dx[ci, cj] if dv_dx.shape == local_ssh.shape else dv_dx

            # Strain and vorticity
            s_n = du_dx_c - dv_dy_c
            s_s = du_dy_c + dv_dx_c
            vorticity = dv_dx_c - du_dy_c

            W = s_n**2 + s_s**2 - vorticity**2

            if W < -1e-5:
                status = "🌀 Eddy Edge / Core (Foraging)"
            elif W < 0:
                status = "🔄 Weak Eddy Strain"
            else:
                status = "🌊 Strain / Laminar"

            return float(W), status
        except Exception:
            pass

    # Fallback simulated method
    random.seed(int(lat*lon*1000))
    strain = random.uniform(0, 10)
    vorticity = random.uniform(0, 10)
    W = (strain**2) - (vorticity**2)
    if W < -20:
        status = "🌀 Eddy Core (Trap)"
    elif W < 0:
        status = "🔄 Eddy Edge (Foraging)"
    else:
        status = "🌊 Laminar Flow"
    return W, status

# ==============================================================================
# 🧠 NEW: DIETARY & PREDATION ENGINE (Fixed Images & Analytics)
# ==============================================================================

def get_dietary_profile(species, region, lat, lon):
    """
    Returns the specific diet, prey images, and nutritional data 
    based on the Shark Species and current Region.
    """
    # Create a unique seed based on location to vary the diet
    loc_seed = int(abs(lat + lon) * 1000)
    random.seed(loc_seed)

    # 1. DEFINE PREY DATABASE (Updated to Unsplash for Reliability)
    prey_db = {
        "Seal": {
            "img": "https://images.unsplash.com/photo-1552353617-3bfd679b3bdd?auto=format&fit=crop&w=600&q=80", 
            "kcal": "60,000", "fat": "Very High", "protein": "High",
            "tactic": "Ambush from below (Silhouette Targeting)",
            "defense": "Haul-out on land / Agility",
            "rivals": "Orcas, Large White Sharks",
            "macros": {"Fat": 70, "Protein": 25, "Bone/Other": 5},
            "hunt_depth": "Surface - 30m",
            "efficiency": "⭐⭐⭐⭐⭐ (High Yield)"
        },
        "Tuna": {
            "img": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?auto=format&fit=crop&w=600&q=80", 
            "kcal": "15,000", "fat": "Med", "protein": "Very High",
            "tactic": "High-Speed Pursuit (Endurance)",
            "defense": "Speed bursts / Deep diving",
            "rivals": "Mako Sharks, Humans",
            "macros": {"Fat": 15, "Protein": 80, "Bone/Other": 5},
            "hunt_depth": "50m - 200m",
            "efficiency": "⭐⭐⭐ (High Effort)"
        },
        "Turtle": {
            "img": "https://images.unsplash.com/photo-1437622368342-7a3d73a34c8f?auto=format&fit=crop&w=600&q=80", 
            "kcal": "8,000", "fat": "Low", "protein": "Med",
            "tactic": "Crushing Bite (Shell penetration)",
            "defense": "Hard Shell / Maneuverability",
            "rivals": "Tiger Sharks, Crocodiles",
            "macros": {"Fat": 10, "Protein": 40, "Bone/Other": 50},
            "hunt_depth": "Surface - 20m",
            "efficiency": "⭐⭐⭐⭐ (Consistent)"
        },
        "Squid": {
            "img": "https://images.unsplash.com/photo-1566311132952-1522f7cc4baf?auto=format&fit=crop&w=600&q=80", 
            "kcal": "2,000", "fat": "Low", "protein": "High",
            "tactic": "Night Stalking (Visual)",
            "defense": "Ink Cloud / Jet Propulsion",
            "rivals": "Sperm Whales, Blue Sharks",
            "macros": {"Fat": 5, "Protein": 85, "Bone/Other": 10},
            "hunt_depth": "300m - 800m",
            "efficiency": "⭐⭐ (Volume Required)"
        },
        "Ray": {
            "img": "https://images.unsplash.com/photo-1559762717-99c81ac85459?auto=format&fit=crop&w=600&q=80", 
            "kcal": "5,000", "fat": "Med", "protein": "Med",
            "tactic": "Bottom Scanning (Electro-reception)",
            "defense": "Venomous Barb / Sand Camouflage",
            "rivals": "Hammerhead Sharks",
            "macros": {"Fat": 20, "Protein": 60, "Bone/Other": 20},
            "hunt_depth": "Seabed",
            "efficiency": "⭐⭐⭐ (Specialized)"
        },
        "Mackerel": {
            "img": "https://images.unsplash.com/photo-1534043464124-3832c2a009e8?auto=format&fit=crop&w=600&q=80", 
            "kcal": "1,200", "fat": "High", "protein": "Med",
            "tactic": "Ram Feeding (School interception)",
            "defense": "Baitball Formation / Flash Scatter",
            "rivals": "Tuna, Dolphins, Seabirds",
            "macros": {"Fat": 30, "Protein": 60, "Bone/Other": 10},
            "hunt_depth": "Surface - 50m",
            "efficiency": "⭐⭐ (Snack)"
        }
    }
    
    # 2. MATCH SPECIES TO PREY
    if "White Shark" in species:
        target = "Seal" if region in ["Temperate", "Polar"] else "Tuna"
        metabolism = "Endothermic (High Burn)"
        gut_biome = "High Acidic Efficiency"
    elif "Tiger" in species:
        target = "Turtle"
        metabolism = "Ectothermic (Slow Burn)"
        gut_biome = "Generalist Scavenger"
    elif "Mako" in species:
        target = "Tuna"
        metabolism = "Endothermic (Extreme Burn)"
        gut_biome = "Rapid Protein Absorption"
    elif "Blue" in species:
        target = "Squid"
        metabolism = "Ectothermic"
        gut_biome = "Cephalopod Specialist"
    elif "Hammerhead" in species:
        target = "Ray"
        metabolism = "Ectothermic"
        gut_biome = "Venom Tolerant"
    else:
        target = "Mackerel" # Generic
        metabolism = "Standard"
        gut_biome = "Opportunistic"

    # 3. GENERATE HUNTING STATUS
    status_options = ["🥣 Digesting", "🏹 Hunting Mode", "🩸 Feeding Frenzy", "📉 Caloric Deficit"]
    current_status = random.choice(status_options)
    
    digest_percent = random.randint(10, 90) if "Digesting" in current_status else 0
    
    return {
        "prey_name": target,
        "prey_data": prey_db.get(target, prey_db["Mackerel"]),
        "metabolism": metabolism,
        "gut_biome": gut_biome,
        "status": current_status,
        "digest_progress": digest_percent,
        "last_meal": f"{random.randint(2, 48)} hours ago",
        "hunt_success": f"{random.randint(20, 60)}%",
        "energy_expenditure": f"{random.randint(500, 3000)} kcal/day"
    }

# ==============================================================================
# 🧠 BIO-MORPHIC ECOSYSTEM ENGINE (Scientific Simulation)
# ==============================================================================

def get_local_ecosystem(lat, lon, depth, temp):
    """Simulates a scientifically accurate local ecosystem."""
    # Seed based on location for procedural variety
    geo_seed = int(abs(lat * lon * (depth + 1)) * 100)
    random.seed(geo_seed)

    ecosystem = {"flora": [], "fauna": []}
    
    abs_lat = abs(lat)
    if abs_lat < 23.5: region = "Tropical"
    elif abs_lat < 50: region = "Temperate"
    else: region = "Polar"

    if depth < 200: zone = "Photic (Surface)"
    elif depth < 1000: zone = "Mesopelagic (Twilight)"
    else: zone = "Bathypelagic (Midnight)"

    # --- FLORA SPAWNING ---
    if zone == "Photic (Surface)":
        if region == "Tropical":
            ecosystem["flora"] = [
                {"icon": "🌿", "name": "Thalassia Seagrass", "type": "Seabed", "base_reaction": "Physical disturbance (Wake)", "density": random.randint(500, 2000)},
                {"icon": "🦠", "name": "Zooxanthellae", "type": "Micro", "base_reaction": "No direct impact", "density": random.randint(100000, 5000000)},
                {"icon": "🎋", "name": "Mangrove Roots", "type": "Coastal", "base_reaction": "Vibration detection", "density": random.randint(10, 50)}
            ]
        elif region == "Temperate":
            ecosystem["flora"] = [
                {"icon": "🥬", "name": "Giant Kelp", "type": "Forest", "base_reaction": "Frond displacement", "density": random.randint(20, 100)},
                {"icon": "🍂", "name": "Sargassum", "type": "Floating", "base_reaction": "Surface scatter", "density": random.randint(200, 800)},
                {"icon": "🌱", "name": "Eelgrass", "type": "Seabed", "base_reaction": "Sediment plume", "density": random.randint(1000, 5000)}
            ]
        else: 
            ecosystem["flora"] = [
                {"icon": "❄️", "name": "Ice Algae", "type": "Surface", "base_reaction": "Micro-turbulence", "density": random.randint(50000, 200000)},
                {"icon": "🧪", "name": "Phytoplankton", "type": "Micro", "base_reaction": "Displacement", "density": random.randint(1000000, 9000000)}
            ]
    else:
        ecosystem["flora"] = [
            {"icon": "🌨️", "name": "Marine Snow", "type": "Detritus", "base_reaction": "Turbidity increase", "density": random.randint(5000, 20000)},
            {"icon": "🌋", "name": "Vent Bacteria", "type": "Micro", "base_reaction": "Thermal plume shift", "density": random.randint(100000, 999999)}
        ]

    # --- FAUNA SPAWNING ---
    if zone == "Photic (Surface)":
        if region == "Tropical":
            ecosystem["fauna"] = [
                {"icon": "🐟", "name": "Yellowfin Tuna", "role": "Prey", "status": "Alert", "pop": random.randint(12, 50)},
                {"icon": "🐢", "name": "Green Turtle", "role": "Prey", "status": "Vulnerable", "pop": random.randint(1, 3)},
                {"icon": "🦈", "name": "Reef Shark", "role": "Competitor", "status": "Avoidance", "pop": random.randint(1, 5)}
            ]
        elif region == "Temperate":
            ecosystem["fauna"] = [
                {"icon": "🦭", "name": "Harbor Seal", "role": "High-Value Prey", "status": "Evasive", "pop": random.randint(5, 15)},
                {"icon": "🐟", "name": "Mackerel", "role": "Baitfish", "status": "Schooling", "pop": random.randint(200, 800)},
                {"icon": "🐋", "name": "Orca", "role": "Apex Threat", "status": "Aggressive", "pop": random.randint(3, 6)}
            ]
        else: 
            ecosystem["fauna"] = [
                {"icon": "🐘", "name": "Elephant Seal", "role": "Prey", "status": "Haul-out", "pop": random.randint(10, 40)},
                {"icon": "🐟", "name": "Arctic Cod", "role": "Baitfish", "status": "Deep Scatter", "pop": random.randint(100, 500)},
                {"icon": "🦈", "name": "Sleeper Shark", "role": "Competitor", "status": "Passive", "pop": 1}
            ]
            
    elif zone == "Mesopelagic (Twilight)":
        ecosystem["fauna"] = [
            {"icon": "🦑", "name": "Humboldt Squid", "role": "Aggressive Prey", "status": "Defensive", "pop": random.randint(20, 100)},
            {"icon": "🐠", "name": "Lanternfish", "role": "Baitfish", "status": "Bioluminescent Flash", "pop": random.randint(1000, 5000)},
            {"icon": "🗡️", "name": "Swordfish", "role": "Competitor", "status": "Stand-off", "pop": 1}
        ]
    else: 
        ecosystem["fauna"] = [
            {"icon": "🐙", "name": "Giant Squid", "role": "Apex Rival", "status": "Territorial", "pop": 1},
            {"icon": "🐍", "name": "Viperfish", "role": "Opportunist", "status": "Ignoring", "pop": random.randint(5, 20)},
            {"icon": "🐋", "name": "Sperm Whale", "role": "Apex Threat", "status": "Hunting Shark", "pop": random.randint(1, 2)}
        ]
        
    return ecosystem, region

def calculate_ecosystem_impact(shark_action, ecosystem, speed):
    impact_data = {"flora": [], "fauna": []}
    
    for animal in ecosystem['fauna']:
        reaction = "Unaware"
        stress = 0
        if "Pursuit" in shark_action or speed > 15:
            if animal['role'] in ["Prey", "Baitfish"]:
                reaction = "⚡ FLASH SCATTER (Panic)"
                stress = 95
            elif animal['role'] == "High-Value Prey":
                reaction = "🚀 RAPID EVASION"
                stress = 85
            elif "Competitor" in animal['role']:
                reaction = "👀 VIGILANCE (Retreat)"
                stress = 60
            elif "Apex" in animal['role']:
                reaction = "⚔️ COMBAT POSTURE"
                stress = 90
        elif "Foraging" in shark_action:
            if "Prey" in animal['role']:
                reaction = "🛡️ SHOALING (Defense)"
                stress = 50
            else:
                reaction = "⚠️ CAUTION (Tracking)"
                stress = 30
        else: 
            if "Prey" in animal['role']:
                reaction = "👁️ WATCHFUL"
                stress = 20
            else:
                reaction = "💤 IGNORING"
                stress = 5

        impact_data["fauna"].append({
            "Icon": animal['icon'],
            "Species": animal['name'],
            "Role": animal['role'],
            "Reaction": reaction,
            "Stress": stress,
            "Population": animal['pop']
        })

    for plant in ecosystem['flora']:
        effect = plant['base_reaction']
        stress = 0
        if speed > 12 and plant['type'] in ["Forest", "Bed"]:
            effect = "🌊 HYDRODYNAMIC SHEAR"
            stress = 40
        elif speed > 20:
            effect = "💥 PHYSICAL TRAUMA RISK"
            stress = 80
        elif speed < 2:
            effect = "🍃 Minimal Disturbance"
            stress = 10
            
        impact_data["flora"].append({
            "Icon": plant['icon'],
            "Species": plant['name'],
            "Role": plant['type'],
            "Reaction": effect,
            "Stress": stress,
            "Population": plant['density']
        })
        
    return impact_data

# ==============================================================================
# 🧠 STANDARD HELPER FUNCTIONS
# ==============================================================================

def generate_shark_identity(shark_id):
    """Generates a realistic bio-profile for a given shark ID."""
    names = ["Mary Lee", "Breton", "LeeBeth", "Katharine", "Lydia", "Genie", "Ironbound", "Nova", "Luna", "Echo"]
    try: numeric_id = int(float(shark_id))
    except: numeric_id = hash(str(shark_id)) 
    random.seed(numeric_id) 
    return {
        "name": names[numeric_id % len(names)] + f" ({shark_id})",
        "species": "White Shark", # Default, overridden by live data
        "length_ft": round(random.uniform(9.0, 16.5), 1),
        "weight_lbs": random.randint(1200, 3500),
        "tag_type": "SPOT-6 Satellite Tag"
    }

def get_ocean_zone_label(depth):
    if depth < 200: return "☀️ Epipelagic (Sunlight)"
    elif depth < 1000: return "🌑 Mesopelagic (Twilight)"
    else: return "⚫ Bathypelagic (Midnight)"


def make_prey_svg(prey_name):
    """Return an inline SVG data URI (base64) for a given prey name. This avoids external image failures."""
    import base64
    # Simple illustrated placeholder (styled rectangle + silhouette-like shape)
    title = prey_name.replace('&', '&amp;')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400">
        <defs>
            <linearGradient id="g" x1="0" x2="1">
                <stop offset="0%" stop-color="#dff1ff"/>
                <stop offset="100%" stop-color="#eaf7ff"/>
            </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#g)" rx="12"/>
        <g transform="translate(100,70)">
            <ellipse cx="200" cy="120" rx="120" ry="60" fill="#9ad0e8"/>
            <circle cx="270" cy="100" r="24" fill="#7fb8d7"/>
            <rect x="320" y="108" width="36" height="14" rx="7" fill="#7fb8d7" transform="rotate(-12 338 115)"/>
        </g>
        <text x="50%" y="82%" font-family="Arial, Helvetica, sans-serif" font-size="18" fill="#2b5b6f" text-anchor="middle">Primary Target: {title}</text>
    </svg>'''
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"

def calculate_speed(prev_row, curr_row):
    """Estimates speed between two points (Knots)."""
    if prev_row is None: return 0.0
    R = 6371  # Earth radius km
    lat1, lon1 = np.radians(prev_row['lat']), np.radians(prev_row['lon'])
    lat2, lon2 = np.radians(curr_row['lat']), np.radians(curr_row['lon'])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    dist_km = R * c
    return round((dist_km / 1.0) * 0.539957, 1) # Knots

def get_ai_prediction(row, speed, prev_row):
    depth = row.get('depth', 0)
    hour = int(str(row.get('time', '00:00:00')).split(':')[-2]) if 'time' in row else 12
    is_night = hour < 6 or hour > 18
    
    behavior = "Unknown"
    details = "Analyzing telemetry..."
    action_log = "System initializing..."
    threat = "LOW"
    confidence = random.randint(50, 60)
    factors = []

    if speed > 15:
        behavior = "🚀 High-Velocity Pursuit"
        details = "Extreme acceleration detected. Subject is engaging fast pelagic prey."
        action_log = "⚠️ ADRENALINE SPIKE: Tail-beat frequency > 4Hz. Attack vector locked."
        threat = "CRITICAL"
        confidence = random.randint(94, 99)
        factors = ["Velocity > 15 kts", "Rapid Turn Radius", "Burst Energy Signature"]
    elif depth < 20 and speed < 3 and not is_night:
        behavior = "☀️ Solar Basking"
        details = "Holding surface position to regulate body temperature via solar radiation."
        action_log = "✅ THERMAL RECHARGE: Metabolic rate slowed. Surface breach detected."
        threat = "LOW"
        confidence = random.randint(88, 95)
        factors = ["Depth < 20ft", "Low Movement", "UV Exposure High"]
    elif depth > 1000:
        behavior = "🌑 Deep Scattering Layer Tracking"
        details = "Entered Midnight Zone. Hunting bio-luminescent squid biomass."
        action_log = "👁️ PUPIL DILATION: Low-light hunting mode engaged. Vertical dive profile active."
        threat = "MEDIUM"
        confidence = random.randint(75, 88)
        factors = ["Depth > 1000ft", "Bio-luminescence range", "Vertical Vector"]
    elif 200 < depth < 600 and speed > 3:
        behavior = "🌡️ Thermocline Patrol"
        details = "Patrolling the temperature break for stunned prey fish."
        action_log = "📉 SENSOR ALERT: Rapid temp drop (-5°C). Hunting pattern established."
        threat = "MEDIUM"
        confidence = random.randint(80, 90)
        factors = ["Temp Gradient Delta", "Mid-water Column", "Steady Velocity"]
    elif is_night and depth < 100:
        behavior = "🌙 Nocturnal Surface Foraging"
        details = "Using darkness to hunt surface dwellers with limited visibility."
        action_log = "🕵️ STEALTH MODE: Lateral line sensitivity maxed. Erratic search pattern."
        threat = "HIGH"
        confidence = random.randint(70, 85)
        factors = ["Low Light", "Surface Proximity", "Erratic Path"]
    elif speed > 5:
        behavior = "🌊 Trans-Oceanic Migration"
        details = "Consistent heading suggests long-distance transit between habitats."
        action_log = "🧭 NAVIGATION LOCK: Magnetic heading maintained. Ignoring local stimuli."
        threat = "LOW"
        confidence = random.randint(65, 80)
        factors = ["Sustained Velocity", "Linear Trajectory", "Ignoring Stimuli"]
    else:
        behavior = "💤 Energy Conservation"
        details = "Minimal activity. Drifting to conserve caloric burn."
        action_log = "🔋 LOW POWER: Heart rate nominal. Gliding pattern detected."
        threat = "NONE"
        confidence = random.randint(50, 70)
        factors = ["Zero Velocity", "Neutral Buoyancy", "Heart Rate Low"]
        
    return behavior, details, action_log, threat, confidence, factors

def generate_animated_map_html(df_input):
    df = df_input.copy()
    if 'icon' not in df.columns: df['icon'] = "🦈"
    if 'size' not in df.columns: df['size'] = 25

    # Prefer a human-readable UTC timestamp for animation frames when available
    if 'time' in df.columns or 'datetime' in df.columns:
        # Accept either `time` or `datetime` as the timestamp column
        time_col = 'time' if 'time' in df.columns else 'datetime'
        times = pd.to_datetime(df[time_col], errors='coerce', utc=True)
        df['frame_label'] = [t.strftime('%Y-%m-%d %H:%M:%S UTC') if not pd.isnull(t) else f"Ping {i+1}" for i, t in enumerate(times)]
    else:
        df['frame_label'] = [f"Ping {i+1}" for i in range(len(df))]

    fig = px.scatter_mapbox(
        df, lat="lat", lon="lon", text="icon", size="size",
        animation_frame="frame_label", zoom=6, height=550
    )
    trace_line = px.line_mapbox(df, lat="lat", lon="lon").data[0]
    trace_line.line.color = 'rgba(0, 119, 182, 0.6)'
    trace_line.line.width = 3
    fig.add_trace(trace_line)
    fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 150
    return fig.to_html(include_plotlyjs='cdn')

def render_tactical_console(df, shark_name, shark_species_actual):
    """Renders the FOUR-BLOCK dashboard (Telemetry, AI, Ecosystem, Diet)."""
    
    # --- 0. TIMELINE CONTROL ---
    with st.container():
        if len(df) > 1:
            # If timestamps exist, show human-friendly UTC labels via select_slider so users pick by time
            if 'time' in df.columns or 'datetime' in df.columns:
                time_col = 'time' if 'time' in df.columns else 'datetime'
                times = pd.to_datetime(df[time_col], errors='coerce', utc=True)
                time_labels = [t.strftime('%Y-%m-%d %H:%M:%S UTC') if not pd.isna(t) else f'Ping {i+1}' for i, t in enumerate(times)]
                selected_label = st.select_slider("📼 Scrub Mission Timeline (UTC):", options=time_labels, value=time_labels[0])
                selected_index = time_labels.index(selected_label)
            else:
                selected_index = st.slider("📼 Scrub Mission Timeline:", 0, len(df) - 1, 0, format="Ping #%d")
        else:
            selected_index = 0
            
    # --- 1. DATA GENERATION ---
    unique_seed = hash(shark_name + str(selected_index)) % (2**32)
    np.random.seed(unique_seed)
    random.seed(unique_seed)
    
    row = df.iloc[selected_index]
    prev = df.iloc[selected_index - 1] if selected_index > 0 else None
    
    # 1. KALMAN FILTER SMOOTHING (Advanced Math Feature)
    smoothed_lats, smoothed_lons = apply_kalman_smoothing(df.iloc[:selected_index+1])
    current_smooth_lat = smoothed_lats[-1] if smoothed_lats else row['lat']
    current_smooth_lon = smoothed_lons[-1] if smoothed_lons else row['lon']

    # Physics
    shark_depth_bias = (hash(shark_name) % 800)
    sim_depth = int(abs(np.sin(selected_index * 0.2) * 400 + shark_depth_bias + np.random.normal(0, 50)))
    sim_temp = max(4.0, 28.0 - (sim_depth / 150.0)) + np.random.normal(0, 0.5)
    
    depth = row.get('depth', sim_depth)
    temp = row.get('temp', round(sim_temp, 1))

    # Compute smoothed speed using Kalman outputs (preferred)
    smooth_speed_kts = 0.0
    turn_angle_deg = None
    try:
        if len(smoothed_lats) >= 2:
            lat1, lon1 = smoothed_lats[-2], smoothed_lons[-2]
            lat2, lon2 = smoothed_lats[-1], smoothed_lons[-1]
            dist_km = haversine_km(lat1, lon1, lat2, lon2)
            # time delta (hours) between pings
            tcol = 'time' if 'time' in df.columns else 'datetime' if 'datetime' in df.columns else None
            if tcol:
                times = pd.to_datetime(df[tcol].iloc[:selected_index+1], errors='coerce', utc=True)
                t1 = times.iloc[-2]
                t2 = times.iloc[-1]
                dt_hours = max((t2 - t1).total_seconds() / 3600.0, 1.0/3600.0) if not pd.isna(t1) and not pd.isna(t2) else 1.0
            else:
                dt_hours = 1.0
            smooth_speed_kts = round((dist_km / 1.852) / dt_hours, 1)
        if len(smoothed_lats) >= 3:
            # compute turn angle between last two segments
            lat0, lon0 = smoothed_lats[-3], smoothed_lons[-3]
            lat1, lon1 = smoothed_lats[-2], smoothed_lons[-2]
            lat2, lon2 = smoothed_lats[-1], smoothed_lons[-1]
            def bearing(a_lat,a_lon,b_lat,b_lon):
                y = np.sin(np.radians(b_lon-a_lon)) * np.cos(np.radians(b_lat))
                x = np.cos(np.radians(a_lat))*np.sin(np.radians(b_lat)) - np.sin(np.radians(a_lat))*np.cos(np.radians(b_lat))*np.cos(np.radians(b_lon-a_lon))
                return (np.degrees(np.arctan2(y,x)) + 360) % 360
            b1 = bearing(lat0, lon0, lat1, lon1)
            b2 = bearing(lat1, lon1, lat2, lon2)
            diff = abs((b2 - b1 + 180) % 360 - 180)
            turn_angle_deg = round(diff, 1)
    except Exception:
        smooth_speed_kts = 0.0
        turn_angle_deg = None

    # use smoothed speed to feed downstream calculations where available
    final_speed = smooth_speed_kts if smooth_speed_kts > 0 else max(0.0, round(calculate_speed(prev, row) + np.random.uniform(-1.0, 2.0), 1))
    
    # AI Logic
    ai_beh, ai_det, ai_act, ai_thr, ai_conf, ai_fac = get_ai_prediction(row, final_speed, prev)
    
    # Ecosystem Logic
    local_ecosystem, current_region = get_local_ecosystem(row['lat'], row['lon'], depth, temp)
    impact_data = calculate_ecosystem_impact(ai_beh, local_ecosystem, final_speed)
    
    # Diet Logic
    diet_info = get_dietary_profile(shark_species_actual, current_region, row['lat'], row['lon'])
    
    # NEW: Advanced Analytics (use real fields when available)
    spatial_buffer = analyze_spatial_buffer(row['lat'], row['lon'], map_chlor if 'map_chlor' in globals() else None, globals().get('lat_grid'), globals().get('lon_grid'))
    okubo_w, eddy_status = calculate_okubo_weiss(row['lat'], row['lon'], globals().get('map_ssh'), globals().get('lat_grid'), globals().get('lon_grid'))

    # =========================================================
    # BLOCK 1: TELEMETRY
    # =========================================================
    st.markdown(f"### 🕵️ Tactical Telemetry: {shark_name}")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)

        # Format time as UTC if possible (accept `time` or `datetime`)
        time_raw = None
        if 'time' in row.index:
            time_raw = row.get('time')
        elif 'datetime' in row.index:
            time_raw = row.get('datetime')

        try:
            time_parsed = pd.to_datetime(time_raw, errors='coerce', utc=True)
            time_utc_str = time_parsed.strftime('%Y-%m-%d %H:%M:%S UTC') if not pd.isna(time_parsed) else 'N/A'
        except Exception:
            time_utc_str = 'N/A'

        c1.metric("🕒 Time (UTC)", time_utc_str)
        c2.metric("🚀 Velocity (Kalman)", f"{final_speed} kts", delta="Smoothed", delta_color="normal")
        c3.metric("📉 Depth", f"-{depth} ft")
        c4.caption(f"ZONE: {get_ocean_zone_label(depth)}")

        # Supplemental telemetry: turn angle and local productivity
        s1, s2, s3 = st.columns([1,1,1])
        s1.metric("🔁 Turn Angle", f"{turn_angle_deg}°" if turn_angle_deg is not None else "N/A")
        if isinstance(spatial_buffer, dict) and spatial_buffer.get('stats'):
            s2.metric("🌿 Mean Chlorophyll (5km)", f"{spatial_buffer['stats']['mean_chl']:.2f} mg/m^3")
            s3.metric("🌿 Max Chlorophyll (5km)", f"{spatial_buffer['stats']['max_chl']:.2f}")
        else:
            s2.metric("🌿 Means Chlorophyll (5km)", "N/A")
            s3.metric("🌿 Max Chlorophyll (5km)", "N/A")

    # =========================================================
    # BLOCK 2: NEURAL NETWORK
    # =========================================================
    st.markdown("### 🧠 Neural Network Analysis")
    status_color = "red" if ai_thr == "CRITICAL" else "orange" if ai_thr == "HIGH" else "green"
    with st.container(border=True):
        h1, h2 = st.columns([3, 1])
        h1.subheader(f"{ai_beh}")
        h2.progress(ai_conf / 100)
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.markdown(f"**THREAT LEVEL:** :{status_color}[**{ai_thr}**]")
            st.code(ai_act, language=None)
        
        with c2:
            st.info(f"**Interpretation:** {ai_det}")
            st.markdown("**🌊 Advanced Ocean Dynamics (SWOT/NASA)**")
            st.markdown(f"- **Eddy Status:** `{eddy_status}`")
            st.markdown(f"- **Okubo-Weiss (W):** `{okubo_w:.3f}`")
            if isinstance(spatial_buffer, dict) and spatial_buffer.get('stats'):
                st.markdown(f"- **Buffer (5km):** `{spatial_buffer.get('feature')}`")
                st.markdown(f"  - Mean Chlorophyll: `{spatial_buffer['stats']['mean_chl']:.3f}` mg/m^3")
                st.markdown(f"  - Max Chlorophyll: `{spatial_buffer['stats']['max_chl']:.3f}` mg/m^3")
            else:
                st.markdown(f"- **Buffer (5km):** `{spatial_buffer}`")

    # =========================================================
    # BLOCK 3: ECOSYSTEM
    # =========================================================
    st.markdown("### 🌿 Bio-Morphic Ecosystem Impact")
    st.caption("Real-time simulation of local flora/fauna reactions based on shark vector.")
    
    st.markdown("#### 🐟 Local Marine Fauna")
    cols = st.columns(3)
    for i, animal in enumerate(impact_data['fauna']):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {animal['Icon']} {animal['Species']}")
                st.caption(f"**Role:** {animal['Role']}")
                st.metric("Est. Population", f"{animal['Population']}", delta="Present", delta_color="off")
                if animal['Stress'] > 80: st.error(f"**{animal['Reaction']}**")
                elif animal['Stress'] > 40: st.warning(f"**{animal['Reaction']}**")
                else: st.success(f"**{animal['Reaction']}**")
                st.progress(animal['Stress'] / 100, text="Bio-Stress Level")

    st.markdown("#### 🍃 Local Marine Flora")
    f_cols = st.columns(3)
    for i, plant in enumerate(impact_data['flora']):
        with f_cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {plant['Icon']} {plant['Species']}")
                st.caption(f"**Type:** {plant['Role']}")
                st.metric("Density", f"{plant['Population']}")
                if plant['Stress'] > 50: st.warning(f"**{plant['Reaction']}**")
                else: st.info(f"**{plant['Reaction']}**")

    # =========================================================
    # BLOCK 4: NEW PREDATION & DIET ANALYSIS (EXPANDED)
    # =========================================================
    st.markdown("### 🍽️ Predation & Dietary Analytics")
    st.caption(f"Species-specific metabolic tracking for **{shark_species_actual}** in **{current_region}** waters.")
    
    with st.container(border=True):
        d1, d2 = st.columns([1, 2])
        
        with d1:
            # High-Res Image of Prey (validate URL and provide fallback if unavailable)
            img_url = diet_info['prey_data'].get('img', '')
            fallback = "https://via.placeholder.com/600x400?text=No+image+available"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Referer": "https://unsplash.com/"}
            img_bytes = None
            debug_info = {}

            def _is_image_bytes(b):
                if not b or not isinstance(b, (bytes, bytearray)):
                    return False
                # JPEG, PNG, GIF, WEBP
                return b.startswith(b"\xff\xd8") or b.startswith(b"\x89PNG") or b.startswith(b"GIF8") or b[0:4] == b"RIFF"

            try:
                if not img_url:
                    raise ValueError("No image URL provided")
                r = requests.get(img_url, headers=headers, timeout=6)
                debug_info['url_status'] = getattr(r, 'status_code', None)
                debug_info['content_type'] = r.headers.get('content-type', '') if r is not None else ''
                content = r.content if r is not None else None
                if r.status_code // 100 == 2 and (debug_info['content_type'].startswith('image') or _is_image_bytes(content)):
                    img_bytes = content
                r.close()
            except Exception as e:
                debug_info['error'] = str(e)
                img_bytes = None

            # Try fallback if primary failed
            if img_bytes is None:
                try:
                    rf = requests.get(fallback, timeout=6)
                    debug_info['fb_status'] = getattr(rf, 'status_code', None)
                    debug_info['fb_ct'] = rf.headers.get('content-type', '') if rf is not None else ''
                    if rf.status_code // 100 == 2 and _is_image_bytes(rf.content):
                        img_bytes = rf.content
                    rf.close()
                except Exception as e:
                    debug_info['fb_error'] = str(e)
                    img_bytes = None

            if img_bytes is not None:
                st.image(img_bytes, caption=f"Primary Target: {diet_info['prey_name']}", use_container_width=True)
            else:
                # Use a locally generated SVG 'photo' so users see a proper image even when remote fetch fails
                svg_data_uri = make_prey_svg(diet_info['prey_name'])
                # Render via <img> tag to ensure consistent sizing
                components.html(f'<img src="{svg_data_uri}" style="width:100%;height:auto;border-radius:6px;"/>', height=260)
                # Subtle caption (no HTTP errors shown)
                st.caption("Image source unavailable — showing local artwork.")
            
        with d2:
            st.subheader(f"Current Status: {diet_info['status']}")
            
            # Digestion Bar
            if diet_info['digest_progress'] > 0:
                st.progress(diet_info['digest_progress'] / 100, text=f"Digestion Cycle: {diet_info['digest_progress']}% Complete")
            else:
                st.info("⚠️ Stomach Empty: Hunting algorithms engaged.")
            
            # Nutrition Stats
            m1, m2, m3 = st.columns(3)
            m1.metric("Est. Calories", f"{diet_info['prey_data']['kcal']}", "kcal")
            m2.metric("Fat Content", diet_info['prey_data']['fat'])
            m3.metric("Protein", diet_info['prey_data']['protein'])
            
            st.markdown("---")
            st.markdown(f"**⚔️ Hunting Strategy:** {diet_info['prey_data']['tactic']}")
            st.markdown(f"**🛡️ Prey Defense:** {diet_info['prey_data']['defense']}")
            st.markdown(f"**⚠️ Competition:** {diet_info['prey_data']['rivals']}")
            
            st.markdown(f"**🎯 Target Depth:** `{diet_info['prey_data']['hunt_depth']}` | **⚡ Yield:** `{diet_info['prey_data']['efficiency']}`")
            
            # Macronutrient Chart (Simulated Pie Chart)
            macros = diet_info['prey_data']['macros']
            fig_pie = px.pie(
                values=list(macros.values()), 
                names=list(macros.keys()),
                title=f"Nutritional Profile: {diet_info['prey_name']}",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_pie.update_layout(height=250, margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_pie, use_container_width=True)

@st.cache_data
def load_simulation_data():
    model = joblib.load("models/shark_ai_model.pkl")
    try: imputer = joblib.load("models/shark_imputer.pkl")
    except: imputer = None

    map_sst = np.nan_to_num(np.load("models/map_sst.npy"), nan=0.0)
    map_chlor = np.nan_to_num(np.load("models/map_chlor.npy"), nan=0.0)
    map_depth = np.nan_to_num(np.load("models/map_depth.npy"), nan=0.0)

    # Optional grids / SSH (SWOT-derived) if available
    try:
        lat_grid = np.load("models/lat_grid.npy")
        lon_grid = np.load("models/lon_grid.npy")
    except Exception:
        lat_grid = None
        lon_grid = None

    try:
        map_ssh = np.load("models/map_ssh.npy")
    except Exception:
        map_ssh = None

    df = pd.read_csv("models/shark_data.csv")
    return model, imputer, map_sst, map_chlor, map_depth, lat_grid, lon_grid, map_ssh, df

# ==============================================================================
# MAIN APP LOGIC
# ==============================================================================
st.sidebar.title("🦈 Command Center")
app_mode = st.sidebar.selectbox("Select Mission Profile:", 
                                ["AI Habitat Simulation (Offline)", "Live Global Tracker (Real-Time)"])
st.sidebar.markdown("---")

if app_mode == "Live Global Tracker (Real-Time)":
    
    if not NETWORK_AVAILABLE:
        st.error("❌ 'shark_network.py' not found! Please create the file to use Live Tracking.")
        st.stop()

    st.title("🌍 Global Shark Tracker (Live Satellite Feed)")
    with st.spinner("📡 Establishing Downlink with Argonaut Satellites..."):
        df_live = fetch_live_sharks()
    
    if df_live.empty:
        st.warning("⚠️ No signals received.")
    else:
        tab1, tab2 = st.tabs(["📍 Global Map View", "🔬 Mission Analysis"])

        with tab1:
            st.subheader(f"Active Signals: {len(df_live)} Tags Online")

            # Allow user to show all tags or limit for performance
            max_markers = st.sidebar.number_input(
                "Max markers to display on global map (0 = all)",
                min_value=0,
                max_value=int(len(df_live)),
                value=0,
                step=100
            )

            if int(max_markers) == 0:
                df_plot = df_live
            else:
                df_plot = df_live.head(int(max_markers))

            if len(df_plot) > 2000:
                st.warning("Rendering many markers may be slow in the browser; consider limiting the number or use the Mission Analysis tab.")

            fig_global = px.scatter_geo(
                df_plot, lat="lat", lon="lon",
                hover_name="name", hover_data=["species", "last_seen"],
                color="species", projection="natural earth",
                title="Real-Time Fleet Positions"
            )
            fig_global.update_geos(showcountries=True, countrycolor="Black", showocean=True, oceancolor="Azure")
            fig_global.update_layout(height=600, margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_global, use_container_width=True)

        with tab2:
            col1, col2 = st.columns([1, 3])

            with col1:
                st.markdown("### 🎯 Target Lock")
                shark_options = df_live['name'].tolist()
                selected_name = st.selectbox("Select Animal:", shark_options)
                tgt = df_live[df_live['name'] == selected_name].iloc[0]
                
                if tgt['image_url']: st.image(tgt['image_url'], use_container_width=True)
                
                with st.expander("Bio-Profile", expanded=True):
                    st.markdown(f"""
                    **Name:** {tgt['name']}  
                    **Species:** {tgt['species']}  
                    **Last Ping:** {tgt['last_seen']}
                    """)

                if st.button("📡 Download Path History", type="primary"):
                    with st.spinner("Retrieving archival telemetry..."):
                        df_path = fetch_shark_path(int(tgt['id']))
                        st.session_state['path_data'] = df_path
                        st.session_state['path_name'] = selected_name
                        st.session_state['path_species'] = tgt['species'] # Capture Species
                        st.session_state['show_shark_map'] = True 
                    st.success(f"Data Loaded: {len(df_path)} Pings")

            with col2:
                has_data = ('path_data' in st.session_state and 
                            st.session_state.get('path_name') == selected_name and 
                            not st.session_state['path_data'].empty)

                if st.session_state.get('show_shark_map') and has_data:
                    st.subheader(f"🗺️ Trajectory Analysis: {selected_name}")
                    
                    with st.container(border=True):
                        map_html = generate_animated_map_html(st.session_state['path_data'])
                        components.html(map_html, height=550)
                    
                    # RENDER THE NEW 4-BLOCK CONSOLE (Pass Species)
                    # Use default 'White Shark' if species not found for robustness
                    species_for_diet = st.session_state.get('path_species', 'White Shark')
                    render_tactical_console(st.session_state['path_data'], selected_name, species_for_diet)
                    
                    if st.button("❌ Close Mission Replay"):
                        st.session_state['show_shark_map'] = False
                        st.rerun()

                elif has_data:
                    st.info("Tracking Data Ready. Click 'Download Path History' to re-open.")
                else:
                    st.info("👈 Select a shark from the list and download path history to begin analysis.")

else:
    # --- SIMULATION MODE (PRESERVED FULLY) ---
    try:
        model, imputer, map_sst, map_chlor, map_depth, lat_grid, lon_grid, map_ssh, df_sharks = load_simulation_data()
        # Expose to module scope for helper functions
        globals()['lat_grid'] = lat_grid
        globals()['lon_grid'] = lon_grid
        globals()['map_ssh'] = map_ssh
    except Exception as e:
        st.error(f"❌ Error loading simulation models: {e}")
        st.stop()

    st.sidebar.subheader("📡 Tracker Settings")
    unique_sharks = df_sharks['shark_id'].unique() if 'shark_id' in df_sharks.columns else list(range(1, 6))
    selected_id = st.sidebar.selectbox("Select Tagged Shark:", unique_sharks)
    profile = generate_shark_identity(selected_id)
    
    st.sidebar.info(f"**TRACKING: {profile['name']}**")
    st.sidebar.markdown("---")
    
    temp_adjust = st.sidebar.slider("Ocean Warming (°C)", 0.0, 4.0, 0.0, 0.5)
    eddy_boost = st.sidebar.slider("Eddy Strength", 0.5, 2.0, 1.0, 0.1)
    
    layer = st.sidebar.radio("Select Layer:", 
                            ["🦈 AI Habitat Prediction", "🌀 Okubo-Weiss (Eddies)", "🌡️ Temperature (SST)", "🌿 Chlorophyll"])

    st.title("🦈 AI Habitat Monitor (NASA-Grade)")
    
    current_sst = map_sst + temp_adjust
    dy, dx = np.gradient(current_sst)
    map_gradient = np.clip(np.nan_to_num(np.sqrt(dx**2 + dy**2)), 0, 0.1)
    
    if layer == "🦈 AI Habitat Prediction":
        with st.spinner("Calculating..."):
            X_map = np.column_stack((current_sst.flatten(), map_depth.flatten(), map_chlor.flatten(), map_gradient.flatten(), map_gradient.flatten()))
            if imputer: X_map = imputer.transform(X_map)
            probs = model.predict_proba(X_map)[:, 1]
            display_map = probs.reshape(current_sst.shape)
            title = "Habitat Suitability Probability"
            cmap = "inferno"
    else:
        display_map = current_sst
        title = "Surface Temperature"
        cmap = "viridis"

    fig = px.imshow(display_map, color_continuous_scale=cmap, origin='lower', title=title)
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    col1.metric("Avg Habitat Suitability", f"{np.mean(display_map):.1%}")
    col2.metric("Current Target", profile['name'])