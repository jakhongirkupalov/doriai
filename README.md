# 🧬 DoriAI — kimyoviy birikmalarni laboratoriyadan oldin baholash

> Umummilly AI Xakaton, Xorazm bosqichi · **Tibbiyot treki**

Yangi dori yaratish **10–15 yil** va milliardlab dollar talab qiladi. Klinik nomzodlarning taxminan 90 foizi
sinovlarda to'xtaydi — ko'pincha samarasizlik yoki toksiklik tufayli, ya'ni oldinroq aniqlanishi mumkin
bo'lgan sabablar bilan.

**DoriAI** — tadqiqotchi molekulani sintez qilishdan oldin uning dori bo'lishga yaroqliligini baholaydigan
va mavjud dorilardan yangi qo'llanish nomzodlarini topadigan veb-ilova.

## Modullar

| Modul | Nima qiladi |
| --- | --- |
| 🔬 **Molekula tahlili** | Bitta molekulaning to'liq profili: fizik-kimyoviy xossalar, Lipinski/Veber, QED, sintez qiyinligi, PAINS/Brenk ogohlantirishlari, 15 ta ADMET bashorati va izohlanuvchi **DoriAI Score** (0–100) |
| 🧪 **Virtual skrining** | Molekulalar ro'yxatini (CSV) baholab reyting tuzadi, toksik va "yolg'on-musbat" nomzodlarni ajratadi |
| 💊 **Drug repurposing** | Kasallik nishonini tanlab (tayyor ro'yxat yoki ChEMBL qidiruvi), **3311 ta tasdiqlangan dori** orasidan nomzod topadi. Har bir nomzod nishonga ta'sir kuchi va xavfsizlik (DoriAI Score) bo'yicha baholanadi |

Keyingi bosqich (kod tayyor, `app/kelajak/`): klinik tadqiqotni rejalashtirish (ClinicalTrials.gov) va
ilmiy adabiyot tahlili (PubMed).

## AI qismi: o'zimiz o'qitgan modellar

Tayyor AI xizmatlariga so'rov yuborilmaydi. Barcha bashorat qiluvchi modellar ochiq ilmiy ma'lumotlarda
**o'zimiz tomonimizdan o'qitilgan** (Random Forest, scikit-learn).

| Model | Ma'lumot | Natija |
| --- | --- | --- |
| EGFR faolligi (repurposing namunasi) | ChEMBL, 1985 molekula | R² = 0.72, RMSE = 0.68 (5-fold CV) |
| Suvda eruvchanlik | ESOL, 1128 molekula | R² = 0.78 |
| Klinik toksiklik xavfi | ClinTox, 1480 molekula | ROC-AUC = 0.70 |
| Toksiklik mexanizmlari (12 ta) | Tox21, ~7800 molekula | `models/admet/metrics.json` |

ADMET modellari **scaffold split** bilan baholangan: test to'plamiga faqat o'qitishda uchramagan kimyoviy
skeletlar tushadi. Bu natijalarni real laboratoriya sharoitiga yaqinlashtiradi.

## Ishga tushirish

```bash
git clone https://github.com/jakhongirkupalov/doriai.git
cd doriai
python -m venv .venv
source .venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt      # paketning o'zi ham o'rnatiladi

streamlit run app/Home.py
```

O'qitilgan modellar va dorilar kutubxonasi repozitoriyada mavjud, qayta o'qitish shart emas.
Modellarni noldan qayta yaratish uchun:

```bash
python scripts/download_datasets.py
python scripts/train_admet.py
python scripts/fetch_approved_drugs.py
```

## Texnologiyalar

Python · RDKit · scikit-learn · pandas · Streamlit · Plotly · ChEMBL API

## Ma'lumot manbalari

ChEMBL (EMBL-EBI, CC BY-SA 3.0) · MoleculeNet: ESOL, BBBP, ClinTox, Tox21 (NIH/EPA/FDA) · RDKit (BSD)

## Cheklovlar

- Modellar molekulaning 2D tuzilishiga asoslanadi; 3D docking hisobga olinmaydi.
- DoriAI Score umumiy maqsadli dorilar uchun sozlangan; onkologik dorilar sitotoksikligi tufayli past baholanishi mumkin.
- Bashoratlar laboratoriya tajribasini almashtirmaydi — ular qaysi birikmani birinchi navbatda tekshirishni tanlashga yordam beradi.

## Mas'uliyat cheklovi

DoriAI — tadqiqot uchun qarorni qo'llab-quvvatlovchi vosita. Tibbiy tavsiya hisoblanmaydi.
