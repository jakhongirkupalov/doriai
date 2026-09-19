# DoriAI — final demo ssenariysi

Format: **3 daqiqa taqdimot + 2 daqiqa demo + 2 daqiqa savol-javob.**

## Demo'dan 10 daqiqa oldin

1. `streamlit run app/Home.py` — ilovani ishga tushiring.
2. **Virtual skrining** → "Namuna to'plam" → "Baholash" tugmasini bir marta bosing.
3. **Drug repurposing** → "EGFR — o'pka saratoni" → "Nomzod izlash" tugmasini bosing va **to'liq tugashini kuting** (1–2 daqiqa). Endi model xotirada — demo paytida natija bir zumda chiqadi.
4. Streamlit'ni **to'xtatmang**. Brauzerni bosh sahifaga qaytaring.
5. Zaxira video tayyor turibdimi — tekshiring.

## Taqdimot (3 daqiqa)

**0:00–0:40 — Muammo.** Yangi dori 10–15 yil va milliardlab dollar talab qiladi, klinik nomzodlarning ~90% sinovlarda to'xtaydi — ko'pincha toksiklik yoki samarasizlik tufayli. Tadqiqotchi qaysi birikmaga oylar sarflashni hozir ko'pincha intuitsiya bilan tanlaydi.

**0:40–1:20 — Yechim.** DoriAI birikmalarni laboratoriyadan oldin baholaydi: xavfsizlik, dori-o'xshashlik, sintez qulayligi. Mavjud dorilar orasidan yangi kasallik uchun nomzod ham topadi. Barcha bashoratlar ochiq ilmiy ma'lumotlarda **o'zimiz o'qitgan 15 ta model** asosida.

**1:20–2:30 — Asosiy dalil.** EGFR nishonida model 3311 ta tasdiqlangan dori orasidan o'qitishda **ko'rmagan** afatinib va dacomitinibni haqiqiy EGFR dorilari sifatida topdi. COX-2 nishonida — mefenam kislotani. Ikki mustaqil kasallik nishonida bir xil natija.

**2:30–3:00 — Kim uchun.** Institut va universitet tadqiqot guruhlari. Xorijiy dasturlar qimmat, bepul vositalar dasturlashni talab qiladi, LLM'lar esa e'lon qilinmagan molekulani tashqi serverga yuborishni talab qiladi. DoriAI institut ichida ishlaydi va o'zbek tilida.

## Demo (2 daqiqa)

**1. Virtual skrining (40 soniya).**
Natija allaqachon ekranda. Ko'rsating:
- Yashil — ibuprofen, kofein, **harmin (isiriq alkaloidi)**: "Mahalliy o'simlik birikmasi istiqbolli chiqdi."
- Qizil — nitrobenzol: "Toksik fragment."
- Qizil — rodanin va kversetin, "⛔ Yolg'on-musbat xavfi (PAINS)" belgisi bilan: "Bular laboratoriya testlarini aldaydi — testda faol ko'rinadi, aslida emas."
- "Yolg'on-musbat natija beruvchilarni chiqarish" belgisini qo'ying — rodanin va kversetin yo'qoladi: "Tizim ularni laboratoriyaga yuborishdan oldin ajratadi."

**2. Drug repurposing (60 soniya).**
"EGFR — o'pka saratoni" → "Nomzod izlash" (natija xotirada, bir zumda chiqadi). Ko'rsating:
- **Model aniqligi: R² 0.72 — yaxshi.**
- **Yashil xabar:** "Model o'qitishda ko'rmagan afatinib va dacomitinibni topdi. Biz unga bu dorilarning nomini aytmadik."
- **Xavfsizlik ustuni:** "Har bir nomzod skrining moduli bilan xavfsizlik bo'yicha ham baholanadi — ta'sir qiladimi VA xavfsizmi."

**3. Yakun (20 soniya).**
"Tizim o'z chegarasini ham biladi: past ishonchli bashoratlar yashiriladi, har bir natija yonida ishonch darajasi turadi."

## Savol-javob (2 daqiqa) — qisqa javoblar

**Nega LLM'ga tashlamadingiz?**
LLM matn yozadi, hisoblamaydi. Bizning modellar laboratoriya o'lchovlarida o'qitilgan, aniqligi raqam bilan o'lchangan va har safar bir xil natija beradi. E'lon qilinmagan molekula esa tashqi serverga chiqmaydi.

**Model qanchalik aniq?**
EGFR R² 0.72, eruvchanlik R² 0.78, klinik toksiklik ROC-AUC 0.70. Scaffold split bilan — model o'zi ko'rmagan kimyoviy sinflarda tekshirilgan.

**Model xato qiladimi?**
Ha. Paklitaksel EGFR ingibitori emas, lekin model uni yuqori baholadi — chunki o'qitishdagi dotsetakselga juda o'xshaydi. Xatosini tushuntirib bera oladigan tizim — ishonchli tizim.

**Cheklovlar?**
Faollik samaradorlikni kafolatlamaydi; 3D docking yo'q; ball og'irliklari ekspert bahosi asosida, ularni ClinTox datasetida validatsiya qilish keyingi qadam.

**Kim to'laydi?**
Institutlar grant loyihalari orqali; korporativ mijozlar — o'z serverida o'rnatish uchun. Narxni pilot bosqichida aniqlaymiz.

