
<<<<<<< HEAD
# Sharks From Space 🦈🌊

**Short description:** A reproducible pipeline and interactive dashboard for exploring shark habitat preferences using satellite data (chlorophyll, SST) and bathymetry. Built with Python, Xarray, scikit-learn and Streamlit.

---

## Table of Contents
- **Quick start** ✅
- **Project structure** 📁
- **Notebooks & scripts** 🧪
- **Outputs** 📦
- **Troubleshooting** ⚠️
- **Contributing** 🤝
- **License** 📜

---

## Quick start ✅
1. Create an environment and install dependencies:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Fetch required satellite data and bathymetry (examples):

```bash
python get_sst.py
python get_depth.py
python get_data.py
```

3. Run the exploratory notebook:

- Open `notebooks/exploration.ipynb` in Jupyter or VS Code and run cells in order.
- The notebook prepares training data, trains models (1–3 variables), creates prediction maps, and saves artifacts to `../models/` and `../reports/`.

4. Start the interactive app:

```bash
streamlit run shark_app.py
```

---

## Project structure 📁
- `notebooks/` — exploratory and modeling notebooks (main workflow is `exploration.ipynb`).
- `data/` — processed CSVs (e.g., `my_training_data.csv`, `shark_tracks.csv`).
- `downloads/` — raw downloaded NetCDFs (chlorophyll, sst, bathymetry).
- `models/` — saved numpy arrays, trained model(s), scalers, and supporting grids.
- `reports/` — generated figures, maps, and interactive HTML dashboard.
- `shark_app.py` — Streamlit application to visualize maps and shark data.
- `get_sst.py`, `get_depth.py`, `get_data.py` — data fetching scripts.
- `main.py` — project-level orchestration (data processing / pipeline runner).

---

## Notebooks & scripts 🧪
- `notebooks/exploration.ipynb` — end-to-end analysis:
  - Extracts satellite values at shark and background points
  - Trains logistic regression models (1-3 vars)
  - Builds prediction maps and a lightweight interactive dashboard
  - Saves models/scalers (`models/shark_ai_model.pkl`, `models/shark_scaler.pkl`) and final images (`reports/`)

- `shark_app.py` — Streamlit app that loads `models/*.npy` and `shark_data.csv` to produce an interactive mapping app.

---

## Outputs 📦
- `models/lat_grid.npy`, `models/lon_grid.npy`, `models/map_*.npy` — precomputed raster layers for fast app loading.
- `models/shark_ai_model.pkl`, `models/shark_scaler.pkl` — trained model and scaler.
- `reports/shark_dashboard.html`, `reports/shark_habitat_map.png` — visual outputs and dashboard.

---

## Troubleshooting & Tips ⚠️
- If the notebooks cannot find satellite files, confirm `downloads/` exists and contains `.nc` files for `chlorophyll`, `sst`, and `bathymetry`.
- Large NetCDF bathymetry files may cause RAM issues. The notebook includes safe downsampling and resizing strategies (check the "Safe Mode" steps in `exploration.ipynb`).
- If models or scalers are not found, re-run the model training cells (Steps 12–14 in `exploration.ipynb`) and re-save them (there's a cell to re-save final model/scaler).
- Windows users: be mindful of path separators when running commands from PowerShell.

---

## Contributing 🤝
- Open an issue to report bugs or request features.
- Submit PRs against `main` with tests or reproducible examples.

---

## License 📜
Add a LICENSE file (for example, MIT) to make the intended license explicit. If you want, I can add one for you.

---

If you'd like, I can also add a short `CONTRIBUTING.md`, common `Makefile`/`run.sh` commands, or badges for CI and coverage. Let me know what you'd prefer. ✅
=======
# Sharks

Tools and experiments for working with shark foraging and long‑term movement data, built primarily in Python and Jupyter notebooks. [web:0]

## Project structure

- `.venv/` – Local virtual environment (not tracked in detail in this repo). [web:0]  
- `.vscode/` – Editor configuration for working on the project in VS Code. [web:0]  
- `data/` – Input data files for shark-related analyses (add a short description of each dataset here). [web:0]  
>>>>>>> e2f038a040a903b38ee8aa00b0e24ec022c45d70
- `create_shark_notebook.py` – Helper script to generate or configure shark analysis notebooks. [web:0]  
- `shark_Foraging_LongTerm.ipynb` – Main notebook exploring long‑term shark foraging patterns. [web:0]

## Getting started

1. Clone the repository:
   ```
   git clone https://github.com/Amisha2121/Sharks.git
   cd Sharks
   ```
2. (Optional) Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies (create a `requirements.txt` and update this step once ready):
   ```
   pip install -r requirements.txt
   ```

## Usage

- Run the helper script:
  ```
  python create_shark_notebook.py
  ```
- Open `shark_Foraging_LongTerm.ipynb` in Jupyter Lab, Jupyter Notebook, or VS Code to explore the analyses.

## Technologies

The repository is mainly Python, with Jupyter notebooks and some compiled‑language dependencies (C, C++, Cython, CMake) via libraries. [web:0]

## Contributing

1. Fork the repo and create a new branch.  
2. Make your changes with clear commit messages.  
3. Open a pull request describing what you changed and why.

## License

Add a license of your choice (for example, MIT) and describe it here.
```

To make it downloadable:

1. Create a new file in the repo named `README.md`.
2. Paste the content above and commit it.
3. On GitHub, open `README.md`, click the “Download raw file” button (or use `curl`/`wget`) to download it when needed.

[1](https://github.com/Amisha2121/Sharks)
