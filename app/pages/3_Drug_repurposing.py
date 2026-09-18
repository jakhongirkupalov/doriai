import plotly.express as px
import streamlit as st

from doriai.data_sources import chembl
from doriai.repurposing.target_model import build_target_model, rank_library
from doriai.ui import DISCLAIMER, get_library, mol_image, page_setup, smiles_input

page_setup("Drug repurposing — mavjud dorilarni qayta qo'llash", "💊")
lib = get_library()
st.caption(f"Kutubxona: {len(lib)} ta tasdiqlangan dori ({lib.source})")

tab1, tab2 = st.tabs(["🎯 Nishon (oqsil) bo'yicha", "🧩 Strukturaviy o'xshashlik bo'yicha"])

# ---------------------------------------------------------------- 1: target-based
with tab1:
    st.markdown("Oqsil-nishonni tanlang → ChEMBL faolliklarida AI model o'qitiladi → "
                "model **barcha tasdiqlangan dorilarni** shu nishonga qarshi baholaydi.")
    q = st.text_input("Nishon nomi (inglizcha)", "EGFR",
                      help="Masalan: EGFR, acetylcholinesterase, cyclooxygenase-2, DPP4")
    if st.button("Nishonlarni qidirish"):
        try:
            st.session_state["targets"] = chembl.search_targets(q)
        except ConnectionError as e:
            st.error(str(e))

    targets = st.session_state.get("targets")
    if targets is not None and not targets.empty:
        human = targets[targets["organism"] == "Homo sapiens"]
        opts = (human if not human.empty else targets).copy()
        # Oddiy oqsillar (SINGLE PROTEIN) birinchi — ularda o'lchovlar eng ko'p
        opts = opts.sort_values("target_type", key=lambda s: s != "SINGLE PROTEIN", kind="stable")
        label = opts.apply(lambda r: f"{r.target_chembl_id} — {r.pref_name} ({r.target_type})", axis=1)
        choice = st.selectbox("Nishon", label.tolist())
        target_id = choice.split(" — ")[0]

        if st.button("🧠 Modelni o'qitish va dorilarni reytinglash", type="primary"):
            with st.spinner("ChEMBL'dan faolliklar olinmoqda..."):
                acts = chembl.fetch_activities(target_id, max_records=3000)
            st.write(f"{len(acts)} ta noyob molekula topildi.")
            try:
                with st.spinner("Model o'qitilmoqda (5-fold cross-validation)..."):
                    tm = build_target_model(acts, target_id)
                st.session_state["repurp"] = (tm, rank_library(tm, lib, top_k=25))
            except ValueError as e:
                st.error(str(e))

    if "repurp" in st.session_state:
        tm, ranked = st.session_state["repurp"]
        a, b, c = st.columns(3)
        a.metric("O'quv to'plami", tm.n_train)
        b.metric("CV R²", f"{tm.cv_r2:.2f}")
        c.metric("CV RMSE (pChEMBL)", f"{tm.cv_rmse:.2f}")
        st.plotly_chart(px.bar(ranked.head(15), x="pred_pchembl", y="name", color="confidence",
                               orientation="h", title="Nishonga qarshi bashorat qilingan faollik",
                               height=450,
                               category_orders={"name": ranked.head(15)["name"].tolist()}),
                        use_container_width=True)
        st.dataframe(ranked, use_container_width=True, hide_index=True)
        n_known = int(ranked["known_active"].sum())
        new_hits = ranked[(~ranked["known_active"]) & (ranked["confidence"] == "yuqori")]["name"].tolist()
        st.info(f"✔️ Top-25 ichida {n_known} ta dori o'qitish ma'lumotlarida bor edi — model ularni to'g'ri "
                f"eslab qoldi. O'qitishda bo'lmagan, lekin yuqori ishonch bilan topilganlar: "
                f"{', '.join(new_hits) or '—'}. Ular laboratoriyada tekshirishga arzigulik gipotezalar.")
        if "chembl_id" in ranked.columns:
            pick = st.selectbox("Dori ko'rsatmalarini ko'rish", ranked["name"].tolist())
            row = ranked[ranked["name"] == pick].iloc[0]
            cc1, cc2 = st.columns([1, 2])
            cc1.image(mol_image(row["smiles"]), width=300)
            try:
                cc2.write("**Hozirgi ko'rsatmalari (ChEMBL):**")
                cc2.write(", ".join(chembl.fetch_indications(row["chembl_id"])) or "—")
            except ConnectionError:
                cc2.write("Internet yo'q")

# ------------------------------------------------------------ 2: similarity-based
with tab2:
    st.markdown("Faol birikma (masalan, laboratoriyada topilgan yoki tabiiy modda) SMILES'ini kiriting — "
                "unga strukturaviy o'xshash **tasdiqlangan dorilar** topiladi.")
    smi = smiles_input("rep", default="Kurkumin (tabiiy birikma)")
    k = st.slider("Nechta natija", 5, 30, 10)
    if smi:
        try:
            sim = lib.similar_to(smi, top_k=k)
            st.plotly_chart(px.bar(sim, x="similarity", y="name", orientation="h", range_x=[0, 1],
                                   title="Tanimoto o'xshashlik").update_yaxes(autorange="reversed"),
                            use_container_width=True)
            st.dataframe(sim, use_container_width=True, hide_index=True)
        except ValueError as e:
            st.error(str(e))
st.caption(DISCLAIMER)
