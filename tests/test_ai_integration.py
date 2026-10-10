from __future__ import annotations

import base64
import json

from fastapi.testclient import TestClient

from app import database, vision, semantic
from app import main as main_module
from app.main import app, IMAGES


client = TestClient(app)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_gemini_vision_provider_parses_structured_response(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    payload = {
        "candidates": [{
            "content": {"parts": [{"text": json.dumps({
                "subject": "red fox", "category": "animal",
                "attributes": ["orange fur", "forest"],
                "caption": "A red fox standing in a forest", "confidence": 0.96
            })}]}
        }]
    }
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        captured["payload"] = kwargs["json"]
        return FakeResponse(payload)

    monkeypatch.setattr(vision.httpx, "post", fake_post)
    result = vision.analyze_image(b"fake-image-bytes", "image/png")
    assert captured["headers"]["x-goog-api-key"] == "test-key"
    assert result["subject"] == "red fox"
    assert result["confidence"] == 0.96
    assert captured["payload"]["contents"][0]["parts"][1]["inline_data"]["data"] == base64.b64encode(b"fake-image-bytes").decode()


def test_upload_endpoint_runs_vision_and_persists_image(monkeypatch, tmp_path):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "restart-test.db")
    database.init_db()
    monkeypatch.setattr(main_module, "vision_analyze", lambda content, mime: {
        "subject": "red fox", "category": "animal",
        "attributes": ["orange fur"], "caption": "A red fox in woodland",
        "confidence": 0.95,
    })
    database.clear_demo_state()
    IMAGES.clear()

    response = client.post(
        "/images/upload",
        files={"file": ("fox.png", b"\x89PNG\r\n\x1a\nfake-png-content", "image/png")},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["metadata"]["subject"] == "red fox"
    assert (tmp_path / "uploads" / f"{payload['id']}.png").read_bytes() == b"\x89PNG\r\n\x1a\nfake-png-content"
    assert any(item["id"] == payload["id"] for item in client.get("/images").json()["images"])

    # Complete the upload-to-match workflow using the explicit offline baseline.
    match = client.post(
        "/posts/fox-post/match",
        json={"post_id": "fox-post", "text": "red fox in woodland", "threshold": 0.0},
    )
    assert match.status_code == 200, match.text
    assert match.json()["suggestion"]["image_id"] == payload["id"]

    # Simulate a fresh process rebuilding its in-memory catalogue from SQLite.
    IMAGES.clear()
    IMAGES.extend(main_module._image_from_record(row) for row in database.load_images())
    assert any(image.id == payload["id"] and image.subject == "red fox" for image in IMAGES)


def test_gemini_embedding_provider_parses_vectors(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    captured = {}

    def fake_post(url, **kwargs):
        captured["headers"] = kwargs["headers"]
        captured["payload"] = kwargs["json"]
        return FakeResponse({"embeddings": [{"values": [1.0, 0.0]}, {"values": [0.0, 1.0]}]})

    monkeypatch.setattr(semantic.httpx, "post", fake_post)
    vectors = semantic._embed_batch(["fox article", "fox caption"])
    assert captured["headers"]["x-goog-api-key"] == "test-key"
    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    assert captured["payload"]["requests"][0]["taskType"] == "RETRIEVAL_QUERY"
    assert captured["payload"]["requests"][1]["taskType"] == "RETRIEVAL_DOCUMENT"



def test_upload_rejects_spoofed_image_content(monkeypatch):
    response = client.post(
        "/images/upload",
        files={"file": ("fake.png", b"this is not a PNG", "image/png")},
    )
    assert response.status_code == 415
    assert "does not match" in response.json()["detail"]
