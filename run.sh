#!/usr/bin/env bash
set -euo pipefail

echo "Setting up environment (Unix)..."
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

echo "Fetching data..."
python get_sst.py
python get_depth.py
python get_data.py

echo "Done. To run the app: streamlit run shark_app.py"