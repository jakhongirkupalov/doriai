"""Molekulani ML model tushunadigan son vektoriga aylantirish (featurization).

Morgan fingerprint (ECFP4 analogi): molekuladagi har bir atom atrofidagi
2 bog' radiusdagi fragmentlarni 2048 bitli vektorga "xeshlaydi".
Unga bir nechta global deskriptorlar qo'shiladi.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
from rdkit import DataStructs
from rdkit.Chem import Crippen, Descriptors, rdFingerprintGenerator, rdMolDescriptors

from doriai.chem.molecule import parse_smiles, standardize

FP_SIZE = 2048
_MORGAN = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=FP_SIZE)

_DESCRIPTORS = [
    Descriptors.MolWt,
    Crippen.MolLogP,
    rdMolDescriptors.CalcTPSA,
    rdMolDescriptors.CalcNumHBD,
    rdMolDescriptors.CalcNumHBA,
    rdMolDescriptors.CalcNumRotatableBonds,
    rdMolDescriptors.CalcNumAromaticRings,
    rdMolDescriptors.CalcFractionCSP3,
    Descriptors.HeavyAtomCount,
]


def morgan_bitvect(mol):
    """O'xshashlik (Tanimoto) hisoblash uchun RDKit bit-vektori."""
    return _MORGAN.GetFingerprint(mol)


def featurize_mol(mol) -> np.ndarray:
    fp = _MORGAN.GetFingerprintAsNumPy(mol).astype(np.float32)
    desc = np.array([f(mol) for f in _DESCRIPTORS], dtype=np.float32)
    return np.concatenate([fp, desc])


def featurize_smiles(smiles: Iterable[str]) -> tuple[np.ndarray, list[int]]:
    """SMILES ro'yxatidan X matritsa. Qaytaradi: (X, yaroqli_indekslar)."""
    rows, valid = [], []
    for i, s in enumerate(smiles):
        mol = parse_smiles(s)
        if mol is None:
            continue
        rows.append(featurize_mol(standardize(mol)))
        valid.append(i)
    n_feat = FP_SIZE + len(_DESCRIPTORS)
    X = np.vstack(rows) if rows else np.empty((0, n_feat), dtype=np.float32)
    return X, valid


def tanimoto_to_many(query_fp, fps: list) -> np.ndarray:
    return np.array(DataStructs.BulkTanimotoSimilarity(query_fp, fps))
