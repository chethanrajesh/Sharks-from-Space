import earthaccess
from pathlib import Path

def download_sample_data(output_dir):
    """
    Searches for and downloads sample files from NASA satellite missions:
    - PACE (Phytoplankton, Aerosols, Clouds, Ecosystem)
    - MODIS-Aqua (Moderate Resolution Imaging Spectroradiometer)
    - SWOT (Surface Water and Ocean Topography)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Searching for NASA satellite data to save in {output_dir}...")

    # Authenticate with earthaccess
    try:
        earthaccess.login(strategy="environment")
    except Exception as e:
        print(f"Note: Using local credentials or unauthenticated search - {e}")

    # List of datasets to fetch (in priority order)
    datasets = [
        {
            'short_name': 'PACE_OCI_L2_BGC',
            'description': 'PACE Biogeochemical (Chlorophyll/Food Web)',
            'count': 1
        },
        {
            'short_name': 'MODIS_AQUA_L3_CHL_MO_4KM',
            'description': 'MODIS-Aqua Monthly Chlorophyll (20+ year timeseries)',
            'count': 1
        },
        {
            'short_name': 'SWOT_L3_LR_SSH_SSH_2_1_Gridded',
            'description': 'SWOT Sea Surface Height (Eddy Detection)',
            'count': 1
        }
    ]

    for dataset in datasets:
        try:
            print(f"\n🛰️ Searching for {dataset['description']}...")
            results = earthaccess.search_data(
                short_name=dataset['short_name'],
                count=dataset['count']
            )
            
            if results:
                print(f"✅ Found {len(results)} file(s). Downloading...")
                earthaccess.download(results, str(output_dir))
                print(f"✅ Downloaded {dataset['description']}")
            else:
                print(f"⚠️ No {dataset['description']} found.")
        except Exception as e:
            print(f"⚠️ Could not fetch {dataset['description']}: {e}")
    
    print("\n✅ Data fetching complete!")