import pandas as pd
import plotly.express as px
import streamlit as st

from doriai.chem.molecule import profile_molecule
from doriai.screening.scoring import WEIGHTS, doriai_score, verdict
from doriai.ui import DISCLAIMER, get_predictor, mol_image, page_setup, score_gauge, smiles_input

page_setup("Molekula tahlili", "🔬")
smiles = smiles_input("mol")
if not smiles:
    st.stop()

prof = profile_molecule(smiles)
if prof is None:
    st.error("SMILES noto'g'ri — molekulani o'qib bo'lmadi.")
    st.stop()

pred = get_predictor()
preds = pred.predict([smiles]) if pred.available else pd.DataFrame()
admet = pred.summarize(preds.iloc[0]) if not preds.empty else {}
p = prof.to_dict()
score, comps = doriai_score(p, admet)

left, mid, right = st.columns([1.1, 1, 1])
left.image(mol_image(smiles), caption=prof.smiles)
with mid:
    st.plotly_chart(score_gauge(score), use_container_width=True)
    st.markdown(f"**Xulosa:** {verdict(score)}")
with right:
    comp_df = pd.DataFrame({"komponent": list(comps), "qiymat": list(comps.values()),
                            "og'irlik": [WEIGHTS[k] for k in comps]})
    st.plotly_chart(px.bar(comp_df, x="qiymat", y="komponent", orientation="h",
                           range_x=[0, 1], height=260, title="Ball tarkibi (izohlanuvchi AI)"),
                    use_container_width=True)

st.subheader("Fizik-kimyoviy xossalar va dori-o'xshashlik")
m = st.columns(6)
m[0].metric("Molekulyar massa", p["mw"], help="Lipinski: ≤ 500")
m[1].metric("logP", p["logp"], help="Lipinski: ≤ 5")
m[2].metric("H-donor / akseptor", f'{p["hbd"]} / {p["hba"]}', help="≤ 5 / ≤ 10")
m[3].metric("TPSA", p["tpsa"], help="Veber: ≤ 140 Å²")
m[4].metric("QED", p["qed"], help="0..1, dori-o'xshashlik")
m[5].metric("SA score", p["sa_score"] or "—", help="1 oson … 10 juda qiyin sintez")

st.write(f"Lipinski: {'✅' if prof.lipinski_ok else '❌'} ({p['lipinski_violations']} buzilish) · "
         f"Veber: {'✅' if p['veber_ok'] else '❌'}")
if p["pains"]:
    st.error("PAINS ogohlantirishlari (skriningda yolg'on-musbat natija xavfi): " + ", ".join(p["pains"]))
if p["brenk"]:
    st.warning("Brenk ogohlantirishlari (toksik/reaktiv fragmentlar): " + ", ".join(p["brenk"]))

st.subheader("ADMET bashoratlari")
if preds.empty:
    st.info("ADMET modellari o'qitilmagan.")
else:
    rows = []
    for task in pred.available:
        spec = pred.spec(task)
        val = preds.iloc[0][task]
        rows.append({"ko'rsatkich": spec.label, "turi": spec.group,
                     "bashorat": round(float(val), 3),
                     "izoh": "ehtimollik (0–1)" if spec.kind == "classification" else "logS (mol/L)"})
    tdf = pd.DataFrame(rows)
    tox = tdf[tdf["ko'rsatkich"].str.startswith("Tox21")]
    c1, c2 = st.columns([1, 1.3])
    c1.dataframe(tdf[~tdf.index.isin(tox.index)], hide_index=True, use_container_width=True)
    c2.plotly_chart(px.bar(tox, x="bashorat", y="ko'rsatkich", orientation="h", range_x=[0, 1],
                           title="Tox21 toksiklik profili", height=380), use_container_width=True)

def _md(d: dict) -> str:
    return "\n".join(f"- **{k}**: {v}" for k, v in d.items())


report = (f"# DoriAI hisobot\n\nSMILES: `{prof.smiles}`\n\n"
          f"DoriAI Score: **{score}** — {verdict(score)}\n\n"
          f"## Xossalar\n{_md(p)}\n\n## ADMET\n{_md(admet)}\n\n"
          f"## Ball tarkibi\n{_md(comps)}\n\n{DISCLAIMER}\n")
st.download_button("📄 Hisobotni yuklab olish (.md)", report, file_name="doriai_report.md")
st.caption(DISCLAIMER)
