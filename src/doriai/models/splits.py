"""Scaffold split — dori kashfiyotida modelni halol baholash usuli.

Oddiy tasodifiy bo'lishda test to'plamida o'quv to'plamidagi molekulalarning
"qarindoshlari" (bir xil skeletli) bo'ladi va model yaxshiroq ko'rinadi.
Scaffold split'da bir xil Murcko skeletiga ega molekulalar faqat bitta
to'plamga tushadi — bu model YANGI kimyoviy sinflarda qanday ishlashini ko'rsatadi.
"""
from __future__ import annotations

from collections import defaultdict

from rdkit.Chem.Scaffolds import MurckoScaffold

from doriai.chem.molecule import parse_smiles


def murcko_scaffold(smiles: str) -> str:
    mol = parse_smiles(smiles)
    if mol is None:
        return ""
    try:
        return MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=False)
    except Exception:
        return ""


def scaffold_split(smiles: list[str], test_size: float = 0.2) -> tuple[list[int], list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(smiles):
        groups[murcko_scaffold(s)].append(i)

    # Katta skelet guruhlari -> train, kichik/noyob skeletlar -> test (DeepChem uslubi)
    ordered = sorted(groups.values(), key=len, reverse=True)
    n_test_target = int(round(test_size * len(smiles)))
    train, test = [], []
    # Eng katta skelet guruhlaridan boshlab to'ldiramiz: shunda test to'plamiga ham
    # yirik, xilma-xil guruhlar tushadi va u bitta sinfdan iborat bo'lib qolmaydi.
    for g in ordered:
        if len(test) + len(g) <= n_test_target:
            test.extend(g)
        else:
            train.extend(g)
    return train, test
