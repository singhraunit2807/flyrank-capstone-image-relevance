from fastapi.testclient import TestClient

from app.main import app, IMAGES, SUGGESTIONS


client = TestClient(app)


def setup_function() -> None:
    IMAGES.clear()
    SUGGESTIONS.clear()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_validates_confidence_range() -> None:
    response = client.post(
        "/images/analyze",
        json={
            "subject": "red fox",
            "category": "animal",
            "attributes": ["orange fur", "forest"],
            "caption": "A red fox in a forest",
            "confidence": 0.94,
        },
    )
    assert response.status_code == 200
    assert response.json()["metadata"]["confidence"] == 0.94


def test_mismatch_guard_rejects_wolf_for_fox_post() -> None:
    client.post(
        "/images/analyze",
        json={
            "subject": "wolf",
            "category": "animal",
            "attributes": ["gray fur", "forest"],
            "caption": "A gray wolf in a forest",
            "confidence": 0.95,
        },
    )
    response = client.get("/posts/fox-post/images", params={"text": "The behavior of red foxes"})
    assert response.status_code == 200
    assert response.json()["ranked"][0]["decision"] == "rejected"
    assert "expected fox" in response.json()["ranked"][0]["reason"].lower()
