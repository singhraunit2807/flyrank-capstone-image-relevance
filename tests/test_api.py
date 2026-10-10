from fastapi.testclient import TestClient

from app.main import app, IMAGES, SUGGESTIONS, REVIEWS


client = TestClient(app)


def setup_function() -> None:
    IMAGES.clear()
    SUGGESTIONS.clear()
    REVIEWS.clear()


def seed() -> None:
    response = client.post("/demo/seed")
    assert response.status_code == 200


def test_health_and_seed_catalogue() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    seed()
    catalogue = client.get("/images")
    assert catalogue.status_code == 200
    assert catalogue.json()["count"] >= 10


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

    invalid = client.post(
        "/images/analyze",
        json={"subject": "fox", "category": "animal", "caption": "fox", "confidence": 1.5},
    )
    assert invalid.status_code == 422


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
    response = client.get(
        "/posts/fox-post/images",
        params={"text": "The behavior of red foxes", "threshold": 0.0},
    )
    assert response.status_code == 200
    ranked = response.json()["ranked"]
    assert ranked[0]["decision"] == "rejected"
    assert "expected fox" in ranked[0]["reason"].lower()
    assert response.json()["suggestion"] is None


def test_seeded_catalogue_returns_fox_and_rejects_wolf() -> None:
    seed()
    response = client.post(
        "/posts/fox-post/match",
        json={"post_id": "fox-post", "text": "The behavior of red foxes", "threshold": 0.10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["suggestion"] is not None
    assert data["suggestion"]["image_id"].startswith("fox-")
    wolf_results = [item for item in data["ranked"] if item["image_id"].startswith("wolf-")]
    assert wolf_results
    assert all(item["decision"] == "rejected" for item in wolf_results)


def test_review_approve_and_explanation() -> None:
    seed()
    response = client.get("/posts/fox-post/images", params={"text": "red fox", "threshold": 0.0})
    suggestion_id = response.json()["ranked"][0]["suggestion_id"]

    explanation = client.get(f"/review/{suggestion_id}/why")
    assert explanation.status_code == 200

    approved = client.post(f"/review/{suggestion_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    explanation = client.get(f"/review/{suggestion_id}/why")
    assert explanation.json()["review_status"] == "approved"


def test_post_id_mismatch_returns_400() -> None:
    response = client.post(
        "/posts/path-id/match",
        json={"post_id": "body-id", "text": "red fox"},
    )
    assert response.status_code == 400
