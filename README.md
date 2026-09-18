# 🧬 DoriAI — AI yordamida dori kashfiyotini tezlashtirish

> Umummilly AI Xakaton, Xorazm bosqichi · **Tibbiyot treki** 

Yangi dori yaratish **10–15 yil** va milliardlab dollar talab qiladi; nomzodlarning katta qismi
samarasizlik yoki toksiklik tufayli klinik bosqichda to'xtaydi. DoriAI shu voronkaning
**eng qimmat xatolarini erta bosqichda** aniqlaydi va 5 ta bosqichni bitta platformada birlashtiradi.

| Modul | Nima qiladi | Texnologiya |
|---|---|---|
| 🔬 Molekula tahlili | Lipinski/Veber, QED, SA score, PAINS/Brenk, ADMET profil, izohlanuvchi **DoriAI Score** | RDKit + Random Forest |
| 🧪 Virtual skrining | Minglab birikmani saralab, reyting va filtrlar | ECFP4 fingerprint + ML |
| 💊 Drug repurposing | Nishonga (ChEMBL) model o'qitib, tasdiqlangan dorilarni qayta qo'llash gipotezalari | QSAR + Tanimoto |
| 📋 Klinik reja | ClinicalTrials.gov benchmark, tanlama hajmi, protokol sinopsisi | API v2 + LLM |
| 📚 Ilmiy tahlil | PubMed trendlari, TF-IDF atamalar, manbali AI xulosa | E-utilities + LLM |

## Tez start

```bash
git clone <repo> && cd doriai
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .

python scripts/download_datasets.py        # ochiq datasetlar (~10 MB)
python scripts/train_admet.py --tasks solubility bbbp clintox   # tezkor variant
python scripts/fetch_approved_drugs.py     # ixtiyoriy: ChEMBL kutubxonasi
cp .env.example .env                       # ixtiyoriy: LLM kaliti

streamlit run app/Home.py
```

## Ma'lumot manbalari
ChEMBL (CC BY-SA 3.0) · MoleculeNet / DeepChem (MIT) · ClinicalTrials.gov API v2 · PubMed E-utilities · RDKit (BSD).

## Mas'uliyat cheklovi
DoriAI — **tadqiqot uchun qarorni qo'llab-quvvatlovchi vosita**. Bashoratlar laboratoriya
tajribalari va klinik tekshiruvni almashtirmaydi va tibbiy tavsiya hisoblanmaydi.
