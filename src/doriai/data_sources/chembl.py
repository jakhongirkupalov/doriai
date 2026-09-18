"""ChEMBL (EMBL-EBI) — bioaktivlik ma'lumotlarining eng yirik ochiq bazasi.

Litsenziya: CC BY-SA 3.0. Hujjat: https://www.ebi.ac.uk/chembl/api/data/docs
"""
from __future__ import annotations

import pandas as pd

from doriai.data_sources.http import get

BASE = "https://www.ebi.ac.uk"
API = f"{BASE}/chembl/api/data"


def _paginate(first_url: str, params: dict, key: str, max_records: int) -> list[dict]:
    items, url, p = [], first_url, dict(params)
    while url and len(items) < max_records:
        data = get(url, params=p)
        items.extend(data.get(key, []))
        nxt = data.get("page_meta", {}).get("next")
        url, p = (BASE + nxt, None) if nxt else (None, None)
    return items[:max_records]


def search_targets(query: str, limit: int = 20) -> pd.DataFrame:
    """Masalan: 'EGFR', 'acetylcholinesterase', 'COX-2'."""
    data = get(f"{API}/target/search.json", params={"q": query, "limit": limit})
    rows = [{
        "target_chembl_id": t.get("target_chembl_id"),
        "pref_name": t.get("pref_name"),
        "organism": t.get("organism"),
        "target_type": t.get("target_type"),
    } for t in data.get("targets", [])]
    return pd.DataFrame(rows)


def fetch_activities(target_id: str, max_records: int = 3000) -> pd.DataFrame:
    """Nishonga qarshi o'lchangan faolliklar (pChEMBL = -log10(IC50/Ki/EC50, M))."""
    items = _paginate(
        f"{API}/activity.json",
        {"target_chembl_id": target_id, "pchembl_value__isnull": "false",
         "standard_relation": "=", "limit": 1000},
        "activities", max_records,
    )
    df = pd.DataFrame([{
        "molecule_chembl_id": a.get("molecule_chembl_id"),
        "smiles": a.get("canonical_smiles"),
        "pchembl": a.get("pchembl_value"),
        "type": a.get("standard_type"),
    } for a in items])
    if df.empty:
        return df
    df["pchembl"] = pd.to_numeric(df["pchembl"], errors="coerce")
    df = df.dropna(subset=["smiles", "pchembl"])
    # Bir molekula uchun bir nechta o'lchov bo'lsa — mediana
    return (df.groupby(["molecule_chembl_id", "smiles"], as_index=False)["pchembl"].median())


def fetch_approved_drugs(max_records: int = 5000) -> pd.DataFrame:
    """Tasdiqlangan (max_phase=4) kichik molekulali dorilar."""
    items = _paginate(
        f"{API}/molecule.json",
        {"max_phase": 4, "molecule_type": "Small molecule", "limit": 1000},
        "molecules", max_records,
    )
    rows = []
    for m in items:
        struct = m.get("molecule_structures") or {}
        smi = struct.get("canonical_smiles")
        if smi:
            rows.append({
                "chembl_id": m.get("molecule_chembl_id"),
                "name": (m.get("pref_name") or m.get("molecule_chembl_id")).title(),
                "smiles": smi,
                "first_approval": m.get("first_approval"),
            })
    return pd.DataFrame(rows)


def fetch_indications(chembl_id: str, limit: int = 20) -> list[str]:
    """Dori qaysi kasalliklarga qo'llanilishi (MeSH sarlavhalari)."""
    data = get(f"{API}/drug_indication.json",
               params={"molecule_chembl_id": chembl_id, "limit": limit})
    return sorted({d.get("mesh_heading") for d in data.get("drug_indications", [])
                   if d.get("mesh_heading")})
