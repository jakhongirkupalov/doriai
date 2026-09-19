"""Virtual skrining — ko'plab birikmalarni laboratoriyadan oldin saralash.

Sahifa tartibi:
  1. Birikmalarni yuklash (namuna to'plam, CSV fayl yoki matn)
  2. Natija: nechta birikma qaysi toifaga tushdi
  3. Reyting jadvali — tushunarli ustunlar bilan
  4. Eng yaxshi nomzod
  5. Batafsil ma'lumotlar (yig'iladigan bo'lim)
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from doriai.config import SEED_DIR
from doriai.screening.screener import screen
from doriai.ui import DISCLAIMER, get_predictor, mol_image, page_setup

VERDICT_COLORS = {
    "Istiqbolli nomzod": "#2EAD6B",
    "Optimallashtirish kerak": "#E0A526",
    "Xavfli / past ustuvorlik": "#E05252",
}
VERDICT_ORDER = list(VERDICT_COLORS)


def risk_level(value) -> str:
    if value is None or pd.isna(value):
        return "—"
    return "past" if value < 0.3 else "o'rta" if value < 0.5 else "yuqori"


def solubility_level(logS) -> str:
    if logS is None or pd.isna(logS):
        return "—"
    return "yaxshi" if logS >= -2 else "o'rtacha" if logS >= -4 else "yomon"


def toxicity(row) -> float | None:
    parts = [v for v in (row.get("tox21_mean"), row.get("clintox")) if v is not None and pd.notna(v)]
    return sum(parts) / len(parts) if parts else None


def warning_text(row) -> str:
    if row["pains"] > 0:
        return "⛔ Yolg'on-musbat xavfi (PAINS)"
    if row["brenk"] > 0:
        return "⚠️ Toksik fragment (Brenk)"
    return "✅ Yo'q"


# =============================================================== 1. Kirish
page_setup("Virtual skrining", "🧪")
st.caption("Birikmalar ro'yxatini yuklang — DoriAI har birini xavfsizlik, dori-o'xshashlik va sintez "
           "qulayligi bo'yicha baholab, laboratoriyada birinchi navbatda tekshirishga arziydiganlarini ajratadi.")

source = st.radio("Birikmalar manbai",
                  ["Namuna to'plam (12 ta birikma)", "CSV fayl", "Matn ko'rinishida"],
                  horizontal=True)

names, smiles = [], []
if source.startswith("Namuna"):
    demo = pd.read_csv(SEED_DIR / "demo_compounds.csv")
    names, smiles = demo["name"].astype(str).tolist(), demo["smiles"].astype(str).tolist()
    st.caption("Tarkibi: ma'lum dorilar, tabiiy birikmalar (harmin, kurkumin, kversetin) va ataylab "
               "qo'shilgan xavfli namunalar (nitrobenzol, rodanin).")
elif source == "CSV fayl":
    up = st.file_uploader("CSV fayl: `smiles` ustuni majburiy, `name` ustuni ixtiyoriy", type=["csv"])
    if up:
        df_in = pd.read_csv(up)
        df_in.columns = [c.strip().lower() for c in df_in.columns]
        if "smiles" not in df_in.columns:
            st.error("Faylda `smiles` ustuni topilmadi.")
        else:
            smiles = df_in["smiles"].astype(str).tolist()
            names = (df_in["name"].astype(str).tolist() if "name" in df_in.columns
                     else [f"Birikma {i + 1}" for i in range(len(smiles))])
else:
    txt = st.text_area("Har bir qatorda: nom, SMILES",
                       "Aspirin, CC(=O)Oc1ccccc1C(=O)O\nIbuprofen, CC(C)Cc1ccc(cc1)C(C)C(=O)O", height=140)
    for line in txt.strip().splitlines():
        if "," in line:
            n, s = line.split(",", 1)
            names.append(n.strip())
            smiles.append(s.strip())

if smiles and st.button(f"🚀 {len(smiles)} ta birikmani baholash", type="primary"):
    with st.spinner("Birikmalar baholanmoqda..."):
        st.session_state["screen_res"] = screen(smiles, names, get_predictor())

res = st.session_state.get("screen_res")
if res is None:
    st.caption(DISCLAIMER)
    st.stop()

# ================================================================ Filtrlar
st.divider()
f1, f2 = st.columns(2)
only_oral = f1.checkbox("Faqat og'iz orqali qabul qilishga yaroqlilar (Lipinski qoidasi)")
hide_pains = f2.checkbox("Yolg'on-musbat natija beruvchilarni chiqarish (PAINS)", value=False)

invalid = res[~res["valid"].astype(bool)]
view = res[res["valid"].astype(bool)].copy()
if only_oral:
    view = view[view["lipinski_ok"].astype(bool)]
if hide_pains:
    view = view[view["pains"] == 0]
view = view.reset_index(drop=True)

# =============================================================== 2. Natija
st.subheader("Natija")
counts = view["verdict"].value_counts()
k = st.columns(4)
k[0].metric("Baholandi", len(view))
k[1].metric("🟢 Istiqbolli", int(counts.get("Istiqbolli nomzod", 0)))
k[2].metric("🟡 Optimallashtirish kerak", int(counts.get("Optimallashtirish kerak", 0)))
k[3].metric("🔴 Xavfli", int(counts.get("Xavfli / past ustuvorlik", 0)))
if len(invalid):
    st.caption(f"{len(invalid)} ta yozuvni o'qib bo'lmadi (SMILES noto'g'ri) — pastdagi batafsil bo'limga qarang.")

if view.empty:
    st.info("Tanlangan filtrlar bo'yicha birikma qolmadi.")
    st.stop()

top = view.head(15)
fig = px.bar(top, x="doriai_score", y="name", color="verdict", orientation="h", text="doriai_score",
             color_discrete_map=VERDICT_COLORS, category_orders={"verdict": VERDICT_ORDER,
                                                                 "name": top["name"].tolist()},
             range_x=[0, 105], height=max(260, 32 * len(top) + 80))
fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
fig.update_layout(xaxis_title="DoriAI Score (0–100)", yaxis_title=None, legend_title=None,
                  margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

# ======================================================= 3. Reyting jadvali
st.subheader("Reyting")
table = pd.DataFrame({
    "O'rin": range(1, len(view) + 1),
    "Birikma": view["name"],
    "DoriAI Score": view["doriai_score"],
    "Xulosa": view["verdict"],
    "Toksiklik xavfi": view.apply(lambda r: risk_level(toxicity(r)), axis=1),
    "Og'iz orqali qabul": view["lipinski_ok"].map({True: "✅ yaroqli", False: "❌ yaroqsiz"}),
    "Suvda eruvchanlik": view["logS"].apply(solubility_level),
    "Ogohlantirish": view.apply(warning_text, axis=1),
})
st.dataframe(table, hide_index=True, use_container_width=True,
             column_config={"DoriAI Score": st.column_config.ProgressColumn(
                 "DoriAI Score", min_value=0, max_value=100, format="%.0f")})
st.download_button("⬇️ Reytingni yuklab olish (CSV)", table.to_csv(index=False).encode("utf-8-sig"),
                   "doriai_skrining.csv")

# ====================================================== 4. Eng yaxshi nomzod
best = view.iloc[0]
st.subheader(f"🥇 Eng yaxshi nomzod: {best['name']}")
c1, c2 = st.columns([1, 1.4])
c1.image(mol_image(best["smiles"]))
with c2:
    st.markdown(f"**DoriAI Score:** {best['doriai_score']:.0f} — {best['verdict']}")
    st.markdown(f"**Toksiklik xavfi:** {risk_level(toxicity(best))}")
    st.markdown(f"**Og'iz orqali qabul:** {'yaroqli' if best['lipinski_ok'] else 'yaroqsiz'}")
    st.markdown(f"**Suvda eruvchanlik:** {solubility_level(best['logS'])}")
    st.caption("Batafsil tahlil uchun quyidagi SMILES'ni nusxalab, Molekula tahlili sahifasiga kiriting:")
    st.code(best["smiles"], language=None)

# ============================================================ 5. Batafsil
st.divider()
with st.expander("Batafsil: dori-o'xshashlik va umumiy ball", expanded=False):
    st.caption("Har bir nuqta — bitta birikma. O'ngga — mavjud dorilarga ko'proq o'xshaydi (QED), "
               "yuqoriga — umumiy ball yuqori. Doira hajmi — molekulyar massa.")
    sfig = px.scatter(view, x="qed", y="doriai_score", size="mw", color="verdict", hover_name="name",
                      color_discrete_map=VERDICT_COLORS, category_orders={"verdict": VERDICT_ORDER})
    sfig.update_layout(xaxis_title="Dori-o'xshashlik (QED, 0–1)", yaxis_title="DoriAI Score",
                       legend_title=None, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(sfig, use_container_width=True)

with st.expander("Batafsil: barcha raqamli ko'rsatkichlar", expanded=False):
    tech = view[["name", "doriai_score", "qed", "mw", "logp", "tpsa", "sa_score",
                 "tox21_mean", "clintox", "logS", "bbbp", "smiles"]].rename(columns={
        "name": "Birikma", "doriai_score": "DoriAI Score", "qed": "Dori-o'xshashlik (QED)",
        "mw": "Molekulyar massa", "logp": "logP", "tpsa": "Qutbli sirt (TPSA)",
        "sa_score": "Sintez qiyinligi (1–10)", "tox21_mean": "Tox21 o'rtacha xavf",
        "clintox": "Klinik toksiklik xavfi", "logS": "Eruvchanlik (logS)",
        "bbbp": "Miyaga o'tish ehtimoli", "smiles": "SMILES"})
    st.dataframe(tech.round(2), hide_index=True, use_container_width=True)

if len(invalid):
    with st.expander(f"O'qib bo'lmagan yozuvlar ({len(invalid)} ta)", expanded=False):
        st.dataframe(invalid[["name", "smiles"]].rename(columns={"name": "Birikma", "smiles": "SMILES"}),
                     hide_index=True, use_container_width=True)

st.caption(DISCLAIMER)