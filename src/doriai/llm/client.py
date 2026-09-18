"""OpenAI-mos Chat Completions mijoz.

Bitta kod bilan ishlaydi: Ollama (ochiq kodli, lokal), Groq, OpenRouter, OpenAI, vLLM.
LLM sozlanmagan bo'lsa None qaytaradi — ilova shablon asosida ishlashda davom etadi.
"""
from __future__ import annotations

import requests

from doriai.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

SYSTEM_SCIENTIST = (
    "Siz farmatsevtika va dori kashfiyoti bo'yicha tajribali tadqiqotchisiz. "
    "Javoblarni o'zbek tilida (lotin yozuvida), aniq va tuzilgan holda bering. "
    "Faqat berilgan ma'lumotlarga tayaning; ishonchingiz komil bo'lmasa, buni ochiq ayting. "
    "Bu tadqiqot yordamchisi, klinik tavsiya emas."
)


def is_configured() -> bool:
    return bool(LLM_BASE_URL and LLM_MODEL)


def chat(user: str, system: str = SYSTEM_SCIENTIST, temperature: float = 0.2,
         max_tokens: int = 1500, timeout: int = 120) -> str | None:
    if not is_configured():
        return None
    headers = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        r = requests.post(f"{LLM_BASE_URL}/chat/completions", json=payload,
                          headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:  # tarmoq yoki kalit xatosi — ilovani yiqitmaymiz
        return f"⚠️ LLM xatosi: {e}"
