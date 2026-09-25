# Arxitektura

```
Foydalanuvchi (Streamlit, 5 sahifa)
            │
            ▼
   src/doriai — mustaqil biznes-mantiq (UI'ga bog'liq emas)
   ├── chem/          SMILES → standartlashtirish → deskriptor va fingerprint
   ├── models/        ADMET Random Forest + scaffold split
   ├── screening/     DoriAI Score (izohlanuvchi) + partiyali skrining
   ├── repurposing/   dorilar kutubxonasi + nishonga QSAR model
   ├── trials/        klinik tadqiqot statistikasi, tanlama hajmi, protokol
   ├── literature/    TF-IDF + LLM xulosa
   ├── data_sources/  ChEMBL · ClinicalTrials.gov · PubMed (kesh + retry)
   └── llm/           OpenAI-mos mijoz (Ollama/Groq/OpenRouter)
```

**Nega shunday:** UI va mantiq ajratilgani uchun ertaga Streamlit o'rniga FastAPI qo'yish
yoki modullarni Telegram botga ulash kodni qayta yozishni talab qilmaydi. Har bir tashqi
API javobi `data/cache/` ga yoziladi — demo internetsiz ham ishlaydi.

## Ilmiy jihatdan muhim qarorlar
1. **Scaffold split** — tasodifiy bo'lish modelni sun'iy ravishda yaxshi ko'rsatadi; biz
   yangi kimyoviy skeletlarda baholaymiz, ya'ni real sharoitga yaqin.
2. **Qo'llanish sohasi (applicability domain)** — har bir repurposing bashorati yonida
   o'quv to'plamiga eng yaqin o'xshashlik va ishonch darajasi ko'rsatiladi.
3. **Retrospektiv validatsiya** — model top ro'yxatida allaqachon ma'lum faol dorilarni
   qayta topsa, bu uning ishlayotganining dalili (`known_active` ustuni).
4. **Izohlanuvchanlik** — DoriAI Score komponentlari va og'irliklari ochiq ko'rsatiladi.

## Cheklovlar 
- 2D fingerprint asosidagi modellar; 3D dokking va oqsil strukturasi hisobga olinmaydi.
- ADMET modellari bashorat, o'lchov emas: ROC-AUC ~0,7–0,85 oralig'ida.
- Generativ molekula dizayni MVP'ga kirmagan — keyingi bosqich rejasi.
