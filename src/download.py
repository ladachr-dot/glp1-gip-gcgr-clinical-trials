import json
import time
from pathlib import Path

import requests

URL = "https://clinicaltrials.gov/api/v2/studies"
RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)

DRUGS = [
    "semaglutide", "tirzepatide", "retatrutide", "survodutide",
    "mazdutide", "orforglipron",
]


def download(drug, page_size=1000):
    studies = []
    params = {"query.intr": drug, "pageSize": page_size, "format": "json"}
    while True:
        r = requests.get(URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        studies.extend(data.get("studies", []))
        token = data.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
        time.sleep(0.5)
    return studies


if __name__ == "__main__":
    for drug in DRUGS:
        studies = download(drug)
        with open(RAW_DIR / f"{drug}.json", "w", encoding="utf-8") as f:
            json.dump(studies, f)
        print(drug, len(studies))