"""DoriAI — bosh sahifa.  Ishga tushirish:  streamlit run app/Home.py"""
import streamlit as st

from doriai.llm import client as llm
from doriai.ui import DISCLAIMER, get_library, get_predictor, page_setup

page_setup("DoriAI — AI Drug Discovery platformasi", "🧬")

st.markdown("""
**Muammo:** yangi dori yaratish 10–15 yil va milliardlab dollar talab qiladi, nomzodlarning
aksariyati klinik bosqichlarda — ko'pincha samarasizlik yoki toksiklik tufayli — to'xtaydi.

**Yechim:** DoriAI dori kashfiyotining 5 ta bosqichini bitta platformada AI bilan tezlashtiradi:
""")

c = st.columns(5)
cards = [
    ("🔬", "Molekula tahlili", "Dori-o'xshashlik, ADMET, toksiklik — soniyalarda"),
    ("🧪", "Virtual skrining", "Minglab birikmalarni saralash va reytinglash"),
    ("💊", "Drug repurposing", "Tasdiqlangan dorilarga yangi qo'llanish topish"),
    ("📋", "Klinik reja", "ClinicalTrials.gov tahlili + protokol loyihasi"),
    ("📚", "Ilmiy tahlil", "PubMed adabiyotlarini AI bilan umumlashtirish"),
]
for col, (icon, title, desc) in zip(c, cards):
    col.markdown(f"### {icon}\n**{title}**\n\n{desc}")

st.divider()
st.subheader("Tizim holati")
pred, lib = get_predictor(), get_library()
s1, s2, s3 = st.columns(3)
s1.metric("ADMET modellari", len(pred.available))
s2.metric("Dorilar kutubxonasi", len(lib), help=f"Manba: {lib.source}")
s3.metric("LLM", "ulangan" if llm.is_configured() else "o'chiq")

if not pred.available:
    st.warning("ADMET modellari hali o'qitilmagan: `python scripts/download_datasets.py` va "
               "`python scripts/train_admet.py` buyruqlarini bajaring.")
else:
    with st.expander("Modellar sifati (scaffold split, test to'plam)"):
        st.dataframe(pred.metrics(), use_container_width=True)

st.caption(DISCLAIMER)
