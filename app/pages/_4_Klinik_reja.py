import pandas as pd
import plotly.express as px
import streamlit as st

from doriai.data_sources.clinicaltrials import search_studies
from doriai.trials.planner import (draft_protocol, sample_size_two_proportions,
                                   trial_statistics, with_dropout)
from doriai.ui import DISCLAIMER, page_setup

page_setup("Klinik tadqiqotni rejalashtirish", "📋")

c1, c2, c3 = st.columns(3)
condition = c1.text_input("Kasallik (inglizcha)", "type 2 diabetes")
drug = c2.text_input("Dori / aralashuv", "metformin")
phase = c3.selectbox("Rejalashtirilgan faza", ["PHASE1", "PHASE2", "PHASE3"], index=1)

if st.button("🔎 O'xshash tadqiqotlarni tahlil qilish", type="primary"):
    try:
        with st.spinner("ClinicalTrials.gov'dan olinmoqda..."):
            df = search_studies(condition, drug or None, max_studies=300)
        st.session_state["trials"] = (df, trial_statistics(df))
    except ConnectionError as e:
        st.error(str(e))

if "trials" in st.session_state:
    df, stats = st.session_state["trials"]
    if df.empty:
        st.warning("Tadqiqot topilmadi.")
    else:
        m = st.columns(3)
        m[0].metric("Topilgan tadqiqotlar", stats["n_studies"])
        cr = stats["completion_rate"]
        m[1].metric("Yakunlanish darajasi", f"{cr:.0%}" if cr is not None else "—",
                    help="COMPLETED / (COMPLETED + TERMINATED + WITHDRAWN + SUSPENDED)")
        m[2].metric("Fazalar soni", len(stats["by_phase"]))

        g1, g2 = st.columns(2)
        g1.plotly_chart(px.pie(names=list(stats["status_counts"]), values=list(stats["status_counts"].values()),
                               title="Holatlar bo'yicha"), use_container_width=True)
        if len(stats["top_countries"]):
            tc = stats["top_countries"].rename_axis("davlat").reset_index(name="soni")
            g2.plotly_chart(px.bar(tc, x="soni", y="davlat", orientation="h", title="Top davlatlar")
                            .update_yaxes(autorange="reversed"), use_container_width=True)
        st.subheader("Fazalar bo'yicha mediana ko'rsatkichlar (benchmark)")
        st.dataframe(stats["by_phase"], hide_index=True, use_container_width=True)
        with st.expander("Barcha tadqiqotlar"):
            st.dataframe(df, hide_index=True, use_container_width=True)

st.divider()
st.subheader("🧮 Tanlama hajmi kalkulyatori")
s = st.columns(5)
p0 = s[0].number_input("Nazorat guruhida javob", 0.01, 0.99, 0.30)
p1 = s[1].number_input("Davolash guruhida javob", 0.01, 0.99, 0.45)
alpha = s[2].selectbox("α", [0.05, 0.01], index=0)
power = s[3].selectbox("Quvvat (1-β)", [0.8, 0.9], index=0)
drop = s[4].slider("Chiqib ketish", 0.0, 0.4, 0.15)
try:
    n = sample_size_two_proportions(p0, p1, alpha, power)
    st.success(f"Har bir guruhga **{n}** ta; chiqib ketishni hisobga olganda **{with_dropout(n, drop)}**, "
               f"jami **{2 * with_dropout(n, drop)}** ishtirokchi.")
except ValueError as e:
    st.error(str(e))

st.divider()
st.subheader("📝 Protokol sinopsisi loyihasi (AI)")
if st.button("Protokol loyihasini yaratish"):
    df, stats = st.session_state.get("trials", (None, {}))
    with st.spinner("Yozilmoqda..."):
        text = draft_protocol(condition, drug, phase, stats or {},
                              df if df is not None else pd.DataFrame())
    st.session_state["protocol"] = text
if "protocol" in st.session_state:
    st.markdown(st.session_state["protocol"])
    st.download_button("⬇️ Protokol (.md)", st.session_state["protocol"], "protocol_draft.md")
st.caption(DISCLAIMER)
