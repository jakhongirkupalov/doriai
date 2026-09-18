"""1-qadam: ochiq MoleculeNet datasetlarini data/raw/ ga yuklab olish.

Ishga tushirish:  python scripts/download_datasets.py
"""
import requests

from doriai.config import RAW_DIR
from doriai.models.admet import DATASET_URLS


def main() -> None:
    for fname, url in DATASET_URLS.items():
        dest = RAW_DIR / fname
        if dest.exists():
            print(f"✓ {fname} allaqachon mavjud")
            continue
        print(f"↓ {fname} yuklanmoqda...")
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print(f"  saqlandi: {dest} ({len(r.content) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
