"""Drug repurposing — tasdiqlangan dorilar orasidan yangi kasallik uchun nomzod izlash.

Sahifa tartibi:
  1. Kasallik nishonini tanlash (tayyor ro'yxat yoki ChEMBL qidiruvi)
  2. Model sifati va validatsiya — natijaga qanchalik ishonish mumkin
  3. Nomzod dorilar: ta'sir kuchi + ishonchlilik + xavfsizlik (DoriAI Score)
  4. Tanlangan dori haqida: tuzilishi va hozirgi qo'llanilishi
  5. Batafsil texnik ma'lumotlar (yig'iladigan)
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from doriai.data_sources import chembl
from doriai.repurposing.target_model import build_target_model, rank_library
from doriai.screening.screener import screen
from doriai.ui import DISCLAIMER, get_library, get_predictor, mol_image, page_setup, smiles_input

# Ko'p ishlatiladigan nishonlar: nomi -> (ChEMBL ID, izoh)
PRESETS = {
    "EGFR — o'pka saratoni": ("CHEMBL203", "Hujayra o'sishini boshqaruvchi retseptor; ba'zi saraton turlarida haddan tashqari faol"),
    "COX-2 — og'riq va yallig'lanish": ("CHEMBL230", "Yallig'lanish moddalarini ishlab chiqaruvchi ferment"),
    "DPP-4 — 2-tur qandli diabet": ("CHEMBL284", "Qonda qand miqdorini boshqaruvchi gormonlarni parchalovchi ferment"),
    "Atsetilxolinesteraza — Altsgeymer kasalligi": ("CHEMBL220", "Nerv signallarini uzatuvchi moddani parchalovchi ferment"),
}
CONF_COLORS = {"yuqori": "#0B5FA5", "o'rta": "#5DA9E9", "past": "#C9D6E3"}


def strength(pchembl: float) -> str:
    """pChEMBL -> ta'sir kuchi so'z bilan (8 = 10 nM, 7 = 100 nM, 6 = 1 µM)."""
    if pchembl >= 8:
        return "juda kuchli"
    if pchembl >= 7:
        return "kuchli"
    if pchembl >= 6:
        return "o'rtacha"
    return "zaif"


def r2_word(r2: float) -> str:
    return "yaxshi" if r2 >= 0.7 else "o'rtacha" if r2 >= 0.5 else "past"


lib = get_library()


@st.cache_resource(show_spinner=False, max_entries=20, ttl=7 * 24 * 3600)
def train_and_rank(target_id: str):
    """Bir nishon uchun model bir marta o'qitiladi va bir hafta xotirada saqlanadi."""
    acts = chembl.fetch_activities(target_id, max_records=3000)
    tm = build_target_model(acts, target_id)
    ranked = rank_library(tm, lib, top_k=30)
    ranked["confidence"] = ranked["confidence"].astype(str)
    # Har bir nomzodning xavfsizligini skrining moduli bilan baholaymiz
    key = "chembl_id" if "chembl_id" in ranked.columns else "name"
    sc = screen(ranked["smiles"].tolist(), ranked[key].astype(str).tolist(), get_predictor())
    sc = sc[sc["valid"].astype(bool)].set_index("name")[["doriai_score", "verdict"]]
    ranked = ranked.join(sc, on=key)
    return len(acts), tm, ranked


# ================================================================ Kirish
page_setup("Drug repurposing — mavjud dorilarni qayta qo'llash", "💊")
st.caption("Tasdiqlangan dorilar xavfsizlik sinovlaridan allaqachon o'tgan. Agar ulardan biri boshqa kasallik "
           "nishoniga ham ta'sir qilsa, yangi dori yaratishga ketadigan yillar qisqaradi. "
           f"Kutubxonada {len(lib)} ta tasdiqlangan dori bor.")

tab1, tab2 = st.tabs(["🎯 Kasallik nishoni bo'yicha", "🧩 O'xshash dori izlash"])

