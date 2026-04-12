from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from neuro_api.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())


class TestMetaEndpoints:

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_healthz(self, client):
        r = client.get("/neuro/healthz")
        assert r.status_code == 200

    def test_info(self, client):
        r = client.get("/neuro/info")
        assert r.status_code == 200
        body = r.json()
        assert body

    def test_openapi_json(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        spec = r.json()
        paths = spec.get("paths", {})
        assert "/neuro/analyze" in paths
        assert "/neuro/analyze/narrative" in paths


class TestAnalyzeEndpoint:

    def test_normal_payload(self, client):
        r = client.post("/neuro/analyze", json={
            "sex": 1, "age": 50,
            "bmi": 26, "sbp": 130,
            "glucose": 95, "hgb": 14.5, "tchol": 200, "hdl": 50,
            "crp": 1.5,
        })
        assert r.status_code == 200
        body = r.json()
        assert body

    def test_at_risk_patient(self, client):
        r = client.post("/neuro/analyze", json={
            "sex": 2, "age": 50, "bmi": 32,
            "sbp": 145, "glucose": 115, "a1c": 6.0,
            "tchol": 220, "hdl": 38, "trigly": 240,
            "crp": 6.5, "vitd_25oh": 14,
            "income_ratio": 1.2,
        })
        assert r.status_code == 200

    def test_seven_targets_in_response(self, client):
        r = client.post("/neuro/analyze", json={
            "sex": 1, "age": 50, "bmi": 26, "sbp": 130,
            "glucose": 95, "tchol": 200, "hdl": 50,
        })
        assert r.status_code == 200
        body = r.json()
        body_str = str(body).lower()
        for target in ("depression", "sleep", "daytime", "suicidal", "snore"):
            assert target in body_str

    def test_empty_payload_accepted(self, client):
        r = client.post("/neuro/analyze", json={})
        assert r.status_code == 200


class TestNarrativeEndpoint:

    def test_narrative_default_lang(self, client):
        r = client.post("/neuro/analyze/narrative", json={
            "sex": 2, "age": 50, "bmi": 32,
            "sbp": 145, "glucose": 115,
            "tchol": 220, "hdl": 38, "crp": 6.5,
        })
        assert r.status_code == 200

    def test_narrative_en_lang(self, client):
        r = client.post("/neuro/analyze/narrative?lang=en", json={
            "sex": 2, "age": 50, "bmi": 32,
            "sbp": 145, "glucose": 115,
            "tchol": 220, "hdl": 38, "crp": 6.5,
        })
        assert r.status_code == 200

    def test_narrative_empty_payload(self, client):
        r = client.post("/neuro/analyze/narrative", json={})
        assert r.status_code == 200
