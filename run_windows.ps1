# PowerShell script to setup environment and run app (Windows)
Set-StrictMode -Version Latest

Write-Host "Setting up virtual environment (Windows)..."
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Write-Host "Fetching data..."
python get_sst.py
python get_depth.py
python get_data.py

Write-Host "Done. To run the app: streamlit run shark_app.py"