
# Sharks From Space 🦈🌊

**A reproducible pipeline and interactive app for exploring shark habitat using satellite data (chlorophyll, SST) and bathymetry.**

---

## Table of contents
- Quick start ✅
- Data & downloads 📥
- Usage 🔧
- Project structure 📁
- Outputs & artifacts 📦
- Troubleshooting ⚠️
- Contributing & license 🤝📜

---

## Quick start ✅
1. Clone the repo:

```bash
git clone https://github.com/Amisha2121/Sharks-from-Space-main.git
cd Sharks-from-Space-main
```

2. Create and activate a virtual environment (recommended):

- macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

- Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Fetch required satellite and bathymetry data:

```bash
python get_sst.py
python get_depth.py
python get_data.py
```

5. Run the interactive app (Streamlit):

```bash
streamlit run shark_app.py
```

Tip: Windows users can run the prepared `run_windows.ps1` script to create the venv, install dependencies, fetch data, and print the command to run the app.

---

## Data & downloads 📥
- Raw NetCDF downloads are stored in `downloads/` (subfolders: `chlorophyll/`, `sst/`, `bathymetry/`).
- `get_sst.py`, `get_depth.py`, and `get_data.py` are helper scripts to obtain and subset the data needed for the analyses.

---

## Usage 🔧
- Notebooks
  - Open `notebooks/exploration.ipynb` or `notebooks/shark_Foraging_LongTerm.ipynb` to reproduce analyses and model training.
- App
  - `shark_app.py` loads precomputed grids and model artifacts from `models/` and visualizes predictions and shark tracks.

---

## Project structure 📁
- `notebooks/` — analysis and modeling notebooks
- `data/` — processed CSVs (training data, shark tracks)
- `downloads/` — raw satellite and bathymetry NetCDFs
- `models/` — precomputed grids and saved model/scaler artifacts
- `reports/` — generated dashboards and figures
- `shark_app.py` — Streamlit app
- `get_*.py` — data fetching utilities

---

## Outputs & artifacts 📦
- `models/lat_grid.npy`, `models/lon_grid.npy`, `models/map_*.npy` — grids and map layers
- `models/shark_ai_model.pkl`, `models/shark_scaler.pkl` — trained model & scaler (if produced)
- `reports/` — HTML dashboard and figures

---

## Troubleshooting ⚠️
- App fails to start or exits with code 1:
  - Reproduce and capture the traceback by running:

    ```bash
    python -m streamlit run shark_app.py --logger.level=debug
    # or
    streamlit run shark_app.py
    ```
  - Inspect the terminal stack trace — it usually shows the missing import or failing operation.

- Common fixes:
  - ModuleNotFoundError / ImportError: install missing packages:

    ```bash
    pip install -r requirements.txt
    pip install streamlit-folium folium
    ```

  - PowerShell / activation errors (Windows): allow script execution and activate the venv:

    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

  - Missing `models/` or `downloads/` files: re-run the data fetch scripts or regenerate model artifacts from the notebooks:

    ```bash
    python get_sst.py
    python get_depth.py
    python get_data.py
    ```

  - Port or server conflicts: run on a different port:

    ```bash
    streamlit run shark_app.py --server.port 8502
    ```

  - Folium / map rendering issues: ensure `streamlit-folium` is installed and up to date; try a compatible version if UI breaks.

- How to narrow the issue quickly:
  - Comment out heavy processing blocks or large imports in `shark_app.py` and run incrementally to locate the failing line.
  - Create a minimal reproducer that only imports libraries one-by-one until the error appears.

- Still stuck? Copy the full terminal traceback and open an issue or share it here; I’ll help diagnose and fix the specific error.

---

## Contributing & license 🤝📜
- See `CONTRIBUTING.md` for contribution guidelines and PR checklist.
- This project is licensed under the **MIT License** — see `LICENSE`.

---

## Maintainers / Contact
- Maintainer: Amisha V. (see repo for contact or open an issue)

---

If you'd like, I can add CI badges, a short summary README for `notebooks/`, or improve the Quick Start to include Docker or GitHub Actions; say which you prefer and I can add it. ✅

```

To make it downloadable:

1. Create a new file in the repo named `README.md`.
2. Paste the content above and commit it.
3. On GitHub, open `README.md`, click the “Download raw file” button (or use `curl`/`wget`) to download it when needed.

[1](https://github.com/Amisha2121/Sharks)
