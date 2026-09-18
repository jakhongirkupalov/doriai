"""ClinicalTrials.gov API v2 — dunyodagi klinik sinovlar reestri.

Hujjat: https://clinicaltrials.gov/data-api/api
"""
from __future__ import annotations

import pandas as pd

from doriai.data_sources.http import get

API = "https://clinicaltrials.gov/api/v2/studies"


def _g(d: dict, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
    return default if d is None else d


def parse_study(study: dict) -> dict:
    ps = study.get("protocolSection", {})
    locations = _g(ps, "contactsLocationsModule", "locations", default=[]) or []
    phases = _g(ps, "designModule", "phases", default=[]) or []
    return {
        "nct_id": _g(ps, "identificationModule", "nctId"),
        "title": _g(ps, "identificationModule", "briefTitle"),
        "status": _g(ps, "statusModule", "overallStatus"),
        "phase": "/".join(phases) if phases else "NA",
        "study_type": _g(ps, "designModule", "studyType"),
        "enrollment": _g(ps, "designModule", "enrollmentInfo", "count"),
        "start_date": _g(ps, "statusModule", "startDateStruct", "date"),
        "completion_date": _g(ps, "statusModule", "primaryCompletionDateStruct", "date"),
        "sponsor": _g(ps, "sponsorCollaboratorsModule", "leadSponsor", "name"),
        "conditions": "; ".join(_g(ps, "conditionsModule", "conditions", default=[]) or []),
        "countries": "; ".join(sorted({l.get("country") for l in locations if l.get("country")})),
        "primary_outcomes": "; ".join(
            o.get("measure", "") for o in
            (_g(ps, "outcomesModule", "primaryOutcomes", default=[]) or [])[:3]),
    }


def search_studies(condition: str, intervention: str | None = None,
                   max_studies: int = 300) -> pd.DataFrame:
    params = {"query.cond": condition, "pageSize": 100, "format": "json"}
    if intervention:
        params["query.intr"] = intervention
    studies, token = [], None
    while len(studies) < max_studies:
        p = dict(params)
        if token:
            p["pageToken"] = token
        data = get(API, params=p)
        studies.extend(data.get("studies", []))
        token = data.get("nextPageToken")
        if not token:
            break
    return pd.DataFrame([parse_study(s) for s in studies[:max_studies]])
