"""RDKit talab qilmaydigan testlar: statistika va API javoblarini tahlil qilish."""
import pandas as pd
import pytest

from doriai.data_sources.clinicaltrials import parse_study
from doriai.data_sources.pubmed import parse_pubmed_xml
from doriai.trials.planner import sample_size_two_proportions, trial_statistics, with_dropout


def test_sample_size_known_value():
    # Klassik misol: 50% vs 30%, alpha=0.05, quvvat=80% -> har guruhda 93
    assert sample_size_two_proportions(0.5, 0.3) == 93


def test_sample_size_invalid():
    with pytest.raises(ValueError):
        sample_size_two_proportions(0.3, 0.3)


def test_dropout():
    assert with_dropout(85, 0.15) == 100


STUDY = {"protocolSection": {
    "identificationModule": {"nctId": "NCT000001", "briefTitle": "Test"},
    "statusModule": {"overallStatus": "COMPLETED",
                     "startDateStruct": {"date": "2020-01"},
                     "primaryCompletionDateStruct": {"date": "2021-01"}},
    "designModule": {"phases": ["PHASE2"], "studyType": "INTERVENTIONAL",
                     "enrollmentInfo": {"count": 120}},
    "conditionsModule": {"conditions": ["Diabetes"]},
    "contactsLocationsModule": {"locations": [{"country": "Uzbekistan"}]},
}}


def test_parse_study_and_stats():
    row = parse_study(STUDY)
    assert row["nct_id"] == "NCT000001" and row["phase"] == "PHASE2"
    assert row["countries"] == "Uzbekistan"
    stats = trial_statistics(pd.DataFrame([row, {**row, "nct_id": "NCT2", "status": "TERMINATED"}]))
    assert stats["completion_rate"] == 0.5
    assert stats["by_phase"].iloc[0]["median_enrollment"] == 120


def test_parse_study_missing_fields():
    assert parse_study({})["nct_id"] is None


PUBMED_XML = """<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID>
<Article><Journal><Title>J Test</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
<ArticleTitle>Metformin in <i>cancer</i></ArticleTitle>
<Abstract><AbstractText>Part one.</AbstractText><AbstractText>Part two.</AbstractText></Abstract>
</Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""


def test_parse_pubmed():
    a = parse_pubmed_xml(PUBMED_XML)[0]
    assert a["pmid"] == "123" and a["year"] == 2024
    assert a["title"] == "Metformin in cancer"
    assert a["abstract"] == "Part one. Part two."