# ======================================================= 1-tab: nishon
with tab1:
    st.markdown("**1-qadam. Kasallik bilan bog'liq oqsilni (nishonni) tanlang**")
    mode = st.radio("Nishon manbai", ["Tayyor ro'yxatdan", "ChEMBL bazasidan qidirish"],
                    horizontal=True, label_visibility="collapsed")

    target_id, target_label = None, None
    if mode == "Tayyor ro'yxatdan":
        choice = st.selectbox("Nishon", list(PRESETS))
        target_id, desc = PRESETS[choice]
        target_label = choice
        st.caption(f"{desc}. ChEMBL ID: {target_id}")
    else:
        q = st.text_input("Oqsil nomi (inglizcha)", "EGFR",
                          help="Masalan: EGFR, cyclooxygenase-2, DPP4, acetylcholinesterase")
        if st.button("Qidirish"):
            try:
                st.session_state["targets"] = chembl.search_targets(q)
            except ConnectionError as e:
                st.error(f"ChEMBL bilan aloqa yo'q: {e}")
        targets = st.session_state.get("targets")
        if targets is not None and not targets.empty:
            human = targets[targets["organism"] == "Homo sapiens"]
            opts = (human if not human.empty else targets).copy()
            opts = opts.sort_values("target_type", key=lambda s: s != "SINGLE PROTEIN", kind="stable")
            labels = opts.apply(lambda r: f"{r.target_chembl_id} — {r.pref_name} ({r.target_type})", axis=1)
            pick = st.selectbox("Topilgan nishonlar", labels.tolist())
            target_id, target_label = pick.split(" — ")[0], pick
            st.caption("Maslahat: \"SINGLE PROTEIN\" turidagi nishonni tanlang — ularda o'lchovlar eng ko'p.")
        elif targets is not None:
            st.warning("Hech narsa topilmadi. Boshqa nom bilan qidirib ko'ring.")

    if target_id:
        st.markdown("**2-qadam. Nomzodlarni izlash**")
        if st.button("🔎 Mavjud dorilar orasidan nomzod izlash", type="primary"):
            try:
                with st.spinner("Model o'qitilmoqda va dorilar baholanmoqda (birinchi marta 1–2 daqiqa)..."):
                    n_acts, tm, ranked = train_and_rank(target_id)
                st.session_state["repurp"] = (target_label, n_acts, tm, ranked)
            except ValueError as e:
                st.error(f"Bu nishon uchun o'lchovlar yetarli emas: {e}")
            except ConnectionError as e:
                st.error(f"ChEMBL bilan aloqa yo'q: {e}")

    # Eski versiyadan qolgan natija bo'lsa — tozalaymiz
    if "repurp" in st.session_state and len(st.session_state["repurp"]) != 4:
        del st.session_state["repurp"]

    if "repurp" in st.session_state:
        label, n_acts, tm, ranked_all = st.session_state["repurp"]
        st.divider()
        st.subheader(f"Natija: {label}")

        # ---- Model sifati
        m = st.columns(3)
        m[0].metric("O'qitish ma'lumotlari", f"{tm.n_train} molekula",
                    help="ChEMBL'dagi shu nishonga qarshi laboratoriyada o'lchangan molekulalar")
        m[1].metric("Model aniqligi (R²)", f"{tm.cv_r2:.2f} — {r2_word(tm.cv_r2)}",
                    help="5 qismli tekshiruv: 1 ga yaqin — aniq, 0.7 dan yuqori — yaxshi")
        m[2].metric("Tekshirilgan dorilar", len(lib))

        # ---- Validatsiya
        n_known = int(ranked_all["known_active"].sum())
        new_hits = ranked_all[(~ranked_all["known_active"].astype(bool))
                              & (ranked_all["confidence"] == "yuqori")]["name"].tolist()
        if new_hits:
            st.success(f"**Model o'qitishda ko'rmagan, lekin yuqori ishonch bilan topgan dorilar:** "
                       f"{', '.join(new_hits)}. Ular laboratoriyada tekshirishga arzigulik gipotezalar. "
                       f"Yana {n_known} ta dori o'qitish ma'lumotlarida bor edi — model ularni to'g'ri tanidi.")
        else:
            st.info(f"Ro'yxatdagi {n_known} ta dori o'qitish ma'lumotlarida bor edi — model ularni to'g'ri tanidi. "
                    "O'qitishda bo'lmagan yuqori ishonchli nomzod topilmadi.")

        # ---- Nomzodlar
        st.markdown("**Nomzod dorilar**")
        ranked = ranked_all
        if st.checkbox("Faqat ishonchli bashoratlarni ko'rsatish", value=True,
                       help="Model yaxshi bilmaydigan kimyoviy hududdagi dorilar yashiriladi"):
            ranked = ranked_all[ranked_all["confidence"] != "past"].reset_index(drop=True)

        if ranked.empty:
            st.info("Ishonchli nomzod qolmadi. Belgini olib tashlab, barcha bashoratlarni ko'ring.")
        else:
            top = ranked.head(15)
            fig = px.bar(top, x="pred_pchembl", y="name", color="confidence", orientation="h",
                         color_discrete_map=CONF_COLORS,
                         category_orders={"name": top["name"].tolist(),
                                          "confidence": ["yuqori", "o'rta", "past"]},
                         labels={"confidence": "Ishonchlilik"},
                         height=max(260, 30 * len(top) + 80))
            fig.update_layout(xaxis_title="Nishonga ta'sir kuchi (pChEMBL: 6 — o'rtacha, 7 — kuchli, 8 — juda kuchli)",
                              yaxis_title=None, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

            table = pd.DataFrame({
                "O'rin": range(1, len(ranked) + 1),
                "Dori": ranked["name"],
                "Ta'sir kuchi": ranked["pred_pchembl"].apply(lambda v: f"{strength(v)} ({v:.1f})"),
                "Ishonchlilik": ranked["confidence"],
                "Holat": ranked["known_active"].map({True: "Ma'lum faol", False: "🆕 Yangi gipoteza"}),
                "Xavfsizlik (DoriAI Score)": ranked["doriai_score"],
                "Tasdiqlangan yil": (ranked["first_approval"] if "first_approval" in ranked.columns
                                     else pd.Series([pd.NA] * len(ranked))),
            })
            st.dataframe(table, hide_index=True, use_container_width=True,
                         column_config={
                             "Xavfsizlik (DoriAI Score)": st.column_config.ProgressColumn(
                                 "Xavfsizlik (DoriAI Score)", min_value=0, max_value=100, format="%.0f"),
                             "Tasdiqlangan yil": st.column_config.NumberColumn(format="%d"),
                         })
            st.caption("**Ma'lum faol** — dori bu nishonga qarshi laboratoriyada allaqachon o'lchangan. "
                       "**Yangi gipoteza** — bunday o'lchov yo'q, bashorat tekshirilishi kerak. "
                       "**Xavfsizlik** — Virtual skrining modulidagi baho.")

            # ---- Tanlangan dori
            st.markdown("**Dori haqida batafsil**")
            pick = st.selectbox("Dorini tanlang", ranked["name"].tolist(), label_visibility="collapsed")
            row = ranked[ranked["name"] == pick].iloc[0]
            c1, c2 = st.columns([1, 1.6])
            c1.image(mol_image(row["smiles"]))
            with c2:
                st.markdown(f"**Ta'sir kuchi:** {strength(row['pred_pchembl'])} "
                            f"(taxminiy samarali konsentratsiya ~{row['pred_IC50_nM']:.0f} nM)")
                st.markdown(f"**Ishonchlilik:** {row['confidence']}")
                if pd.notna(row.get("doriai_score")):
                    st.markdown(f"**Xavfsizlik:** {row['doriai_score']:.0f} — {row['verdict']}")
                if "chembl_id" in row.index and pd.notna(row["chembl_id"]):
                    try:
                        ind = chembl.fetch_indications(row["chembl_id"])
                        st.markdown("**Hozirgi qo'llanilishi (ChEMBL):** " + (", ".join(ind[:12]) or "—"))
                    except ConnectionError:
                        st.caption("Qo'llanilish ma'lumotini olish uchun internet kerak.")
                elif "indication" in row.index:
                    st.markdown(f"**Hozirgi qo'llanilishi:** {row['indication']}")

        # ---- Batafsil
        with st.expander("Batafsil: texnik ma'lumotlar", expanded=False):
            st.caption(f"Model: Random Forest, {tm.n_train} ta ChEMBL o'lchovida o'qitilgan. "
                       f"R² = {tm.cv_r2:.2f}, o'rtacha xato (RMSE) = {tm.cv_rmse:.2f} pChEMBL birligi. "
                       "\"O'qitishga o'xshashlik\" — dori o'qitish molekulalariga qanchalik o'xshashi (1 — aynan o'zi).")
            tech = ranked_all[["name", "pred_pchembl", "pred_IC50_nM", "nearest_train_sim",
                               "confidence", "known_active", "smiles"]].rename(columns={
                "name": "Dori", "pred_pchembl": "pChEMBL", "pred_IC50_nM": "IC50 (nM)",
                "nearest_train_sim": "O'qitishga o'xshashlik", "confidence": "Ishonchlilik",
                "known_active": "Ma'lum faol", "smiles": "SMILES"})
            st.dataframe(tech, hide_index=True, use_container_width=True)

# ================================================ 2-tab: o'xshashlik
with tab2:
    st.caption("Laboratoriyada faol chiqqan birikma yoki tabiiy moddaning SMILES'ini kiriting — unga tuzilishi "
               "o'xshash tasdiqlangan dorilar topiladi. Tuzilishi o'xshash molekulalar ko'pincha o'xshash ta'sir qiladi.")
    smi = smiles_input("rep", default="Kurkumin (tabiiy birikma)")
    k = st.slider("Nechta dori ko'rsatilsin", 5, 30, 10)
    if smi:
        try:
            sim = lib.similar_to(smi, top_k=k).copy()
            sim["O'xshashlik"] = (sim["similarity"] * 100).round().astype(int)
            fig = px.bar(sim, x="O'xshashlik", y="name", orientation="h", range_x=[0, 100],
                         text="O'xshashlik", height=max(260, 30 * len(sim) + 80))
            fig.update_traces(marker_color="#5DA9E9", texttemplate="%{text}%", textposition="outside")
            fig.update_layout(xaxis_title="Tuzilish o'xshashligi (%)", yaxis_title=None,
                              yaxis={"autorange": "reversed"}, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("50% dan yuqori — sezilarli o'xshashlik; 30% dan past — deyarli o'xshamaydi.")
        except ValueError:
            st.error("SMILES noto'g'ri — molekulani o'qib bo'lmadi.")

st.caption(DISCLAIMER)