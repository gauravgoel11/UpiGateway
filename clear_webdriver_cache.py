
import os
import shutil

home_dir = os.path.expanduser("~")
wdm_cache_path = os.path.join(home_dir, ".wdm")

if os.path.exists(wdm_cache_path):
    print(f"Deleting webdriver cache at: {wdm_cache_path}")
    try:
        shutil.rmtree(wdm_cache_path)
        print("Cache deleted successfully.")
    except OSError as e:
        print(f"Error deleting cache: {e}")
else:
    print("Webdriver cache directory not found.")
