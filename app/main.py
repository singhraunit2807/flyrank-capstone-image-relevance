from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .core import Image, Suggestion, rank_images

app = FastAPI(title="FlyRank Image Relevance API", version="0.1.0")

IMAGES: list[Image] = []
SUGGESTIONS: dict[str, Suggestion] = {}


class AnalyzeRequest(BaseModel):
    subject: str = Field(min_length=1)
    category: str = Field(min_length=1)
    attributes: list[str] = []
    caption: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class PostRequest(BaseModel):
    post_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    threshold: float = Field(default=0.20, ge=0, le=1)


class ReviewResponse(BaseModel):
    suggestion_id: str
    status: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/images/analyze")
def analyze_image(request: AnalyzeRequest) -> dict:
    """Accept validated structured vision output and store it in memory."""
    image = Image(
        id=f"img-{len(IMAGES) + 1}",
        subject=request.subject,
        category=request.category,
        attributes=tuple(request.attributes),
        caption=request.caption,
        confidence=request.confidence,
    )
    IMAGES.append(image)
    return {"id": image.id, "metadata": image.__dict__}


@app.post("/posts/{post_id}/match")
def match_post(post_id: str, request: PostRequest) -> dict:
    if request.post_id != post_id:
        raise HTTPException(status_code=400, detail="post_id mismatch")
    ranked = rank_images(request.text, IMAGES, request.threshold)
    for item in ranked:
        SUGGESTIONS[f"{post_id}:{item.image_id}"] = item
    accepted = next((item for item in ranked if item.decision == "accepted"), None)
    return {
        "post_id": post_id,
        "suggestion": accepted.__dict__ if accepted else None,
        "ranked": [item.__dict__ for item in ranked],
        "message": "No confident match" if accepted is None else "Match found",
    }


@app.get("/posts/{post_id}/images")
def get_ranked_images(post_id: str, text: str, threshold: float = 0.20) -> dict:
    ranked = rank_images(text, IMAGES, threshold)
    for item in ranked:
        SUGGESTIONS[f"{post_id}:{item.image_id}"] = item
    return {"post_id": post_id, "ranked": [item.__dict__ for item in ranked]}


@app.get("/review/{suggestion_id}/why")
def why(suggestion_id: str) -> dict:
    item = SUGGESTIONS.get(suggestion_id)
    if not item:
        raise HTTPException(status_code=404, detail="suggestion not found")
    return {"suggestion_id": suggestion_id, "decision": item.decision, "reason": item.reason, "score": item.score}


@app.post("/review/{suggestion_id}/approve", response_model=ReviewResponse)
def approve(suggestion_id: str) -> ReviewResponse:
    if suggestion_id not in SUGGESTIONS:
        raise HTTPException(status_code=404, detail="suggestion not found")
    return ReviewResponse(suggestion_id=suggestion_id, status="approved")


@app.post("/review/{suggestion_id}/reject", response_model=ReviewResponse)
def reject(suggestion_id: str) -> ReviewResponse:
    if suggestion_id not in SUGGESTIONS:
        raise HTTPException(status_code=404, detail="suggestion not found")
    return ReviewResponse(suggestion_id=suggestion_id, status="rejected")
