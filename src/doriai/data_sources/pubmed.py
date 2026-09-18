"""PubMed (NCBI E-utilities) — biotibbiy ilmiy maqolalar bazasi."""
from __future__ import annotations

import xml.etree.ElementTree as ET

from doriai.config import NCBI_EMAIL
from doriai.data_sources.http import get

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search_ids(term: str, retmax: int = 30) -> list[str]:
    params = {"db": "pubmed", "term": term, "retmax": retmax, "retmode": "json", "sort": "relevance"}
    if NCBI_EMAIL:
        params["email"] = NCBI_EMAIL
    data = get(f"{EUTILS}/esearch.fcgi", params=params)
    return data.get("esearchresult", {}).get("idlist", [])


def parse_pubmed_xml(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    out = []
    for art in root.findall(".//PubmedArticle"):
        pmid = art.findtext(".//MedlineCitation/PMID", default="")
        title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
        abstract = " ".join("".join(t.itertext()) for t in art.findall(".//Abstract/AbstractText"))
        year = art.findtext(".//JournalIssue/PubDate/Year") or \
            (art.findtext(".//JournalIssue/PubDate/MedlineDate") or "")[:4]
        journal = art.findtext(".//Journal/Title", default="")
        out.append({"pmid": pmid, "title": title.strip(), "abstract": abstract.strip(),
                    "year": int(year) if year.isdigit() else None, "journal": journal})
    return out


def fetch_articles(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    text = get(f"{EUTILS}/efetch.fcgi",
               params={"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}, as_json=False)
    return parse_pubmed_xml(text)


def search(term: str, retmax: int = 30) -> list[dict]:
    return fetch_articles(search_ids(term, retmax))
