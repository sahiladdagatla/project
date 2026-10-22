import os
import urllib.request
import json

BASE_URL = "https://storage.googleapis.com/sen1floods11/v1.1"
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "satellite")
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Download metadata GeoJSON
meta_url = f"{BASE_URL}/Sen1Floods11_Metadata.geojson"
meta_dest = os.path.join(DATA_DIR, "Sen1Floods11_Metadata.geojson")
if not os.path.exists(meta_dest):
    print("Downloading Sen1Floods11 metadata...")
    urllib.request.urlretrieve(meta_url, meta_dest)
    print(f"Metadata saved to {meta_dest} ({os.path.getsize(meta_dest)} bytes)")

# 2. Download split CSVs
splits_dir = os.path.join(DATA_DIR, "splits")
os.makedirs(splits_dir, exist_ok=True)
for split in ["train", "valid", "test"]:
    csv_url = f"{BASE_URL}/splits/flood_handlabeled/flood_{split}_data.csv"
    csv_dest = os.path.join(splits_dir, f"flood_{split}_data.csv")
    if not os.path.exists(csv_dest):
        print(f"Downloading {split} split...")
        urllib.request.urlretrieve(csv_url, csv_dest)
        print(f"{split} split saved ({os.path.getsize(csv_dest)} bytes)")

# 3. Download sample test chips for verification
chips_dir = os.path.join(DATA_DIR, "chips")
os.makedirs(chips_dir, exist_ok=True)

sample_chips = [
    "Ghana_313799",
    "Ghana_1078550",
    "Ghana_359826",
    "Ghana_319168"
]

for chip_id in sample_chips:
    # S1 SAR
    s1_url = f"{BASE_URL}/data/flood_events/HandLabeled/S1Hand/{chip_id}_S1Hand.tif"
    s1_dest = os.path.join(chips_dir, f"{chip_id}_S1Hand.tif")
    if not os.path.exists(s1_dest):
        print(f"Downloading SAR chip {chip_id}_S1Hand.tif...")
        try:
            urllib.request.urlretrieve(s1_url, s1_dest)
            print(f"Downloaded {chip_id}_S1Hand.tif ({os.path.getsize(s1_dest)} bytes)")
        except Exception as e:
            print(f"Error downloading {s1_url}: {e}")

    # Label
    label_url = f"{BASE_URL}/data/flood_events/HandLabeled/LabelHand/{chip_id}_LabelHand.tif"
    label_dest = os.path.join(chips_dir, f"{chip_id}_LabelHand.tif")
    if not os.path.exists(label_dest):
        print(f"Downloading Label chip {chip_id}_LabelHand.tif...")
        try:
            urllib.request.urlretrieve(label_url, label_dest)
            print(f"Downloaded {chip_id}_LabelHand.tif ({os.path.getsize(label_dest)} bytes)")
        except Exception as e:
            print(f"Error downloading {label_url}: {e}")

print("Satellite data preparation completed.")
