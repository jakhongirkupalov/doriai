"""Klinik tadqiqotni rejalashtirish yordamchisi.

- Shunga o'xshash tadqiqotlar tarixidan statistika (faza, hajm, davomiylik, yakunlanish darajasi)
- Tanlama hajmi kalkulyatori (ikki nisbatni solishtirish, normal yaqinlashuv)
- LLM yordamida protokol sinopsisi loyihasi (LLM bo'lmasa — shablon)
"""
from __future__ import annotations

import math
from statistics import NormalDist

import pandas as pd

from doriai.llm import client as llm

FAILED = {"TERMINATED", "WITHDRAWN", "SUSPENDED"}


def sample_size_two_proportions(p_control: float, p_treatment: float,
                                alpha: float = 0.05, power: float = 0.80) -> int:
    """Har bir guruh uchun zarur ishtirokchilar soni (ikki tomonlama test)."""
    if not (0 < p_control < 1 and 0 < p_treatment < 1) or p_control == p_treatment:
        raise ValueError("Nisbatlar (0;1) oralig'ida va turlicha bo'lishi kerak")
    z_a = NormalDist().inv_cdf(1 - alpha / 2)
    z_b = NormalDist().inv_cdf(power)
    p_bar = (p_control + p_treatment) / 2
    num = (z_a * math.sqrt(2 * p_bar * (1 - p_bar))
           + z_b * math.sqrt(p_control * (1 - p_control) + p_treatment * (1 - p_treatment))) ** 2
    return math.ceil(num / (p_control - p_treatment) ** 2)


def with_dropout(n_per_group: int, dropout: float = 0.15) -> int:
    return math.ceil(n_per_group / (1 - dropout))


def trial_statistics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    d = df.copy()
    d["start"] = pd.to_datetime(d["start_date"], errors="coerce")
    d["end"] = pd.to_datetime(d["completion_date"], errors="coerce")
    d["duration_months"] = (d["end"] - d["start"]).dt.days / 30.44
    d["enrollment"] = pd.to_numeric(d["enrollment"], errors="coerce")

    finished = d[d["status"].isin(FAILED | {"COMPLETED"})]
    completion_rate = (finished["status"].eq("COMPLETED").mean() if len(finished) else None)

    by_phase = (d[d["phase"] != "NA"].groupby("phase")
                .agg(n=("nct_id", "count"),
                     median_enrollment=("enrollment", "median"),
                     median_duration_months=("duration_months", "median"))
                .round(1).reset_index())

    countries = (d["countries"].str.split("; ").explode().replace("", pd.NA).dropna()
                 .value_counts().head(10))
    return {
        "n_studies": int(len(d)),
        "completion_rate": None if completion_rate is None else round(float(completion_rate), 3),
        "status_counts": d["status"].value_counts().to_dict(),
        "by_phase": by_phase,
        "top_countries": countries,
        "frame": d,
    }


def _protocol_prompt(condition: str, drug: str, phase: str, stats: dict,
                     examples: pd.DataFrame) -> str:
    ex = "\n".join(f"- {r.nct_id} | {r.phase} | n={r.enrollment} | {r.primary_outcomes}"
                   for r in examples.head(8).itertuples())
    return f"""Quyidagi ma'lumotlar asosida klinik tadqiqot PROTOKOL SINOPSISI loyihasini tuzing.

Kasallik: {condition}
Dori / aralashuv: {drug}
Rejalashtirilgan faza: {phase}
O'xshash tadqiqotlar soni: {stats.get('n_studies')}
Yakunlanish darajasi: {stats.get('completion_rate')}
O'xshash tadqiqotlar namunalari (NCT | faza | hajm | asosiy natija):
{ex}

Bo'limlar: 1) Maqsad va gipoteza, 2) Dizayn (randomizatsiya, ko'r-ko'rona, nazorat),
3) Kiritish va chiqarish mezonlari, 4) Asosiy va qo'shimcha natija ko'rsatkichlari,
5) Tanlama hajmi mantig'i, 6) Xavfsizlik monitoringi, 7) Asosiy xavflar va ularni kamaytirish,
8) O'zbekistonda o'tkazish uchun me'yoriy talablar (etika qo'mitasi, GCP). Qisqa va aniq yozing."""


def draft_protocol(condition: str, drug: str, phase: str, stats: dict,
                   examples: pd.DataFrame) -> str:
    text = llm.chat(_protocol_prompt(condition, drug, phase, stats, examples))
    if text:
        return text
    # LLM yo'q — shablon asosidagi zaxira variant
    return f"""### Protokol sinopsisi (shablon)
**Kasallik:** {condition}  |  **Aralashuv:** {drug}  |  **Faza:** {phase}

1. **Maqsad:** {drug} ning {condition} bo'yicha samaradorligi va xavfsizligini baholash.
2. **Dizayn:** randomizatsiyalangan, ikki tomonlama ko'r, platsebo/standart terapiya nazoratli.
3. **Kiritish mezonlari:** tasdiqlangan tashxis, 18–75 yosh, yozma rozilik.
4. **Asosiy natija:** o'xshash tadqiqotlarda eng ko'p ishlatilgan ko'rsatkich (jadvalga qarang).
5. **Tanlama hajmi:** kalkulyator natijasi + 15% chiqib ketish zaxirasi.
6. **Xavfsizlik:** mustaqil ma'lumotlar monitoringi qo'mitasi (DSMB), jiddiy nojo'ya hodisalar hisoboti.
7. **Me'yoriy talablar:** etika qo'mitasi ruxsati, ICH-GCP, milliy vakolatli organ ruxsati.

*O'xshash tadqiqotlar: {stats.get('n_studies')}, yakunlanish darajasi: {stats.get('completion_rate')}.*
"""
