from __future__ import annotations

import pytest

from fastapi.testclient import TestClient

from risk_api.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())



class TestMetaEndpoints:

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_healthz(self, client):
        r = client.get("/risk/healthz")
        assert r.status_code == 200

    def test_info(self, client):
        r = client.get("/risk/info")
        assert r.status_code == 200
        body = r.json()
        assert body

    def test_openapi_json(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        spec = r.json()
        paths = spec.get("paths", {})
        assert "/risk/analyze" in paths
        assert "/risk/analyze/narrative" in paths



class TestAnalyzeEndpoint:

    def test_normal_payload(self, client):
        r = client.post("/risk/analyze", json={
            "sex": 1, "age": 50,
            "bmi": 26, "sbp": 130, "dbp": 82,
            "glucose": 95, "a1c": 5.6,
            "creatinine": 1.0,
            "tchol": 200, "hdl": 50, "trigly": 130,
        })
        assert r.status_code == 200
        body = r.json()
        assert "risks" in body or "result" in body

    def test_diabetic_high_risk_detected(self, client):
        r = client.post("/risk/analyze", json={
            "sex": 2, "age": 65, "bmi": 35,
            "glucose": 220, "a1c": 9.5,
            "sbp": 165, "dbp": 100,
            "creatinine": 1.4,
            "tchol": 260, "hdl": 32, "trigly": 320,
        })
        assert r.status_code == 200

    def test_six_targets_in_response(self, client):
        r = client.post("/risk/analyze", json={
            "sex": 1, "age": 50, "bmi": 26, "sbp": 130,
            "glucose": 95, "tchol": 200, "hdl": 50,
        })
        assert r.status_code == 200
        body = r.json()
        body_str = str(body).lower()
        for target in ("htn", "diabetes", "chol", "chd", "chf", "stroke"):
            assert target in body_str

    def test_dropped_keys_surfaced(self, client):
        r = client.post("/risk/analyze", json={
            "sex": 1, "age": 50,
            "glucose": "totally garbage",
            "sbp": 130, "bmi": 26, "hdl": 50, "tchol": 200,
        })
        assert r.status_code == 200



class TestNarrativeEndpoint:

    def test_narrative_default_lang(self, client):
        r = client.post("/risk/analyze/narrative", json={
            "sex": 2, "age": 58, "bmi": 32,
            "sbp": 145, "glucose": 180, "a1c": 8.5,
            "tchol": 220, "hdl": 38,
        })
        assert r.status_code == 200

    def test_narrative_en_lang(self, client):
        r = client.post("/risk/analyze/narrative?lang=en", json={
            "sex": 2, "age": 58, "bmi": 32,
            "sbp": 145, "glucose": 180, "a1c": 8.5,
            "tchol": 220, "hdl": 38,
        })
        assert r.status_code == 200

    def test_narrative_empty_payload(self, client):
        r = client.post("/risk/analyze/narrative", json={})
        assert r.status_code == 200
