"""ADMET (Absorbsiya, Distribusiya, Metabolizm, Ekskretsiya, Toksiklik) modellari.

Ochiq MoleculeNet datasetlarida Random Forest modellari o'qitiladi:
  * ESOL     — suvda eruvchanlik (regressiya, logS)
  * BBBP     — gematoensefalik to'siqdan o'tish (klassifikatsiya)
  * ClinTox  — klinik sinovlarda toksiklik tufayli muvaffaqiyatsizlik (klassifikatsiya)
  * Tox21    — 12 ta toksiklik yo'lagi (nuklear retseptorlar, stress javobi)
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)

from doriai.chem.featurize import featurize_smiles
from doriai.config import ADMET_DIR, RANDOM_STATE, RAW_DIR
from doriai.models.splits import scaffold_split

MOLNET = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets"
DATASET_URLS = {
    "delaney-processed.csv": f"{MOLNET}/delaney-processed.csv",
    "BBBP.csv": f"{MOLNET}/BBBP.csv",
    "clintox.csv.gz": f"{MOLNET}/clintox.csv.gz",
    "tox21.csv.gz": f"{MOLNET}/tox21.csv.gz",
}


@dataclass(frozen=True)
class TaskSpec:
    name: str
    file: str
    smiles_col: str
    target: str
    kind: str          # "classification" | "regression"
    label: str         # interfeysdagi o'zbekcha nomi
    group: str         # "toxicity" | "pk" (farmakokinetika)


TOX21_TARGETS = [
    "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD",
    "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53",
]

TASKS: dict[str, TaskSpec] = {
    "solubility": TaskSpec("solubility", "delaney-processed.csv", "smiles",
                           "measured log solubility in mols per litre", "regression",
                           "Suvda eruvchanlik (logS)", "pk"),
    "bbbp": TaskSpec("bbbp", "BBBP.csv", "smiles", "p_np", "classification",
                     "Gematoensefalik to'siqdan o'tish ehtimoli", "pk"),
    "clintox": TaskSpec("clintox", "clintox.csv.gz", "smiles", "CT_TOX", "classification",
                        "Klinik toksiklik xavfi", "toxicity"),
}
for _t in TOX21_TARGETS:
    _key = "tox21_" + _t.lower().replace("-", "_")
    TASKS[_key] = TaskSpec(_key, "tox21.csv.gz", "smiles", _t, "classification",
                           f"Tox21 {_t} faolligi", "toxicity")


# ----------------------------------------------------------------- o'qitish
def _make_model(kind: str):
    if kind == "classification":
        return RandomForestClassifier(
            n_estimators=200, min_samples_leaf=2, class_weight="balanced_subsample",
            n_jobs=-1, random_state=RANDOM_STATE,
        )
    return RandomForestRegressor(
        n_estimators=200, min_samples_leaf=2, n_jobs=-1, random_state=RANDOM_STATE,
    )


def load_task_data(spec: TaskSpec, raw_dir: Path = RAW_DIR) -> tuple[np.ndarray, np.ndarray, list[str]]:
    path = raw_dir / spec.file
    if not path.exists():
        raise FileNotFoundError(f"{path} topilmadi. Avval: python scripts/download_datasets.py")
    df = pd.read_csv(path)[[spec.smiles_col, spec.target]].dropna()
    smiles = df[spec.smiles_col].astype(str).tolist()
    X, valid = featurize_smiles(smiles)
    y = df[spec.target].to_numpy()[valid]
    if spec.kind == "classification":
        y = y.astype(int)
    return X, y, [smiles[i] for i in valid]


def _evaluate(spec: TaskSpec, model, X_test, y_test) -> dict:
    if spec.kind == "classification":
        proba = model.predict_proba(X_test)[:, 1]
        metrics = {"accuracy": float(accuracy_score(y_test, proba >= 0.5))}
        if len(np.unique(y_test)) > 1:
            metrics["roc_auc"] = float(roc_auc_score(y_test, proba))
        return metrics
    pred = model.predict(X_test)
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "mae": float(mean_absolute_error(y_test, pred)),
        "r2": float(r2_score(y_test, pred)),
    }


def train_task(spec: TaskSpec, out_dir: Path = ADMET_DIR) -> dict:
    """Scaffold split bilan baholaydi, so'ng to'liq ma'lumotda qayta o'qitib saqlaydi."""
    X, y, smiles = load_task_data(spec)
    train_idx, test_idx = scaffold_split(smiles, test_size=0.2)

    model = _make_model(spec.kind).fit(X[train_idx], y[train_idx])
    metrics = _evaluate(spec, model, X[test_idx], y[test_idx])
    metrics.update(n_total=int(len(y)), n_train=len(train_idx), n_test=len(test_idx),
                   split="scaffold")

    final_model = _make_model(spec.kind).fit(X, y)
    joblib.dump({"model": final_model, "spec": asdict(spec), "metrics": metrics},
                out_dir / f"{spec.name}.joblib", compress=3)
    return metrics


def save_metrics(all_metrics: dict, out_dir: Path = ADMET_DIR) -> None:
    (out_dir / "metrics.json").write_text(json.dumps(all_metrics, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------- bashorat
class ADMETPredictor:
    """models/admet/ ichidagi barcha o'qitilgan modellarni yuklaydi va bashorat qiladi."""

    def __init__(self, model_dir: Path = ADMET_DIR):
        self.bundles: dict[str, dict] = {}
        for p in sorted(model_dir.glob("*.joblib")):
            self.bundles[p.stem] = joblib.load(p)

    @property
    def available(self) -> list[str]:
        return list(self.bundles)

    def spec(self, name: str) -> TaskSpec:
        return TaskSpec(**self.bundles[name]["spec"])

    def metrics(self) -> dict:
        return {k: b["metrics"] for k, b in self.bundles.items()}

    def predict(self, smiles: list[str]) -> pd.DataFrame:
        """Har bir vazifa uchun ustun: klassifikatsiyada 1-sinf ehtimoli, regressiyada qiymat."""
        out = pd.DataFrame(index=range(len(smiles)))
        if not self.bundles:
            return out
        X, valid = featurize_smiles(smiles)
        for name, b in self.bundles.items():
            col = np.full(len(smiles), np.nan)
            if len(valid):
                model = b["model"]
                if b["spec"]["kind"] == "classification":
                    col[valid] = model.predict_proba(X)[:, 1]
                else:
                    col[valid] = model.predict(X)
            out[name] = col
        return out

    def summarize(self, row: pd.Series) -> dict:
        """Bitta molekula bashoratlaridan yig'ma ko'rsatkichlar."""
        tox_cols = [c for c in row.index if c.startswith("tox21_") and pd.notna(row[c])]
        return {
            "tox21_mean": float(row[tox_cols].mean()) if tox_cols else None,
            "tox21_max": float(row[tox_cols].max()) if tox_cols else None,
            "clintox": _get(row, "clintox"),
            "bbbp": _get(row, "bbbp"),
            "solubility": _get(row, "solubility"),
        }


def _get(row: pd.Series, key: str):
    return float(row[key]) if key in row.index and pd.notna(row[key]) else None
