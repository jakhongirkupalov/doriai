"""Loyiha bo'yicha umumiy sozlamalar: papkalar yo'llari va muhit o'zgaruvchilari.

Barcha modullar yo'llarni shu yerdan oladi — shunda loyiha qaysi papkadan
ishga tushirilishidan qat'i nazar, fayllar to'g'ri joyda saqlanadi.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# src/doriai/config.py -> parents[2] = loyiha ildizi
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"            # yuklab olingan xom datasetlar
PROCESSED_DIR = DATA_DIR / "processed"  # tozalangan / tayyor ma'lumotlar
SEED_DIR = DATA_DIR / "seed"          # repoda saqlanadigan kichik boshlang'ich fayllar
CACHE_DIR = DATA_DIR / "cache"        # API javoblari keshi
MODELS_DIR = ROOT_DIR / "models"
ADMET_DIR = MODELS_DIR / "admet"      # o'qitilgan ADMET modellari

for _d in (RAW_DIR, PROCESSED_DIR, SEED_DIR, CACHE_DIR, ADMET_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# LLM (OpenAI-mos endpoint: Ollama, Groq, OpenRouter, OpenAI ...)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").rstrip("/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "")

NCBI_EMAIL = os.getenv("NCBI_EMAIL", "")
HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))
RANDOM_STATE = 42
