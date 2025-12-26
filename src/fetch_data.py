import earthaccess
from pathlib import Path

def download_sample_data(output_dir):
    """
    Searches for and downloads 1 sample file from the PACE satellite.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Searching for PACE data to save in {output_dir}...")

    # Authenticate with earthaccess
    try:
        earthaccess.login(strategy="environment")
    except Exception as e:
        print(f"Note: Using local credentials or unauthenticated search - {e}")

    # Use 'BGC' (Biogeochemical) to get Chlorophyll/Food data
    try:
        results = earthaccess.search_data(
            short_name='PACE_OCI_L2_BGC', 
            count=1
        )
    except Exception as e:
        print(f"Search failed: {e}")
        return

    if not results:
        print("No results found! Check your search parameters.")
        return

    # Download the file
    print(f"Found {len(results)} file(s). Downloading...")
    try:
        earthaccess.download(results, str(output_dir))
        print("Download complete!")
    except Exception as e:
        print(f"Download failed: {e}")