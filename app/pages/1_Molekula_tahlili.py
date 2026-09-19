"""Molekula tahlili — bitta birikmani laboratoriyadan oldin baholash.

Sahifa uch qismdan iborat:
  1. Xulosa        — rasm, DoriAI Score va asosiy xavflar (qaror uchun yetarli)
  2. Nega shunday  — ball qaysi mezonlardan tashkil topgani va ogohlantirishlar
  3. Batafsil      — kimyoviy xossalar va 15 ta modelning to'liq bashoratlari (yig'iladigan)
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from doriai.chem.molecule import profile_molecule
from doriai.screening.scoring import WEIGHTS, doriai_score, verdict
from doriai.ui import DISCLAIMER, get_predictor, mol_image, page_setup, score_gauge, smiles_input

ACCENT = "#C94FE0"  # Firuza temada: "#2EC4B6"

CRITERIA = {
    "safety": ("Xavfsizlik", "toksiklik modellari bashorati"),
    "drug_likeness": ("Dori-o'xshashlik", "mavjud dorilarga o'xshashlik (QED)"),
    "synthesizability": ("Sintez qulayligi", "laboratoriyada yasash osonligi"),
    "solubility": ("Suvda eruvchanlik", "organizmga so'rilish uchun muhim"),
    "clean_structure": ("Toza struktura", "PAINS/Brenk fragmentlari yo'qligi"),
}

TOX21 = {
    "tox21_nr_ar": ("Gormon tizimi", "Androgen retseptori"),
    "tox21_nr_ar_lbd": ("Gormon tizimi", "Androgen retseptori (bog'lanish qismi)"),
    "tox21_nr_ahr": ("Gormon tizimi", "Aril-uglevodorod retseptori"),
    "tox21_nr_aromatase": ("Gormon tizimi", "Aromataza fermenti"),
    "tox21_nr_er": ("Gormon tizimi", "Estrogen retseptori"),
    "tox21_nr_er_lbd": ("Gormon tizimi", "Estrogen retseptori (bog'lanish qismi)"),
    "tox21_nr_ppar_gamma": ("Gormon tizimi", "PPAR-gamma retseptori"),
    "tox21_sr_are": ("Hujayra stressi", "Oksidlovchi stress"),
    "tox21_sr_atad5": ("Hujayra stressi", "DNK shikastlanishi (ATAD5)"),
    "tox21_sr_hse": ("Hujayra stressi", "Issiqlik stressi"),
    "tox21_sr_mmp": ("Hujayra stressi", "Mitoxondriya shikastlanishi"),
    "tox21_sr_p53": ("Hujayra stressi", "DNK shikastlanishi (p53)"),
}


def level(value: float, low: float, high: float) -> str:
    """0..1 xavf qiymatini so'zga aylantiradi."""
    return "past" if value < low else "o'rta" if value < high else "yuqori"


def solubility_text(logS: float) -> str:
    if logS >= -2:
        return "yaxshi eriydi"
    if logS >= -4:
        return "o'rtacha eriydi"
    return "yomon eriydi"


# ======================================================================= kirish
page_setup("Molekula tahlili", "🔬")
st.caption("Birikmani sintez qilishdan oldin tekshiring: u dori sifatida ishlay oladimi, toksik emasmi, "
           "sintezi qanchalik qiyin. Skriningda yuqori chiqqan nomzodni batafsil o'rganish uchun ham ishlatiladi.")

smiles = smiles_input("mol")
if not smiles:
    st.stop()

prof = profile_molecule(smiles)
if prof is None:
    st.error("SMILES noto'g'ri — molekulani o'qib bo'lmadi. Yozuvni tekshiring yoki PubChem'dan nusxalang.")
    st.stop()

pred = get_predictor()
preds = pred.predict([smiles]) if pred.available else pd.DataFrame()
admet = pred.summarize(preds.iloc[0]) if not preds.empty else {}
p = prof.to_dict()
score, comps = doriai_score(p, admet)

# Umumiy toksiklik xavfi — DoriAI Score'dagi "Xavfsizlik" mezoni bilan bir xil manba
tox_parts = [v for v in (admet.get("tox21_mean"), admet.get("clintox")) if v is not None]
tox_risk = sum(tox_parts) / len(tox_parts) if tox_parts else None

# ================================================================ 1. Xulosa
st.subheader("Xulosa")
left, mid, right = st.columns([1.1, 1, 1.1])

left.image(mol_image(smiles))

with mid:
    st.plotly_chart(score_gauge(score), use_container_width=True)
    box = st.success if score >= 70 else st.warning if score >= 50 else st.error
    box(f"**{verdict(score)}**")

with right:
    st.markdown("**Asosiy ko'rsatkichlar**")
    if tox_risk is not None:
        st.markdown(f"🧪 Toksiklik xavfi: **{level(tox_risk, 0.3, 0.5)}** ({tox_risk:.2f})")
    st.markdown(f"💊 Tabletka sifatida (Lipinski): **{'mos' if prof.lipinski_ok else 'mos emas'}**")
    if admet.get("solubility") is not None:
        st.markdown(f"💧 Suvda: **{solubility_text(admet['solubility'])}**")
    if p["sa_score"] is not None:
        sa_word = "oson" if p["sa_score"] < 4 else "o'rtacha" if p["sa_score"] < 6 else "qiyin"
        st.markdown(f"⚗️ Sintez: **{sa_word}**")
    if p["pains"]:
        st.markdown("⛔ **PAINS:** laboratoriya testlarida yolg'on natija berishi mumkin")
    elif p["brenk"]:
        st.markdown("⚠️ **Brenk:** toksik yoki beqaror fragment bor")
    else:
        st.markdown("✅ Xavfli fragmentlar topilmadi")

