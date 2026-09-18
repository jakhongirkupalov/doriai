"""DoriAI Score — tushuntiriladigan (explainable) yig'ma baho, 0–100.

Bu "qora quti" emas: har bir komponent va uning og'irligi ko'rinib turadi,
shuning uchun kimyogar nima uchun molekula yuqori/past baholanganini tushunadi.
"""
from __future__ import annotations

WEIGHTS = {
    "drug_likeness": 0.30,   # QED
    "safety": 0.35,          # Tox21 + ClinTox bashoratlari
    "synthesizability": 0.15,  # SA score
    "solubility": 0.10,      # ESOL bashorati
    "clean_structure": 0.10,  # PAINS / Brenk ogohlantirishlari yo'qligi
}


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score_components(profile: dict, admet: dict | None = None) -> dict[str, float]:
    """Har bir komponentni 0..1 oralig'ida hisoblaydi. Ma'lumot yo'q bo'lsa — komponent tashlab ketiladi."""
    admet = admet or {}
    comp: dict[str, float] = {"drug_likeness": _clip01(profile["qed"])}

    if profile.get("sa_score") is not None:
        # SA: 1 (oson) ... 10 (juda qiyin)
        comp["synthesizability"] = _clip01(1 - (profile["sa_score"] - 1) / 9)

    tox_parts = [v for v in (admet.get("tox21_mean"), admet.get("clintox")) if v is not None]
    if tox_parts:
        comp["safety"] = _clip01(1 - sum(tox_parts) / len(tox_parts))

    if admet.get("solubility") is not None:
        # logS: -8 (erimaydi) ... 0 (yaxshi eriydi)
        comp["solubility"] = _clip01((admet["solubility"] + 8) / 8)

    if profile.get("pains"):
        comp["clean_structure"] = 0.0
    elif profile.get("brenk"):
        comp["clean_structure"] = 0.5
    else:
        comp["clean_structure"] = 1.0
    return comp


def doriai_score(profile: dict, admet: dict | None = None) -> tuple[float, dict[str, float]]:
    comp = score_components(profile, admet)
    total_w = sum(WEIGHTS[k] for k in comp)
    score = sum(WEIGHTS[k] * v for k, v in comp.items()) / total_w

    # Lipinski qoidasi jiddiy buzilsa — jarima
    if profile.get("lipinski_violations", 0) >= 2:
        score *= 0.8
    # Strukturaviy ogohlantirish — qat'iy jarima: PAINS skriningda yolg'on-musbat
    # beradi, Brenk esa toksik/reaktiv fragment (masalan, nitro-guruh) demakdir.
    if profile.get("pains"):
        score *= 0.5
    elif profile.get("brenk"):
        score *= 0.85
    # Juda kichik molekulalar "fragment" bo'lib, dori nomzodi hisoblanmaydi
    if profile.get("mw", 500) < 150:
        score *= 0.75
    return round(100 * score, 1), {k: round(v, 3) for k, v in comp.items()}


def verdict(score: float) -> str:
    if score >= 70:
        return "Istiqbolli nomzod"
    if score >= 50:
        return "Optimallashtirish kerak"
    return "Xavfli / past ustuvorlik"
