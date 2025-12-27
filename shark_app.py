import streamlit as st
import numpy as np
import pandas as pd
import joblib
import plotly.express as px
import plotly.graph_objects as go
import random
from datetime import datetime
import streamlit.components.v1 as components

# Import Real-Time Engine (Must be in the same folder as shark_network.py)
try:
    from shark_network import fetch_live_sharks, fetch_shark_path
    NETWORK_AVAILABLE = True
except ImportError:
    NETWORK_AVAILABLE = False

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shark Habitat AI - Global Uplink", layout="wide", page_icon="🦈")

# ==============================================================================
# 🧠 NEW: DIETARY & PREDATION ENGINE (Fixed Images & Analytics)
# ==============================================================================

def get_dietary_profile(species, region):
    """
    Returns the specific diet, prey images, and nutritional data 
    based on the Shark Species and current Region.
    """
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
    if 'time' in df.columns: df['frame_label'] = df['time'].astype(str)
    else: df['frame_label'] = [f"Ping {i+1}" for i in range(len(df))]

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
            selected_index = st.slider("📼 Scrub Mission Timeline:", 0, len(df) - 1, 0, format="Ping #%d")
        else: selected_index = 0
            
    # --- 1. DATA GENERATION ---
    unique_seed = hash(shark_name + str(selected_index)) % (2**32)
    np.random.seed(unique_seed)
    random.seed(unique_seed)
    
    row = df.iloc[selected_index]
    prev = df.iloc[selected_index - 1] if selected_index > 0 else None
    
    # Physics
    shark_depth_bias = (hash(shark_name) % 800)
    sim_depth = int(abs(np.sin(selected_index * 0.2) * 400 + shark_depth_bias + np.random.normal(0, 50)))
    sim_temp = max(4.0, 28.0 - (sim_depth / 150.0)) + np.random.normal(0, 0.5)
    
    depth = row.get('depth', sim_depth)
    temp = row.get('temp', round(sim_temp, 1))
    
    calc_speed = calculate_speed(prev, row)
    final_speed = max(0.0, round(calc_speed + np.random.uniform(-1.0, 2.0), 1))
    
    # AI Logic
    ai_beh, ai_det, ai_act, ai_thr, ai_conf, ai_fac = get_ai_prediction(row, final_speed, prev)
    
    # Ecosystem Logic
    local_ecosystem, current_region = get_local_ecosystem(row['lat'], row['lon'], depth, temp)
    impact_data = calculate_ecosystem_impact(ai_beh, local_ecosystem, final_speed)
    
    # Diet Logic
    diet_info = get_dietary_profile(shark_species_actual, current_region)
    
    # =========================================================
    # BLOCK 1: TELEMETRY
    # =========================================================
    st.markdown(f"### 🕵️ Tactical Telemetry: {shark_name}")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🕒 Time (UTC)", str(row.get('time', 'N/A')).split(" ")[-1])
        c2.metric("🚀 Velocity", f"{final_speed} kts")
        c3.metric("📉 Depth", f"-{depth} ft")
        c4.caption(f"ZONE: {get_ocean_zone_label(depth)}")

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
        c1.markdown(f"**THREAT LEVEL:** :{status_color}[**{ai_thr}**]")
        c1.code(ai_act, language=None)
        c2.info(f"**Interpretation:** {ai_det}")
        c2.caption("🔍 **FACTORS:** " + ", ".join(ai_fac))

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
            # High-Res Image of Prey
            st.image(diet_info['prey_data']['img'], caption=f"Primary Target: {diet_info['prey_name']}", use_container_width=True)
            
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
    df = pd.read_csv("models/shark_data.csv")
    return model, imputer, map_sst, map_chlor, map_depth, df

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
            fig_global = px.scatter_geo(
                df_live.head(100), lat="lat", lon="lon",
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
        model, imputer, map_sst, map_chlor, map_depth, df_sharks = load_simulation_data()
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