"""Tasdiqlangan dorilar kutubxonasi va o'xshashlik bo'yicha qidiruv.

G'oya ("o'xshash xossa printsipi"): strukturasi o'xshash molekulalar ko'pincha
o'xshash biologik faollikka ega. Agar yangi faol birikma mavjud doriga o'xshasa —
o'sha dori yangi kasallik uchun qayta qo'llanish nomzodi bo'lishi mumkin.
"""
from __future__ import annotations

import pandas as pd

from doriai.chem.featurize import morgan_bitvect, tanimoto_to_many
from doriai.chem.molecule import inchikey14, parse_smiles, standardize
from doriai.config import PROCESSED_DIR, SEED_DIR

FULL_LIBRARY = PROCESSED_DIR / "approved_drugs.csv"   # scripts/fetch_approved_drugs.py
SEED_LIBRARY = SEED_DIR / "approved_drugs_seed.csv"   # repodagi kichik zaxira


class DrugLibrary:
    def __init__(self, df: pd.DataFrame):
        mols, keep = [], []
        for i, s in enumerate(df["smiles"]):
            m = parse_smiles(s)
            if m is not None:
                mols.append(standardize(m))
                keep.append(i)
        self.df = df.iloc[keep].reset_index(drop=True).copy()
        self.mols = mols
        self.fps = [morgan_bitvect(m) for m in mols]
        self.df["ik14"] = [inchikey14(m) for m in mols]
        self.source = "custom"

    @classmethod
    def load(cls) -> "DrugLibrary":
        path = FULL_LIBRARY if FULL_LIBRARY.exists() else SEED_LIBRARY
        lib = cls(pd.read_csv(path))
        lib.source = path.name
        return lib

    def __len__(self) -> int:
        return len(self.df)

    def similar_to(self, smiles: str, top_k: int = 10) -> pd.DataFrame:
        mol = parse_smiles(smiles)
        if mol is None:
            raise ValueError("SMILES noto'g'ri")
        sims = tanimoto_to_many(morgan_bitvect(standardize(mol)), self.fps)
        out = self.df.assign(similarity=sims.round(3))
        return out.sort_values("similarity", ascending=False).head(top_k).drop(columns=["ik14"])
