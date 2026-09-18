"""Molekula bilan ishlashning asosiy funksiyalari.

- SMILES'ni o'qish va standartlashtirish
- Fizik-kimyoviy deskriptorlar (MW, logP, TPSA ...)
- Dori-o'xshashlik qoidalari (Lipinski, Veber), QED, sintez qiyinligi (SA score)
- Strukturaviy ogohlantirishlar (PAINS, Brenk) — "yolg'on-musbat" va toksik fragmentlar
"""
from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass, field
from functools import lru_cache

from rdkit import Chem, RDConfig, RDLogger
from rdkit.Chem import QED, Crippen, Descriptors, rdMolDescriptors
from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
from rdkit.Chem.MolStandardize import rdMolStandardize

RDLogger.DisableLog("rdApp.*")  # noto'g'ri SMILES haqidagi shovqinli loglarni o'chiramiz

# SA score RDKit'ning Contrib papkasida joylashgan (Ertl & Schuffenhauer, 2009)
try:
    sys.path.append(os.path.join(RDConfig.RDContribDir, "SA_Score"))
    import sascorer  # type: ignore
except Exception:  # pragma: no cover - ba'zi o'rnatmalarda Contrib bo'lmaydi
    sascorer = None


# ----------------------------------------------------------------- o'qish
def parse_smiles(smiles: str | None) -> Chem.Mol | None:
    """SMILES qatorini RDKit molekulasiga aylantiradi. Xato bo'lsa None."""
    if not smiles or not isinstance(smiles, str):
        return None
    return Chem.MolFromSmiles(smiles.strip())


def standardize(mol: Chem.Mol) -> Chem.Mol:
    """Tuzlar/erituvchilarni olib tashlaydi, eng katta fragmentni qoldiradi, zaryadni neytrallaydi."""
    try:
        cleaned = rdMolStandardize.Cleanup(mol)
        cleaned = rdMolStandardize.FragmentParent(cleaned)
        cleaned = rdMolStandardize.Uncharger().uncharge(cleaned)
        # Standartlashtirishdan keyin halqa (ring) ma'lumoti yo'qolishi mumkin —
        # fingerprint hisoblashdan oldin uni qayta tiklaymiz.
        Chem.SanitizeMol(cleaned)
        mol = cleaned
    except Exception:
        # Standartlashtirish muvaffaqiyatsiz bo'lsa, asl molekulani ishlatamiz
        try:
            Chem.SanitizeMol(mol)
        except Exception:
            return mol
    return mol


def canonical_smiles(smiles: str) -> str | None:
    mol = parse_smiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(standardize(mol))


def inchikey14(mol: Chem.Mol) -> str | None:
    """InChIKey'ning birinchi 14 belgisi — stereokimyodan qat'i nazar bir xil 'skelet'."""
    try:
        return Chem.MolToInchiKey(mol)[:14]
    except Exception:
        return None


# --------------------------------------------------- strukturaviy ogohlantirish
@lru_cache(maxsize=None)
def _catalog(name: str) -> FilterCatalog:
    params = FilterCatalogParams()
    params.AddCatalog(getattr(FilterCatalogParams.FilterCatalogs, name))
    return FilterCatalog(params)


def structural_alerts(mol: Chem.Mol, catalog: str) -> list[str]:
    """catalog: 'PAINS' yoki 'BRENK'. Topilgan fragment nomlarini qaytaradi."""
    matches = _catalog(catalog).GetMatches(mol)
    return sorted({m.GetDescription() for m in matches})


# ------------------------------------------------------------------ profil
@dataclass
class MolProfile:
    smiles: str
    mw: float
    logp: float
    hbd: int
    hba: int
    tpsa: float
    rot_bonds: int
    rings: int
    qed: float
    sa_score: float | None
    lipinski_violations: int
    veber_ok: bool
    pains: list[str] = field(default_factory=list)
    brenk: list[str] = field(default_factory=list)

    @property
    def lipinski_ok(self) -> bool:
        # Lipinski: 1 tagacha buzilishga ruxsat beriladi
        return self.lipinski_violations <= 1

    def to_dict(self) -> dict:
        d = asdict(self)
        d["lipinski_ok"] = self.lipinski_ok
        return d


def profile_molecule(smiles: str) -> MolProfile | None:
    """Bitta molekula uchun to'liq fizik-kimyoviy va dori-o'xshashlik profili."""
    mol = parse_smiles(smiles)
    if mol is None:
        return None
    mol = standardize(mol)

    mw = Descriptors.MolWt(mol)
    logp = Crippen.MolLogP(mol)
    hbd = rdMolDescriptors.CalcNumHBD(mol)
    hba = rdMolDescriptors.CalcNumHBA(mol)
    tpsa = rdMolDescriptors.CalcTPSA(mol)
    rot = rdMolDescriptors.CalcNumRotatableBonds(mol)

    violations = sum([mw > 500, logp > 5, hbd > 5, hba > 10])
    sa = None
    if sascorer is not None:
        try:
            sa = float(sascorer.calculateScore(mol))
        except Exception:
            sa = None

    return MolProfile(
        smiles=Chem.MolToSmiles(mol),
        mw=round(mw, 2),
        logp=round(logp, 2),
        hbd=hbd,
        hba=hba,
        tpsa=round(tpsa, 2),
        rot_bonds=rot,
        rings=rdMolDescriptors.CalcNumRings(mol),
        qed=round(QED.qed(mol), 3),
        sa_score=None if sa is None else round(sa, 2),
        lipinski_violations=int(violations),
        veber_ok=(rot <= 10 and tpsa <= 140),
        pains=structural_alerts(mol, "PAINS"),
        brenk=structural_alerts(mol, "BRENK"),
    )
