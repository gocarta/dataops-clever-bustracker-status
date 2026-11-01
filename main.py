# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "datablob",
#     "playwright",
#     "simple-env",
# ]
# ///
import datablob
from datetime import datetime
from playwright.sync_api import sync_playwright
import simple_env as se
import subprocess
import time

AWS_BUCKET_NAME = se.get("AWS_BUCKET_NAME")
AWS_BUCKET_PATH = se.get("AWS_BUCKET_PATH")

current_status = None
current_time = None

with sync_playwright() as p:
    try:
        browser = p.chromium.launch(headless=True)
        print("[dataops-clever-bustracker-uptime] launched browser")
    except Exception as e:
        print(e)
        subprocess.run(["playwright", "install"], check=True)
        browser = p.chromium.launch(headless=True)
        print("[dataops-clever-bustracker-uptime] launched browser")

    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    current_time = int(time.time())
    page.goto("https://bustracker.gocarta.org")
    # title starts as 'Loading...' before page finishes loading
    page.wait_for_load_state("networkidle")
    current_status = int(page.title() == "CARTA")
    browser.close()


client = datablob.DataBlobClient(
    bucket_name=AWS_BUCKET_NAME, bucket_path=AWS_BUCKET_PATH
)

# fetch existing dataset
# rows = []
rows = client.get_dataset_as_json(name="clever_bustracker_status", version="1")

row = {
    "time": current_time,
    "status": current_status
}
print("[dataops-clever-bustracker-status] row:", row)
rows.append(row)

column_names = [
    "time",
    "status"
]

client.update_dataset(
    name="clever_bustracker_status",
    version="1",
    data=rows,
    column_names=column_names,
    description="History of uptime status of https://bustracker.gocarta.org, the Clever Devices' Bus Tracker for CARTA"
)
print(f"[dataops-clever-bustracker-status] updated {len(rows)} rows")
