"""3-qadam: ChEMBL'dan tasdiqlangan dorilar kutubxonasini yuklab olish.

Natija: data/processed/approved_drugs.csv  (drug repurposing uchun)
Ishga tushirish:  python scripts/fetch_approved_drugs.py
"""
from doriai.data_sources.chembl import fetch_approved_drugs
from doriai.repurposing.library import FULL_LIBRARY


def main() -> None:
    print("ChEMBL'dan tasdiqlangan dorilar olinmoqda (1–3 daqiqa)...")
    df = fetch_approved_drugs(max_records=5000)
    df = df.drop_duplicates(subset="smiles")
    df.to_csv(FULL_LIBRARY, index=False)
    print(f"✓ {len(df)} ta dori saqlandi: {FULL_LIBRARY}")


if __name__ == "__main__":
    main()
