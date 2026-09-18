# 7 daqiqalik final demo ssenariysi (3 taqdimot + 2 demo + 2 savol-javob)

**0:00–0:40 — Muammo.** Bitta dori = 10–15 yil, ~2 mlrd $; nomzodlarning ~90% klinik
bosqichda to'xtaydi. Xatolar kech aniqlangani uchun qimmatga tushadi.

**0:40–1:20 — Yechim.** DoriAI kashfiyot voronkasining 5 bosqichini bitta platformaga
birlashtiradi va xavfli nomzodni birinchi kunda ajratadi.

**1:20–3:00 — Demo 1 (skrining).** `data/seed/demo_compounds.csv` yuklanadi.
Ko'rsatish kerak: PAINS bayrog'i bilan rodanin va nitrobenzol pastga tushadi, kurkumin
PAINS sifatida belgilanadi (adabiyotdagi mashhur muammo — bu tizim ishlayotganining dalili).

**3:00–4:30 — Demo 2 (repurposing).** Nishon: EGFR → model o'qitiladi → top-25.
Asosiy jumla: "model ro'yxatida ma'lum EGFR ingibitorlari qayta topildi — demak reyting
tasodifiy emas; `known_active=False` bo'lganlar esa tekshirishga arzigulik gipotezalar".

**4:30–5:30 — Demo 3 (klinik reja).** Kasallik + dori → benchmark, tanlama hajmi,
protokol sinopsisi. "Bu bir haftalik analitik ishni 30 soniyaga qisqartiradi."

**5:30–6:00 — Biznes va ta'sir.** B2B SaaS: farma kompaniyalar, universitet laboratoriyalari,
Sog'liqni saqlash vazirligi tadqiqot markazlari. O'zbekistonda mahalliy o'simlik birikmalarini
(isiriq, shirinmiya, yantoq) tizimli skrining qilish — hozir hech kim qilmayotgan ish.

**6:00–7:00 — Savol-javob.** Tayyor javoblar: model aniqligi (scaffold split raqamlari),
cheklovlar (2D, dokking yo'q), keyingi qadam (generativ dizayn, 3D dokking), ma'lumot litsenziyalari.
