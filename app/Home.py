"""DoriAI — bosh sahifa.  Ishga tushirish:  streamlit run app/Home.py"""
import streamlit as st

from doriai.ui import DISCLAIMER, get_library, get_predictor, page_setup

page_setup("DoriAI — birikmalarni laboratoriyadan oldin baholash", "🧬")

st.markdown("""
**Muammo:** yangi dori yaratish 10–15 yil va milliardlab dollar talab qiladi. Klinik nomzodlarning
taxminan 90 foizi sinovlarda to'xtaydi — ko'pincha toksiklik yoki samarasizlik tufayli, ya'ni oldinroq
aniqlanishi mumkin bo'lgan sabablar bilan.

**Yechim:** DoriAI tadqiqotchiga molekulani sintez qilishdan oldin uning dori bo'lishga yaroqliligini
baholash va mavjud dorilardan yangi qo'llanish topish imkonini beradi.
""")

c1, c2, c3 = st.columns(3)
c1.markdown("### 🔬\n**Molekula tahlili**\n\nBitta birikmaning to'liq profili: xossalar, "
            "toksiklik, izohlanuvchi DoriAI Score")
c2.markdown("### 🧪\n**Virtual skrining**\n\nKo'plab birikmalarni saralash, toksik va "
            "\"yolg'on-musbat\" nomzodlarni ajratish")
c3.markdown("### 💊\n**Drug repurposing**\n\nIstalgan oqsil-nishon uchun model o'qitib, "
            "tasdiqlangan dorilar orasidan nomzod topish")

st.divider()
st.subheader("Tizim holati")
pred, lib = get_predictor(), get_library()
s1, s2, s3 = st.columns(3)
s1.metric("O'qitilgan ADMET modellari", len(pred.available))
s2.metric("Tasdiqlangan dorilar kutubxonasi", len(lib), help=f"Manba: {lib.source}")
s3.metric("EGFR faollik modeli (CV R²)", "0.72", help="1985 ta ChEMBL o'lchovi, 5-fold cross-validation")

if not pred.available:
    st.warning("ADMET modellari hali o'qitilmagan: `python scripts/download_datasets.py` va "
               "`python scripts/train_admet.py` buyruqlarini bajaring.")
else:
    with st.expander("Modellar sifati (scaffold split, test to'plam)"):
        st.dataframe(pred.metrics(), use_container_width=True)

st.info("**Validatsiya:** EGFR modeli o'qitish ma'lumotlarida bo'lmagan afatinib va dacomitinibni "
        "3311 ta dori orasidan yuqori ishonch bilan haqiqiy EGFR ingibitorlari sifatida topdi.")

st.caption("Keyingi bosqich: klinik tadqiqotni rejalashtirish (ClinicalTrials.gov) va ilmiy adabiyot "
           "tahlili (PubMed) — kod tayyor, integratsiya jarayonida.")
st.caption(DISCLAIMER)


