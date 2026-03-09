from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

from fastapi.testclient import TestClient

from chem_api.app import create_app


@pytest.fixture(scope="module")
def client():
    return TestClient(create_app())



class TestMetaEndpoints:

    def test_health(self, client):
        r = client.get("/chem/health")
        assert r.status_code == 200

    def test_info(self, client):
        r = client.get("/chem/info")
        assert r.status_code == 200
        body = r.json()
        assert body

    def test_labs_list(self, client):
        r = client.get("/chem/labs")
        assert r.status_code == 200
        body = r.json()
        assert body

    def test_labs_detail(self, client):
        r = client.get("/chem/labs/glucose")
        assert r.status_code == 200
        body = r.json()
        assert "glucose" in str(body).lower()

    def test_labs_detail_unknown(self, client):
        r = client.get("/chem/labs/nonexistent_lab_xyz")
        assert r.status_code in (400, 404, 422)

    def test_openapi_json(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        spec = r.json()
        paths = spec.get("paths", {})
        assert "/chem/analyze" in paths
        assert "/chem/analyze/narrative" in paths



class TestAnalyzeEndpoint:

    def test_normal_payload(self, client):
        r = client.post("/chem/analyze", json={
            "sex": "male", "age": 35,
            "glucose": 95, "creatinine": 1.0, "alt": 25,
        })
        assert r.status_code == 200
        body = r.json()
        assert body.get("version") or body.get("result", {}).get("version")

    def test_diabetes_detected(self, client):
        r = client.post("/chem/analyze", json={
            "sex": "female", "age": 58,
            "glucose": 180, "a1c": 8.5,
        })
        assert r.status_code == 200
        body = r.json()
        data = body.get("result") if "result" in body else body
        sig_ids = {s["id"] for s in data.get("signals", [])}
        assert "glucose_diabetes_range" in sig_ids or "a1c_diabetes_range" in sig_ids

    def test_empty_payload_accepted(self, client):
        r = client.post("/chem/analyze", json={"sex": "male", "age": 30})
        assert r.status_code == 200



class TestNarrativeEndpoint:

    def test_narrative_default_lang(self, client):
        r = client.post("/chem/analyze/narrative", json={
            "sex": "female", "age": 28,
            "ferritin": 9, "iron": 40, "tibc": 460,
        })
        assert r.status_code == 200

    def test_narrative_en_lang(self, client):
        r = client.post("/chem/analyze/narrative?lang=en", json={
            "sex": "female", "age": 28,
            "ferritin": 9, "iron": 40, "tibc": 460,
        })
        assert r.status_code == 200
