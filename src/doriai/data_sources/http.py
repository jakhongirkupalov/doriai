"""Tashqi API'lar uchun umumiy HTTP yordamchi: qayta urinish + diskka keshlash.

Kesh xakatonda juda muhim: internet uzilsa ham demo avval so'ralgan
natijalar bilan ishlayveradi.
"""
from __future__ import annotations

import hashlib
import json
import time

import requests

from doriai.config import CACHE_DIR, HTTP_TIMEOUT

_session = requests.Session()
_session.headers.update({"User-Agent": "DoriAI-MVP/0.1 (hackathon research prototype)"})


def _cache_path(url: str, params: dict | None):
    key = hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()
    return CACHE_DIR / f"{key}.cache"


def get(url: str, params: dict | None = None, as_json: bool = True,
        use_cache: bool = True, retries: int = 3):
    path = _cache_path(url, params)
    if use_cache and path.exists():
        text = path.read_text(encoding="utf-8")
        return json.loads(text) if as_json else text

    last_err = None
    for attempt in range(retries):
        try:
            r = _session.get(url, params=params, timeout=HTTP_TIMEOUT)
            if r.status_code == 429:  # rate limit — biroz kutamiz
                time.sleep(2 * (attempt + 1))
                continue
            r.raise_for_status()
            if use_cache:
                path.write_text(r.text, encoding="utf-8")
            return r.json() if as_json else r.text
        except requests.RequestException as e:
            last_err = e
            time.sleep(1 + attempt)
    raise ConnectionError(f"So'rov bajarilmadi: {url} ({last_err})")
