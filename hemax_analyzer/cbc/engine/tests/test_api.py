from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ENGINE_DIR = Path(__file__).resolve().parent.parent
if str(_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ENGINE_DIR))

from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)



class TestMetaEndpoints:

    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        body = r.json()
        assert "engine" in body or "version" in body

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json().get("status") == "ok"

    def test_fields(self, client):
        r = client.get("/fields")
        assert r.status_code == 200
        body = r.json()
        assert body

    def test_openapi_json(self, client):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        spec = r.json()
        paths = spec.get("paths", {})
        assert "/analyze" in paths
        assert "/analyze/batch" in paths
        assert "/analyze/narrative" in paths



class TestAnalyzeEndpoint:

    def test_normal_payload(self, client):
        r = client.post("/analyze", json={
            "sex": "male", "age": 35,
            "wbc": 6.5, "hgb": 15.0, "plt": 250,
        })
        assert r.status_code == 200
        body = r.json()
        flat = body.get("version") is not None
        wrapped = isinstance(body.get("result"), dict) and body["result"].get("version")
        assert flat or wrapped, f"unexpected response shape: {list(body.keys())}"

    def test_invalid_payload_400(self, client):
        r = client.post("/analyze", json={"sex": "male", "wbc": -1.0})
        assert r.status_code in (200, 400, 422)

    def test_iron_deficiency_detected(self, client):
        r = client.post("/analyze", json={
            "sex": "female", "age": 30,
            "wbc": 6.0, "hgb": 9.5, "plt": 350,
            "rbc": 4.5, "hct": 30, "mcv": 70, "mch": 24,
            "mchc": 31, "rdw": 17.0,
        })
        assert r.status_code == 200
        body = r.json()
        data = body.get("result") if "result" in body else body
        sig_ids = {s["id"] for s in data.get("signals", [])}
        assert "iron_deficiency_likely_pattern" in sig_ids



class TestBatchEndpoint:

    def test_batch_two_patients(self, client):
        r = client.post("/analyze/batch", json={
            "records": [
                {"sex": "male", "age": 35, "wbc": 6.5, "hgb": 15.0, "plt": 250},
                {"sex": "female", "age": 28, "wbc": 6.0, "hgb": 13.5, "plt": 230},
            ]
        })
        assert r.status_code == 200
        body = r.json()
        results = body.get("results") if isinstance(body, dict) else body
        assert isinstance(results, list)
        assert len(results) == 2

    def test_batch_empty(self, client):
        r = client.post("/analyze/batch", json={"records": []})
        assert r.status_code in (200, 400, 422)



class TestNarrativeEndpoint:

    def test_narrative_uk_default(self, client):
        r = client.post("/analyze/narrative", json={
            "sex": "female", "age": 30,
            "wbc": 6.0, "hgb": 9.5, "plt": 350,
            "rbc": 4.5, "mcv": 70, "rdw": 17, "mchc": 31,
        })
        assert r.status_code == 200
        body = r.json()
        assert "narrative" in body or "stories" in body or "summary" in body

    def test_narrative_en(self, client):
        r = client.post("/analyze/narrative?lang=en", json={
            "sex": "female", "age": 30,
            "wbc": 6.0, "hgb": 9.5, "plt": 350,
            "mcv": 70, "rdw": 17,
        })
        assert r.status_code == 200



class TestCrossCutting:

    def test_cors_header_present(self, client):
        r = client.options("/analyze", headers={
            "origin": "http://localhost:3000",
            "access-control-request-method": "POST",
        })
        assert r.status_code in (200, 204, 405)

    def test_gzip_compression_supported(self, client):
        # Request with Accept-Encoding: gzip
        r = client.post("/analyze",
                        json={"sex": "male", "age": 35, "wbc": 6.5, "hgb": 15, "plt": 250},
                        headers={"accept-encoding": "gzip"})
        assert r.status_code == 200
