"""Virtual skrining: ko'plab molekulalarni bir vaqtda baholab, reyting tuzish."""
from __future__ import annotations

import pandas as pd

from doriai.chem.molecule import profile_molecule
from doriai.models.admet import ADMETPredictor
from doriai.screening.scoring import doriai_score, verdict


def screen(smiles: list[str], names: list[str] | None = None,
           predictor: ADMETPredictor | None = None) -> pd.DataFrame:
    names = names or [f"mol_{i + 1}" for i in range(len(smiles))]
    preds = predictor.predict(smiles) if predictor and predictor.available else None

    rows = []
    for i, (smi, name) in enumerate(zip(smiles, names)):
        prof = profile_molecule(smi)
        if prof is None:
            rows.append({"name": name, "smiles": smi, "valid": False})
            continue
        p = prof.to_dict()
        admet = predictor.summarize(preds.iloc[i]) if preds is not None else {}
        score, comps = doriai_score(p, admet)
        rows.append({
            "name": name,
            "smiles": p["smiles"],
            "valid": True,
            "doriai_score": score,
            "verdict": verdict(score),
            "qed": p["qed"],
            "mw": p["mw"],
            "logp": p["logp"],
            "tpsa": p["tpsa"],
            "sa_score": p["sa_score"],
            "lipinski_ok": p["lipinski_ok"],
            "pains": len(p["pains"]),
            "brenk": len(p["brenk"]),
            "tox21_mean": admet.get("tox21_mean"),
            "clintox": admet.get("clintox"),
            "logS": admet.get("solubility"),
            "bbbp": admet.get("bbbp"),
            **{f"c_{k}": v for k, v in comps.items()},
        })

    df = pd.DataFrame(rows)
    if "doriai_score" in df:
        df = df.sort_values("doriai_score", ascending=False, na_position="last")
    return df.reset_index(drop=True)
