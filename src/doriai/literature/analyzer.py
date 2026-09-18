"""Ilmiy adabiyotlarni tahlil qilish: trendlar, kalit atamalar va LLM xulosasi."""
from __future__ import annotations

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from doriai.llm import client as llm


def top_terms(docs: list[str], n: int = 25) -> pd.DataFrame:
    docs = [d for d in docs if d]
    if len(docs) < 2:
        return pd.DataFrame(columns=["term", "weight"])
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_df=0.8, min_df=2)
    X = vec.fit_transform(docs)
    weights = X.mean(axis=0).A1
    terms = vec.get_feature_names_out()
    df = pd.DataFrame({"term": terms, "weight": weights})
    return df.sort_values("weight", ascending=False).head(n).reset_index(drop=True)


def year_trend(articles: list[dict]) -> pd.DataFrame:
    years = [a["year"] for a in articles if a.get("year")]
    return pd.Series(years, name="year").value_counts().sort_index().rename_axis("year") \
        .reset_index(name="count")


def summarize(question: str, articles: list[dict], max_articles: int = 15) -> str | None:
    ctx = "\n\n".join(
        f"[PMID {a['pmid']}] ({a.get('year')}) {a['title']}\n{a['abstract'][:1200]}"
        for a in articles[:max_articles] if a.get("abstract")
    )
    prompt = f"""Savol: {question}

Quyidagi PubMed annotatsiyalari asosida tahlil qiling:
1) Asosiy topilmalar (har bir da'vodan keyin [PMID xxxx] manbasini ko'rsating)
2) Istiqbolli molekulalar / mexanizmlar / nishonlar
3) Ziddiyatli yoki yetarli o'rganilmagan jihatlar
4) Keyingi tadqiqot uchun 3 ta aniq taklif

Annotatsiyalar:
{ctx}"""
    return llm.chat(prompt, max_tokens=1800)
