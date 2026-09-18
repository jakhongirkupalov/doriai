"""Nishonga asoslangan drug repurposing (target-based).

1) ChEMBL'dan tanlangan oqsil-nishonga (masalan EGFR) qarshi o'lchangan faolliklar olinadi
2) Molekula -> pChEMBL (faollik kuchi) regressiya modeli o'qitiladi
3) Model BARCHA tasdiqlangan dorilarga qo'llanadi -> faolligi yuqori bashorat qilinganlar reytingi
4) Qo'llanish sohasi (applicability domain): dori o'quv to'plamiga qanchalik o'xshash —
   past o'xshashlikdagi bashoratlarga ishonch kamroq.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict

from doriai.chem.featurize import featurize_mol, morgan_bitvect, tanimoto_to_many
from doriai.chem.molecule import inchikey14, parse_smiles, standardize
from doriai.config import RANDOM_STATE
from doriai.repurposing.library import DrugLibrary


@dataclass
class TargetModel:
    target_id: str
    model: RandomForestRegressor
    train_fps: list
    train_ik14: set
    cv_r2: float
    cv_rmse: float
    n_train: int


def build_target_model(activities: pd.DataFrame, target_id: str) -> TargetModel:
    X, y, fps, iks = [], [], [], set()
    for smi, p in zip(activities["smiles"], activities["pchembl"]):
        m = parse_smiles(smi)
        if m is None:
            continue
        m = standardize(m)
        X.append(featurize_mol(m))
        y.append(p)
        fps.append(morgan_bitvect(m))
        iks.add(inchikey14(m))
    if len(y) < 30:
        raise ValueError(f"Model uchun ma'lumot kam: {len(y)} ta molekula (kamida 30 kerak)")
    X, y = np.vstack(X), np.array(y)

    model = RandomForestRegressor(n_estimators=300, min_samples_leaf=2, n_jobs=-1,
                                  random_state=RANDOM_STATE)
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    y_cv = cross_val_predict(model, X, y, cv=cv)
    model.fit(X, y)
    return TargetModel(target_id, model, fps, iks,
                       cv_r2=float(r2_score(y, y_cv)),
                       cv_rmse=float(np.sqrt(mean_squared_error(y, y_cv))),
                       n_train=len(y))


def rank_library(tm: TargetModel, lib: DrugLibrary, top_k: int = 25) -> pd.DataFrame:
    X = np.vstack([featurize_mol(m) for m in lib.mols])
    pred = tm.model.predict(X)
    # Qo'llanish sohasi: har bir dori uchun o'quv to'plamidagi eng yaqin qo'shniga o'xshashlik
    ad = np.array([tanimoto_to_many(fp, tm.train_fps).max() for fp in lib.fps])
    out = lib.df.copy()
    out["pred_pchembl"] = pred.round(2)
    out["pred_IC50_nM"] = (10 ** (9 - pred)).round(1)
    out["nearest_train_sim"] = ad.round(2)
    out["confidence"] = pd.cut(ad, [-0.01, 0.3, 0.5, 1.01], labels=["past", "o'rta", "yuqori"])
    out["known_active"] = out["ik14"].isin(tm.train_ik14)
        # Bir molekulaning tuz shakllarini birlashtiramiz — qisqa nomli yozuv qoladi
    out["_len"] = out["name"].str.len()
    out = (out.sort_values(["pred_pchembl", "_len"], ascending=[False, True])
              .drop_duplicates(subset="ik14"))
    return out.drop(columns=["ik14", "_len"]).head(top_k).reset_index(drop=True)
