from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .core import Image, Suggestion, rank_images

IMAGES: list[Image] = []
SUGGESTIONS: dict[str, Suggestion] = {}
REVIEWS: dict[str, str] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not IMAGES:
        from .seed import seed
        seed()
    yield


app = FastAPI(
    title="FlyRank AI Image Relevance API",
    description="Offline-capable demo API for image metadata, relevance ranking, mismatch guards, and human review.",
    version="1.0.0",
    lifespan=lifespan,
)


class AnalyzeRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=100)
    attributes: list[str] = Field(default_factory=list, max_length=30)
    caption: str = Field(min_length=1, max_length=1000)
    confidence: float = Field(ge=0, le=1)


class PostRequest(BaseModel):
    post_id: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=1, max_length=2000)
    threshold: float = Field(default=0.20, ge=0, le=1)


class ReviewResponse(BaseModel):
    suggestion_id: str
    status: str


def _suggestion_id(post_id: str, image_id: str) -> str:
    return f"{post_id}:{image_id}"


def _as_result(post_id: str, item: Suggestion) -> dict[str, Any]:
    suggestion_id = _suggestion_id(post_id, item.image_id)
    return {
        "suggestion_id": suggestion_id,
        "image_id": item.image_id,
        "score": round(item.score, 4),
        "decision": item.decision,
        "reason": item.reason,
        "review_status": REVIEWS.get(suggestion_id, "pending"),
    }


def _rank(post_id: str, text: str, threshold: float) -> list[dict[str, Any]]:
    ranked = rank_images(text, IMAGES, threshold)
    for item in ranked:
        SUGGESTIONS[_suggestion_id(post_id, item.image_id)] = item
    return [_as_result(post_id, item) for item in ranked]


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "FlyRank AI Image Relevance API", "docs": "/docs", "health": "/health"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "catalogue": "ready" if IMAGES else "empty"}


@app.get("/images")
def list_images() -> dict[str, Any]:
    return {"count": len(IMAGES), "images": [image.__dict__ for image in IMAGES]}


@app.post("/demo/seed")
def seed_demo() -> dict[str, Any]:
    from .seed import seed
    count = seed()
    SUGGESTIONS.clear()
    REVIEWS.clear()
    return {"status": "seeded", "count": count, "message": "Demo catalogue reset successfully."}


@app.post("/images/analyze")
def analyze_image(request: AnalyzeRequest) -> dict[str, Any]:
    """Store validated metadata supplied by a vision model or a human annotator.

    This endpoint does not upload or inspect raw image files; callers provide
    structured image metadata and confidence explicitly.
    """
    image_id = f"img-{len(IMAGES) + 1}"
    image = Image(
        id=image_id,
        subject=request.subject.strip(),
        category=request.category.strip(),
        attributes=tuple(attribute.strip() for attribute in request.attributes if attribute.strip()),
        caption=request.caption.strip(),
        confidence=request.confidence,
    )
    IMAGES.append(image)
    return {"id": image.id, "metadata": image.__dict__}


@app.post("/posts/{post_id}/match")
def match_post(post_id: str, request: PostRequest) -> dict[str, Any]:
    if request.post_id != post_id:
        raise HTTPException(status_code=400, detail="post_id mismatch")
    ranked = _rank(post_id, request.text, request.threshold)
    accepted = next((item for item in ranked if item["decision"] == "accepted"), None)
    return {
        "post_id": post_id,
        "suggestion": accepted,
        "ranked": ranked,
        "message": "Match found" if accepted else "No confident match",
    }


@app.get("/posts/{post_id}/images")
def get_ranked_images(
    post_id: str,
    text: str = Query(min_length=1, max_length=2000),
    threshold: float = Query(default=0.20, ge=0, le=1),
) -> dict[str, Any]:
    ranked = _rank(post_id, text, threshold)
    accepted = next((item for item in ranked if item["decision"] == "accepted"), None)
    return {
        "post_id": post_id,
        "suggestion": accepted,
        "ranked": ranked,
        "message": "Match found" if accepted else "No confident match",
    }


@app.get("/review/{suggestion_id:path}/why")
def why(suggestion_id: str) -> dict[str, Any]:
    item = SUGGESTIONS.get(suggestion_id)
    if not item:
        raise HTTPException(status_code=404, detail="suggestion not found; run a match first")
    return {
        "suggestion_id": suggestion_id,
        "decision": item.decision,
        "reason": item.reason,
        "score": round(item.score, 4),
        "review_status": REVIEWS.get(suggestion_id, "pending"),
    }


@app.post("/review/{suggestion_id:path}/approve", response_model=ReviewResponse)
def approve(suggestion_id: str) -> ReviewResponse:
    if suggestion_id not in SUGGESTIONS:
        raise HTTPException(status_code=404, detail="suggestion not found; run a match first")
    REVIEWS[suggestion_id] = "approved"
    return ReviewResponse(suggestion_id=suggestion_id, status="approved")


@app.post("/review/{suggestion_id:path}/reject", response_model=ReviewResponse)
def reject(suggestion_id: str) -> ReviewResponse:
    if suggestion_id not in SUGGESTIONS:
        raise HTTPException(status_code=404, detail="suggestion not found; run a match first")
    REVIEWS[suggestion_id] = "rejected"
    return ReviewResponse(suggestion_id=suggestion_id, status="rejected")
