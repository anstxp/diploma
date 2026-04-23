from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from derma_api.app import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture
def synthetic_image_bytes() -> bytes:
    img = Image.new("RGB", (224, 224), (200, 180, 170))
    pixels = img.load()
    for x in range(80, 144):
        for y in range(80, 144):
            r = ((x - 112) ** 2 + (y - 112) ** 2) ** 0.5
            if r < 32:
                pixels[x, y] = (90, 60, 50)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()



def test_healthz(client):
    r = client.get("/derma/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert "model_loaded" in body


def test_info_seven_classes(client):
    r = client.get("/derma/info")
    if r.status_code == 503:
        pytest.skip("Model not loaded — train it first")
    assert r.status_code == 200
    data = r.json()
    expected = {"akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"}
    assert set(data["classes"]) == expected

def test_analyze_returns_valid_response(client, synthetic_image_bytes):
    r = client.post(
        "/derma/analyze",
        files={"image": ("test.jpg", synthetic_image_bytes, "image/jpeg")},
        data={"top_k": 3},
    )
    if r.status_code == 503:
        pytest.skip("Model not loaded")
    assert r.status_code == 200, r.text
    data = r.json()

    assert data["top_class"] in {"akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"}
    assert "confidence" in data and 0 <= data["confidence"] <= 1
    assert "all_probabilities" in data
    total = sum(data["all_probabilities"].values())
    assert abs(total - 1.0) < 0.01
    assert "top_k" in data
    assert len(data["top_k"]) == 3
    probs = [item["probability"] for item in data["top_k"]]
    assert probs == sorted(probs, reverse=True)
    assert data["severity"] in ("critical", "high", "medium", "low")
    if data["top_class"] == "mel":
        assert data["severity"] == "critical"


def test_analyze_grayscale_image(client):
    img = Image.new("L", (300, 300), 128)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    r = client.post(
        "/derma/analyze",
        files={"image": ("gray.jpg", buf.getvalue(), "image/jpeg")},
    )
    if r.status_code == 503:
        pytest.skip("Model not loaded")
    assert r.status_code == 200


def test_analyze_rgba_image(client):
    img = Image.new("RGBA", (224, 224), (200, 100, 80, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    r = client.post(
        "/derma/analyze",
        files={"image": ("rgba.png", buf.getvalue(), "image/png")},
    )
    if r.status_code == 503:
        pytest.skip("Model not loaded")
    assert r.status_code == 200


def test_analyze_invalid_bytes_returns_400(client):
    r = client.post(
        "/derma/analyze",
        files={"image": ("bad.jpg", b"not an image", "image/jpeg")},
    )
    if r.status_code == 503:
        pytest.skip("Model not loaded")
    assert r.status_code == 400



def test_analyze_accepts_ukrainian_sex_label(client, synthetic_image_bytes):
    for sex_input in ("F", "Female", "жінка", "ж", "2"):
        r = client.post(
            "/derma/analyze",
            files={"image": ("test.jpg", synthetic_image_bytes, "image/jpeg")},
            data={"sex": sex_input, "top_k": 1},
        )
        if r.status_code == 503:
            pytest.skip("Model not loaded")
        assert r.status_code == 200, f"sex={sex_input!r} produced {r.status_code}"



def test_calibration_preserves_probability_sum(client, synthetic_image_bytes):
    r = client.post(
        "/derma/analyze",
        files={"image": ("test.jpg", synthetic_image_bytes, "image/jpeg")},
    )
    if r.status_code == 503:
        pytest.skip("Model not loaded")
    data = r.json()
    total = sum(data["all_probabilities"].values())
    assert abs(total - 1.0) < 0.01, \
        f"Calibrated probs should still sum to 1, got {total}"
    probs = [item["probability"] for item in data["top_k"]]
    assert probs == sorted(probs, reverse=True), \
        "top_k must be in descending probability order"
