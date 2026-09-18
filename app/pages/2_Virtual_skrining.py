import pandas as pd
import plotly.express as px
import streamlit as st

from doriai.screening.screener import screen
from doriai.ui import DISCLAIMER, EXAMPLES, get_predictor, mol_image, page_setup

page_setup("Virtual skrining", "🧪")
st.write("Birikmalar ro'yxatini yuklang — DoriAI ularni baholab, eng istiqbollilarini ajratadi.")

src = st.radio("Manba", ["CSV fayl (ustunlar: name, smiles)", "Matn (har qatorda: nom,SMILES)"],
               horizontal=True)
names, smiles = [], []
if src.startswith("CSV"):
    up = st.file_uploader("CSV yuklang", type=["csv"])
    if up:
        df_in = pd.read_csv(up)
        smiles = df_in["smiles"].astype(str).tolist()
        names = df_in["name"].astype(str).tolist() if "name" in df_in else None
else:
    default = "\n".join(f"{k},{v}" for k, v in EXAMPLES.items())
    txt = st.text_area("Molekulalar", default, height=180)
    for line in txt.strip().splitlines():
        if "," in line:
            n, s = line.split(",", 1)
            names.append(n.strip())
            smiles.append(s.strip())

f1, f2 = st.columns(2)
only_lipinski = f1.checkbox("Faqat Lipinski qoidasiga mos")
no_pains = f2.checkbox("PAINS ogohlantirishi borlarni chiqarib tashlash", value=True)

if smiles and st.button(f"🚀 {len(smiles)} ta molekulani skrining qilish", type="primary"):
    with st.spinner("Baholanmoqda..."):
        res = screen(smiles, names, get_predictor())
    st.session_state["screen_res"] = res

res = st.session_state.get("screen_res")
if res is not None:
    bad = res[~res["valid"]]
    view = res[res["valid"]].copy()
    if only_lipinski:
        view = view[view["lipinski_ok"]]
    if no_pains:
        view = view[view["pains"] == 0]

    k = st.columns(4)
    k[0].metric("Jami", len(res))
    k[1].metric("Filtrdan o'tdi", len(view))
    k[2].metric("Istiqbolli (≥70)", int((view["doriai_score"] >= 70).sum()))
    k[3].metric("Noto'g'ri SMILES", len(bad))

    st.plotly_chart(px.bar(view.head(15), x="doriai_score", y="name", orientation="h",
                           color="verdict", title="Top nomzodlar", height=420)
                    .update_yaxes(autorange="reversed"), use_container_width=True)
    if len(view) > 1:
        st.plotly_chart(px.scatter(view, x="qed", y="doriai_score", size="mw", color="verdict",
                                   hover_name="name", title="Dori-o'xshashlik va umumiy ball"),
                        use_container_width=True)

    st.dataframe(view.drop(columns=["valid"]), use_container_width=True, hide_index=True)
    st.download_button("⬇️ Natijalar (CSV)", view.to_csv(index=False), "doriai_screening.csv")

    if len(view):
        best = view.iloc[0]
        st.subheader(f"🥇 Eng yaxshi nomzod: {best['name']}")
        st.image(mol_image(best["smiles"]), width=360)
st.caption(DISCLAIMER)