# ======================================================= 2. Nega shunday baho
st.divider()
st.subheader("Nega shunday baho")
st.caption("Ball besh mezondan tashkil topadi. Har bir mezon 0–100 baholanadi; "
           "qavs ichida — uning umumiy balldagi ulushi.")

comp_df = pd.DataFrame([
    {"Mezon": f"{CRITERIA[k][0]} ({int(WEIGHTS[k] * 100)}%)", "Baho": round(v * 100),
     "Izoh": CRITERIA[k][1]}
    for k, v in sorted(comps.items(), key=lambda kv: -WEIGHTS[kv[0]])
])
fig = px.bar(comp_df, x="Baho", y="Mezon", orientation="h", text="Baho",
             hover_data={"Izoh": True, "Mezon": False}, range_x=[0, 110], height=260)
fig.update_traces(marker_color=ACCENT, textposition="outside")
fig.update_layout(xaxis_title=None, yaxis_title=None, yaxis={"autorange": "reversed"},
                  margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

if p["pains"]:
    st.error("**PAINS ogohlantirishi** — molekulada laboratoriya testlarini \"aldaydigan\" fragment bor: "
             + ", ".join(p["pains"]) + ". Testdagi faollik haqiqiy bo'lmasligi mumkin.")
if p["brenk"]:
    st.warning("**Brenk ogohlantirishi** — toksik yoki kimyoviy beqaror fragment: "
               + ", ".join(p["brenk"]) + ".")

# ============================================================ 3. Batafsil
st.divider()
st.subheader("Batafsil")

with st.expander("Kimyoviy xossalar (RDKit bilan aniq hisoblangan)", expanded=False):
    m = st.columns(3)
    m[0].metric("Molekulyar massa", p["mw"])
    m[0].caption("Og'iz orqali qabul qilinadigan dorilarda odatda 500 dan kichik")
    m[1].metric("logP", p["logp"])
    m[1].caption("Yog' va suvda erish muvozanati; 5 dan kichik bo'lgani ma'qul")
    m[2].metric("TPSA", p["tpsa"])
    m[2].caption("Qutbli sirt maydoni; 140 dan katta bo'lsa hujayraga qiyin kiradi")
    m = st.columns(3)
    m[0].metric("H-donor / akseptor", f'{p["hbd"]} / {p["hba"]}')
    m[0].caption("Vodorod bog'lari; 5 va 10 dan oshmagani ma'qul")
    m[1].metric("QED", p["qed"])
    m[1].caption("Mavjud dorilarga o'xshashlik: 0 dan 1 gacha")
    m[2].metric("SA score", p["sa_score"] if p["sa_score"] is not None else "—")
    m[2].caption("Sintez qiyinligi: 1 oson, 10 juda qiyin")
    st.write(f"Lipinski qoidasi: {'✅ mos' if prof.lipinski_ok else '❌ mos emas'} "
             f"({p['lipinski_violations']} ta buzilish, 1 tagacha ruxsat etiladi) · "
             f"Veber qoidasi: {'✅ mos' if p['veber_ok'] else '❌ mos emas'}")

if not preds.empty:
    with st.expander("15 ta AI modelining bashoratlari", expanded=False):
        st.caption("Bular o'qitilgan modellarning taxmini, laboratoriya o'lchovi emas.")
        row = preds.iloc[0]

        # Farmakokinetika — son va so'z bilan
        pk = []
        if "solubility" in row.index:
            pk.append({"Ko'rsatkich": "Suvda eruvchanlik (logS)", "Bashorat": f"{row['solubility']:.2f}",
                       "Ma'nosi": solubility_text(row["solubility"])})
        if "bbbp" in row.index:
            pk.append({"Ko'rsatkich": "Miyaga o'tish ehtimoli", "Bashorat": f"{row['bbbp']:.0%}",
                       "Ma'nosi": "miya kasalliklari uchun kerak, boshqalar uchun istalmagan"})
        if "clintox" in row.index:
            pk.append({"Ko'rsatkich": "Klinik toksiklik xavfi", "Bashorat": f"{row['clintox']:.0%}",
                       "Ma'nosi": f"xavf {level(row['clintox'], 0.3, 0.5)}"})
        if pk:
            st.dataframe(pd.DataFrame(pk), hide_index=True, use_container_width=True)

        # Tox21 — guruhlangan, tushunarli nomlar bilan
        tox = [{"Mexanizm": TOX21[k][1], "Guruh": TOX21[k][0], "Ehtimollik": round(float(row[k]), 2)}
               for k in TOX21 if k in row.index]
        if tox:
            tdf = pd.DataFrame(tox).sort_values("Ehtimollik", ascending=False)
            tfig = px.bar(tdf, x="Ehtimollik", y="Mexanizm", color="Guruh", orientation="h",
                          range_x=[0, 1], height=420,
                          title="Tox21: 12 ta toksiklik mexanizmi (1 ga yaqin — xavfli)")
            tfig.update_layout(yaxis={"autorange": "reversed"}, yaxis_title=None,
                               margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(tfig, use_container_width=True)

# ============================================================== Hisobot
def _md(d: dict) -> str:
    return "\n".join(f"- **{k}**: {v}" for k, v in d.items())


report = (f"# DoriAI hisobot\n\nSMILES: `{prof.smiles}`\n\n"
          f"DoriAI Score: **{score}** — {verdict(score)}\n\n"
          f"## Mezonlar (0–1)\n{_md({CRITERIA[k][0]: v for k, v in comps.items()})}\n\n"
          f"## Kimyoviy xossalar\n{_md(p)}\n\n## Model bashoratlari\n{_md(admet)}\n\n{DISCLAIMER}\n")
st.download_button("📄 Hisobotni yuklab olish", report, file_name="doriai_hisobot.md")
st.caption(DISCLAIMER)
