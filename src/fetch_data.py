import earthaccess
from pathlib import Path

def download_sample_data(output_dir):
    """
    Searches for and downloads 1 sample file from the PACE satellite.
    """
    output_dir = Path(output_dir)
    print(f"Searching for PACE data to save in {output_dir}...")

    # CHANGE HERE: Use 'BGC' (Biogeochemical) to get Chlorophyll/Food data
    results = earthaccess.search_data(
        short_name='PACE_OCI_L2_BGC', 
        count=1
    )

    if not results:
        print("No results found! Check your search parameters.")
        return

    # 2. Download the file
    print(f"Found {len(results)} file(s). Downloading...")
    earthaccess.download(results, str(output_dir)) # Added str() just in case
    print("Download complete!")