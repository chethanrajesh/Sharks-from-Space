import os
from pathlib import Path
from getpass import getpass

def setup_earthdata_login():
    """
    Prompts user for NASA credentials if not found in env or netrc.
    """
    # Check if already set in environment
    if os.environ.get("EARTHDATA_USERNAME") and os.environ.get("EARTHDATA_PASSWORD"):
        print("✅ Credentials found in environment variables.")
        return

    # Check for .netrc
    netrc_path = Path.home() / "_netrc"
    if netrc_path.exists():
        print("✅ Found _netrc file.")
        return

    # If neither, ask user
    print("⚠️ No credentials found. Please enter them now (session only).")
    os.environ["EARTHDATA_USERNAME"] = input("NASA Username: ")
    os.environ["EARTHDATA_PASSWORD"] = getpass("NASA Password: ")
    print("✅ Credentials set for this session.")
