"""Kimyoviy modullar testlari (RDKit kerak)."""
import pytest

pytest.importorskip("rdkit")

from doriai.chem.featurize import FP_SIZE, featurize_smiles  # noqa: E402
from doriai.chem.molecule import canonical_smiles, profile_molecule  # noqa: E402
from doriai.models.splits import scaffold_split  # noqa: E402
from doriai.screening.scoring import doriai_score  # noqa: E402
from doriai.screening.screener import screen  # noqa: E402

ASPIRIN = "CC(=O)Oc1ccccc1C(=O)O"


def test_profile_aspirin():
    p = profile_molecule(ASPIRIN)
    assert 179 < p.mw < 181
    assert p.lipinski_ok and p.veber_ok
    assert 0 < p.qed <= 1


def test_invalid_smiles():
    assert profile_molecule("not_a_smiles") is None


def test_salt_is_stripped():
    # Natriy tuzi standartlashtirishdan so'ng neytral kislotaga aylanadi
    assert canonical_smiles("CC(=O)Oc1ccccc1C(=O)[O-].[Na+]") == canonical_smiles(ASPIRIN)


def test_featurize_skips_invalid():
    X, valid = featurize_smiles([ASPIRIN, "xxx", "CCO"])
    assert valid == [0, 2] and X.shape[1] > FP_SIZE


def test_score_range():
    score, comps = doriai_score(profile_molecule(ASPIRIN).to_dict(), {})
    assert 0 <= score <= 100 and "drug_likeness" in comps


def test_scaffold_split_disjoint():
    smiles = ["c1ccccc1C", "c1ccccc1CC", "C1CCNCC1C", "C1CCNCC1CC", "CCO", "CCCO"]
    tr, te = scaffold_split(smiles, test_size=0.34)
    assert set(tr).isdisjoint(te) and len(tr) + len(te) == len(smiles)


def test_screen_without_models():
    df = screen([ASPIRIN, "bad"], ["aspirin", "bad"])
    assert df.iloc[0]["name"] == "aspirin" and not df.iloc[1]["valid"]
