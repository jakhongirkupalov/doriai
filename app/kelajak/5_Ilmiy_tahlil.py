import plotly.express as px
import streamlit as st

from doriai.data_sources import pubmed
from doriai.literature.analyzer import summarize, top_terms, year_trend
from doriai.llm import client as llm
from doriai.ui import DISCLAIMER, page_setup

page_setup("Ilmiy ma'lumotlarni tahlil qilish", "📚")

q = st.text_input("PubMed so'rovi (inglizcha)", "metformin repurposing cancer")
n = st.slider("Maqolalar soni", 10, 60, 30)
if st.button("🔎 Qidirish va tahlil qilish", type="primary"):
    try:
        with st.spinner("PubMed'dan olinmoqda..."):
            st.session_state["papers"] = pubmed.search(q, retmax=n)
            st.session_state.pop("lit_summary", None)
    except ConnectionError as e:
        st.error(str(e))

papers = st.session_state.get("papers")
if papers:
    st.metric("Topilgan maqolalar", len(papers))
    c1, c2 = st.columns(2)
    yt = year_trend(papers)
    if not yt.empty:
        c1.plotly_chart(px.bar(yt, x="year", y="count", title="Yillar bo'yicha nashrlar"),
                        use_container_width=True)
    terms = top_terms([p["title"] + " " + p["abstract"] for p in papers])
    if not terms.empty:
        c2.plotly_chart(px.bar(terms.head(15), x="weight", y="term", orientation="h",
                               title="Kalit atamalar (TF-IDF)").update_yaxes(autorange="reversed"),
                        use_container_width=True)

    st.subheader("🤖 AI xulosasi")
    if not llm.is_configured():
        st.info("LLM sozlanmagan (.env). Kalit atamalar va maqolalar ro'yxati baribir mavjud.")
    elif st.button("Xulosa tayyorlash"):
        with st.spinner("LLM tahlil qilmoqda..."):
            st.session_state["lit_summary"] = summarize(q, papers)
    if st.session_state.get("lit_summary"):
        st.markdown(st.session_state["lit_summary"])

    st.subheader("Maqolalar")
    for p in papers:
        with st.expander(f"{p.get('year') or ''} · {p['title']}"):
            st.write(f"*{p['journal']}* — [PMID {p['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/)")
            st.write(p["abstract"] or "Annotatsiya yo'q")
st.caption(DISCLAIMER)
